"""
Business logic for prompts: talks to MongoDB, applies validation,
and raises well-defined exceptions that routes translate into HTTP errors.
"""
import re
from bson import ObjectId
from bson.errors import InvalidId
from pymongo import ASCENDING, DESCENDING, ReturnDocument
from pymongo.errors import PyMongoError, DuplicateKeyError

from config import Config
from models.prompt_model import (
    validate_prompt_payload,
    prompt_to_dict,
    now,
    PromptValidationError,
)
from utils.slug import generate_slug
from services.db import get_prompts_collection


class PromptNotFoundError(Exception):
    pass


class PromptServiceError(Exception):
    """Wraps unexpected database errors so routes can return 500 cleanly."""
    pass


def _oid(prompt_id):
    try:
        return ObjectId(prompt_id)
    except (InvalidId, TypeError):
        raise PromptNotFoundError(f"'{prompt_id}' is not a valid prompt id")


def _unique_slug(collection, base_slug, exclude_id=None):
    """Ensure slug uniqueness by appending -2, -3, ... if needed."""
    slug = base_slug
    counter = 2
    while True:
        query = {"slug": slug}
        if exclude_id is not None:
            query["_id"] = {"$ne": exclude_id}
        if not collection.find_one(query):
            return slug
        slug = f"{base_slug}-{counter}"
        counter += 1


_SORT_MAP = {
    "newest": [("createdAt", DESCENDING)],
    "oldest": [("createdAt", ASCENDING)],
    "title":  [("title", ASCENDING)],
}


def list_prompts(search=None, category=None, sort="newest", page=None, limit=None):
    collection = get_prompts_collection()
    query = {}

    if search:
        # re.escape prevents ReDoS from user-supplied regex metacharacters
        pattern = re.escape(search)
        query["$or"] = [
            {"title":    {"$regex": pattern, "$options": "i"}},
            {"prompt":   {"$regex": pattern, "$options": "i"}},
            {"category": {"$regex": pattern, "$options": "i"}},
        ]

    if category:
        query["category"] = {"$regex": f"^{re.escape(category)}$", "$options": "i"}

    sort_order = _SORT_MAP.get(sort, _SORT_MAP["newest"])

    try:
        total = collection.count_documents(query)
        cursor = collection.find(query).sort(sort_order)

        if page is not None and limit is not None:
            cursor = cursor.skip((page - 1) * limit).limit(limit)
        else:
            # Always cap to prevent unbounded full-collection reads
            cursor = cursor.limit(Config.MAX_QUERY_LIMIT)

        return {"prompts": [prompt_to_dict(doc) for doc in cursor], "total": total}
    except PyMongoError as e:
        raise PromptServiceError(str(e))


def get_prompt(prompt_id):
    collection = get_prompts_collection()
    oid = _oid(prompt_id)
    try:
        doc = collection.find_one({"_id": oid})
    except PyMongoError as e:
        raise PromptServiceError(str(e))
    if not doc:
        raise PromptNotFoundError(f"No prompt found with id '{prompt_id}'")
    return prompt_to_dict(doc)


def get_prompt_by_slug(slug):
    collection = get_prompts_collection()
    try:
        doc = collection.find_one({"slug": slug})
    except PyMongoError as e:
        raise PromptServiceError(str(e))
    if not doc:
        raise PromptNotFoundError(f"No prompt found with slug '{slug}'")
    return prompt_to_dict(doc)


def create_prompt(payload):
    cleaned = validate_prompt_payload(payload, partial=False)
    collection = get_prompts_collection()

    base_slug = cleaned.get("slug") or generate_slug(cleaned["title"])
    if not base_slug:
        raise PromptValidationError("Could not derive a slug from the title", "slug")
    cleaned["slug"] = _unique_slug(collection, base_slug)
    cleaned.setdefault("category", "")

    timestamp = now()
    cleaned["createdAt"] = timestamp
    cleaned["updatedAt"] = timestamp

    try:
        result = collection.insert_one(cleaned)
        cleaned["_id"] = result.inserted_id
    except DuplicateKeyError:
        raise PromptValidationError("A prompt with this slug already exists", "slug")
    except PyMongoError as e:
        raise PromptServiceError(str(e))

    return prompt_to_dict(cleaned)


def update_prompt(prompt_id, payload):
    collection = get_prompts_collection()
    oid = _oid(prompt_id)

    cleaned = validate_prompt_payload(payload, partial=True)
    if not cleaned:
        raise PromptValidationError("No valid fields provided to update")

    if "slug" in cleaned:
        cleaned["slug"] = _unique_slug(collection, cleaned["slug"], exclude_id=oid)

    cleaned["updatedAt"] = now()

    try:
        updated = collection.find_one_and_update(
            {"_id": oid},
            {"$set": cleaned},
            return_document=ReturnDocument.AFTER,
        )
    except PyMongoError as e:
        raise PromptServiceError(str(e))

    if not updated:
        raise PromptNotFoundError(f"No prompt found with id '{prompt_id}'")

    return prompt_to_dict(updated)


def delete_prompt(prompt_id):
    collection = get_prompts_collection()
    oid = _oid(prompt_id)
    try:
        result = collection.delete_one({"_id": oid})
    except PyMongoError as e:
        raise PromptServiceError(str(e))
    if result.deleted_count == 0:
        raise PromptNotFoundError(f"No prompt found with id '{prompt_id}'")
    return True
