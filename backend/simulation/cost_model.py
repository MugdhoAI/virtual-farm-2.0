from .models import ModelParameters
from .validation import ModelDataError


def calculate_cost_breakdown(
    farm_size_bigha: float,
    seed_quality: str,
    fertilizer_type: str,
    labor_choice: str,
    irrigation_choice: str,
    parameters: ModelParameters,
) -> dict[str, float]:
    if farm_size_bigha <= 0:
        raise ValueError("farm_size_bigha must be greater than zero")

    choices = {
        "seed": parameters.seed_choices[seed_quality],
        "fertilizer": parameters.fertilizer_choices[fertilizer_type],
        "labor": parameters.labor_choices[labor_choice],
        "irrigation": parameters.irrigation_choices[irrigation_choice],
    }
    breakdown = {}
    for name, choice in choices.items():
        if choice.cost_bdt_per_bigha is None:
            raise ModelDataError(f"Cost data for {name} choice {choice.key!r} is not configured")
        breakdown[name] = farm_size_bigha * choice.cost_bdt_per_bigha
    return breakdown


def calculate_costs(
    farm_size_bigha: float,
    seed_quality: str,
    fertilizer_type: str,
    labor_choice: str,
    irrigation_choice: str,
    parameters: ModelParameters,
) -> float:
    return sum(
        calculate_cost_breakdown(
            farm_size_bigha,
            seed_quality,
            fertilizer_type,
            labor_choice,
            irrigation_choice,
            parameters,
        ).values()
    )
