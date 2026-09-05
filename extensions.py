"""
Flask extension instances — created here to avoid circular imports.
Each extension is initialised with the app inside create_app() in app.py.
"""
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://",
)
