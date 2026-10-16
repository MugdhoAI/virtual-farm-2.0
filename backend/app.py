import logging
import os
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from simulation.engine import run_full_simulation
from simulation.validation import DecisionValidationError, ModelDataError
from werkzeug.exceptions import BadRequest, RequestEntityTooLarge

from early_access import (
    DuplicateSubscriberError,
    normalize_email,
    signup_request_is_limited,
    subscribe_email,
)

app = Flask(__name__)
logger = logging.getLogger(__name__)
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
app.config["MAX_CONTENT_LENGTH"] = 4096
app.config["EARLY_ACCESS_DATABASE"] = os.environ.get(
    "VIRTUAL_FARM_EARLY_ACCESS_DB",
    str(Path(app.instance_path) / "early_access.sqlite3"),
)


@app.get("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "virtual-farm-simulation"})


@app.errorhandler(RequestEntityTooLarge)
def request_too_large(exc):
    return jsonify({
        "error": "request_too_large",
        "message": "The request is too large.",
    }), exc.code


@app.post("/early-access")
def early_access_signup():
    if signup_request_is_limited(request.remote_addr):
        return jsonify({
            "error": "rate_limited",
            "message": "Too many signup attempts. Please try again shortly.",
        }), 429
    if not request.is_json:
        return jsonify({
            "error": "invalid_request",
            "message": "Content-Type must be application/json",
        }), 400
    try:
        payload = request.get_json()
    except BadRequest:
        return jsonify({
            "error": "invalid_request",
            "message": "Request body must contain valid JSON",
        }), 400
    if not isinstance(payload, dict):
        return jsonify({
            "error": "invalid_request",
            "message": "Request body must be a JSON object",
        }), 400
    unexpected = payload.keys() - {"email", "website"}
    if unexpected:
        return jsonify({
            "error": "invalid_request",
            "message": "The request contains unexpected fields.",
        }), 400
    if "email" not in payload:
        return jsonify({
            "error": "invalid_request",
            "message": "An email address is required.",
        }), 400
    if payload.get("website"):
        return jsonify({
            "error": "invalid_submission",
            "message": "The signup could not be accepted.",
        }), 400
    try:
        email = normalize_email(payload["email"])
    except ValueError as exc:
        return jsonify({"error": "invalid_email", "message": str(exc)}), 400

    try:
        subscribe_email(email, app.config["EARLY_ACCESS_DATABASE"])
    except DuplicateSubscriberError:
        return jsonify({
            "error": "already_subscribed",
            "message": "This address is already on the early-access list.",
        }), 409
    except Exception:
        logger.exception("Early-access signup could not be stored")
        return jsonify({
            "error": "signup_unavailable",
            "message": "Signup is temporarily unavailable. Please try again later.",
        }), 500

    return jsonify({
        "status": "subscribed",
        "message": "You’re on the early-access list.",
    }), 201


@app.post("/simulate")
def simulate():
    if not request.is_json:
        return jsonify({
            "error": "invalid_request",
            "message": "Content-Type must be application/json",
        }), 400
    try:
        payload = request.get_json()
    except BadRequest:
        return jsonify({
            "error": "invalid_request",
            "message": "Request body must contain valid JSON",
        }), 400
    if not isinstance(payload, dict):
        return jsonify({
            "error": "invalid_request",
            "message": "Request body must be a JSON object",
        }), 400
    unexpected = payload.keys() - {"decisions", "seed"}
    if unexpected:
        return jsonify({
            "error": "invalid_request",
            "message": f"Unexpected request fields: {', '.join(sorted(unexpected))}",
        }), 400
    if "decisions" not in payload:
        return jsonify({
            "error": "invalid_request",
            "message": "Request body must contain a decisions object",
        }), 400
    try:
        result = run_full_simulation(payload["decisions"], seed=payload.get("seed"))
        return jsonify(result)
    except DecisionValidationError as exc:
        return jsonify({"error": "invalid_request", "message": str(exc)}), 400
    except ModelDataError as exc:
        response = {
            "error": "simulation_model_not_ready",
            "message": str(exc),
        }
        if exc.missing_inputs:
            response["missing_inputs"] = list(exc.missing_inputs)
        return jsonify(response), 503
    except Exception:
        logger.exception("Unexpected error while running simulation")
        return jsonify({
            "error": "internal_server_error",
            "message": "An unexpected error occurred while running the simulation",
        }), 500


if __name__ == "__main__":
    app.run(debug=False)
