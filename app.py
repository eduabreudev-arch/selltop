import os
import sys
import logging
from datetime import timedelta

from flask import Flask, redirect, url_for, session

# Adiciona o diretório raiz ao path para imports relativos funcionarem
sys.path.insert(0, os.path.dirname(__file__))

from config import config
from repositories.user_repository import UserRepository, init_db
from services.auth_service import AuthService
from services.email_service import EmailService
from controllers.auth_controller import auth_bp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)

def create_app(env: str = "development") -> Flask:
    app = Flask(__name__)
    cfg = config.get(env, config["default"])
    app.config.from_object(cfg)
    app.permanent_session_lifetime = timedelta(seconds=app.config["PERMANENT_SESSION_LIFETIME"])

    # Banco de dados
    db_path = app.config["DATABASE"]
    init_db(db_path)

    # Injeção de dependências
    repo      = UserRepository(db_path)
    email_svc = EmailService(app.config)
    base_url  = os.environ.get("BASE_URL", "http://localhost:5000")

    app.auth_service = AuthService(
        repo         = repo,
        email_svc    = email_svc,
        secret_key   = app.config["SECRET_KEY"],
        token_max_age= app.config["TOKEN_MAX_AGE"],
        base_url     = base_url,
    )

    # Blueprints
    app.register_blueprint(auth_bp)

    @app.route("/")
    def index():
        if "user_id" in session:
            return redirect(url_for("auth.dashboard"))
        return redirect(url_for("auth.login"))

    @app.errorhandler(403)
    def forbidden(e):
        from flask import render_template
        return render_template("error.html", code=403, message="Acesso negado."), 403

    @app.errorhandler(404)
    def not_found(e):
        from flask import render_template
        return render_template("error.html", code=404, message="Página não encontrada."), 404

    return app


if __name__ == "__main__":
    app = create_app("development")
    print("\n  IAM App rodando em http://localhost:5000\n")
    app.run(debug=True, port=5000)
