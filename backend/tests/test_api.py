import sqlite3
from dataclasses import replace
from pathlib import Path

import app as app_module
import early_access as early_access_module
import pytest
from app import app

DECISIONS = {
    "farm_size_bigha": 1,
    "seed_quality": "brri_certified",
    "fertilizer_type": "organic",
    "labor_choice": "power_tiller",
    "irrigation_choice": "pump",
    "sell_or_store": "sell",
}


@pytest.fixture(autouse=True)
def isolated_signup_database(tmp_path, monkeypatch):
    monkeypatch.setitem(
        app.config,
        "EARLY_ACCESS_DATABASE",
        str(tmp_path / "early_access.sqlite3"),
    )
    monkeypatch.setattr(early_access_module, "_signup_attempts", {})


def test_health():
    response = app.test_client().get("/health")

    assert response.status_code == 200
    assert response.json["status"] == "ok"


def test_root_serves_the_connected_six_decision_form():
    response = app.test_client().get("/")
    html = response.get_data(as_text=True)
    decision_controls = (
        "sim-farm-size",
        "sim-seed-quality",
        "sim-fertilizer",
        "sim-labor",
        "sim-irrigation",
        "sim-sale",
    )
    unavailable_example_values = (
        "BDT 1,200/bigha",
        "4.2 t",
        "39%",
        "8% yield uplift",
        "15% chance of 10% yield reduction",
        "BDT −3,200",
        "Mild stress weather event this season",
        "+8,400",
        "+14,800",
        "Rahim Uddin",
    )

    assert response.status_code == 200
    assert response.mimetype == "text/html"
    assert 'id="early-access-form"' in html
    assert 'id="early-access-email"' in html
    assert 'id="early-access-submit"' in html
    assert 'id="simulation-form"' in html
    assert 'fetch(\'/simulate\'' in html
    assert all(f'id="{control}"' in html for control in decision_controls)
    assert 'id="simulation-error"' in html
    assert 'id="simulation-result"' in html
    assert 'id="simulation-result-title" tabindex="-1"' in html
    assert 'id="simulation-replay"' in html
    assert 'id="simulation-reset"' in html
    assert 'id="simulation-result-reset"' in html
    assert all(value not in html for value in unavailable_example_values)


def test_early_access_signup_persists_normalized_email_without_echoing_it():
    email = "  Virtual.Farm+Test@Example.COM  "

    response = app.test_client().post("/early-access", json={"email": email})

    assert response.status_code == 201
    assert response.json == {
        "status": "subscribed",
        "message": "You’re on the early-access list.",
    }
    assert email not in response.get_data(as_text=True)
    with sqlite3.connect(app.config["EARLY_ACCESS_DATABASE"]) as connection:
        rows = connection.execute(
            "SELECT email, created_at FROM early_access_subscribers"
        ).fetchall()
    assert len(rows) == 1
    assert rows[0][0] == "virtual.farm+test@example.com"
    assert rows[0][1]


@pytest.mark.parametrize(
    "email",
    [
        "",
        "not-an-email",
        "name@localhost",
        "name..last@example.com",
        ".name@example.com",
        "name@example..com",
    ],
)
def test_early_access_rejects_invalid_email(email):
    response = app.test_client().post("/early-access", json={"email": email})

    assert response.status_code == 400
    assert response.json["error"] == "invalid_email"
    assert "email" not in response.json


def test_early_access_rejects_missing_email():
    response = app.test_client().post("/early-access", json={})

    assert response.status_code == 400
    assert response.json == {
        "error": "invalid_request",
        "message": "An email address is required.",
    }


def test_early_access_rejects_malformed_and_non_json_requests():
    client = app.test_client()

    malformed = client.post(
        "/early-access",
        data='{"email":',
        content_type="application/json",
    )
    non_json = client.post("/early-access", data='{"email":"person@example.com"}')

    assert malformed.status_code == 400
    assert malformed.json["error"] == "invalid_request"
    assert non_json.status_code == 400
    assert non_json.json["error"] == "invalid_request"


def test_early_access_bounds_request_size():
    response = app.test_client().post(
        "/early-access",
        json={"email": "a" * 5000},
    )

    assert response.status_code == 413
    assert response.json["error"] == "request_too_large"


