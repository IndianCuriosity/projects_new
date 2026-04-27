procedures = {
    "fx_vol_trade_checklist": [
        "Check implied volatility percentile",
        "Compare implied vol vs realized vol",
        "Inspect skew and term structure",
        "Estimate gamma/theta breakeven",
        "Check event calendar",
        "Define stop loss and hedge frequency",
    ]
}

for step in procedures["fx_vol_trade_checklist"]:
    print("-", step)
