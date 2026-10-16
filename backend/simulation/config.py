import hashlib
import json
import math
from pathlib import Path
import re
from typing import Any

from .models import (
    Choice,
    DataRecord,
    MarketScenario,
    ModelParameters,
    WeatherEvent,
    WeatherScenario,
)
from .validation import ModelDataError

MODEL_DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "production_model.json"
FULL_ECONOMIC_COSTS_IMPLEMENTED = False


def _as_number(record: DataRecord) -> float | None:
    if record.value is None:
        return None
    source_fields = (
        record.unit,
        record.required_source_institution,
        record.source_institution,
        record.source_document,
        record.source_year,
        record.geographic_scope,
        record.methodology,
        record.provenance,
    )
    if not all(isinstance(value, str) and value.strip() for value in source_fields):
        return None
    allowed_sources = {
        source.strip()
        for source in record.required_source_institution.split("/")
        if source.strip()
    }
    if record.source_institution not in allowed_sources:
        return None
    if not record.source_year or not re.fullmatch(
        r"\d{4}(?:[-/]\d{2,4})?", record.source_year
    ):
        return None
    return record.value


def load_parameters(path: Path = MODEL_DATA_PATH) -> ModelParameters:
    try:
        raw: Any = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ModelDataError(f"Unable to load production model data from {path}") from exc

    if not isinstance(raw, dict) or not isinstance(raw.get("records"), dict):
        raise ModelDataError("Production model data must contain a records object")
    if not isinstance(raw.get("model_version"), str) or not raw["model_version"].strip():
        raise ModelDataError("Production model data must declare a model_version")
    if not isinstance(raw.get("data_version"), str) or not raw["data_version"].strip():
        raise ModelDataError("Production model data must declare a data_version")
    try:
        serialized_records = json.dumps(
            raw["records"], sort_keys=True, separators=(",", ":"), allow_nan=False
        )
    except (TypeError, ValueError) as exc:
        raise ModelDataError("Production data records are not valid JSON values") from exc
    fingerprint = hashlib.sha256(serialized_records.encode("utf-8")).hexdigest()[:12]

    records: dict[str, DataRecord] = {}
    invalid_records: list[str] = []
    metadata_fields = (
        "unit",
        "required_source_institution",
        "source_institution",
        "source_document",
        "source_year",
        "geographic_scope",
        "methodology",
        "provenance",
    )
    for key, item in raw["records"].items():
        if not isinstance(item, dict):
            raise ModelDataError(f"Production data record {key!r} must be an object")
        value = item.get("value")
        if value is not None:
            try:
                valid_number = (
                    not isinstance(value, bool)
                    and isinstance(value, (int, float))
                    and math.isfinite(float(value))
                )
            except (OverflowError, ValueError):
                valid_number = False
            if not valid_number:
                invalid_records.append(f"{key}: value must be a finite number")
                value = None

        data_record = DataRecord(
            value=float(value) if value is not None else None,
            unit=(
                item.get("unit", "")
                if isinstance(item.get("unit", ""), str)
                else ""
            ),
            required_source_institution=(
                item.get("required_source_institution", "")
                if isinstance(item.get("required_source_institution", ""), str)
                else ""
            ),
            source_institution=item.get("source_institution"),
            source_document=item.get("source_document"),
            source_year=str(item["source_year"]) if item.get("source_year") is not None else None,
            geographic_scope=item.get("geographic_scope"),
            methodology=item.get("methodology"),
            provenance=item.get("provenance"),
        )
        if value is not None:
            missing_metadata = [
                name
                for name in metadata_fields
                if not isinstance(getattr(data_record, name), str)
                or not getattr(data_record, name).strip()
            ]
            allowed_sources = {
                source.strip()
                for source in data_record.required_source_institution.split("/")
                if source.strip()
            }
            if (
                not isinstance(data_record.source_institution, str)
                or data_record.source_institution not in allowed_sources
            ):
                missing_metadata.append(
                    f"source_institution must be one of: {', '.join(sorted(allowed_sources))}"
                )
            if not data_record.source_year or not re.fullmatch(
                r"\d{4}(?:[-/]\d{2,4})?", data_record.source_year
            ):
                missing_metadata.append("source_year must identify the source year or period")
            if missing_metadata:
                invalid_records.append(
                    f"{key}: missing provenance fields: {', '.join(missing_metadata)}"
                )
        records[key] = data_record

    def number(key: str) -> float | None:
        record = records.get(key)
        if record is None:
            invalid_records.append(f"{key}: record is missing")
            return None
        if record.value is not None and _as_number(record) is None:
            return None
        return _as_number(record)

    def choices(
        group: str,
        keys: tuple[str, ...],
        *,
        with_yield_multiplier: bool,
    ) -> dict[str, Choice]:
        return {
            key: Choice(
                key=key,
                cost_bdt_per_bigha=number(f"{group}.{key}.cost_bdt_per_bigha"),
                yield_multiplier=(
                    number(f"{group}.{key}.yield_multiplier")
                    if with_yield_multiplier
                    else None
                ),
            )
            for key in keys
        }

    weather_keys: tuple[WeatherEvent, ...] = ("ideal", "mild_stress", "severe_event")
    weather = {
        key: WeatherScenario(
            key=key,
            probability=number(f"weather.{key}.probability"),
            yield_multiplier=number(f"weather.{key}.yield_multiplier"),
        )
        for key in weather_keys
    }
    base_price = number("market.base_price_bdt_per_40kg")
    market = {
        "sell": MarketScenario(
            key="sell",
            price_bdt_per_40kg=base_price,
            price_multiplier=1.0,
            spoilage_probability=0.0,
            spoilage_effect=0.0,
        ),
        "store": MarketScenario(
            key="store",
            price_bdt_per_40kg=base_price,
            price_multiplier=number("market.store.price_multiplier"),
            spoilage_probability=number("market.store.spoilage_probability"),
            spoilage_effect=number("market.store.spoilage_fraction"),
        ),
    }
    return ModelParameters(
        base_yield_tonnes_per_bigha=number("yield.base_tonnes_per_bigha"),
        seed_choices=choices(
            "seed", ("local", "brri_certified"), with_yield_multiplier=True
        ),
        fertilizer_choices=choices(
            "fertilizer", ("organic", "chemical"), with_yield_multiplier=True
        ),
        labor_choices=choices(
            "labor", ("seasonal_workers", "power_tiller"), with_yield_multiplier=False
        ),
        irrigation_choices=choices(
            "irrigation", ("rainfed", "pump"), with_yield_multiplier=False
        ),
        weather_scenarios=weather,
        market_scenarios=market,
        model_version=str(raw.get("model_version", "")),
        data_version=f"{raw.get('data_version', '')}+sha256-{fingerprint}",
        data_records=records,
        invalid_data_records=tuple(invalid_records),
        is_production_data=True,
        full_economic_costs_implemented=FULL_ECONOMIC_COSTS_IMPLEMENTED,
    )


PARAMETERS = load_parameters()
