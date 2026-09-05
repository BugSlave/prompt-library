"""
Flask application entry point for the TheStrugglerCoder AI Prompt Library API.

Run locally with:
    python app.py
"""
from flask import Flask
from flask_cors import CORS
import threading
import time
import requests

from config import Config
from extensions import limiter
from routes.prompt_routes import prompt_bp
from utils.responses import error

def keep_alive():
    while True:
        time.sleep(600)
        try:
            requests.get("https://prompt-library-56nt.onrender.com/api/health", timeout=10)
        except Exception:
            pass

def create_app():
    Config.validate()

    app = Flask(__name__)
    app.config["ADMIN_API_KEY"]      = Config.ADMIN_API_KEY
    app.config["MAX_CONTENT_LENGTH"] = Config.MAX_CONTENT_LENGTH

    CORS(
        app,
        resources={r"/api/*": {"origins": Config.CORS_ORIGINS}},
        allow_headers=["Content-Type", "X-API-Key"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        supports_credentials=False,
    )

    limiter.init_app(app)
    app.register_blueprint(prompt_bp)

    @app.get("/api/health")
    def health():
        return {"success": True, "status": "ok"}

    @app.errorhandler(404)
    def not_found(_e):
        return error("Route not found", status=404)

    @app.errorhandler(405)
    def method_not_allowed(_e):
        return error("Method not allowed", status=405)

    @app.errorhandler(413)
    def too_large(_e):
        return error("Request body too large (max 1 MB)", status=413)

    @app.errorhandler(429)
    def rate_limited(_e):
        return error("Too many requests — slow down and try again", status=429)

    @app.errorhandler(500)
    def internal_error(_e):
        return error("Internal server error", status=500)

    return app


app = create_app()

# Start keep-alive only when running for real, not during import/testing
if Config.FLASK_ENV == "production":
    threading.Thread(target=keep_alive, daemon=True).start()

if __name__ == "__main__":
    # Bind to localhost only in debug mode — never expose debugger to the network
    host = "127.0.0.1" if Config.DEBUG else "0.0.0.0"
    app.run(host=host, port=Config.PORT, debug=Config.DEBUG)
