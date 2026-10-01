"""
Consent-gated visitor tracking endpoints.

These are only ever called after a visitor explicitly accepts the consent
banner in the frontend (ConsentBanner.jsx). No data is written here unless
that acceptance has happened client-side first.
"""
from flask import Blueprint, request

from config import Config
from extensions import limiter
from services import visitor_service
from models.visitor_model import (
    validate_consent_payload,
    validate_activity_payload,
    VisitorValidationError,
)
from utils.responses import success, error

visitor_bp = Blueprint("visitors", __name__, url_prefix="/api/visitors")


@visitor_bp.post("/consent")
@limiter.limit(Config.RATE_LIMIT_WRITE)
def post_consent():
    payload = request.get_json(silent=True)
    if payload is None:
        return error("Request body must be valid JSON", status=400)
    try:
        cleaned = validate_consent_payload(payload)
    except VisitorValidationError as e:
        return error(e.message, status=422, details={"field": e.field})

    try:
        visitor_service.record_consent(request, cleaned)
        return success({"recorded": True})
    except visitor_service.VisitorServiceError as e:
        details = str(e) if request.host.startswith("127.") else None
        return error("Database error while recording consent", status=500, details=details)


@visitor_bp.post("/activity")
@limiter.limit(Config.RATE_LIMIT_READ)
def post_activity():
    payload = request.get_json(silent=True)
    if payload is None:
        return error("Request body must be valid JSON", status=400)
    try:
        cleaned = validate_activity_payload(payload)
    except VisitorValidationError as e:
        return error(e.message, status=422, details={"field": e.field})

    try:
        recorded = visitor_service.record_activity(cleaned)
        return success({"recorded": recorded})
    except visitor_service.VisitorServiceError as e:
        details = str(e) if request.host.startswith("127.") else None
        return error("Database error while recording activity", status=500, details=details)
