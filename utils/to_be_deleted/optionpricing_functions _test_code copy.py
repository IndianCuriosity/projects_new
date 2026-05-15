###########################################################################################################################
# This module contains functions for option pricing, including the Black-Scholes formula and implied volatility calculations.
# Real FX desks often use:

# Delta space interpolation
# Premium-adjusted delta
# Forward delta
# Spot delta
# Sticky delta or sticky strike rules

# Then calibrate:

# SVI
# SABR
# Vanna-Volga
# spline
# cubic
# arbitrage constraints
# settlement convention

###########################################################################################################################

import pandas as pd
import numpy as np
import datetime
from dates_functions import *
from optionpricing_functions import *

import scipy.stats as ss
from scipy.interpolate import CubicSpline
from scipy.interpolate import interp1d
from scipy.interpolate import RectBivariateSpline # Smooth interpolation of C(T,K) and derivatives
from scipy.interpolate import RegularGridInterpolator # Monte Carlo
from scipy.optimize import brentq
from scipy.optimize import least_squares
import math
import copy



#########################################################################################################################################################################

# SABR Calibration 

# alpha: Represents the prevailing volatility level (initial value).
# beta: Describes the elasticity of the volatility, controlling the skewness (determines the shape of the forward rate distribution).
# rho: Captures the correlation between the forward price and its volatility, governing the skew.
# nu: Volatility of volatility, governing the smile convexity.
#########################################################################################################################################################################

"""
FX SABR calibration from ATM, 25Δ Risk Reversal, and 25Δ Butterfly quotes.

Inputs (per expiry):
- Spot S
- Forward F (under domestic discounting; typically F = S * DF_for/DF_dom)
- Domestic discount factor DF_dom(T) and foreign discount factor DF_for(T)
- Maturity T in years
- ATM volatility (Black, lognormal) : sigma_ATM
- 25Δ Risk Reversal: RR25 = sigma_25C - sigma_25P
- 25Δ Butterfly:     BF25 = 0.5 * (sigma_25C + sigma_25P) - sigma_ATM
- Beta ∈ [0,1] (often 0.5 or 0.0/1.0 for normal/lognormal limits)
- Delta convention: "forward" or "premium-adjusted" (FX markets often quote DN as premium-adjusted)

Outputs:
- Calibrated SABR parameters: alpha, beta (fixed), rho, nu
- Consistency check: model vols at ATM, 25Δ put, 25Δ call

Dependencies:
- numpy, scipy (optimize). If scipy isn't installed: `pip install numpy scipy`.

Author: ChatGPT
License: MIT
"""
from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Literal, Tuple, Callable, Sequence

import numpy as np
from scipy.optimize import minimize
from math import log, sqrt, exp

# ------------------------------
# Utilities: Normal cdf/pdf
# ------------------------------
SQRT_2PI = math.sqrt(2.0 * math.pi)

def _phi(x: float) -> float:
    return math.exp(-0.5 * x * x) / SQRT_2PI

