"""
Data shape + validation for visitor consent / activity documents.

These documents only get written once a visitor has explicitly accepted
the consent banner on the frontend — see routes/visitor_routes.py.
"""
from datetime import datetime, timezone

MAX_STRING_LEN = 500
MAX_ACTIVITY_TYPE_LEN = 50


class VisitorValidationError(Exception):
    def __init__(self, message, field=None):
        super().__init__(message)
        self.message = message
        self.field = field


def _clean_str(value, field, max_len=MAX_STRING_LEN, required=False):
    if value is None:
        if required:
            raise VisitorValidationError(f"{field} is required", field)
        return None
    if not isinstance(value, str):
        raise VisitorValidationError(f"{field} must be a string", field)
    value = value.strip()[:max_len]
    return value or None


def validate_consent_payload(data):
    if not isinstance(data, dict):
        raise VisitorValidationError("Request body must be a JSON object")

    visitor_id = _clean_str(data.get("visitorId"), "visitorId", max_len=100, required=True)

    device = data.get("device") or {}
    if not isinstance(device, dict):
        raise VisitorValidationError("device must be an object", "device")

    gps = data.get("gpsLocation")
    cleaned_gps = None
    if gps is not None:
        if not isinstance(gps, dict):
            raise VisitorValidationError("gpsLocation must be an object", "gpsLocation")
        lat, lon = gps.get("lat"), gps.get("lon")
        if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
            cleaned_gps = {"lat": float(lat), "lon": float(lon), "accuracy": gps.get("accuracy")}

    return {
        "visitorId": visitor_id,
        "device": {
            "userAgent": _clean_str(device.get("userAgent"), "device.userAgent"),
            "platform":  _clean_str(device.get("platform"), "device.platform"),
            "language":  _clean_str(device.get("language"), "device.language"),
            "timezone":  _clean_str(device.get("timezone"), "device.timezone"),
            "screen":    _clean_str(device.get("screen"), "device.screen"),
        },
        "gpsLocation": cleaned_gps,
        "consentGiven": bool(data.get("consentGiven", True)),
    }


def validate_activity_payload(data):
    if not isinstance(data, dict):
        raise VisitorValidationError("Request body must be a JSON object")

    visitor_id = _clean_str(data.get("visitorId"), "visitorId", max_len=100, required=True)
    activity_type = _clean_str(data.get("type"), "type", max_len=MAX_ACTIVITY_TYPE_LEN, required=True)

    return {
        "visitorId": visitor_id,
        "type": activity_type,
        "promptId": _clean_str(data.get("promptId"), "promptId", max_len=100),
        "query": _clean_str(data.get("query"), "query", max_len=200),
    }


def now():
    return datetime.now(timezone.utc)
