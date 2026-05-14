from flask import Blueprint, render_template
from app.middleware.auth_middleware import login_required

pages_bp = Blueprint("pages", __name__)

@pages_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("pages/dashboard.html")