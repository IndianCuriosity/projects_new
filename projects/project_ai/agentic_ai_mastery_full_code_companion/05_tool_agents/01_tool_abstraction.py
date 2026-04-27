from langchain_core.tools import tool

@tool
def fx_forward_points(spot: float, domestic_rate: float, foreign_rate: float, years: float) -> float:
    """Approximate FX forward points using covered interest parity."""
    forward = spot * (1 + domestic_rate * years) / (1 + foreign_rate * years)
    return forward - spot

print(fx_forward_points.invoke({"spot": 1.10, "domestic_rate": 0.05, "foreign_rate": 0.03, "years": 0.25}))
