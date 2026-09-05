"""
Small helpers so every route returns JSON in a consistent shape:
    { "success": bool, "data": ..., "error": "..." }
"""
from flask import jsonify


def success(data=None, status=200, meta=None):
    body = {"success": True, "data": data}
    if meta is not None:
        body["meta"] = meta
    return jsonify(body), status


def error(message, status=400, details=None):
    body = {"success": False, "error": message}
    if details is not None:
        body["details"] = details
    return jsonify(body), status
