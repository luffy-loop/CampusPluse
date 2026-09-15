from flask import Blueprint, request, render_template, redirect, url_for, session

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/student/login", methods=["GET", "POST"])
def student_login():
    if request.method == "GET":
        return render_template("student_login.html")

    roll_no = request.form.get("roll_no", "").strip()

    if not roll_no:
        return render_template(
            "student_login.html",
            error="University roll number is required."
        ), 400

    session["student_roll_no"] = roll_no
    return redirect(url_for("student_portal"))