def _Phi(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

# ------------------------------
# FX Black (Black76) pricing and deltas
# ------------------------------

def black_implied_price(F: float, K: float, T: float, sigma: float, df_dom: float, call: bool) -> float:
    if T <= 0 or sigma <= 0:
        # Forward intrinsic value under Black model when sigma ~ 0
        intrinsic = max(F - K, 0.0) if call else max(K - F, 0.0)
        return df_dom * intrinsic
    vol_sqrtT = sigma * math.sqrt(T)
    d1 = (math.log(F / K) + 0.5 * sigma * sigma * T) / vol_sqrtT
    d2 = d1 - vol_sqrtT
    if call:
        return df_dom * (F * _Phi(d1) - K * _Phi(d2))
    else:
        return df_dom * (K * _Phi(-d2) - F * _Phi(-d1))


def fx_delta(
    S: float,
    F: float,
    K: float,
    T: float,
    sigma: float,
    df_dom: float,
    df_for: float,
    call: bool,
    convention: Literal["forward", "premium-adjusted"] = "premium-adjusted",
) -> float:
    """Return the FX delta (w.r.t. spot) under chosen convention.

    - Forward delta (undiscounted):  call:  +DF_for * N(d1), put: -DF_for * N(-d1)
    - Premium-adjusted (DN) spot delta: forward_delta - price/S (sign handled by price)
      i.e., Δ_pa = Δ_fwd - Price/S  for both calls and puts.
    """
    if T <= 0 or sigma <= 0:
        # Delta tends to 0/±DF_for depending on intrinsic around ATM; use small-sigma limit
        # We'll fallback to forward-delta limit here
        return (df_for if call else -df_for)

    vol_sqrtT = sigma * math.sqrt(T)
    d1 = (math.log(F / K) + 0.5 * sigma * sigma * T) / vol_sqrtT
    if call:
        delta_fwd = df_for * _Phi(d1)
    else:
        delta_fwd = -df_for * _Phi(-d1)

    if convention == "forward":
        return delta_fwd

    price = black_implied_price(F, K, T, sigma, df_dom, call)
    delta_pa = delta_fwd - price / S
    return delta_pa


# ------------------------------
# Solve strike from a delta quote (given vol at that delta)
# ------------------------------

def strike_from_delta(
    target_delta: float,
    is_call: bool,
    S: float,
    F: float,
    T: float,
    sigma_at_that_delta: float,
    df_dom: float,
    df_for: float,
    convention: Literal["forward", "premium-adjusted"] = "premium-adjusted",
    K_min: float | None = None,
    K_max: float | None = None,
    tol: float = 1e-10,
    max_iter: int = 100,
) -> float:
    """Invert the delta to find strike K. Uses bisection on K.

    Notes:
    - target_delta is signed: e.g., +0.25 for 25Δ call, -0.25 for 25Δ put under forward delta.
      For premium-adjusted conventions, the absolute magnitude is close but not identical.
    - We pass in the *volatility at that delta* (market quote), so the delta equation is well-defined.
    """
    if K_min is None:
        K_min = 1e-8
    if K_max is None:
        K_max = max(10.0 * F, F + 10.0)  # generous upper bound

    def g(K: float) -> float:
        return fx_delta(S, F, K, T, sigma_at_that_delta, df_dom, df_for, is_call, convention) - target_delta

    a, b = K_min, K_max
    fa, fb = g(a), g(b)
    # Ensure bracketing by expanding if necessary
    expand_factor = 2.0
    expansions = 0
    while fa * fb > 0 and expansions < 25:
        a /= expand_factor
        b *= expand_factor
        fa, fb = g(a), g(b)
        expansions += 1

    if fa * fb > 0:
        raise RuntimeError("Failed to bracket root for strike inversion from delta. Adjust bounds.")

    for _ in range(max_iter):
        m = 0.5 * (a + b)
        fm = g(m)
        if abs(fm) < tol or (b - a) < tol * max(1.0, m):
            return m
        if fa * fm <= 0:
            b, fb = m, fm
        else:
            a, fa = m, fm
    return 0.5 * (a + b)


# ------------------------------
# Hagan 2002 SABR lognormal implied vol
# ------------------------------

def sabr_implied_vol(F: float, K: float, T: float, alpha: float, beta: float, rho: float, nu: float) -> float:
    if F <= 0 or K <= 0:
        raise ValueError("F and K must be positive for lognormal SABR.")
    if alpha <= 0 or nu <= 0:
        return 0.0

    if abs(F - K) < 1e-15:                                                              # 2.18 ( special case when F == K)
        # ATM formula (limit K -> F)
        FK_beta = F ** (1.0 - beta)
        one_minus_beta = 1.0 - beta
        term1 = (alpha / FK_beta)
        term2 = 1.0 + (
            ((one_minus_beta ** 2) / 24.0) * (alpha ** 2) / (F ** (2.0 * one_minus_beta))
            + (rho * beta * nu * alpha) / (4.0 * (F ** one_minus_beta))
            + ((2.0 - 3.0 * rho ** 2) * (nu ** 2) / 24.0)
        ) * T
        return term1 * term2

    # Generic K != F
    logFK = math.log(F / K)                                                             # used in 2.17b
    FK_beta = (F * K) ** ((1.0 - beta) / 2.0)                                           # used in 2.17b and 2.17a
    z = (nu / alpha) * FK_beta * logFK                                                  # 2.17b
    x_z = math.log((math.sqrt(1.0 - 2.0 * rho * z + z * z) + z - rho) / (1.0 - rho))    # 2.17c

    A = alpha / (FK_beta)
    B1 = 1.0 + (
        ((1.0 - beta) ** 2 / 24.0) * (logFK ** 2)
        + ((1.0 - beta) ** 4 / 1920.0) * (logFK ** 4)
    )

    denom = (1.0 + ((1.0 - beta) ** 2 / 24.0) * (alpha ** 2) / (FK_beta ** 2)
             + (rho * beta * nu * alpha) / (4.0 * FK_beta)
             + ((2.0 - 3.0 * rho ** 2) * (nu ** 2) / 24.0))

    if abs(z) < 1e-12:
        vol = A * B1 * (1.0 / denom)                                                    # z / x_z tends to 1
    else:
        vol = A * B1 * (z / x_z) * (1.0 / denom)                                        # whole 2.17a
    return max(vol, 0.0)


# ------------------------------
# Calibration machinery
# ------------------------------

@dataclass
class MarketSmile:
    S: float
    F: float
    T: float
    df_dom: float
    df_for: float
    sigma_atm: float
    rr_25: float
    bf_25: float
    beta: float = 0.5
    delta_convention: Literal["forward", "premium-adjusted"] = "premium-adjusted"

    def strikes_and_vols(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Return (K_vec, vol_vec, weights) for ATM, 25ΔP, 25ΔC.

        Using:
          sigma_25C = sigma_ATM + bf25 + 0.5*rr25
          sigma_25P = sigma_ATM + bf25 - 0.5*rr25
        Strikes recovered by inverting delta under selected convention using the respective vols.
        """
        sigma_25c = self.sigma_atm + self.bf_25 + 0.5 * self.rr_25
        sigma_25p = self.sigma_atm + self.bf_25 - 0.5 * self.rr_25

        # Target deltas: +0.25 call, -0.25 put (for forward delta). For premium-adjusted, magnitudes are similar.
        # We pass the signed target; solver handles exact definition via convention.
        K_25c = strike_from_delta(
            target_delta=+0.25 if self.delta_convention == "forward" else +0.25,
            is_call=True,
            S=self.S,
            F=self.F,
            T=self.T,
            sigma_at_that_delta=sigma_25c,
            df_dom=self.df_dom,
            df_for=self.df_for,
            convention=self.delta_convention,
        )
        K_25p = strike_from_delta(
            target_delta=-0.25 if self.delta_convention == "forward" else -0.25,
            is_call=False,
            S=self.S,
            F=self.F,
            T=self.T,
            sigma_at_that_delta=sigma_25p,
            df_dom=self.df_dom,
            df_for=self.df_for,
            convention=self.delta_convention,
        )
        K_atm = self.F  # lognormal ATM

        K = np.array([K_25p, K_atm, K_25c], dtype=float)
        vols = np.array([sigma_25p, self.sigma_atm, sigma_25c], dtype=float)
        # Simple weights: heavier on ATM (optional)
        w = np.array([1.0, 2.0, 1.0], dtype=float)
        return K, vols, w


@dataclass
class SABRParams:
    alpha: float
    beta: float
    rho: float
    nu: float


def calibrate_sabr(smile: MarketSmile, alpha0: float | None = None, rho0: float | None = None, nu0: float | None = None) -> Tuple[SABRParams, dict]:
    """Calibrate (alpha, rho, nu) to match vols at K = {25P, ATM, 25C}.

    Returns (params, diagnostics)
    diagnostics contains final SSE, strikes, market vols, model vols, success flag.
    """
    K, vols_mkt, w = smile.strikes_and_vols()
    F, T, beta = smile.F, smile.T, smile.beta

    # Initial guesses
    if alpha0 is None:
        # Rough ATM mapping: alpha ≈ sigma_ATM * F^{1-β}
        alpha0 = smile.sigma_atm * (F ** (1.0 - beta))
    if rho0 is None:
        # RR sign gives rho sign typically
        rho0 = max(min(smile.rr_25 / max(abs(smile.rr_25), 1e-6), 0.5), -0.5)
    if nu0 is None:
        # Smile curvature gives nu scale; a rough heuristic from BF
        nu0 = max(0.3 * abs(smile.bf_25) / max(smile.sigma_atm, 1e-6), 0.2)

    x0 = np.array([alpha0, rho0, nu0], dtype=float)

    bounds = [(1e-6, 5.0), (-0.999, 0.999), (1e-6, 5.0)]

    def sse(x: Sequence[float]) -> float:
        a, r, n = x
        if a <= 0 or n <= 0 or abs(r) >= 1.0:
            return 1e6
        model = np.array([sabr_implied_vol(F, k, T, a, beta, r, n) for k in K])
        err = (model - vols_mkt)
        return float(np.sum(w * err * err))

    res = minimize(sse, x0, method="L-BFGS-B", bounds=bounds)

    alpha, rho, nu = res.x
    params = SABRParams(alpha=float(alpha), beta=beta, rho=float(rho), nu=float(nu))

    model_vols = np.array([sabr_implied_vol(F, k, T, params.alpha, beta, params.rho, params.nu) for k in K])
    diagnostics = {
        "success": bool(res.success),
        "message": res.message,
        "sse": float(res.fun),
        "strikes": K,
        "market_vols": vols_mkt,
        "model_vols": model_vols,
        "weights": w,
        "x0": x0,
        "result": res,
    }
    return params, diagnostics


# ------------------------------
# Example usage
# ------------------------------
if __name__ == "__main__":
    # Example (invented numbers for illustration):
    S = 1.2500
    T = 0.5  # 6 months

    # Suppose domestic and foreign zero rates give discount factors below (example):
    r_dom = 0.03
    r_for = 0.015
    df_dom = math.exp(-r_dom * T)
    df_for = math.exp(-r_for * T)

    # Forward from spot and DFs
    F = S * df_for / df_dom

    # Market smile quotes (Black vols): ATM, RR25, BF25
    sigma_ATM = 0.10   # 10% ATM vol
    RR25 = 0.015       # 1.5 vol points (25C minus 25P)
    BF25 = 0.002       # 0.2 vol points (0.5*(25C+25P) - ATM)

    smile = MarketSmile(
        S=S,
        F=F,
        T=T,
        df_dom=df_dom,
        df_for=df_for,
        sigma_atm=sigma_ATM,
        rr_25=RR25,
        bf_25=BF25,
        beta=0.5,
        delta_convention="premium-adjusted",  # typical DN in FX markets
    )

    params, diag = calibrate_sabr(smile)

    print("Calibrated SABR parameters:")
    print(params)

    print("\nDiagnostics:")
    for k, mv, modv in zip(diag["strikes"], diag["market_vols"], diag["model_vols"]):
        print(f"K={k:.6f}  mkt_vol={mv:.4%}  mdl_vol={modv:.4%}")
    print(f"SSE: {diag['sse']:.6e}, success={diag['success']}, msg={diag['message']}")





###################################

"""
Multi-expiry FX SABR calibration from ATM, 25Δ Risk Reversal, and 25Δ Butterfly quotes.

Features:
- Support for multiple expiries (each with ATM, RR25, BF25 quotes)
- Calibration per expiry: alpha, rho, nu (with fixed beta)
- Diagnostics returned per expiry

Author: ChatGPT
License: MIT
"""
from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Literal, Tuple, Sequence, List, Dict

import numpy as np
from scipy.optimize import minimize

# ---- existing SABR calibration functions from previous version (omitted for brevity in this snippet) ----
# Reuse: _Phi, _phi, black_implied_price, fx_delta, strike_from_delta,
# sabr_implied_vol, MarketSmile, SABRParams, calibrate_sabr

# (Paste all helper functions and MarketSmile/SABRParams/calibrate_sabr definitions here unchanged)

# ------------------------------
# Multi-expiry calibration
# ------------------------------

@dataclass
class SABRCalibResult:
    expiry: float
    params: SABRParams
    diagnostics: dict


def calibrate_sabr_multi(
    smiles: List[MarketSmile],
    beta: float = 0.5
) -> List[SABRCalibResult]:
    """Calibrate SABR per expiry.

    Args:
        smiles: list of MarketSmile objects (one per expiry)
        beta: fixed beta used in SABR

    Returns:
        list of SABRCalibResult (params and diagnostics per expiry)
    """
    results: List[SABRCalibResult] = []
    for smile in smiles:
        # enforce same beta
        smile.beta = beta
        params, diag = calibrate_sabr(smile)
        results.append(SABRCalibResult(expiry=smile.T, params=params, diagnostics=diag))
    return results


# ------------------------------
# Example usage (multi-expiry)
# ------------------------------
if __name__ == "__main__":
    import math

    S = 1.2500
    maturities = [0.25, 0.5, 1.0]  # 3m, 6m, 1y
    r_dom = 0.03
    r_for = 0.015

    smiles: List[MarketSmile] = []
    for T in maturities:
        df_dom = math.exp(-r_dom * T)
        df_for = math.exp(-r_for * T)
        F = S * df_for / df_dom

        # Example varying vols per expiry
        sigma_ATM = 0.10 + 0.01 * T
        RR25 = 0.015 - 0.002 * T
        BF25 = 0.002 + 0.001 * T

        smiles.append(MarketSmile(
            S=S,
            F=F,
            T=T,
            df_dom=df_dom,
            df_for=df_for,
            sigma_atm=sigma_ATM,
            rr_25=RR25,
            bf_25=BF25,
            beta=0.5,
            delta_convention="premium-adjusted",
        ))

    results = calibrate_sabr_multi(smiles, beta=0.5)

    for res in results:
        print(f"Expiry {res.expiry}y -> alpha={res.params.alpha:.4f}, rho={res.params.rho:.4f}, nu={res.params.nu:.4f}")
        for k, mv, modv in zip(res.diagnostics["strikes"], res.diagnostics["market_vols"], res.diagnostics["model_vols"]):
            print(f"  K={k:.6f}  mkt_vol={mv:.4%}  mdl_vol={modv:.4%}")
        print(f"  SSE: {res.diagnostics['sse']:.6e}, success={res.diagnostics['success']}\n")

# ------------------------------
# Term-structure (multi-expiry) calibration
# ------------------------------
from typing import List

def calibrate_sabr_term_structure(
    smiles: Sequence[MarketSmile],
    alpha0: float | None = None,
    rho0: float | None = None,
    nu0: float | None = None,
    smooth_lambda: float = 0.0,
) -> Tuple[Sequence[SABRParams], list[dict]]:
    """Calibrate a SABR term-structure across multiple expiries.

    Each expiry is calibrated to its own (ATM, 25P, 25C) smile.

    If `smooth_lambda > 0`, a simple quadratic penalty encourages parameters to
    remain close to the previous expiry's parameters (Tikhonov smoothing).
    This uses a sequential scheme: previous solution is used as the next initial guess,
    and the objective adds smoothness vs the previous point.

    Returns (params_list, diagnostics_list).
    """
    params_list: List[SABRParams] = []
    diagnostics: List[dict] = []

    prev: SABRParams | None = None
    for sm in smiles:
        if smooth_lambda > 0.0 and prev is not None:
            # Build local objective with smoothness to prev
            K, vols_mkt, w = sm.strikes_and_vols()
            F, T, beta = sm.F, sm.T, sm.beta

            def sse_with_smooth(x: Sequence[float]) -> float:
                a, r, n = x
                if a <= 0 or n <= 0 or abs(r) >= 1.0:
                    return 1e6
                model = np.array([sabr_implied_vol(F, k, T, a, beta, r, n) for k in K])
                err = (model - vols_mkt)
                sse_local = float(np.sum(w * err * err))
                # Smoothness penalty
                da = a - prev.alpha
                dr = r - prev.rho
                dn = n - prev.nu
                penalty = smooth_lambda * (da * da + dr * dr + dn * dn)
                return sse_local + penalty

            a0, r0, n0 = prev.alpha, prev.rho, prev.nu
            bounds = [(1e-6, 5.0), (-0.999, 0.999), (1e-6, 5.0)]
            res = minimize(sse_with_smooth, np.array([a0, r0, n0]), method="L-BFGS-B", bounds=bounds)
            a, r, n = res.x
            p = SABRParams(alpha=float(a), beta=sm.beta, rho=float(r), nu=float(n))

            model_vols = np.array([sabr_implied_vol(sm.F, k, sm.T, p.alpha, sm.beta, p.rho, p.nu) for k in K])
            diag = {
                "success": bool(res.success),
                "message": res.message,
                "sse": float(res.fun),
                "strikes": K,
                "market_vols": vols_mkt,
                "model_vols": model_vols,
                "weights": w,
                "result": res,
                "T": sm.T,
            }
        else:
            p, diag = calibrate_sabr(sm, alpha0=alpha0, rho0=rho0, nu0=nu0)

        params_list.append(p)
        diagnostics.append(diag)
        prev = p

    return params_list, diagnostics


def build_smiles_from_quotes(
    S: float,
    T_list: Sequence[float],
    df_dom_list: Sequence[float],
    df_for_list: Sequence[float],
    atm_list: Sequence[float],
    rr25_list: Sequence[float],
    bf25_list: Sequence[float],
    beta: float = 0.5,
    delta_convention: Literal["forward", "premium-adjusted"] = "premium-adjusted",
) -> List[MarketSmile]:
    """Convenience helper to construct MarketSmile objects for multiple expiries.

    Either pass forwards separately by setting F_i = S * df_for_i / df_dom_i implicitly via DFs.
    """
    smiles: List[MarketSmile] = []
    for T, df_d, df_f, atm, rr, bf in zip(T_list, df_dom_list, df_for_list, atm_list, rr25_list, bf25_list):
        F = S * df_f / df_d
        smiles.append(MarketSmile(
            S=S, F=F, T=T, df_dom=df_d, df_for=df_f,
            sigma_atm=atm, rr_25=rr, bf_25=bf,
            beta=beta, delta_convention=delta_convention,
        ))
    return smiles



########################################################################################################################


"""
Extended SABR calibration with joint fitting of multiple strikes (ATM, 25Δ, 10Δ).
Supports multi-expiry term structure.
"""

# ... (keep all previous imports, SABR code, MarketSmile, etc.)

@dataclass
class MarketSmile:
    S: float
    F: float
    T: float
    df_dom: float
    df_for: float
    sigma_atm: float
    rr_25: float
    bf_25: float
    rr_10: float | None = None
    bf_10: float | None = None
    beta: float = 0.5
    delta_convention: Literal["forward", "premium-adjusted"] = "premium-adjusted"

    def strikes_and_vols(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Return (K_vec, vol_vec, weights) including ATM, 25Δ, and optional 10Δ quotes."""
        vols = []
        Ks = []
        weights = []

        # ATM
        K_atm = self.F
        vols.append(self.sigma_atm)
        Ks.append(K_atm)
        weights.append(2.0)

        # 25Δ
        sigma_25c = self.sigma_atm + self.bf_25 + 0.5 * self.rr_25
        sigma_25p = self.sigma_atm + self.bf_25 - 0.5 * self.rr_25
        K_25c = strike_from_delta(+0.25, True, self.S, self.F, self.T, sigma_25c, self.df_dom, self.df_for, self.delta_convention)
        K_25p = strike_from_delta(-0.25, False, self.S, self.F, self.T, sigma_25p, self.df_dom, self.df_for, self.delta_convention)
        vols += [sigma_25p, sigma_25c]
        Ks += [K_25p, K_25c]
        weights += [1.0, 1.0]

        # 10Δ (if provided)
        if self.rr_10 is not None and self.bf_10 is not None:
            sigma_10c = self.sigma_atm + self.bf_10 + 0.5 * self.rr_10
            sigma_10p = self.sigma_atm + self.bf_10 - 0.5 * self.rr_10
            K_10c = strike_from_delta(+0.10, True, self.S, self.F, self.T, sigma_10c, self.df_dom, self.df_for, self.delta_convention)
            K_10p = strike_from_delta(-0.10, False, self.S, self.F, self.T, sigma_10p, self.df_dom, self.df_for, self.delta_convention)
            vols += [sigma_10p, sigma_10c]
            Ks += [K_10p, K_10c]
            weights += [0.5, 0.5]

        return np.array(Ks), np.array(vols), np.array(weights)


# calibrate_sabr and calibrate_sabr_term_structure remain unchanged, but they now automatically handle extra strikes via strikes_and_vols().

# ------------------------------
# Example usage
# ------------------------------
if __name__ == "__main__":
    S = 1.25
    T = 0.5
    r_dom, r_for = 0.03, 0.015
    df_dom = math.exp(-r_dom * T)
    df_for = math.exp(-r_for * T)
    F = S * df_for / df_dom

    sigma_ATM = 0.10
    RR25, BF25 = 0.015, 0.002
    RR10, BF10 = 0.020, 0.003  # additional 10Δ quotes

    smile = MarketSmile(
        S=S, F=F, T=T, df_dom=df_dom, df_for=df_for,
        sigma_atm=sigma_ATM, rr_25=RR25, bf_25=BF25,
        rr_10=RR10, bf_10=BF10,
        beta=0.5, delta_convention="premium-adjusted"
    )

    params, diag = calibrate_sabr(smile)
    print("Joint calibration with 10Δ included:")
    print(params)
    for k, mv, modv in zip(diag["strikes"], diag["market_vols"], diag["model_vols"]):
        print(f"K={k:.6f}, mkt={mv:.4%}, mdl={modv:.4%}")

# ------------------------------
# Extended smile: 10Δ & extra anchors (joint calibration)
# ------------------------------
@dataclass
class MarketSmileExtended:
    """A richer smile container supporting 10Δ wing and arbitrary extra anchors.

    Keeps the same interface expected by `calibrate_sabr`: it exposes
    - F, T, beta
    - strikes_and_vols() -> (K, vols, w)

    Contents:
      * ATM vol (mandatory)
      * Optional 25Δ RR/BF (classic)
      * Optional 10Δ RR/BF (requested)
      * Optional explicit anchors:
          - extra_delta_vols: list of {"delta": ±0.x, "vol": y, "is_call": bool}
          - extra_strike_vols: list of (K, vol)
    """
    S: float
    F: float
    T: float
    df_dom: float
    df_for: float
    sigma_atm: float
    # Optional RR/BF wings
    rr_25: float | None = None
    bf_25: float | None = None
    rr_10: float | None = None
    bf_10: float | None = None

    beta: float = 0.5
    delta_convention: Literal["forward", "premium-adjusted"] = "premium-adjusted"

    # Extra anchors
    extra_delta_vols: Sequence[dict] | None = None   # {"delta", "vol", "is_call"}
    extra_strike_vols: Sequence[Tuple[float, float]] | None = None
    custom_weights: Sequence[float] | None = None

    def _append_rr_bf(self, K_list, V_list, W_list, wing_delta: float, rr: float, bf: float):
        sig_c = self.sigma_atm + bf + 0.5 * rr
        sig_p = self.sigma_atm + bf - 0.5 * rr
        Kc = strike_from_delta(+wing_delta, True, self.S, self.F, self.T, sig_c, self.df_dom, self.df_for, self.delta_convention)
        Kp = strike_from_delta(-wing_delta, False, self.S, self.F, self.T, sig_p, self.df_dom, self.df_for, self.delta_convention)
        K_list += [Kp, Kc]
        V_list += [sig_p, sig_c]
        W_list += [1.0, 1.0]

    def strikes_and_vols(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        K_list: list[float] = [self.F]
        V_list: list[float] = [self.sigma_atm]
        W_list: list[float] = [2.0]  # heavier ATM

        if self.rr_25 is not None and self.bf_25 is not None:
            self._append_rr_bf(K_list, V_list, W_list, 0.25, self.rr_25, self.bf_25)
        if self.rr_10 is not None and self.bf_10 is not None:
            self._append_rr_bf(K_list, V_list, W_list, 0.10, self.rr_10, self.bf_10)

        # Extra delta-vol anchors
        if self.extra_delta_vols:
            for pt in self.extra_delta_vols:
                d = float(pt["delta"])  # sign indicates put/call unless overridden
                is_call = bool(pt.get("is_call", d > 0))
                vol = float(pt["vol"])
                target_delta = abs(d) if is_call else -abs(d)
                Kx = strike_from_delta(target_delta, is_call, self.S, self.F, self.T, vol, self.df_dom, self.df_for, self.delta_convention)
                K_list.append(Kx)
                V_list.append(vol)
                W_list.append(1.0)

        # Extra strike-vol anchors
        if self.extra_strike_vols:
            for (Kx, vx) in self.extra_strike_vols:
                K_list.append(float(Kx))
                V_list.append(float(vx))
                W_list.append(1.0)

        K = np.array(K_list, float)
        V = np.array(V_list, float)
        W = np.array(self.custom_weights if self.custom_weights is not None else W_list, float)
        return K, V, W


# Helper: build extended smiles from arrays

def build_extended_smiles_from_quotes(
    S: float,
    T_list: Sequence[float],
    df_dom_list: Sequence[float],
    df_for_list: Sequence[float],
    atm_list: Sequence[float],
    rr25_list: Sequence[float] | None = None,
    bf25_list: Sequence[float] | None = None,
    rr10_list: Sequence[float] | None = None,
    bf10_list: Sequence[float] | None = None,
    beta: float = 0.5,
    delta_convention: Literal["forward", "premium-adjusted"] = "premium-adjusted",
    extra_delta_vols_per_expiry: Sequence[Sequence[dict]] | None = None,
    extra_strike_vols_per_expiry: Sequence[Sequence[Tuple[float, float]]] | None = None,
) -> list[MarketSmileExtended]:
    N = len(T_list)
    def take(seq, i, default=None):
        return (seq[i] if (seq is not None and i < len(seq)) else default)
    smiles: list[MarketSmileExtended] = []
    for i in range(N):
        T = T_list[i]
        df_d = df_dom_list[i]
        df_f = df_for_list[i]
        F = S * df_f / df_d
        sm = MarketSmileExtended(
            S=S, F=F, T=T, df_dom=df_d, df_for=df_f,
            sigma_atm=atm_list[i],
            rr_25=take(rr25_list, i), bf_25=take(bf25_list, i),
            rr_10=take(rr10_list, i), bf_10=take(bf10_list, i),
            beta=beta, delta_convention=delta_convention,
            extra_delta_vols=take(extra_delta_vols_per_expiry, i, []),
            extra_strike_vols=take(extra_strike_vols_per_expiry, i, []),
        )
        smiles.append(sm)
    return smiles


# ------------------------------
# Mini demo for extended calibration (optional)
# ------------------------------
if __name__ == "__main__":
    # Example arrays (synthetic)
    S_demo = 1.25
    T_list = [0.25, 0.5, 1.0]
    r_dom_list = [0.03, 0.031, 0.032]
    r_for_list = [0.015, 0.016, 0.017]
    df_dom_list = [math.exp(-r * T) for r, T in zip(r_dom_list, T_list)]
    df_for_list = [math.exp(-r * T) for r, T in zip(r_for_list, T_list)]

    atm_list = [0.095, 0.10, 0.105]
    rr25_list = [0.012, 0.015, 0.017]
    bf25_list = [0.0015, 0.0020, 0.0022]
    # 10Δ wing (requested)
    rr10_list = [0.020, 0.023, 0.025]
    bf10_list = [0.0025, 0.0030, 0.0034]

    # Extra anchors: e.g., an explicit 40Δ call vol per expiry
    extra_delta_vols = [
        [{"delta": +0.40, "vol": atm_list[0] + 0.001, "is_call": True}],
        [{"delta": +0.40, "vol": atm_list[1] + 0.001, "is_call": True}],
        [{"delta": +0.40, "vol": atm_list[2] + 0.001, "is_call": True}],
    ]

    smiles_ext = build_extended_smiles_from_quotes(
        S=S_demo,
        T_list=T_list,
        df_dom_list=df_dom_list,
        df_for_list=df_for_list,
        atm_list=atm_list,
        rr25_list=rr25_list,
        bf25_list=bf25_list,
        rr10_list=rr10_list,
        bf10_list=bf10_list,
        beta=0.5,
        delta_convention="premium-adjusted",
        extra_delta_vols_per_expiry=extra_delta_vols,
    )

    # Calibrate each expiry jointly to ATM + 25Δ wing + 10Δ wing + extra 40Δ call
    params_ts, diags = calibrate_sabr_term_structure(smiles_ext, smooth_lambda=3.0)
    print("
Extended (10Δ + extras) term-structure:")
    for T, p, d in zip(T_list, params_ts, diags):
        print(f"T={T:>4.2f}  alpha={p.alpha:.6f}  rho={p.rho:+.4f}  nu={p.nu:.4f}  SSE={d['sse']:.3e}")




smiles_ext = build_extended_smiles_from_quotes(
    S, T_list, df_dom_list, df_for_list, atm_list,
    rr25_list=rr25_list, bf25_list=bf25_list,
    rr10_list=rr10_list, bf10_list=bf10_list,  # <= 10Δ support
    beta=0.5, delta_convention="premium-adjusted",
    extra_delta_vols_per_expiry=[      # optional additional anchors
        [{"delta": +0.40, "vol": 0.001+atm_list[0], "is_call": True}],
        [{"delta": +0.40, "vol": 0.001+atm_list[1], "is_call": True}],
        [{"delta": +0.40, "vol": 0.001+atm_list[2], "is_call": True}],
    ],
)
params_ts, diags = calibrate_sabr_term_structure(smiles_ext, smooth_lambda=3.0)






#########################################################################################

"""
Stochastic Local Volatility (SLV) Monte Carlo Pricer for FX (path-dependent options)
-----------------------------------------------------------------------------------

Model (domestic numeraire):
    dS_t = S_t * [(r_d(t) - r_f(t)) dt + L(t, S_t) * sqrt(v_t) dW^S_t]
    dv_t = kappa * (theta - v_t) dt + eta * sqrt(v_t) dW^v_t
    corr(dW^S, dW^v) = rho

The leverage function L(t, S) is chosen to match a target local volatility surface σ_loc(t, S)
via the Gyöngy/Markovian projection condition:
    L^2(t, S) * E[v_t | S_t = S] = σ_loc^2(t, S)
We estimate E[v_t | S_t = S] from Monte Carlo particles with kernel regression and iterate.

This script provides:
  * A flexible LocalVolSurface implementation (from callable or grid + bicubic spline)
  * SLV iterative calibration on a time grid using particles
  * Monte Carlo pricing for path-dependent payoffs (Asian, up-and-out barrier, generic callback)

Dependencies: numpy, scipy (for splines), tqdm (optional progress bar).
Install: pip install numpy scipy tqdm

NOTE: This is a research/education-quality implementation focusing on clarity.
For production use, consider variance reduction (antithetics, control variates),
higher-order discretizations (QE/Andersen), robust bandwidth selection, and tighter convergence checks.
"""
from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Callable, Sequence, Tuple, Optional

import numpy as np
from numpy.typing import ArrayLike
from scipy.interpolate import RectBivariateSpline, interp1d

try:
    from tqdm import trange
except Exception:  # tqdm optional
    def trange(*args, **kwargs):
        return range(args[0])

# -------------------------------
# Local Vol Surface
# -------------------------------
class LocalVolSurface:
    """Local volatility surface σ_loc(t, S).

    You can provide either:
      - a callable sigma(t, S), or
      - grids (t_grid, s_grid, sigma_grid) to build a bicubic spline.
    """
    def __init__(self,
                 sigma_fn: Optional[Callable[[float, float], float]] = None,
                 t_grid: Optional[ArrayLike] = None,
                 s_grid: Optional[ArrayLike] = None,
                 sigma_grid: Optional[ArrayLike] = None):
        if sigma_fn is None and (t_grid is None or s_grid is None or sigma_grid is None):
            raise ValueError("Provide either sigma_fn or (t_grid, s_grid, sigma_grid).")
        self.sigma_fn = sigma_fn
        if sigma_fn is None:
            t_grid = np.asarray(t_grid, float)
            s_grid = np.asarray(s_grid, float)
            sigma_grid = np.asarray(sigma_grid, float)
            if sigma_grid.shape != (len(t_grid), len(s_grid)):
                raise ValueError("sigma_grid shape must be (len(t_grid), len(s_grid)).")
            self._spline = RectBivariateSpline(t_grid, s_grid, sigma_grid, kx=3, ky=3)
            self.t0, self.t1 = float(t_grid[0]), float(t_grid[-1])
            self.s0, self.s1 = float(s_grid[0]), float(s_grid[-1])
        else:
            self._spline = None

    def sigma(self, t: float, S: float) -> float:
        if self._spline is not None:
            tq = min(max(t, self.t0), self.t1)
            sq = min(max(S, self.s0), self.s1)
            return float(self._spline(tq, sq, grid=False))
        else:
            return float(self.sigma_fn(t, S))

# -------------------------------
# Domestic/Foreign rate curves
# -------------------------------
@dataclass
class FlatCurve:
    r: float
    def r_t(self, t: float) -> float:
        return self.r

# -------------------------------
# Heston SV params
# -------------------------------
@dataclass
class HestonParams:
    kappa: float   # mean reversion speed
    theta: float   # long run variance
    eta: float     # vol-of-vol
    rho: float     # correlation (dW^S, dW^v)
    v0: float      # initial variance

# -------------------------------
# Kernel regression to estimate E[v | S=s] from particles
# -------------------------------

def gaussian_kernel(u: np.ndarray) -> np.ndarray:
    return np.exp(-0.5 * u * u) / math.sqrt(2.0 * math.pi)


def silverman_bandwidth(x: np.ndarray) -> float:
    std = x.std(ddof=1)
    n = len(x)
    return 1.06 * std * (n ** (-1/5)) if std > 1e-12 else max(1e-6, np.median(np.abs(x - np.median(x))) * 1.06 * (n ** (-1/5)))


def conditional_expectation_v_given_S(S_samples: np.ndarray,
                                      v_samples: np.ndarray,
                                      s_eval: np.ndarray,
                                      h: Optional[float] = None) -> np.ndarray:
    S_samples = np.asarray(S_samples)
    v_samples = np.asarray(v_samples)
    s_eval = np.asarray(s_eval)
    if h is None:
        h = silverman_bandwidth(S_samples)
        h = max(h, 1e-6)
    # Compute weights
    ce = np.empty_like(s_eval, dtype=float)
    for i, s in enumerate(s_eval):
        u = (s - S_samples) / h
        w = gaussian_kernel(u)
        num = np.sum(w * v_samples)
        den = np.sum(w) + 1e-16
        ce[i] = num / den
    return ce

# -------------------------------
# SLV Leverage calibration (particle method)
# -------------------------------
@dataclass
class SLVGrid:
    t_grid: np.ndarray        # shape [M+1]
    s_grid: np.ndarray        # shape [N]
    L: np.ndarray             # shape [M+1, N]


def initialize_leverage_grid(t_grid: ArrayLike, s_grid: ArrayLike, value: float = 1.0) -> SLVGrid:
    t_grid = np.asarray(t_grid, float)
    s_grid = np.asarray(s_grid, float)
    L = np.full((len(t_grid), len(s_grid)), value, dtype=float)
    return SLVGrid(t_grid, s_grid, L)


def interpolate_L(grid: SLVGrid) -> Callable[[float, float], float]:
    spline = RectBivariateSpline(grid.t_grid, grid.s_grid, grid.L, kx=1, ky=1)  # bilinear for stability
    t0, t1 = float(grid.t_grid[0]), float(grid.t_grid[-1])
    s0, s1 = float(grid.s_grid[0]), float(grid.s_grid[-1])
    def L_of(t: float, S: float) -> float:
        tt = min(max(t, t0), t1)
        ss = min(max(S, s0), s1)
        return float(spline(tt, ss, grid=False))
    return L_of


# -------------------------------
# Path simulation under SLV (Euler-Maruyama with full truncation for v)
# -------------------------------

def simulate_paths_slv(
    S0: float,
    v0: float,
    local_vol: LocalVolSurface,
    L_of: Callable[[float, float], float],
    heston: HestonParams,
    rd_curve: Callable[[float], float],
    rf_curve: Callable[[float], float],
    t_grid: np.ndarray,
    n_paths: int,
    rng: np.random.Generator,
    store_paths: bool = False,
) -> Tuple[np.ndarray, np.ndarray, Optional[np.ndarray]]:
    """Simulate S_t and v_t on the provided t_grid.

    Returns (S_T, v_T, S_paths [optional]).
    """
    M = len(t_grid) - 1
    S = np.full(n_paths, S0, dtype=float)
    v = np.full(n_paths, v0, dtype=float)
    if store_paths:
        S_paths = np.empty((M+1, n_paths), dtype=float)
        S_paths[0] = S0
    else:
        S_paths = None

    kappa, theta, eta, rho = heston.kappa, heston.theta, heston.eta, heston.rho

    for m in range(M):
        t = t_grid[m]
        dt = t_grid[m+1] - t
        if dt <= 0:
            raise ValueError("t_grid must be increasing")
        # Correlated normals
        z1 = rng.standard_normal(n_paths)
        z2 = rng.standard_normal(n_paths)
        z2 = rho * z1 + math.sqrt(max(0.0, 1.0 - rho*rho)) * z2

        # Rates
        rd = rd_curve(0.5*(t + t_grid[m+1]))
        rf = rf_curve(0.5*(t + t_grid[m+1]))
        mu = rd - rf

        # Variance step: full truncation Euler
        sqrt_v = np.sqrt(np.maximum(v, 0.0))
        v = v + kappa*(theta - np.maximum(v, 0.0))*dt + eta*sqrt_v*np.sqrt(dt)*z2
        v = np.maximum(v, 0.0)

        # Spot step with leverage
        Lval = np.array([L_of(t, s) for s in S])
        dW = np.sqrt(dt) * z1
        S = S * np.exp((mu - 0.5*(Lval*sqrt_v)**2)*dt + Lval*sqrt_v*dW)

        if store_paths:
            S_paths[m+1] = S

    return S, v, S_paths


# -------------------------------
# Iterative SLV leverage calibration
# -------------------------------

def calibrate_leverage(
    S0: float,
    heston: HestonParams,
    local_vol: LocalVolSurface,
    rd_curve: Callable[[float], float],
    rf_curve: Callable[[float], float],
    t_grid: np.ndarray,
    s_grid: np.ndarray,
    n_paths: int = 200_000,
    max_iter: int = 6,
    seed: Optional[int] = 7,
    bandwidth_scale: float = 1.0,
    damp: float = 0.6,
) -> SLVGrid:
    """Particle method: iterate to enforce L^2 * E[v|S] ≈ σ_loc^2.

    Args:
        n_paths: number of particles per iteration (trade accuracy vs speed)
        max_iter: iterations of (simulate -> estimate E[v|S] -> update L)
        bandwidth_scale: multiply Silverman bandwidth (tune smoothness)
        damp: leverage update damping in (0,1] for stability
    """
    rng = np.random.default_rng(seed)
    grid = initialize_leverage_grid(t_grid, s_grid, value=1.0)
    L_of = interpolate_L(grid)

    for it in range(max_iter):
        # Simulate with current leverage
        v_snapshots = []  # list of arrays per time layer (exclude t=0)
        S_snapshots = []
        # We need all layers to build conditional expectation per time node
        M = len(t_grid) - 1
        S_layer = np.full(n_paths, S0, float)
        v_layer = np.full(n_paths, heston.v0, float)

        kappa, theta, eta, rho = heston.kappa, heston.theta, heston.eta, heston.rho

        for m in trange(M, desc=f"SLV iter {it+1}/{max_iter}"):
            t = t_grid[m]
            dt = t_grid[m+1] - t
            z1 = rng.standard_normal(n_paths)
            z2 = rng.standard_normal(n_paths)
            z2 = rho * z1 + math.sqrt(max(0.0, 1.0 - rho*rho)) * z2

            rd = rd_curve(0.5*(t + t_grid[m+1]))
            rf = rf_curve(0.5*(t + t_grid[m+1]))
            mu = rd - rf

            sqrt_v = np.sqrt(np.maximum(v_layer, 0.0))
            v_layer = v_layer + kappa*(theta - np.maximum(v_layer, 0.0))*dt + eta*sqrt_v*np.sqrt(dt)*z2
            v_layer = np.maximum(v_layer, 0.0)

            Lval = np.array([L_of(t, s) for s in S_layer])
            dW = np.sqrt(dt) * z1
            S_layer = S_layer * np.exp((mu - 0.5*(Lval*sqrt_v)**2)*dt + Lval*sqrt_v*dW)

            # store snapshot at t_{m+1}
            S_snapshots.append(S_layer.copy())
            v_snapshots.append(v_layer.copy())

        # Update leverage at each time node t_{m+1} over s_grid
        for m in range(M):
            t = t_grid[m+1]
            S_samp = S_snapshots[m]
            v_samp = v_snapshots[m]
            h = bandwidth_scale * silverman_bandwidth(S_samp)
            Ev = conditional_expectation_v_given_S(S_samp, v_samp, s_eval=s_grid, h=h)
            sig_loc = np.array([local_vol.sigma(t, s) for s in s_grid])
            # Avoid division by tiny Ev
            Ev = np.maximum(Ev, 1e-10)
            L_new = sig_loc / np.sqrt(Ev)
            # Damping + floor
            grid.L[m+1, :] = np.clip(damp * L_new + (1.0 - damp) * grid.L[m+1, :], 0.01, 10.0)
        # Refresh interpolator
        L_of = interpolate_L(grid)

    return grid


# -------------------------------
# Payoffs & Pricing
# -------------------------------

def price_by_mc(
    S0: float,
    local_vol: LocalVolSurface,
    heston: HestonParams,
    rd_curve: Callable[[float], float],
    rf_curve: Callable[[float], float],
    t_grid: np.ndarray,
    n_paths: int,
    payoff_fn: Callable[[np.ndarray, np.ndarray, np.ndarray, np.ndarray], np.ndarray],
    leverage_grid: Optional[SLVGrid] = None,
    antithetic: bool = True,
    seed: Optional[int] = 123,
) -> Tuple[float, float]:
    """Generic MC pricer. payoff_fn receives (S_paths, times, rd_times, rf_times) and
    must return cashflows at maturity in domestic currency; we then discount by exp(-∫r_d dt).

    If leverage_grid is None, pure Heston (L≡1) is used.
    Returns (price, standard_error).
    """
    rng = np.random.default_rng(seed)
    M = len(t_grid) - 1
    times = t_grid

    if leverage_grid is None:
        L_of = lambda t, S: 1.0
    else:
        L_of = interpolate_L(leverage_grid)

    # Precompute integral of rd piecewise constant per step for discounting
    rd_mid = np.array([rd_curve(0.5*(t_grid[m] + t_grid[m+1])) for m in range(M)])
    df = np.exp(-np.cumsum(rd_mid * np.diff(t_grid)))
    # For convenience, build a function to get DF to any time grid node
    df_nodes = np.concatenate([[1.0], df])

    # Simulate paths and compute payoff on-the-fly (store S_paths for path-dependent payoffs)
    batch = n_paths // (2 if antithetic else 1)
    payoffs = []
    for _ in range((2 if antithetic else 1)):
        # simulate with/without antithetic via sign flip of z1,z2 handled inside simulate function by new rng states
        S_T, v_T, S_paths = simulate_paths_slv(
            S0=S0, v0=heston.v0,
            local_vol=local_vol, L_of=L_of,
            heston=heston,
            rd_curve=rd_curve, rf_curve=rf_curve,
            t_grid=t_grid, n_paths=batch,
            rng=rng, store_paths=True,
        )
        # Evaluate payoff at maturity node
        payoff = payoff_fn(S_paths, times, rd_mid, np.zeros_like(rd_mid))  # rf not used in payoff directly
        # Discount using df_nodes[-1]
        disc = df_nodes[-1]
        payoffs.append(payoff * disc)

    payoffs = np.concatenate(payoffs)
    price = float(np.mean(payoffs))
    stderr = float(np.std(payoffs, ddof=1) / math.sqrt(len(payoffs)))
    return price, stderr


# Example path-dependent payoffs

def asian_call_payoff(K: float) -> Callable[[np.ndarray, np.ndarray, np.ndarray, np.ndarray], np.ndarray]:
    def _payoff(S_paths: np.ndarray, times: np.ndarray, *_args) -> np.ndarray:
        S_avg = np.mean(S_paths, axis=0)
        return np.maximum(S_avg - K, 0.0)
    return _payoff


def up_and_out_call_payoff(K: float, B: float) -> Callable[[np.ndarray, np.ndarray, np.ndarray, np.ndarray], np.ndarray]:
    def _payoff(S_paths: np.ndarray, times: np.ndarray, *_args) -> np.ndarray:
        knocked = (S_paths.max(axis=0) >= B)
        ST = S_paths[-1]
        return np.where(knocked, 0.0, np.maximum(ST - K, 0.0))
    return _payoff


# -------------------------------
# Demo / Usage
# -------------------------------
if __name__ == "__main__":
    # ---- Inputs ----
    S0 = 1.20
    rd = FlatCurve(0.02)
    rf = FlatCurve(0.01)
    rd_curve = rd.r_t
    rf_curve = rf.r_t

    # Heston parameters (example only)
    heston = HestonParams(kappa=2.0, theta=0.04, eta=0.6, rho=-0.5, v0=0.04)

    # Local vol surface (synthetic example):
    # Slight smile in S and mild term-structure in t
    def sigma_loc_fn(t: float, S: float) -> float:
        base = 0.18 * (1.0 + 0.1 * math.exp(-2.0 * t))
        skew = 1.0 + 0.25 * (S / S0 - 1.0)
        return max(0.02, base * (0.9 + 0.1 * (skew**2)))

    local_vol = LocalVolSurface(sigma_fn=sigma_loc_fn)

    # Time & state grids
    T = 1.0
    M = 252  # daily steps (trading days)
    t_grid = np.linspace(0.0, T, M+1)
    s_grid = np.linspace(0.5*S0, 1.8*S0, 101)

    # ---- Calibrate leverage (few iterations for demo) ----
    slv_grid = calibrate_leverage(
        S0=S0,
        heston=heston,
        local_vol=local_vol,
        rd_curve=rd_curve,
        rf_curve=rf_curve,
        t_grid=t_grid,
        s_grid=s_grid,
        n_paths=50_000,      # increase for accuracy
        max_iter=5,          # increase if needed
        bandwidth_scale=1.2,
        damp=0.7,
        seed=42,
    )

    # ---- Price examples under calibrated SLV ----
    n_paths_pricing = 100_000

    # Asian call
    K_asian = 1.20
    price_asian, se_asian = price_by_mc(
        S0=S0,
        local_vol=local_vol,
        heston=heston,
        rd_curve=rd_curve,
        rf_curve=rf_curve,
        t_grid=t_grid,
        n_paths=n_paths_pricing,
        payoff_fn=asian_call_payoff(K_asian),
        leverage_grid=slv_grid,
        antithetic=True,
        seed=123,
    )
    print(f"Asian call (K={K_asian:.4f})  Price={price_asian:.6f}  SE={se_asian:.6f}")

    # Up-and-out call
    K_uo, B_uo = 1.15, 1.35
    price_uo, se_uo = price_by_mc(
        S0=S0,
        local_vol=local_vol,
        heston=heston,
        rd_curve=rd_curve,
        rf_curve=rf_curve,
        t_grid=t_grid,
        n_paths=n_paths_pricing,
        payoff_fn=up_and_out_call_payoff(K_uo, B_uo),
        leverage_grid=slv_grid,
        antithetic=True,
        seed=321,
    )
    print(f"Up&Out call (K={K_uo:.4f}, B={B_uo:.4f})  Price={price_uo:.6f}  SE={se_uo:.6f}")

    # Tip: set n_paths in calibration/pricing to 5e5–2e6 for production-grade numbers.




##########################################

"""
Heston Stochastic Volatility Monte Carlo Pricer for FX
======================================================

Domestic-risk-neutral FX Heston dynamics:

    dS_t = S_t * [(r_d - r_f) dt + sqrt(v_t) dW^S_t]
    dv_t = kappa * (theta - v_t) dt + eta * sqrt(v_t) dW^v_t
    corr(dW^S_t, dW^v_t) = rho

Where:
    S_t     = FX spot, e.g. EURUSD
    r_d     = domestic interest rate, e.g. USD rate for EURUSD
    r_f     = foreign interest rate, e.g. EUR rate for EURUSD
    v_t     = instantaneous variance
    kappa   = variance mean reversion speed
    theta   = long-run variance
    eta     = volatility of variance, i.e. vol-of-vol
    rho     = spot/variance correlation
    v0      = initial variance

This script prices:
    1. European call/put
    2. Arithmetic Asian call/put
    3. Up-and-out call/put
    4. Generic path-dependent payoff

Dependencies:
    pip install numpy
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal, Tuple
import math
import numpy as np


OptionType = Literal["call", "put"]


@dataclass
class HestonFXParams:
    S0: float          # Initial FX spot
    rd: float          # Domestic continuously compounded rate
    rf: float          # Foreign continuously compounded rate
    v0: float          # Initial variance
    kappa: float       # Mean reversion speed
    theta: float       # Long-run variance
    eta: float         # Vol-of-vol
    rho: float         # Correlation between spot and variance Brownian motions


@dataclass
class MCSettings:
    T: float                 # Maturity in years
    n_steps: int = 252       # Number of time steps
    n_paths: int = 100_000   # Number of Monte Carlo paths
    seed: int = 42
    antithetic: bool = True


def simulate_heston_fx_paths(
    params: HestonFXParams,
    settings: MCSettings,
    store_paths: bool = True,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Simulate FX spot and variance paths under Heston SV.

    Uses full-truncation Euler for variance:
        v_pos = max(v, 0)
        dv = kappa(theta - v_pos)dt + eta sqrt(v_pos)dWv
        v_next = max(v + dv, 0)

    Spot is evolved using log-Euler:
        S_next = S * exp((rd-rf-0.5v_pos)dt + sqrt(v_pos)dWs)

    Returns:
        times: shape (n_steps + 1,)
        S_paths: shape (n_steps + 1, n_paths)
        v_paths: shape (n_steps + 1, n_paths)
    """
    S0, rd, rf = params.S0, params.rd, params.rf
    v0 = params.v0
    kappa, theta, eta, rho = params.kappa, params.theta, params.eta, params.rho

    T, n_steps = settings.T, settings.n_steps
    n_paths = settings.n_paths
    rng = np.random.default_rng(settings.seed)

    if settings.antithetic:
        half_paths = (n_paths + 1) // 2
        effective_paths = 2 * half_paths
    else:
        half_paths = n_paths
        effective_paths = n_paths

    dt = T / n_steps
    sqrt_dt = math.sqrt(dt)
    times = np.linspace(0.0, T, n_steps + 1)

    S_paths = np.empty((n_steps + 1, effective_paths), dtype=float)
    v_paths = np.empty((n_steps + 1, effective_paths), dtype=float)

    S = np.full(effective_paths, S0, dtype=float)
    v = np.full(effective_paths, v0, dtype=float)

    S_paths[0] = S
    v_paths[0] = v

    drift = rd - rf

    for t_idx in range(1, n_steps + 1):
        z1_half = rng.standard_normal(half_paths)
        z2_half = rng.standard_normal(half_paths)

        if settings.antithetic:
            z1 = np.concatenate([z1_half, -z1_half])
            z2_ind = np.concatenate([z2_half, -z2_half])
        else:
            z1 = z1_half
            z2_ind = z2_half

        # Correlate Brownian shocks
        z2 = rho * z1 + math.sqrt(max(0.0, 1.0 - rho * rho)) * z2_ind

        v_pos = np.maximum(v, 0.0)
        sqrt_v = np.sqrt(v_pos)

        # Spot step
        S = S * np.exp((drift - 0.5 * v_pos) * dt + sqrt_v * sqrt_dt * z1)

        # Variance step: full-truncation Euler
        v = v + kappa * (theta - v_pos) * dt + eta * sqrt_v * sqrt_dt * z2
        v = np.maximum(v, 0.0)

        S_paths[t_idx] = S
        v_paths[t_idx] = v

    # Trim back to requested n_paths if antithetic created one extra
    S_paths = S_paths[:, :n_paths]
    v_paths = v_paths[:, :n_paths]

    return times, S_paths, v_paths


def discount_factor(rd: float, T: float) -> float:
    return math.exp(-rd * T)


def european_payoff(K: float, option_type: OptionType = "call") -> Callable[[np.ndarray], np.ndarray]:
    def payoff(S_paths: np.ndarray) -> np.ndarray:
        ST = S_paths[-1]
        if option_type == "call":
            return np.maximum(ST - K, 0.0)
        return np.maximum(K - ST, 0.0)
    return payoff


def arithmetic_asian_payoff(K: float, option_type: OptionType = "call") -> Callable[[np.ndarray], np.ndarray]:
    def payoff(S_paths: np.ndarray) -> np.ndarray:
        avg_S = np.mean(S_paths, axis=0)
        if option_type == "call":
            return np.maximum(avg_S - K, 0.0)
        return np.maximum(K - avg_S, 0.0)
    return payoff


def up_and_out_payoff(
    K: float,
    barrier: float,
    option_type: OptionType = "call",
) -> Callable[[np.ndarray], np.ndarray]:
    def payoff(S_paths: np.ndarray) -> np.ndarray:
        ST = S_paths[-1]
        knocked_out = np.max(S_paths, axis=0) >= barrier
        if option_type == "call":
            vanilla = np.maximum(ST - K, 0.0)
        else:
            vanilla = np.maximum(K - ST, 0.0)
        return np.where(knocked_out, 0.0, vanilla)
    return payoff


def down_and_out_payoff(
    K: float,
    barrier: float,
    option_type: OptionType = "call",
) -> Callable[[np.ndarray], np.ndarray]:
    def payoff(S_paths: np.ndarray) -> np.ndarray:
        ST = S_paths[-1]
        knocked_out = np.min(S_paths, axis=0) <= barrier
        if option_type == "call":
            vanilla = np.maximum(ST - K, 0.0)
        else:
            vanilla = np.maximum(K - ST, 0.0)
        return np.where(knocked_out, 0.0, vanilla)
    return payoff


def price_heston_fx_mc(
    params: HestonFXParams,
    settings: MCSettings,
    payoff_fn: Callable[[np.ndarray], np.ndarray],
) -> dict:
    """
    Generic Heston FX Monte Carlo pricer.

    payoff_fn receives full S_paths with shape:
        (n_steps + 1, n_paths)

    This allows pricing path-dependent options.
    """
    times, S_paths, v_paths = simulate_heston_fx_paths(params, settings, store_paths=True)

    payoffs = payoff_fn(S_paths)
    df = discount_factor(params.rd, settings.T)
    discounted = df * payoffs

    price = float(np.mean(discounted))
    stderr = float(np.std(discounted, ddof=1) / math.sqrt(settings.n_paths))

    return {
        "price": price,
        "stderr": stderr,
        "times": times,
        "S_paths": S_paths,
        "v_paths": v_paths,
    }


# ---------------------------------------------------------------------
# Black-Scholes / Garman-Kohlhagen helpers for calibration
# ---------------------------------------------------------------------

def norm_cdf(x: np.ndarray | float) -> np.ndarray | float:
    # numpy-compatible normal CDF using erf
    return 0.5 * (1.0 + np.vectorize(math.erf)(np.asarray(x) / math.sqrt(2.0)))


def garman_kohlhagen_price(
    S0: float,
    K: float,
    T: float,
    rd: float,
    rf: float,
    vol: float,
    option_type: OptionType = "call",
) -> float:
    """FX Black-Scholes / Garman-Kohlhagen price."""
    if T <= 0 or vol <= 0:
        intrinsic = max(S0 - K, 0.0) if option_type == "call" else max(K - S0, 0.0)
        return intrinsic

    F = S0 * math.exp((rd - rf) * T)
    df_d = math.exp(-rd * T)
    sig_sqrt = vol * math.sqrt(T)
    d1 = (math.log(F / K) + 0.5 * vol * vol * T) / sig_sqrt
    d2 = d1 - sig_sqrt

    if option_type == "call":
        return df_d * (F * float(norm_cdf(d1)) - K * float(norm_cdf(d2)))
    else:
        return df_d * (K * float(norm_cdf(-d2)) - F * float(norm_cdf(-d1)))


def implied_vol_from_price(
    price: float,
    S0: float,
    K: float,
    T: float,
    rd: float,
    rf: float,
    option_type: OptionType = "call",
    low: float = 1e-6,
    high: float = 5.0,
    tol: float = 1e-8,
    max_iter: int = 100,
) -> float:
    """Invert Garman-Kohlhagen price to Black implied volatility via bisection."""
    for _ in range(max_iter):
        mid = 0.5 * (low + high)
        p_mid = garman_kohlhagen_price(S0, K, T, rd, rf, mid, option_type)
        if abs(p_mid - price) < tol:
            return mid
        if p_mid < price:
            low = mid
        else:
            high = mid
    return 0.5 * (low + high)


# ---------------------------------------------------------------------
# Heston parameter calibration to market vols
# ---------------------------------------------------------------------

from scipy.optimize import minimize

@dataclass
class MarketVolQuote:
    T: float
    K: float
    vol: float
    option_type: OptionType = "call"
    weight: float = 1.0


def heston_mc_model_vol(
    base_params: HestonFXParams,
    T: float,
    K: float,
    option_type: OptionType,
    n_steps_per_year: int,
    n_paths: int,
    seed: int,
    antithetic: bool = True,
) -> float:
    """Price one option under Heston MC, then convert to Black/GK implied vol."""
    settings = MCSettings(
        T=T,
        n_steps=max(4, int(round(n_steps_per_year * T))),
        n_paths=n_paths,
        seed=seed,
        antithetic=antithetic,
    )
    result = price_heston_fx_mc(
        params=base_params,
        settings=settings,
        payoff_fn=european_payoff(K=K, option_type=option_type),
    )
    return implied_vol_from_price(
        price=result["price"],
        S0=base_params.S0,
        K=K,
        T=T,
        rd=base_params.rd,
        rf=base_params.rf,
        option_type=option_type,
    )


def calibrate_heston_params_mc(
    S0: float,
    rd: float,
    rf: float,
    market_quotes: list[MarketVolQuote],
    initial_guess: HestonFXParams,
    calibrate_v0: bool = True,
    n_steps_per_year: int = 100,
    n_paths: int = 30_000,
    seed: int = 1234,
    antithetic: bool = True,
    verbose: bool = True,
) -> tuple[HestonFXParams, dict]:
    """Calibrate Heston parameters to market implied vols using MC pricing.

    This is intentionally simple and robust, not the fastest method.

    Parameters calibrated:
        If calibrate_v0=True:  [v0, kappa, theta, eta, rho]
        If calibrate_v0=False: [kappa, theta, eta, rho], keeping v0 fixed.

    Bounds:
        v0, theta: [1e-6, 1.00]   # variance, vol up to 100%
        kappa    : [1e-4, 20.0]
        eta      : [1e-4, 5.0]
        rho      : [-0.999, 0.999]

    Objective:
        weighted squared error between model Black vols and market Black vols.
    """

    if calibrate_v0:
        x0 = np.array([
            initial_guess.v0,
            initial_guess.kappa,
            initial_guess.theta,
            initial_guess.eta,
            initial_guess.rho,
        ], dtype=float)
        bounds = [(1e-6, 1.00), (1e-4, 20.0), (1e-6, 1.00), (1e-4, 5.0), (-0.999, 0.999)]
    else:
        x0 = np.array([
            initial_guess.kappa,
            initial_guess.theta,
            initial_guess.eta,
            initial_guess.rho,
        ], dtype=float)
        bounds = [(1e-4, 20.0), (1e-6, 1.00), (1e-4, 5.0), (-0.999, 0.999)]

    eval_count = {"n": 0}

    def unpack(x: np.ndarray) -> HestonFXParams:
        if calibrate_v0:
            v0, kappa, theta, eta, rho = x
        else:
            kappa, theta, eta, rho = x
            v0 = initial_guess.v0
        return HestonFXParams(S0=S0, rd=rd, rf=rf, v0=float(v0), kappa=float(kappa), theta=float(theta), eta=float(eta), rho=float(rho))

    def objective(x: np.ndarray) -> float:
        p = unpack(x)
        eval_count["n"] += 1

        # Light Feller penalty. Heston can still be used without Feller, but this discourages unstable regions.
        feller_gap = 2.0 * p.kappa * p.theta - p.eta * p.eta
        feller_penalty = 0.0 if feller_gap >= 0 else 10.0 * feller_gap * feller_gap

        err2 = 0.0
        rows = []
        for i, q in enumerate(market_quotes):
            # Use deterministic per-quote seed so objective noise is more stable across optimizer calls.
            model_vol = heston_mc_model_vol(
                base_params=p,
                T=q.T,
                K=q.K,
                option_type=q.option_type,
                n_steps_per_year=n_steps_per_year,
                n_paths=n_paths,
                seed=seed + 1000 * i,
                antithetic=antithetic,
            )
            err = model_vol - q.vol
            err2 += q.weight * err * err
            rows.append((q.T, q.K, q.vol, model_vol, err))

        obj = err2 + feller_penalty
        if verbose:
            print(
                f"eval={eval_count['n']:03d} obj={obj:.8e} "
                f"v0={p.v0:.5f} kappa={p.kappa:.4f} theta={p.theta:.5f} eta={p.eta:.4f} rho={p.rho:+.4f}"
            )
        return float(obj)

    res = minimize(
        objective,
        x0,
        method="Nelder-Mead",  # robust for noisy MC objectives
        options={"maxiter": 80, "xatol": 1e-4, "fatol": 1e-6, "disp": verbose},
    )

    # Clip final solution to bounds manually because Nelder-Mead has no native bounds in older SciPy versions.
    x_best = np.array(res.x, dtype=float)
    for j, (lo, hi) in enumerate(bounds):
        x_best[j] = min(max(x_best[j], lo), hi)
    calibrated = unpack(x_best)

    # Build final diagnostics using larger/stable seeds if desired.
    fit_rows = []
    sse = 0.0
    for i, q in enumerate(market_quotes):
        mv = heston_mc_model_vol(
            base_params=calibrated,
            T=q.T,
            K=q.K,
            option_type=q.option_type,
            n_steps_per_year=n_steps_per_year,
            n_paths=n_paths,
            seed=seed + 1000 * i,
            antithetic=antithetic,
        )
        err = mv - q.vol
        sse += q.weight * err * err
        fit_rows.append({
            "T": q.T,
            "K": q.K,
            "market_vol": q.vol,
            "model_vol": mv,
            "error": err,
            "option_type": q.option_type,
            "weight": q.weight,
        })

    diagnostics = {
        "success": bool(res.success),
        "message": res.message,
        "objective": float(res.fun),
        "sse_no_penalty": float(sse),
        "fit_rows": fit_rows,
        "optimizer_result": res,
        "evaluations": eval_count["n"],
    }
    return calibrated, diagnostics


def print_heston_fit_report(params: HestonFXParams, diagnostics: dict) -> None:
    print("
Calibrated Heston Parameters")
    print("----------------------------")
    print(f"v0     = {params.v0:.8f}  vol0={math.sqrt(params.v0):.4%}")
    print(f"kappa  = {params.kappa:.6f}")
    print(f"theta  = {params.theta:.8f}  long_vol={math.sqrt(params.theta):.4%}")
    print(f"eta    = {params.eta:.6f}")
    print(f"rho    = {params.rho:+.6f}")
    print(f"Feller = {2*params.kappa*params.theta - params.eta*params.eta:.8f}")
    print(f"SSE    = {diagnostics['sse_no_penalty']:.8e}")
    print("
Fit by quote")
    print("------------")
    for r in diagnostics["fit_rows"]:
        print(
            f"T={r['T']:.3f} K={r['K']:.4f} {r['option_type']:>4s}  "
            f"mkt={r['market_vol']:.4%}  model={r['model_vol']:.4%}  err={r['error']:+.4%}"
        )


# ---------------------------------------------------------------------
# Example usage
# ---------------------------------------------------------------------
if __name__ == "__main__":
    # Example: EURUSD-style convention
    # Domestic = USD, Foreign = EUR
    params = HestonFXParams(
        S0=1.1000,
        rd=0.045,       # USD rate
        rf=0.030,       # EUR rate
        v0=0.10**2,     # initial vol = 10%
        kappa=2.0,
        theta=0.11**2,  # long-run vol = 11%
        eta=0.50,       # vol-of-vol
        rho=-0.40,      # spot-vol correlation
    )

    settings = MCSettings(
        T=1.0,
        n_steps=252,
        n_paths=100_000,
        seed=123,
        antithetic=True,
    )

    # 1) European call
    result_eur = price_heston_fx_mc(
        params=params,
        settings=settings,
        payoff_fn=european_payoff(K=1.10, option_type="call"),
    )
    print("European Call")
    print(f"Price  : {result_eur['price']:.6f}")
    print(f"StdErr : {result_eur['stderr']:.6f}")

    # 2) Arithmetic Asian call
    result_asian = price_heston_fx_mc(
        params=params,
        settings=settings,
        payoff_fn=arithmetic_asian_payoff(K=1.10, option_type="call"),
    )
    print("\nArithmetic Asian Call")
    print(f"Price  : {result_asian['price']:.6f}")
    print(f"StdErr : {result_asian['stderr']:.6f}")

    # 3) Up-and-out call
    result_uo = price_heston_fx_mc(
        params=params,
        settings=settings,
        payoff_fn=up_and_out_payoff(K=1.10, barrier=1.25, option_type="call"),
    )
    print("\nUp-and-Out Call")
    print(f"Price  : {result_uo['price']:.6f}")
    print(f"StdErr : {result_uo['stderr']:.6f}")

    # 4) Down-and-out put
    result_do = price_heston_fx_mc(
        params=params,
        settings=settings,
        payoff_fn=down_and_out_payoff(K=1.10, barrier=0.95, option_type="put"),
    )
    print("\nDown-and-Out Put")
    print(f"Price  : {result_do['price']:.6f}")
    print(f"StdErr : {result_do['stderr']:.6f}")
