from flask import Blueprint, request, jsonify, session
from werkzeug.utils import secure_filename
from uuid import uuid4
from datetime import datetime
from services.ai import analyze_complaint
from mongodb import get_complaints, get_next_id
from config import UPLOAD_FOLDER, ALLOWED_EXTENSIONS, DISABLE_DB

complaints_bp = Blueprint("complaints", __name__)

mock_complaints = {}
mock_complaint_counter = 1


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


@complaints_bp.route("/api/complaints", methods=["POST"])
def create_complaint():
    saved_file = None
    global mock_complaint_counter

    try:
        uni_roll_no = session.get("student_roll_no")
        description = request.form.get("description")
        is_anonymous = (
            request.form.get("is_anonymous", "false").lower()
            == "true"
        )

        evidence = request.files.get("evidence")

        if not uni_roll_no:
            return jsonify({
                "success": False,
                "error": "University roll number is required."
            }), 400

        if not description:
            return jsonify({
                "success": False,
                "error": "Complaint description is required."
            }), 400

        evidence_path = None

        if evidence and evidence.filename:
            if not allowed_file(evidence.filename):
                return jsonify({
                    "success": False,
                    "error": (
                        "Invalid file type. "
                        "Allowed: PNG, JPG, JPEG, WEBP, PDF."
                    )
                }), 400

            original_name = secure_filename(evidence.filename)

            extension = (
                original_name.rsplit(".", 1)[1].lower()
            )

            unique_name = f"{uuid4().hex}.{extension}"

            saved_file = UPLOAD_FOLDER / unique_name

            evidence.save(saved_file)

            evidence_path = f"uploads/{unique_name}"

        try:
            analysis = analyze_complaint(description)

        except Exception as ai_error:
            print("Gemini AI analysis failed:", ai_error)

            analysis = {
                "category": "Other",
                "department": "General Administration",
                "location": "Unknown",
                "severity": 5,
                "priority": "Medium",
                "issue": description[:100],
                "recommended_action": (
                    "Review and assign this complaint manually."
                )
            }

        category = analysis["category"]
        department = analysis["department"]
        location = analysis["location"]
        severity = analysis["severity"]
        priority = analysis["priority"]
        issue = analysis["issue"]
        recommended_action = analysis["recommended_action"]

        if DISABLE_DB:
            complaint_id = mock_complaint_counter
            mock_complaint_counter += 1

            mock_complaints[complaint_id] = {
                "id": complaint_id,
                "uni_roll_no": uni_roll_no,
                "description": description,
                "category": category,
                "department": department,
                "location": location,
                "severity": severity,
                "priority": priority,
                "issue_group": issue,
                "recommended_action": recommended_action,
                "is_anonymous": is_anonymous,
                "evidence_path": evidence_path,
                "status": "Pending",
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }

            return jsonify({
                "success": True,
                "id": complaint_id,
                "message": (
                    "Complaint analyzed and "
                    "submitted successfully (Mock Mode)."
                ),
                "analysis": analysis,
                "evidence_uploaded": (
                    evidence_path is not None
                ),
                "mode": "mock"
            })

        complaint_id = get_next_id()

        complaint = {
            "id": complaint_id,
            "uni_roll_no": uni_roll_no,
            "description": description,
            "category": category,
            "department": department,
            "location": location,
            "severity": severity,
            "priority": priority,
            "issue_group": issue,
            "recommended_action": recommended_action,
            "is_anonymous": is_anonymous,
            "evidence_path": evidence_path,
            "status": "Pending",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }

        get_complaints().insert_one(complaint)

        return jsonify({
            "success": True,
            "id": complaint_id,
            "message": "Complaint analyzed and submitted successfully.",
            "analysis": analysis,
            "evidence_uploaded": evidence_path is not None
        })

    except Exception as e:
        if saved_file and saved_file.exists():
            try:
                saved_file.unlink()
            except Exception:
                pass

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500