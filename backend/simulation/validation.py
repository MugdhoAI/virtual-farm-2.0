import math
from collections.abc import Mapping

from .models import ModelParameters


class DecisionValidationError(ValueError):
    pass


class ModelDataError(Exception):
    def __init__(self, message: str, *, missing_inputs: tuple[str, ...] = ()):
        super().__init__(message)
        self.missing_inputs = missing_inputs


DECISION_KEYS = frozenset(
    {
        "farm_size_bigha",
        "seed_quality",
        "fertilizer_type",
        "labor_choice",
        "irrigation_choice",
        "sell_or_store",
    }
)
SUPPORTED_FARM_SIZES_BIGHA = (1, 3)


def validate_decisions(decisions: object) -> dict:
    if not isinstance(decisions, dict):
        raise DecisionValidationError("decisions must be an object")

    if not all(isinstance(key, str) for key in decisions):
        raise DecisionValidationError("decision names must be strings")
    missing = sorted(DECISION_KEYS - decisions.keys())
    unexpected = sorted(decisions.keys() - DECISION_KEYS)
    if missing:
        raise DecisionValidationError(f"Missing decisions: {', '.join(missing)}")
    if unexpected:
        raise DecisionValidationError(f"Unexpected decisions: {', '.join(unexpected)}")

    farm_size = decisions["farm_size_bigha"]
    try:
        finite_farm_size = (
            not isinstance(farm_size, bool)
            and isinstance(farm_size, (int, float))
            and math.isfinite(float(farm_size))
        )
    except (OverflowError, ValueError):
        finite_farm_size = False
    if not finite_farm_size or farm_size not in SUPPORTED_FARM_SIZES_BIGHA:
        raise DecisionValidationError("farm_size_bigha must be 1 or 3 bigha")

    choice_fields = {
        "seed_quality": {"local", "brri_certified"},
        "fertilizer_type": {"organic", "chemical"},
        "labor_choice": {"seasonal_workers", "power_tiller"},
        "irrigation_choice": {"rainfed", "pump"},
        "sell_or_store": {"sell", "store"},
    }
    for field, allowed in choice_fields.items():
        value = decisions[field]
        if not isinstance(value, str) or value not in allowed:
            choices = ", ".join(sorted(allowed))
            raise DecisionValidationError(f"{field} must be one of: {choices}")

    return decisions


