from flask import (
    Blueprint, render_template, request, redirect,
    url_for, session, flash, current_app, g
)
from app.services.auth_service import AuthService, AuthError
from app.middleware.auth_middleware import login_required, admin_required, guest_only

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def get_svc() -> AuthService:
    return current_app.auth_service

def _set_session(user):
    session.permanent = True
    session["user_id"]   = user.id
    session["user_name"] = user.name
    session["user_role"] = user.role


# ------------------------------------------------------------------ #
# Registro
# ------------------------------------------------------------------ #
@auth_bp.route("/register", methods=["GET", "POST"])
@guest_only
def register():
    if request.method == "POST":
        try:
            user = get_svc().register(
                name     = request.form["name"],
                email    = request.form["email"],
                password = request.form["password"],
            )
            flash("Cadastro realizado! Verifique seu e-mail.", "success")
            return redirect(url_for("auth.verify_code", email=user.email))
        except AuthError as e:
            flash(str(e), "danger")

    return render_template("auth/register.html")


# ------------------------------------------------------------------ #
# Login
# ------------------------------------------------------------------ #
@auth_bp.route("/login", methods=["GET", "POST"])
@guest_only
def login():
    if request.method == "POST":
        try:
            user = get_svc().login(
                email    = request.form["email"],
                password = request.form["password"],
            )
            _set_session(user)
            flash(f"Bem-vindo, {user.name}!", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("pages.dashboard"))
        except AuthError as e:
            flash(str(e), "danger")

    return render_template("auth/login.html")


# ------------------------------------------------------------------ #
# Logout
# ------------------------------------------------------------------ #
@auth_bp.route("/logout")
@login_required
def logout():
    session.clear()
    flash("Você saiu da conta.", "info")
    return redirect(url_for("auth.login"))


# ------------------------------------------------------------------ #
# Verificação por código
# ------------------------------------------------------------------ #
@auth_bp.route("/verify-code", methods=["GET", "POST"])
@guest_only
def verify_code():
    email = request.args.get("email", "")

    if request.method == "POST":
        email = request.form.get("email", "")
        code  = request.form.get("code", "")
        try:
            user = get_svc().verify_code(email, code)
            _set_session(user)
            flash(f"Bem-vindo, {user.name}! Conta verificada com sucesso.", "success")
            return redirect(url_for("pages.dashboard"))
        except AuthError as e:
            flash(str(e), "danger")

    return render_template("auth/verify_code.html", email=email)


# ------------------------------------------------------------------ #
# Reenviar verificação
# ------------------------------------------------------------------ #
@auth_bp.route("/resend-verification", methods=["GET", "POST"])
@guest_only
def resend_verification():
    if request.method == "POST":
        get_svc().resend_verification(request.form["email"])
        flash("Se existir, o código foi reenviado.", "info")
        return redirect(url_for("auth.login"))

    return render_template("auth/resend_verification.html")


# ------------------------------------------------------------------ #
# Forgot password
# ------------------------------------------------------------------ #
@auth_bp.route("/forgot-password", methods=["GET", "POST"])
@guest_only
def forgot_password():
    if request.method == "POST":
        get_svc().request_password_reset(request.form["email"])
        flash("Verifique seu e-mail.", "info")
        return redirect(url_for("auth.login"))

    return render_template("auth/forgot_password.html")


# ------------------------------------------------------------------ #
# Reset password
# ------------------------------------------------------------------ #
@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
@guest_only
def reset_password(token):
    if request.method == "POST":
        try:
            get_svc().reset_password(token, request.form["password"])
            flash("Senha redefinida!", "success")
            return redirect(url_for("auth.login"))
        except AuthError as e:
            flash(str(e), "danger")

    return render_template("auth/reset_password.html", token=token)