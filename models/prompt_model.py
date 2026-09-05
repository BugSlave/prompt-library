"""
Data shape + validation for a Prompt document.
MongoDB is schemaless, so validation is enforced here in application code.
"""
from datetime import datetime, timezone

MAX_TITLE_LEN    = 200
MAX_CATEGORY_LEN = 100
MAX_PROMPT_LEN   = 50_000   # ~50 KB of text


class PromptValidationError(Exception):
    """Raised when incoming prompt data fails validation."""
    def __init__(self, message, field=None):
        super().__init__(message)
        self.message = message
        self.field = field


def validate_prompt_payload(data, partial=False):
    """
    Validate a raw dict coming from the request body.

    partial=True is used for PUT/update, where fields are optional but,
    if present, must still be non-empty.

    Returns a cleaned dict containing only known, validated fields.
    """
    if not isinstance(data, dict):
        raise PromptValidationError("Request body must be a JSON object")

    cleaned = {}

    title = data.get("title")
    if title is not None or not partial:
        if title is None or not isinstance(title, str) or not title.strip():
            raise PromptValidationError("title is required and cannot be empty", "title")
        if len(title.strip()) > MAX_TITLE_LEN:
            raise PromptValidationError(f"title must be {MAX_TITLE_LEN} characters or fewer", "title")
        cleaned["title"] = title.strip()

    prompt_text = data.get("prompt")
    if prompt_text is not None or not partial:
        if prompt_text is None or not isinstance(prompt_text, str) or not prompt_text.strip():
            raise PromptValidationError("prompt is required and cannot be empty", "prompt")
        if len(prompt_text) > MAX_PROMPT_LEN:
            raise PromptValidationError(f"prompt must be {MAX_PROMPT_LEN} characters or fewer", "prompt")
        # Preserve exact whitespace/newlines/markdown inside the prompt body.
        cleaned["prompt"] = prompt_text

    category = data.get("category")
    if category is not None:
        if not isinstance(category, str):
            raise PromptValidationError("category must be a string", "category")
        if len(category.strip()) > MAX_CATEGORY_LEN:
            raise PromptValidationError(f"category must be {MAX_CATEGORY_LEN} characters or fewer", "category")
        cleaned["category"] = category.strip()

    slug = data.get("slug")
    if slug is not None:
        if not isinstance(slug, str) or not slug.strip():
            raise PromptValidationError("slug must be a non-empty string", "slug")
        cleaned["slug"] = slug.strip()

    return cleaned


def prompt_to_dict(doc):
    """Convert a MongoDB document into a JSON-serializable dict."""
    if doc is None:
        return None
    return {
        "id": str(doc.get("_id")),
        "title": doc.get("title"),
        "slug": doc.get("slug"),
        "prompt": doc.get("prompt"),
        "category": doc.get("category", ""),
        "createdAt": doc.get("createdAt").isoformat() if doc.get("createdAt") else None,
        "updatedAt": doc.get("updatedAt").isoformat() if doc.get("updatedAt") else None,
    }


def now():
    return datetime.now(timezone.utc)
