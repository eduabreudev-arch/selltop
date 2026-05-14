from flask import (
    Blueprint, render_template, request,
    session, flash, redirect, url_for, current_app
)
from app.middleware.auth_middleware import login_required
from app.services.auth_service import AuthError

user_bp = Blueprint("user", __name__, url_prefix="/user")

def get_svc():
    return current_app.auth_service


@user_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        action = request.form.get("action")

        try:
            if action == "update_name":
                user = get_svc().update_profile(
                    session["user_id"],
                    request.form["name"]
                )
                session["user_name"] = user.name
                flash("Nome atualizado.", "success")

            elif action == "change_password":
                get_svc().change_password(
                    session["user_id"],
                    request.form["current_password"],
                    request.form["new_password"],
                )
                flash("Senha alterada.", "success")

            elif action == "delete_account":
                get_svc().delete_account(
                    session["user_id"],
                    request.form["confirm_password"]
                )
                session.clear()
                flash("Conta excluída.", "info")
                return redirect(url_for("auth.login"))

        except AuthError as e:
            flash(str(e), "danger")

    return render_template("user/profile.html")