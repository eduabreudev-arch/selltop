import os
import secrets

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", secrets.token_hex(32))
    DATABASE = os.environ.get("DATABASE", "iam_app.db")
    TOKEN_MAX_AGE = 3600  # 1 hora para tokens de reset/verificação

    # E-mail (configure com suas credenciais SMTP)
    MAIL_SERVER   = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT     = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS  = True
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
    MAIL_FROM     = os.environ.get("MAIL_FROM", "noreply@iamapp.com")

    # Sessão
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = 3600

class DevelopmentConfig(Config):
    DEBUG = True
    MAIL_DEBUG = True   # Imprime e-mails no console em dev

class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True

config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