def test_early_access_rate_limits_repeated_requests():
    client = app.test_client()

    for index in range(early_access_module.SIGNUP_RATE_LIMIT):
        response = client.post(
            "/early-access",
            json={"email": f"person{index}@example.com"},
        )
        assert response.status_code == 201

    limited = client.post(
        "/early-access",
        json={"email": "another@example.com"},
    )

    assert limited.status_code == 429
    assert limited.json["error"] == "rate_limited"
    assert "another@example.com" not in limited.get_data(as_text=True)


def test_early_access_normalizes_internationalized_domain():
    response = app.test_client().post(
        "/early-access",
        json={"email": "person@bücher.de"},
    )

    assert response.status_code == 201
    with sqlite3.connect(app.config["EARLY_ACCESS_DATABASE"]) as connection:
        stored_email = connection.execute(
            "SELECT email FROM early_access_subscribers"
        ).fetchone()[0]
    assert stored_email == "person@xn--bcher-kva.de"


def test_early_access_duplicate_is_case_insensitive_and_does_not_echo_email():
    client = app.test_client()
    first = client.post("/early-access", json={"email": "person@example.com"})
    duplicate = client.post("/early-access", json={"email": " Person@EXAMPLE.com "})

    assert first.status_code == 201
    assert duplicate.status_code == 409
    assert duplicate.json == {
        "error": "already_subscribed",
        "message": "This address is already on the early-access list.",
    }
    assert "person@example.com" not in duplicate.get_data(as_text=True)
    with sqlite3.connect(app.config["EARLY_ACCESS_DATABASE"]) as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM early_access_subscribers"
        ).fetchone()[0]
    assert count == 1


def test_early_access_database_failure_is_generic_and_does_not_log_email(
    monkeypatch, caplog
):
    email = "private-address@example.com"

    def fail_to_store(*args):
        assert len(args) == 2
        raise sqlite3.OperationalError("database unavailable")

    monkeypatch.setattr(app_module, "subscribe_email", fail_to_store)
    response = app.test_client().post("/early-access", json={"email": email})

    assert response.status_code == 500
    assert response.json == {
        "error": "signup_unavailable",
        "message": "Signup is temporarily unavailable. Please try again later.",
    }
    assert email not in response.get_data(as_text=True)
    assert email not in caplog.text


def test_early_access_honeypot_rejects_automated_submission():
    response = app.test_client().post(
        "/early-access",
        json={"email": "person@example.com", "website": "filled"},
    )

    assert response.status_code == 400
    assert response.json["error"] == "invalid_submission"
    assert not Path(app.config["EARLY_ACCESS_DATABASE"]).exists()


def test_early_access_subscriber_list_is_not_public():
    response = app.test_client().get("/early-access")

    assert response.status_code == 405
    assert response.json is None


def test_simulation_is_blocked_until_required_data_exists():
    response = app.test_client().post("/simulate", json={"decisions": DECISIONS})

    assert response.status_code == 503
    assert response.json["error"] == "simulation_model_not_ready"
    assert isinstance(response.json["message"], str)
    assert "yield.base_tonnes_per_bigha" in response.json["missing_inputs"]
    assert "market.base_price_bdt_per_40kg" in response.json["missing_inputs"]
    assert "cost.full_economic_category_coverage" in response.json["missing_inputs"]
    assert "cost.six_decision_cost_mapping" in response.json["missing_inputs"]
    assert "gross_yield_tonnes" not in response.json


def test_synthetic_parameters_cannot_be_enabled_as_incomplete_full_cost_production(
    complete_test_parameters, monkeypatch
):
    from simulation import config

    production_parameters = replace(
        complete_test_parameters,
        is_production_data=True,
        full_economic_costs_implemented=False,
    )
    monkeypatch.setattr(config, "PARAMETERS", production_parameters)

    response = app.test_client().post("/simulate", json={"decisions": DECISIONS})

    assert response.status_code == 503
    assert response.json["error"] == "simulation_model_not_ready"
    assert "cost.full_economic_category_coverage" in response.json["missing_inputs"]
    assert "cost.six_decision_cost_mapping" in response.json["missing_inputs"]
    assert "gross_yield_tonnes" not in response.json


def test_three_bigha_farm_size_reaches_model_readiness_check():
    decisions = dict(DECISIONS, farm_size_bigha=3)

    response = app.test_client().post("/simulate", json={"decisions": decisions})

    assert response.status_code == 503
    assert response.json["error"] == "simulation_model_not_ready"


