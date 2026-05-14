import os
import logging
from datetime import timedelta

from flask import Flask, redirect, url_for, session, render_template

from app.config import config
from app.repositories.user_repository import UserRepository, init_db
from app.services.auth_service import AuthService
from app.services.email_service import EmailService

# Blueprints
from app.controllers.auth_controller import auth_bp
from app.controllers.user_controller import user_bp
from app.controllers.admin_controller import admin_bp
from app.controllers.pages_controller import pages_bp


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)


def create_app() -> Flask:
    env = os.getenv("FLASK_ENV", "development")

    app = Flask(__name__)

    # ── Configuração ───────────────────────────────────────────────
    cfg = config.get(env, config["default"])
    app.config.from_object(cfg)

    app.permanent_session_lifetime = timedelta(
        seconds=app.config["PERMANENT_SESSION_LIFETIME"]
    )


    # ── Banco de dados ─────────────────────────────────────────────
    turso_url = app.config.get("TURSO_URL", "")
    turso_token = app.config.get("TURSO_AUTH_TOKEN", "")

    if turso_url:
        db_config = {"url": turso_url, "auth_token": turso_token}
    else:
        db_config = {"path": app.config["DATABASE"]}
        init_db(app.config["DATABASE"])

    # ── Injeção de dependências ────────────────────────────────────
    repo = UserRepository(db_config)
    email_svc = EmailService(app.config)
    base_url = os.environ.get("BASE_URL", "http://localhost:5000")

    app.auth_service = AuthService(
        repo=repo,
        email_svc=email_svc,
        secret_key=app.config["SECRET_KEY"],
        token_max_age=app.config["TOKEN_MAX_AGE"],
        base_url=base_url,
    )

    # ── Blueprints ─────────────────────────────────────────────────
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(pages_bp)

    # ── Rotas base ─────────────────────────────────────────────────
    @app.route("/")
    def index():
        if "user_id" in session:
            return redirect(url_for("pages.dashboard"))
        return redirect(url_for("auth.login"))

    # ── Handlers de erro ───────────────────────────────────────────
    @app.errorhandler(403)
    def forbidden(e):
        return render_template(
            "pages/error.html",
            code=403,
            message="Acesso negado."
        ), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template(
            "pages/error.html",
            code=404,
            message="Página não encontrada."
        ), 404

    return app