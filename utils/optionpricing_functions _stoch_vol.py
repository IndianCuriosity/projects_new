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
# Heston Vol Calibration
#########################################################################################################################################################################

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

from __future__ import annotations                  # Using from __future__ import annotations (introduced in Python 3.7) changes how Python evaluates type hints. 
                                                    # Instead of evaluating them at runtime, Python treats all type hints as plain strings.
from dataclasses import dataclass                   # "data container" objects where the primary purpose is storing values rather than defining complex behaviors
from typing import Callable, Literal, Tuple         # enforce strict type definitions and structural patterns.
import math
import numpy as np


OptionType = Literal["call", "put"]                 #  # Restricts values to exactly these string options


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
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:                     # Stores an immutable sequence of array
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
