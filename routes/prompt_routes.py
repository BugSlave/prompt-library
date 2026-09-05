"""
REST API routes for prompts.

Read routes (GET) are fully public — that's the point of the app.
Write routes (POST/PUT/DELETE) require an X-API-Key header matching
Config.ADMIN_API_KEY, so the public site can't be vandalized once deployed.
"""
import hmac
from functools import wraps
from flask import Blueprint, request, current_app

from config import Config
from extensions import limiter
from services import prompt_service
from models.prompt_model import PromptValidationError
from utils.responses import success, error

prompt_bp = Blueprint("prompts", __name__, url_prefix="/api/prompts")


def require_api_key(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        configured_key = current_app.config.get("ADMIN_API_KEY")
        if not configured_key:
            # Key not configured — refuse all writes rather than allowing anyone in
            return error("Write operations are disabled: ADMIN_API_KEY not configured", status=503)
        provided_key = request.headers.get("X-API-Key", "")
        # compare_digest prevents timing-based key enumeration attacks
        if not hmac.compare_digest(provided_key.encode(), configured_key.encode()):
            return error("Invalid or missing API key", status=401)
        return fn(*args, **kwargs)
    return wrapper


def _db_error(msg, e):
    """Return 500 — leak internal details only in debug mode."""
    details = str(e) if current_app.debug else None
    return error(msg, status=500, details=details)


@prompt_bp.get("")
@limiter.limit(Config.RATE_LIMIT_READ)
def get_prompts():
    search   = request.args.get("search",   default=None, type=str) or None
    category = request.args.get("category", default=None, type=str) or None
    sort     = request.args.get("sort",     default="newest", type=str)
    page     = request.args.get("page",     default=None, type=int)
    limit    = request.args.get("limit",    default=None, type=int)

    if sort not in ("newest", "oldest", "title"):
        sort = "newest"
    if page is not None:
        page = max(1, page)
    if limit is not None:
        limit = min(max(1, limit), 100)

    # Cap search term length to prevent expensive regex queries
    if search and len(search) > 200:
        search = search[:200]

    try:
        result = prompt_service.list_prompts(
            search=search, category=category, sort=sort, page=page, limit=limit
        )
        meta = {"count": len(result["prompts"]), "total": result["total"]}
        if page is not None:
            meta["page"] = page
        if limit is not None:
            meta["limit"] = limit
            meta["pages"] = max(1, -(-result["total"] // limit))
        return success(result["prompts"], meta=meta)
    except prompt_service.PromptServiceError as e:
        return _db_error("Database error while listing prompts", e)


@prompt_bp.get("/slug/<slug>")
@limiter.limit(Config.RATE_LIMIT_READ)
def get_prompt_by_slug(slug):
    try:
        prompt = prompt_service.get_prompt_by_slug(slug)
        return success(prompt)
    except prompt_service.PromptNotFoundError as e:
        return error(str(e), status=404)
    except prompt_service.PromptServiceError as e:
        return _db_error("Database error while fetching prompt", e)


@prompt_bp.get("/<prompt_id>")
@limiter.limit(Config.RATE_LIMIT_READ)
def get_prompt(prompt_id):
    try:
        prompt = prompt_service.get_prompt(prompt_id)
        return success(prompt)
    except prompt_service.PromptNotFoundError as e:
        return error(str(e), status=404)
    except prompt_service.PromptServiceError as e:
        return _db_error("Database error while fetching prompt", e)


@prompt_bp.post("")
@require_api_key
@limiter.limit(Config.RATE_LIMIT_WRITE)
def create_prompt():
    payload = request.get_json(silent=True)
    if payload is None:
        return error("Request body must be valid JSON", status=400)
    try:
        prompt = prompt_service.create_prompt(payload)
        return success(prompt, status=201)
    except PromptValidationError as e:
        return error(e.message, status=422, details={"field": e.field})
    except prompt_service.PromptServiceError as e:
        return _db_error("Database error while creating prompt", e)


@prompt_bp.put("/<prompt_id>")
@require_api_key
@limiter.limit(Config.RATE_LIMIT_WRITE)
def update_prompt(prompt_id):
    payload = request.get_json(silent=True)
    if payload is None:
        return error("Request body must be valid JSON", status=400)
    try:
        prompt = prompt_service.update_prompt(prompt_id, payload)
        return success(prompt)
    except prompt_service.PromptNotFoundError as e:
        return error(str(e), status=404)
    except PromptValidationError as e:
        return error(e.message, status=422, details={"field": e.field})
    except prompt_service.PromptServiceError as e:
        return _db_error("Database error while updating prompt", e)


@prompt_bp.delete("/<prompt_id>")
@require_api_key
@limiter.limit(Config.RATE_LIMIT_WRITE)
def delete_prompt(prompt_id):
    try:
        prompt_service.delete_prompt(prompt_id)
        return success({"deleted": True})
    except prompt_service.PromptNotFoundError as e:
        return error(str(e), status=404)
    except prompt_service.PromptServiceError as e:
        return _db_error("Database error while deleting prompt", e)
