from flask import Blueprint, request, render_template, session, redirect, url_for
import os
import hmac

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "GET":
        return render_template("admin_login.html")

    username = request.form.get("username", "")
    password = request.form.get("password", "")

    admin_username = os.getenv("ADMIN_USERNAME", "")
    admin_password = os.getenv("ADMIN_PASSWORD", "")

    if (
        hmac.compare_digest(username, admin_username)
        and hmac.compare_digest(password, admin_password)
    ):
        session["admin"] = True
        return redirect(url_for("admin"))

    return render_template(
        "admin_login.html",
        error="Invalid username or password."
    ), 401