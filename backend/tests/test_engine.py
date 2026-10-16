import json

import pytest

from simulation.config import MODEL_DATA_PATH, PARAMETERS, load_parameters
from simulation.engine import run_full_simulation
from simulation.validation import (
    DecisionValidationError,
    ModelDataError,
    validate_decisions,
    validate_parameters,
)

DECISIONS = {
    "farm_size_bigha": 1,
    "seed_quality": "brri_certified",
    "fertilizer_type": "organic",
    "labor_choice": "power_tiller",
    "irrigation_choice": "pump",
    "sell_or_store": "sell",
}


def test_production_parameters_fail_closed_with_named_missing_sources():
    with pytest.raises(ModelDataError) as error:
        validate_parameters(PARAMETERS)

    message = str(error.value)
    assert "yield.base_tonnes_per_bigha (required source: BBS)" in message
    assert "labor.seasonal_workers.cost_bdt_per_bigha (required source: DAE)" in message
    assert "market.base_price_bdt_per_40kg (required source: FPMU)" in message
    assert error.value.missing_inputs
    assert PARAMETERS.data_version.startswith("boro-production-data-unconfigured-v1+sha256-")


def test_production_data_manifest_contains_provenance_fields_for_each_input():
    raw = json.loads(MODEL_DATA_PATH.read_text(encoding="utf-8"))
    expected = {
        "value",
        "unit",
        "required_source_institution",
        "source_institution",
        "source_document",
        "source_year",
        "geographic_scope",
        "methodology",
        "provenance",
    }
    assert raw["model_version"] == PARAMETERS.model_version
    assert PARAMETERS.data_version.startswith(raw["data_version"] + "+sha256-")
    assert all(expected <= record.keys() for record in raw["records"].values())
    assert all(record["value"] is None for record in raw["records"].values())


def test_populated_input_without_provenance_is_not_usable(tmp_path):
    raw = json.loads(MODEL_DATA_PATH.read_text(encoding="utf-8"))
    raw["records"]["yield.base_tonnes_per_bigha"]["value"] = 2.0
    data_path = tmp_path / "production_model.json"
    data_path.write_text(json.dumps(raw), encoding="utf-8")

    parameters = load_parameters(data_path)

    assert parameters.base_yield_tonnes_per_bigha is None
    assert any("yield.base_tonnes_per_bigha" in item for item in parameters.invalid_data_records)
    assert parameters.data_version != PARAMETERS.data_version


def test_documented_weather_probabilities_are_not_loaded_as_verified_data():
    raw = json.loads(MODEL_DATA_PATH.read_text(encoding="utf-8"))
    documented = raw["documented_rules"]["weather_scenario_probabilities"]

    assert documented["ideal"] == 0.4
    assert documented["mild_stress"] == 0.35
    assert documented["severe_event"] == 0.25
    assert "not loaded as production data" in documented["status"]
    assert all(scenario.probability is None for scenario in PARAMETERS.weather_scenarios.values())


def test_all_six_decisions_are_validated():
    assert validate_decisions(DECISIONS) == DECISIONS
    for field in DECISIONS:
        invalid = dict(DECISIONS)
        del invalid[field]
        with pytest.raises(DecisionValidationError):
            validate_decisions(invalid)


@pytest.mark.parametrize("farm_size", [1, 1.0, 3, 3.0])
def test_supported_farm_sizes_are_accepted(farm_size):
    decisions = dict(DECISIONS, farm_size_bigha=farm_size)

    assert validate_decisions(decisions) == decisions


@pytest.mark.parametrize(
    "farm_size", [0, -1, 1.5, 2, 4, float("nan"), float("inf"), True, "1"]
)
def test_invalid_farm_size_is_rejected(farm_size):
    decisions = dict(DECISIONS, farm_size_bigha=farm_size)

    with pytest.raises(DecisionValidationError):
        validate_decisions(decisions)


def test_invalid_decision_choice_and_unexpected_field_are_rejected():
    with pytest.raises(DecisionValidationError, match="seed_quality"):
        validate_decisions(dict(DECISIONS, seed_quality="unknown"))
    with pytest.raises(DecisionValidationError, match="Unexpected decisions"):
        validate_decisions(dict(DECISIONS, extra=True))