def validate_parameters(parameters: ModelParameters) -> None:
    missing: list[str] = []
    if parameters.invalid_data_records:
        raise ModelDataError(
            "Production model data contains invalid records: "
            + "; ".join(parameters.invalid_data_records)
        )

    for name, choices, expected in (
        ("seed", parameters.seed_choices, {"local", "brri_certified"}),
        ("fertilizer", parameters.fertilizer_choices, {"organic", "chemical"}),
        ("labor", parameters.labor_choices, {"seasonal_workers", "power_tiller"}),
        ("irrigation", parameters.irrigation_choices, {"rainfed", "pump"}),
        (
            "weather",
            parameters.weather_scenarios,
            {"ideal", "mild_stress", "severe_event"},
        ),
        ("market", parameters.market_scenarios, {"sell", "store"}),
    ):
        absent = sorted(expected - choices.keys())
        unexpected = sorted(choices.keys() - expected)
        if absent or unexpected:
            raise ModelDataError(
                f"Production model {name} scenarios must be exactly "
                f"{', '.join(sorted(expected))}"
            )

    def require(name: str, value: float | None) -> None:
        if value is None:
            missing.append(name)
        elif not math.isfinite(value):
            raise ModelDataError(f"{name} must be finite")

    require("yield.base_tonnes_per_bigha", parameters.base_yield_tonnes_per_bigha)
    if parameters.base_yield_tonnes_per_bigha is not None and parameters.base_yield_tonnes_per_bigha <= 0:
        raise ModelDataError("yield.base_tonnes_per_bigha must be greater than zero")

    for group_name, group in (
        ("seed", parameters.seed_choices),
        ("fertilizer", parameters.fertilizer_choices),
        ("labor", parameters.labor_choices),
        ("irrigation", parameters.irrigation_choices),
    ):
        for key, choice in group.items():
            cost_name = f"{group_name}.{key}.cost_bdt_per_bigha"
            require(cost_name, choice.cost_bdt_per_bigha)
            if choice.cost_bdt_per_bigha is not None and choice.cost_bdt_per_bigha < 0:
                raise ModelDataError(f"{cost_name} cannot be negative")

    for group_name, group in (
        ("seed", parameters.seed_choices),
        ("fertilizer", parameters.fertilizer_choices),
    ):
        for key, choice in group.items():
            name = f"{group_name}.{key}.yield_multiplier"
            require(name, choice.yield_multiplier)
            if choice.yield_multiplier is not None and choice.yield_multiplier < 0:
                raise ModelDataError(f"{name} cannot be negative")

    for key, scenario in parameters.weather_scenarios.items():
        probability_name = f"weather.{key}.probability"
        require(probability_name, scenario.probability)
        require(f"weather.{key}.yield_multiplier", scenario.yield_multiplier)
        if scenario.probability is not None and not 0 <= scenario.probability <= 1:
            raise ModelDataError(f"{probability_name} must be between 0 and 1")
        if scenario.yield_multiplier is not None and scenario.yield_multiplier < 0:
            raise ModelDataError(f"weather.{key}.yield_multiplier cannot be negative")

    if all(scenario.probability is not None for scenario in parameters.weather_scenarios.values()):
        probability_sum = sum(
            scenario.probability
            for scenario in parameters.weather_scenarios.values()
            if scenario.probability is not None
        )
        if not math.isclose(probability_sum, 1.0, rel_tol=0.0, abs_tol=1e-9):
            raise ModelDataError("Weather probabilities must sum to 1.0")

    require(
        "market.base_price_bdt_per_40kg",
        next(iter(parameters.market_scenarios.values())).price_bdt_per_40kg,
    )
    for key, scenario in parameters.market_scenarios.items():
        require(f"market.{key}.price_multiplier", scenario.price_multiplier)
        require(f"market.{key}.spoilage_probability", scenario.spoilage_probability)
        require(f"market.{key}.spoilage_fraction", scenario.spoilage_effect)
        if scenario.price_bdt_per_40kg is not None and scenario.price_bdt_per_40kg < 0:
            raise ModelDataError(f"market.{key}.price_bdt_per_40kg cannot be negative")
        if scenario.price_multiplier is not None and scenario.price_multiplier <= 0:
            raise ModelDataError(f"market.{key}.price_multiplier must be greater than zero")
        if scenario.spoilage_probability is not None and not 0 <= scenario.spoilage_probability <= 1:
            raise ModelDataError(f"market.{key}.spoilage_probability must be between 0 and 1")
        if scenario.spoilage_effect is not None and not 0 <= scenario.spoilage_effect <= 1:
            raise ModelDataError(f"market.{key}.spoilage_fraction must be between 0 and 1")

    if parameters.is_production_data and not parameters.full_economic_costs_implemented:
        missing.extend(
            (
                "cost.full_economic_category_coverage",
                "cost.six_decision_cost_mapping",
            )
        )

    if missing:
        details = []
        for name in missing:
            record = parameters.data_records.get(name)
            if record is not None:
                details.append(f"{name} (required source: {record.required_source_institution})")
            else:
                details.append(name)
        raise ModelDataError(
            "Production model data is incomplete; refusing to use invented values: "
            + ", ".join(details),
            missing_inputs=tuple(missing),
        )

    if parameters.is_production_data:
        if not parameters.model_version or not parameters.data_version:
            raise ModelDataError("Production model and data versions are required")
        for name, record in parameters.data_records.items():
            if record.value is None:
                continue
            provenance: Mapping[str, object] = {
                "source_institution": record.source_institution,
                "source_document": record.source_document,
                "source_year": record.source_year,
                "geographic_scope": record.geographic_scope,
                "methodology": record.methodology,
                "provenance": record.provenance,
            }
            absent = [key for key, value in provenance.items() if not value]
            if absent:
                raise ModelDataError(
                    f"Production input {name} has incomplete provenance: {', '.join(absent)}"
                )
