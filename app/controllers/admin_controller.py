from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, session, current_app
)
from app.middleware.auth_middleware import admin_required
from app.services.auth_service import AuthError

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

def get_svc():
    return current_app.auth_service


@admin_bp.route("/users")
@admin_required
def users():
    users = get_svc().admin_list_users()
    return render_template("admin/users.html", users=users)


@admin_bp.route("/users/<int:user_id>/status", methods=["POST"])
@admin_required
def change_status(user_id):
    try:
        get_svc().admin_change_status(user_id, request.form["status"])
        flash("Status atualizado.", "success")
    except AuthError as e:
        flash(str(e), "danger")

    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/role", methods=["POST"])
@admin_required
def change_role(user_id):
    try:
        get_svc().admin_change_role(user_id, request.form["role"])
        flash("Role atualizada.", "success")
    except AuthError as e:
        flash(str(e), "danger")

    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@admin_required
def delete_user(user_id):
    try:
        if user_id == session["user_id"]:
            flash("Você não pode excluir sua própria conta.", "danger")
        else:
            get_svc().delete_account_admin(user_id)
            flash("Usuário excluído.", "success")
    except Exception as e:
        flash(str(e), "danger")

    return redirect(url_for("admin.users"))