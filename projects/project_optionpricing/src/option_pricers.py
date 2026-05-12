import numpy as np
from scipy.stats import norm




###############################################################################################################
# Vanilla option pricer using Garman-Kohlhagen formula for FX options. The price is in domestic currency per unit of foreign currency.
###############################################################################################################


def garman_kohlhagen_price(
    spot: float,
    strike: float,
    tau: float,
    rd: float,
    rf: float,
    vol: float,
    option_type: str = "call",
) -> float:
    """
    Garman-Kohlhagen FX option price.

    Parameters
    ----------
    spot : float
        FX spot rate, e.g. EURUSD = 1.10
    strike : float
        Option strike
    tau : float
        Time to expiry in years
    rd : float
        Domestic interest rate
    rf : float
        Foreign interest rate
    vol : float
        Implied volatility
    option_type : str
        "call" or "put"

    Returns
    -------
    float
        Option premium in domestic currency per unit foreign currency
    """

    if tau <= 0:
        if option_type.lower() == "call":
            return max(spot - strike, 0.0)
        elif option_type.lower() == "put":
            return max(strike - spot, 0.0)
        else:
            raise ValueError("option_type must be 'call' or 'put'")

    d1 = (
        np.log(spot / strike)
        + (rd - rf + 0.5 * vol**2) * tau
    ) / (vol * np.sqrt(tau))

    d2 = d1 - vol * np.sqrt(tau)

    df_domestic = np.exp(-rd * tau)
    df_foreign = np.exp(-rf * tau)

    if option_type.lower() == "call":
        price = spot * df_foreign * norm.cdf(d1) - strike * df_domestic * norm.cdf(d2)

    elif option_type.lower() == "put":
        price = strike * df_domestic * norm.cdf(-d2) - spot * df_foreign * norm.cdf(-d1)

    else:
        raise ValueError("option_type must be 'call' or 'put'")

    return price



###############################################################################################################
# Digital option pricer using Garman-Kohlhagen formula for FX options. 
###############################################################################################################



###############################################################################################################
# One touch option pricer with Monte Carlo simulation.
###############################################################################################################





###############################################################################################################
# Knock-in, Knock-out option pricer with Monte Carlo simulation.
###############################################################################################################
