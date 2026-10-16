from dataclasses import dataclass, field
from typing import Literal

WeatherEvent = Literal["ideal", "mild_stress", "severe_event"]
SeedQuality = Literal["local", "brri_certified"]
FertilizerType = Literal["organic", "chemical"]
LaborChoice = Literal["seasonal_workers", "power_tiller"]
IrrigationChoice = Literal["rainfed", "pump"]
SaleChoice = Literal["sell", "store"]


@dataclass(frozen=True)
class Choice:
    key: str
    cost_bdt_per_bigha: float | None
    yield_multiplier: float | None = None
    source: str = ""


@dataclass(frozen=True)
class WeatherScenario:
    key: WeatherEvent
    probability: float | None
    yield_multiplier: float | None
    source: str = ""


@dataclass(frozen=True)
class MarketScenario:
    key: SaleChoice
    price_bdt_per_40kg: float | None
    price_multiplier: float | None = None
    spoilage_probability: float | None = None
    spoilage_effect: float | None = None
    source: str = ""


@dataclass(frozen=True)
class DataRecord:
    value: float | None
    unit: str
    required_source_institution: str
    source_institution: str | None
    source_document: str | None
    source_year: str | None
    geographic_scope: str | None
    methodology: str | None
    provenance: str | None


@dataclass(frozen=True)
class ModelParameters:
    base_yield_tonnes_per_bigha: float | None
    seed_choices: dict[str, Choice]
    fertilizer_choices: dict[str, Choice]
    labor_choices: dict[str, Choice]
    irrigation_choices: dict[str, Choice]
    weather_scenarios: dict[str, WeatherScenario]
    market_scenarios: dict[str, MarketScenario]
    model_version: str
    data_version: str
    data_records: dict[str, DataRecord] = field(default_factory=dict)
    invalid_data_records: tuple[str, ...] = ()
    is_production_data: bool = False
    full_economic_costs_implemented: bool = False