def test_missing_decisions_return_400():
    client = app.test_client()

    assert client.post("/simulate", json={}).status_code == 400
    response = client.post("/simulate", json={"decisions": {}})

    assert response.status_code == 400
    assert response.json["error"] == "invalid_request"
    assert "Missing decisions" in response.json["message"]


def test_invalid_decision_returns_400_before_model_readiness_check():
    decisions = dict(DECISIONS, irrigation_choice="flood")

    response = app.test_client().post("/simulate", json={"decisions": decisions})

    assert response.status_code == 400
    assert response.json["error"] == "invalid_request"
    assert "irrigation_choice" in response.json["message"]


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("seed_quality", "unknown"),
        ("fertilizer_type", "unknown"),
        ("labor_choice", "unknown"),
        ("irrigation_choice", "unknown"),
        ("sell_or_store", "unknown"),
    ],
)
def test_each_invalid_choice_returns_structured_400(field, invalid_value):
    decisions = dict(DECISIONS, **{field: invalid_value})

    response = app.test_client().post("/simulate", json={"decisions": decisions})

    assert response.status_code == 400
    assert response.json["error"] == "invalid_request"
    assert field in response.json["message"]
    assert "missing_inputs" not in response.json


def test_unsupported_farm_size_returns_400_before_model_readiness_check():
    decisions = dict(DECISIONS, farm_size_bigha=2)

    response = app.test_client().post("/simulate", json={"decisions": decisions})

    assert response.status_code == 400
    assert response.json["error"] == "invalid_request"
    assert "farm_size_bigha must be 1 or 3 bigha" in response.json["message"]


def test_malformed_json_returns_400():
    response = app.test_client().post(
        "/simulate",
        data='{"decisions":',
        content_type="application/json",
    )

    assert response.status_code == 400
    assert response.json["error"] == "invalid_request"


def test_non_json_request_returns_400():
    response = app.test_client().post("/simulate", data="{}")

    assert response.status_code == 400
    assert response.json["error"] == "invalid_request"


def test_seeded_success_returns_versioned_structured_result(
    complete_test_parameters, monkeypatch
):
    from simulation import config

    monkeypatch.setattr(config, "PARAMETERS", complete_test_parameters)
    client = app.test_client()
    payload = {"decisions": DECISIONS, "seed": 1234}

    first = client.post("/simulate", json=payload)
    second = client.post("/simulate", json=payload)

    assert first.status_code == 200
    assert first.json == second.json
    assert first.json["model_version"] == "synthetic-test-model"
    assert first.json["data_version"] == "synthetic-test-data"
    assert first.json["decisions"] == DECISIONS
    assert first.json["seed"] == 1234
    assert first.json["outcome"] in {"profit", "loss"}
    assert isinstance(first.json["gross_yield_tonnes"], float)
    assert isinstance(first.json["total_costs_bdt"], float)
    assert isinstance(first.json["gross_revenue_bdt"], float)
    assert set(first.json["diagnostic"]) >= {
        "yield",
        "costs_bdt",
        "revenue",
        "profit",
        "causal_claims",
    }
    assert first.json["events"]["weather"] in {
        "ideal",
        "mild_stress",
        "severe_event",
    }
    assert set(first.json["cost_breakdown_bdt"]) == {
        "seed",
        "fertilizer",
        "labor",
        "irrigation",
    }
    assert first.json["diagnostic"]["profit"]["net_profit_bdt"] == first.json[
        "net_profit_bdt"
    ]


def test_invalid_seed_returns_400():
    response = app.test_client().post(
        "/simulate",
        json={"decisions": DECISIONS, "seed": True},
    )

    assert response.status_code == 400
    assert "seed" in response.json["message"]


def test_unexpected_error_returns_generic_500_without_exception_details(monkeypatch):
    def fail_unexpectedly(decisions, *, seed=None):
        assert decisions == DECISIONS
        assert seed is None
        raise RuntimeError("private internal detail")

    monkeypatch.setattr(app_module, "run_full_simulation", fail_unexpectedly)
    response = app.test_client().post("/simulate", json={"decisions": DECISIONS})

    assert response.status_code == 500
    assert response.json == {
        "error": "internal_server_error",
        "message": "An unexpected error occurred while running the simulation",
    }
    assert "private internal detail" not in response.get_data(as_text=True)
