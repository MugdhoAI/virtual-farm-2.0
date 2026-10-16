import math
import random

from .cost_model import calculate_cost_breakdown
from .diagnostics import build_diagnostic
from .market import simulate_market_price, simulate_storage_loss
from .models import ModelParameters
from .validation import DecisionValidationError, validate_decisions, validate_parameters
from .weather import simulate_weather
from .yield_model import calculate_yield

MAX_SEED = (1 << 64) - 1


def validate_seed(seed: object) -> int | None:
    if seed is None:
        return None
    if isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed <= MAX_SEED:
        raise DecisionValidationError(f"seed must be an integer between 0 and {MAX_SEED}")
    return seed


def run_full_simulation(
    decisions: object,
    *,
    seed: int | None = None,
    parameters: ModelParameters | None = None,
) -> dict:
    validated_decisions = validate_decisions(decisions)
    seed = validate_seed(seed)
    if parameters is None:
        from .config import PARAMETERS

        parameters = PARAMETERS
    validate_parameters(parameters)

    rng = random.Random(seed)
    weather_event = simulate_weather(parameters, rng)
    farm_size_bigha = float(validated_decisions["farm_size_bigha"])
    gross_yield_tonnes = calculate_yield(
        farm_size_bigha,
        validated_decisions["seed_quality"],
        validated_decisions["fertilizer_type"],
        weather_event,
        parameters,
    )
    cost_breakdown_bdt = calculate_cost_breakdown(
        farm_size_bigha,
        validated_decisions["seed_quality"],
        validated_decisions["fertilizer_type"],
        validated_decisions["labor_choice"],
        validated_decisions["irrigation_choice"],
        parameters,
    )
    total_costs_bdt = sum(cost_breakdown_bdt.values())
    price_bdt_per_40kg = simulate_market_price(
        validated_decisions["sell_or_store"], parameters
    )
    spoiled, saleable_fraction = simulate_storage_loss(
        validated_decisions["sell_or_store"], parameters, rng
    )
    saleable_yield_tonnes = gross_yield_tonnes * saleable_fraction

    # One tonne contains 25 units of 40 kg.
    revenue_bdt = saleable_yield_tonnes * 25 * price_bdt_per_40kg
    calculated_values = (
        gross_yield_tonnes,
        saleable_yield_tonnes,
        total_costs_bdt,
        price_bdt_per_40kg,
        revenue_bdt,
    )
    if not all(math.isfinite(value) for value in calculated_values):
        raise DecisionValidationError(
            "The selected farm size exceeds the supported calculation range"
        )
    result = build_diagnostic(
        revenue_bdt=revenue_bdt,
        costs_bdt=total_costs_bdt,
        cost_breakdown_bdt=cost_breakdown_bdt,
        gross_yield_tonnes=gross_yield_tonnes,
        saleable_yield_tonnes=saleable_yield_tonnes,
        market_price_bdt_per_40kg=price_bdt_per_40kg,
        decisions=validated_decisions,
        events={"weather": weather_event, "storage_spoiled": spoiled},
    )
    return {
        "model_version": parameters.model_version,
        "data_version": parameters.data_version,
        "seed": seed,
        "gross_yield_tonnes": round(gross_yield_tonnes, 4),
        "saleable_yield_tonnes": round(saleable_yield_tonnes, 4),
        "total_costs_bdt": round(total_costs_bdt, 2),
        "cost_breakdown_bdt": {
            key: round(value, 2) for key, value in cost_breakdown_bdt.items()
        },
        "market_price_bdt_per_40kg": round(price_bdt_per_40kg, 2),
        "gross_revenue_bdt": round(revenue_bdt, 2),
        **result,
    }