def test_complete_test_fixture_runs_with_structured_diagnostics(complete_test_parameters):
    result = run_full_simulation(
        DECISIONS, seed=4, parameters=complete_test_parameters
    )

    assert result["gross_yield_tonnes"] > 0
    expected_weather_multiplier = complete_test_parameters.weather_scenarios[
        result["events"]["weather"]
    ].yield_multiplier
    assert result["gross_yield_tonnes"] == pytest.approx(
        DECISIONS["farm_size_bigha"] * 2.0 * 1.2 * 1.1 * expected_weather_multiplier
    )
    assert result["total_costs_bdt"] == 104.0
    assert result["cost_breakdown_bdt"] == {
        "seed": 17.0,
        "fertilizer": 19.0,
        "labor": 31.0,
        "irrigation": 37.0,
    }
    assert result["gross_revenue_bdt"] >= 0
    assert result["gross_revenue_bdt"] == pytest.approx(
        result["saleable_yield_tonnes"] * 25 * result["market_price_bdt_per_40kg"]
    )
    assert result["net_profit_bdt"] == pytest.approx(
        result["gross_revenue_bdt"] - result["total_costs_bdt"]
    )
    assert result["diagnostic"]["profit"]["net_profit_bdt"] == result["net_profit_bdt"]
    assert result["model_version"] == "synthetic-test-model"
    assert result["data_version"] == "synthetic-test-data"


def test_same_seed_and_inputs_reproduce_identical_result(complete_test_parameters):
    first = run_full_simulation(DECISIONS, seed=1234, parameters=complete_test_parameters)
    second = run_full_simulation(DECISIONS, seed=1234, parameters=complete_test_parameters)

    assert first == second
    assert first["seed"] == 1234


def test_each_decision_is_applied_to_its_documented_calculation(complete_test_parameters):
    base = run_full_simulation(DECISIONS, seed=21, parameters=complete_test_parameters)

    larger_farm = run_full_simulation(
        dict(DECISIONS, farm_size_bigha=3),
        seed=21,
        parameters=complete_test_parameters,
    )
    local_seed = run_full_simulation(
        dict(DECISIONS, seed_quality="local"),
        seed=21,
        parameters=complete_test_parameters,
    )
    chemical_fertilizer = run_full_simulation(
        dict(DECISIONS, fertilizer_type="chemical"),
        seed=21,
        parameters=complete_test_parameters,
    )
    seasonal_labor = run_full_simulation(
        dict(DECISIONS, labor_choice="seasonal_workers"),
        seed=21,
        parameters=complete_test_parameters,
    )
    rainfed = run_full_simulation(
        dict(DECISIONS, irrigation_choice="rainfed"),
        seed=21,
        parameters=complete_test_parameters,
    )
    stored = run_full_simulation(
        dict(DECISIONS, sell_or_store="store"),
        seed=21,
        parameters=complete_test_parameters,
    )

    assert larger_farm["gross_yield_tonnes"] == 3 * base["gross_yield_tonnes"]
    assert larger_farm["total_costs_bdt"] == 3 * base["total_costs_bdt"]
    assert local_seed["gross_yield_tonnes"] < base["gross_yield_tonnes"]
    assert local_seed["cost_breakdown_bdt"]["seed"] < base["cost_breakdown_bdt"]["seed"]
    assert chemical_fertilizer["gross_yield_tonnes"] > base["gross_yield_tonnes"]
    assert (
        chemical_fertilizer["cost_breakdown_bdt"]["fertilizer"]
        > base["cost_breakdown_bdt"]["fertilizer"]
    )
    assert seasonal_labor["gross_yield_tonnes"] == base["gross_yield_tonnes"]
    assert seasonal_labor["cost_breakdown_bdt"]["labor"] < base["cost_breakdown_bdt"]["labor"]
    assert rainfed["gross_yield_tonnes"] == base["gross_yield_tonnes"]
    assert rainfed["cost_breakdown_bdt"]["irrigation"] < base["cost_breakdown_bdt"]["irrigation"]
    assert stored["market_price_bdt_per_40kg"] > base["market_price_bdt_per_40kg"]


def test_storage_spoilage_is_seeded_and_reduces_saleable_yield(complete_test_parameters):
    decisions = dict(DECISIONS, sell_or_store="store")

    result = run_full_simulation(decisions, seed=42, parameters=complete_test_parameters)

    assert result["events"]["storage_spoiled"] is True
    assert result["saleable_yield_tonnes"] == result["gross_yield_tonnes"] / 2


def test_extreme_finite_farm_size_is_rejected_by_decision_validation(
    complete_test_parameters,
):
    decisions = dict(DECISIONS, farm_size_bigha=1e308)

    with pytest.raises(DecisionValidationError, match="1 or 3 bigha"):
        run_full_simulation(decisions, seed=42, parameters=complete_test_parameters)


@pytest.mark.parametrize("seed", [-1, True, 1.5, "1", 1 << 64])
def test_invalid_seed_is_rejected(seed, complete_test_parameters):
    with pytest.raises(DecisionValidationError, match="seed"):
        run_full_simulation(DECISIONS, seed=seed, parameters=complete_test_parameters)
