"""Slug generation helpers."""
from slugify import slugify


def generate_slug(text: str) -> str:
    """Turn a title into a URL/identifier-safe slug."""
    return slugify(text)
