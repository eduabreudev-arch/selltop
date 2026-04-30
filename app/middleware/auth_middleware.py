from functools import wraps
from flask import session, redirect, url_for, flash, abort

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Faça login para continuar.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Faça login para continuar.", "warning")
            return redirect(url_for("auth.login"))
        if session.get("user_role") != "admin":
            abort(403)
        return f(*args, **kwargs)
    return decorated

def guest_only(f):
    """Redireciona usuários já logados para o dashboard."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" in session:
            return redirect(url_for("auth.dashboard"))
        return f(*args, **kwargs)
    return decorated
