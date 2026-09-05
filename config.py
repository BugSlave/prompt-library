"""
Centralized application configuration, loaded from environment variables.
Never hardcode secrets or connection strings here.
"""
import os
import warnings
from dotenv import load_dotenv

load_dotenv()


class Config:
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/the_struggler_coder")
    PORT = int(os.getenv("PORT", 5000))

    # Safe default: debug OFF unless explicitly set to development
    DEBUG = os.getenv("FLASK_ENV", "production") == "development"

    # Comma separated list -> list of allowed origins for CORS
    CORS_ORIGINS = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    ]

    # Key required to create/update/delete prompts.
    ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "")

    # Max request body size: 1 MB
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024

    # Safety cap: max prompts returned when no pagination requested
    MAX_QUERY_LIMIT = 500

    # Rate limits (requests per minute per IP)
    RATE_LIMIT_READ  = "120 per minute"
    RATE_LIMIT_WRITE = "20 per minute"
    FLASK_ENV = os.getenv("FLASK_ENV", "production")

    @classmethod
    def validate(cls):
        """Warn loudly at startup about dangerous misconfigurations."""
        if not cls.ADMIN_API_KEY:
            warnings.warn(
                "[SECURITY] ADMIN_API_KEY is not set — all write endpoints are "
                "unprotected. Set ADMIN_API_KEY in your .env before deploying.",
                RuntimeWarning,
                stacklevel=2,
            )
        if cls.DEBUG:
            warnings.warn(
                "[SECURITY] Running in DEBUG mode — never use in production. "
                "Set FLASK_ENV=production to disable.",
                RuntimeWarning,
                stacklevel=2,
            )
