import random
from .models import ModelParameters, WeatherEvent
from .validation import ModelDataError


def simulate_weather(parameters: ModelParameters, rng: random.Random | None = None) -> WeatherEvent:
    rng = rng if rng is not None else random.Random()
    scenarios = list(parameters.weather_scenarios.values())
    if not scenarios or any(scenario.probability is None for scenario in scenarios):
        raise ModelDataError("Weather probabilities are not configured")
    draw = rng.random()
    cumulative = 0.0
    for scenario in scenarios:
        cumulative += scenario.probability or 0.0
        if draw < cumulative:
            return scenario.key
    return scenarios[-1].key  # defensive floating-point fallback
