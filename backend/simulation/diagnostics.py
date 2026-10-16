def build_diagnostic(
    *,
    revenue_bdt: float,
    costs_bdt: float,
    cost_breakdown_bdt: dict[str, float],
    gross_yield_tonnes: float,
    saleable_yield_tonnes: float,
    market_price_bdt_per_40kg: float,
    decisions: dict,
    events: dict,
) -> dict:
    net_profit = revenue_bdt - costs_bdt
    return {
        "net_profit_bdt": round(net_profit, 2),
        "outcome": "profit" if net_profit >= 0 else "loss",
        "decisions": decisions,
        "events": events,
        "diagnostic": {
            "yield": {
                "gross_yield_tonnes": round(gross_yield_tonnes, 4),
                "saleable_yield_tonnes": round(saleable_yield_tonnes, 4),
                "formula": "farm size x base yield x seed x fertilizer x weather multipliers",
            },
            "costs_bdt": {
                key: round(value, 2) for key, value in cost_breakdown_bdt.items()
            },
            "revenue": {
                "formula": "saleable tonnes x 25 40kg units per tonne x price per 40kg",
                "market_price_bdt_per_40kg": round(market_price_bdt_per_40kg, 2),
                "gross_revenue_bdt": round(revenue_bdt, 2),
            },
            "profit": {
                "formula": "gross revenue - total costs",
                "net_profit_bdt": round(net_profit, 2),
            },
            "causal_claims": "Only calculated components are reported; no unsupported optimal-path claims.",
        },
    }
