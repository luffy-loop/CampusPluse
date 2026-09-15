from flask import Blueprint, request, render_template, redirect, url_for, session
import re

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/student/login", methods=["GET", "POST"])
def student_login():
    if request.method == "GET":
        return render_template("student_login.html")

    roll_no = request.form.get("roll_no", "").strip().upper()

    if not roll_no:
        return render_template(
            "student_login.html",
            error="University roll number is required."
        ), 400

    if not re.fullmatch(r"[A-Z0-9]+", roll_no):
        return render_template(
            "student_login.html",
            error="Enter a valid university roll number."
        ), 400

    session["student_roll_no"] = roll_no
    return redirect(url_for("student_portal"))


@auth_bp.route("/student/logout")
def student_logout():
    session.pop("student_roll_no", None)
    return redirect(url_for("auth.student_login"))