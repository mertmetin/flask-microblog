"""microblog: a small, secure Flask blog."""

from __future__ import annotations

import os
import secrets
from pathlib import Path

from flask import Flask

from .extensions import csrf, db, login_manager


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    secret = os.environ.get("SECRET_KEY")
    app.config.update(
        # A random key per process in development; production must set SECRET_KEY.
        SECRET_KEY=secret or secrets.token_hex(32),
        SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL", f"sqlite:///{Path(app.instance_path) / 'blog.db'}"),
        POSTS_PER_PAGE=5,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("FLASK_ENV") == "production",
    )
    if config:
        app.config.update(config)
    if os.environ.get("FLASK_ENV") == "production" and not secret:
        raise RuntimeError("Set SECRET_KEY in production")

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    from . import auth, blog, cli
    from .markdown import render_markdown

    app.register_blueprint(auth.bp)
    app.register_blueprint(blog.bp)
    cli.register(app)
    app.jinja_env.filters["markdown"] = render_markdown

    @app.after_request
    def security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' https: data:; style-src 'self'; "
            "script-src 'self'; frame-ancestors 'none'",
        )
        return response

    with app.app_context():
        db.create_all()
    return app
