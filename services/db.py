"""MongoDB connection singleton with index setup."""
from pymongo import MongoClient, ASCENDING, DESCENDING
from config import Config

_client = None
_db = None


def get_db():
    global _client, _db
    if _db is None:
        _client = MongoClient(Config.MONGO_URI, serverSelectionTimeoutMS=5000)
        _db = _client.get_default_database("prompt-library")
        _ensure_indexes(_db)
    return _db


def _ensure_indexes(db):
    col = db["prompts"]
    col.create_index("slug", unique=True, background=True)
    col.create_index([("createdAt", DESCENDING)], background=True)
    col.create_index([("title", ASCENDING)], background=True)


def get_prompts_collection():
    return get_db()["prompts"]
