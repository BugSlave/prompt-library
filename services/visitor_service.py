"""
Consent-gated visitor tracking.

IMPORTANT: nothing in this module runs unless the frontend consent banner
has been explicitly accepted by the visitor (see ConsentBanner.jsx +
POST /api/visitors/consent). Do not call these functions from any
unauthenticated/auto-triggered code path.
"""
import requests as http

from services.db import get_visitors_collection
from models.visitor_model import now


class VisitorServiceError(Exception):
    pass


def get_client_ip(request):
    """Best-effort real client IP, honoring a single reverse proxy hop."""
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"


def lookup_ip_location(ip):
    """
    Approximate city/region/country from IP via a free lookup service.
    Best-effort only — returns None on any failure (private IP, timeout, etc).
    """
    if not ip or ip in ("unknown", "127.0.0.1", "::1"):
        return None
    try:
        resp = http.get(f"https://ipapi.co/{ip}/json/", timeout=3)
        if resp.status_code != 200:
            return None
        data = resp.json()
        if data.get("error"):
            return None
        return {
            "city": data.get("city"),
            "region": data.get("region"),
            "country": data.get("country_name"),
            "lat": data.get("latitude"),
            "lon": data.get("longitude"),
        }
    except Exception:
        return None


def record_consent(request, payload):
    """Upsert a visitor document, capturing IP, IP-location, GPS location and device info."""
    col = get_visitors_collection()
    ip = get_client_ip(request)
    ip_location = lookup_ip_location(ip)

    update = {
        "$set": {
            "ip": ip,
            "ipLocation": ip_location,
            "gpsLocation": payload["gpsLocation"],
            "device": payload["device"],
            "consentGiven": payload["consentGiven"],
            "updatedAt": now(),
        },
        "$setOnInsert": {
            "visitorId": payload["visitorId"],
            "createdAt": now(),
        },
    }
    try:
        col.update_one({"visitorId": payload["visitorId"]}, update, upsert=True)
    except Exception as e:
        raise VisitorServiceError(str(e)) from e


def record_activity(payload):
    """Append one activity event (prompt view, search, copy) to the visitor's document."""
    col = get_visitors_collection()
    entry = {
        "type": payload["type"],
        "promptId": payload["promptId"],
        "query": payload["query"],
        "at": now(),
    }
    try:
        result = col.update_one(
            {"visitorId": payload["visitorId"]},
            {"$push": {"activity": {"$each": [entry], "$slice": -200}}},
        )
        if result.matched_count == 0:
            # No consent doc exists yet — ignore rather than creating one implicitly.
            return False
        return True
    except Exception as e:
        raise VisitorServiceError(str(e)) from e
