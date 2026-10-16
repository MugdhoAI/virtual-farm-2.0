import sys
from dataclasses import replace
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from simulation.config import PARAMETERS
from simulation.models import Choice, MarketScenario, WeatherScenario


@pytest.fixture
def complete_test_parameters():
    """Synthetic arithmetic inputs only; this fixture is never production data."""
    return replace(
        PARAMETERS,
        base_yield_tonnes_per_bigha=2.0,
        seed_choices={
            "local": Choice("local", 13.0, 1.0),
            "brri_certified": Choice("brri_certified", 17.0, 1.2),
        },
        fertilizer_choices={
            "organic": Choice("organic", 19.0, 1.1),
            "chemical": Choice("chemical", 23.0, 1.3),
        },
        labor_choices={
            "seasonal_workers": Choice("seasonal_workers", 29.0),
            "power_tiller": Choice("power_tiller", 31.0),
        },
        irrigation_choices={
            "rainfed": Choice("rainfed", 0.0),
            "pump": Choice("pump", 37.0),
        },
        weather_scenarios={
            "ideal": WeatherScenario("ideal", 0.25, 1.0, "synthetic test fixture"),
            "mild_stress": WeatherScenario(
                "mild_stress", 0.35, 0.8, "synthetic test fixture"
            ),
            "severe_event": WeatherScenario(
                "severe_event", 0.4, 0.5, "synthetic test fixture"
            ),
        },
        market_scenarios={
            "sell": MarketScenario("sell", 20.0, 1.0, 0.0, 0.0, "test fixture"),
            "store": MarketScenario("store", 20.0, 1.25, 1.0, 0.5, "test fixture"),
        },
        model_version="synthetic-test-model",
        data_version="synthetic-test-data",
        invalid_data_records=(),
        is_production_data=False,
    )
