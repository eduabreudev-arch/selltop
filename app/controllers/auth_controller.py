from flask import (
    Blueprint, render_template, request, redirect,
    url_for, session, flash, current_app, g
)
from app.services.auth_service import AuthService, AuthError
from middleware.auth_middleware import login_required, admin_required, guest_only

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

def get_svc() -> AuthService:
    return current_app.auth_service

# ------------------------------------------------------------------ #
# Helpers
# ------------------------------------------------------------------ #
def _set_session(user):
    session.permanent = True
    session["user_id"]   = user.id
    session["user_name"] = user.name
    session["user_role"] = user.role
    session["user_email"]= user.email

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
            flash("Cadastro realizado! Verifique seu e-mail para ativar a conta.", "success")
            return redirect(url_for("auth.login"))
        except AuthError as e:
            flash(str(e), "danger")
    return render_template("register.html")

# ------------------------------------------------------------------ #
# Login / Logout
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
            return redirect(next_page or url_for("auth.dashboard"))
        except AuthError as e:
            flash(str(e), "danger")
    return render_template("login.html")

@auth_bp.route("/logout")
@login_required
def logout():
    session.clear()
    flash("Você saiu da conta.", "info")
    return redirect(url_for("auth.login"))

# ------------------------------------------------------------------ #
# Dashboard (área logada)
# ------------------------------------------------------------------ #
@auth_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

# ------------------------------------------------------------------ #
# Verificação de e-mail
# ------------------------------------------------------------------ #
@auth_bp.route("/verify-email/<token>")
def verify_email(token):
    try:
        user = get_svc().verify_email(token)
        flash("E-mail verificado com sucesso! Faça login.", "success")
    except AuthError as e:
        flash(str(e), "danger")
    return redirect(url_for("auth.login"))

@auth_bp.route("/resend-verification", methods=["GET", "POST"])
@guest_only
def resend_verification():
    if request.method == "POST":
        get_svc().resend_verification(request.form["email"])
        flash("Se o e-mail existir e não estiver verificado, um novo link foi enviado.", "info")
        return redirect(url_for("auth.login"))
    return render_template("resend_verification.html")

# ------------------------------------------------------------------ #
# Esqueci minha senha
# ------------------------------------------------------------------ #
@auth_bp.route("/forgot-password", methods=["GET", "POST"])
@guest_only
def forgot_password():
    if request.method == "POST":
        get_svc().request_password_reset(request.form["email"])
        flash("Se o e-mail estiver cadastrado, você receberá as instruções em breve.", "info")
        return redirect(url_for("auth.login"))
    return render_template("forgot_password.html")

@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
@guest_only
def reset_password(token):
    if request.method == "POST":
        try:
            get_svc().reset_password(token, request.form["password"])
            flash("Senha redefinida com sucesso! Faça login.", "success")
            return redirect(url_for("auth.login"))
        except AuthError as e:
            flash(str(e), "danger")
    return render_template("reset_password.html", token=token)

# ------------------------------------------------------------------ #
# Perfil (usuário logado)
# ------------------------------------------------------------------ #
@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        action = request.form.get("action")
        try:
            if action == "update_name":
                user = get_svc().update_profile(session["user_id"], request.form["name"])
                session["user_name"] = user.name
                flash("Nome atualizado com sucesso.", "success")
            elif action == "change_password":
                get_svc().change_password(
                    session["user_id"],
                    request.form["current_password"],
                    request.form["new_password"],
                )
                flash("Senha alterada com sucesso.", "success")
            elif action == "delete_account":
                get_svc().delete_account(session["user_id"], request.form["confirm_password"])
                session.clear()
                flash("Conta excluída permanentemente.", "info")
                return redirect(url_for("auth.login"))
        except AuthError as e:
            flash(str(e), "danger")
    return render_template("profile.html")

# ------------------------------------------------------------------ #
# Painel Admin
# ------------------------------------------------------------------ #
@auth_bp.route("/admin/users")
@admin_required
def admin_users():
    users = get_svc().admin_list_users()
    return render_template("admin_users.html", users=users)

@auth_bp.route("/admin/users/<int:user_id>/status", methods=["POST"])
@admin_required
def admin_change_status(user_id):
    try:
        get_svc().admin_change_status(user_id, request.form["status"])
        flash("Status atualizado.", "success")
    except AuthError as e:
        flash(str(e), "danger")
    return redirect(url_for("auth.admin_users"))

@auth_bp.route("/admin/users/<int:user_id>/role", methods=["POST"])
@admin_required
def admin_change_role(user_id):
    try:
        get_svc().admin_change_role(user_id, request.form["role"])
        flash("Role atualizada.", "success")
    except AuthError as e:
        flash(str(e), "danger")
    return redirect(url_for("auth.admin_users"))

@auth_bp.route("/admin/users/<int:user_id>/delete", methods=["POST"])
@admin_required
def admin_delete_user(user_id):
    try:
        if user_id == session["user_id"]:
            flash("Você não pode excluir sua própria conta pelo painel admin.", "danger")
        else:
            get_svc().delete_account_admin(user_id)
            flash("Usuário excluído.", "success")
    except Exception as e:
        flash(str(e), "danger")
    return redirect(url_for("auth.admin_users"))
