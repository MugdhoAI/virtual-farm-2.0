import random

from .models import ModelParameters
from .validation import ModelDataError


def simulate_market_price(sell_or_store: str, parameters: ModelParameters) -> float:
    scenario = parameters.market_scenarios.get(sell_or_store)
    if scenario is None:
        raise ModelDataError(f"Market scenario {sell_or_store!r} is not configured")
    if scenario.price_bdt_per_40kg is None or scenario.price_multiplier is None:
        raise ModelDataError("Producer-side paddy price data is not configured")
    return scenario.price_bdt_per_40kg * scenario.price_multiplier


def simulate_storage_loss(
    sell_or_store: str,
    parameters: ModelParameters,
    rng: random.Random,
) -> tuple[bool, float]:
    scenario = parameters.market_scenarios.get(sell_or_store)
    if scenario is None:
        raise ModelDataError(f"Market scenario {sell_or_store!r} is not configured")
    if scenario.spoilage_probability is None or scenario.spoilage_effect is None:
        raise ModelDataError("Storage spoilage data is not configured")
    spoiled = (
        sell_or_store == "store"
        and rng.random() < scenario.spoilage_probability
    )
    saleable_fraction = 1.0 - scenario.spoilage_effect if spoiled else 1.0
    return spoiled, saleable_fraction
