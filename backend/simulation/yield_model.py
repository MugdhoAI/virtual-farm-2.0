from .models import ModelParameters
from .validation import ModelDataError


def _required(value: float | None, name: str) -> float:
    if value is None:
        raise ModelDataError(f"Yield input {name} is not configured")
    return value


def calculate_yield(
    farm_size_bigha: float,
    seed_quality: str,
    fertilizer_type: str,
    weather_event: str,
    parameters: ModelParameters,
) -> float:
    if farm_size_bigha <= 0:
        raise ValueError("farm_size_bigha must be greater than zero")
    try:
        seed = parameters.seed_choices[seed_quality]
        fertilizer = parameters.fertilizer_choices[fertilizer_type]
        weather = parameters.weather_scenarios[weather_event]
    except KeyError as exc:
        raise ValueError(f"Unknown simulation choice: {exc.args[0]}") from exc

    return (
        farm_size_bigha
        * _required(parameters.base_yield_tonnes_per_bigha, "base_tonnes_per_bigha")
        * _required(seed.yield_multiplier, f"seed.{seed_quality}.yield_multiplier")
        * _required(
            fertilizer.yield_multiplier,
            f"fertilizer.{fertilizer_type}.yield_multiplier",
        )
        * _required(weather.yield_multiplier, f"weather.{weather_event}.yield_multiplier")
    )
