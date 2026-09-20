from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for
from datetime import datetime
from mongodb import get_complaints
from config import DISABLE_DB

tracking_bp = Blueprint("tracking", __name__)

mock_complaints = {}
mock_complaint_counter = 1


@tracking_bp.route("/track")
def track():
    if not session.get("student_roll_no"):
        return redirect(url_for("auth.student_login"))

    return render_template("track.html")


@tracking_bp.route("/api/complaints", methods=["GET"])
def get_student_complaints():
    try:
        uni_roll_no = session.get("student_roll_no")

        if not uni_roll_no:
            return jsonify({
                "success": False,
                "error": "University roll number is required."
            }), 400

        if DISABLE_DB:
            complaints = [
                c for c in mock_complaints.values()
                if c["uni_roll_no"] == uni_roll_no
            ]

            formatted_complaints = []

            for c in complaints:
                formatted_complaints.append({
                    "id": c["id"],
                    "description": c["description"],
                    "category": c["category"],
                    "department": c["department"],
                    "location": c["location"],
                    "severity": c["severity"],
                    "priority": c["priority"],
                    "issue": c["issue_group"],
                    "recommended_action": c["recommended_action"],
                    "status": c["status"],
                    "created_at": (
                        c["created_at"].strftime(
                            "%d %b %Y, %I:%M %p"
                        )
                        if c["created_at"]
                        else None
                    ),
                    "updated_at": (
                        c["updated_at"].strftime(
                            "%d %b %Y, %I:%M %p"
                        )
                        if c["updated_at"]
                        else None
                    )
                })

            return jsonify({
                "success": True,
                "complaints": formatted_complaints,
                "count": len(formatted_complaints),
                "mode": "mock"
            })

        rows = get_complaints().find(
            {"uni_roll_no": uni_roll_no},
            {
                "_id": 0,
                "id": 1,
                "description": 1,
                "category": 1,
                "department": 1,
                "location": 1,
                "severity": 1,
                "priority": 1,
                "issue_group": 1,
                "recommended_action": 1,
                "status": 1,
                "created_at": 1,
                "updated_at": 1
            }
        ).sort("created_at", -1)

        complaints = []

        for row in rows:
            complaints.append({
                "id": row.get("id"),
                "description": row.get("description"),
                "category": row.get("category"),
                "department": row.get("department"),
                "location": row.get("location"),
                "severity": row.get("severity"),
                "priority": row.get("priority"),
                "issue": row.get("issue_group"),
                "recommended_action": row.get("recommended_action"),
                "status": row.get("status"),
                "created_at": (
                    row["created_at"].strftime(
                        "%d %b %Y, %I:%M %p"
                    )
                    if row.get("created_at")
                    else None
                ),
                "updated_at": (
                    row["updated_at"].strftime(
                        "%d %b %Y, %I:%M %p"
                    )
                    if row.get("updated_at")
                    else None
                )
            })

        return jsonify({
            "success": True,
            "complaints": complaints,
            "count": len(complaints)
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@tracking_bp.route("/api/complaints/<int:complaint_id>")
def get_complaint(complaint_id):
    try:
        if DISABLE_DB:
            if complaint_id not in mock_complaints:
                return jsonify({
                    "success": False,
                    "error": "Complaint not found."
                }), 404

            c = mock_complaints[complaint_id]

            if c["uni_roll_no"] != session.get("student_roll_no"):
                return jsonify({
                    "success": False,
                    "error": "Complaint not found."
                }), 404

            complaint = {
                "id": c["id"],
                "category": c["category"],
                "department": c["department"],
                "location": c["location"],
                "severity": c["severity"],
                "priority": c["priority"],
                "issue": c["issue_group"],
                "recommended_action": c["recommended_action"],
                "status": c["status"],
                "created_at": (
                    c["created_at"].strftime(
                        "%d %b %Y, %I:%M %p"
                    )
                    if c["created_at"]
                    else None
                )
            }

            return jsonify({
                "success": True,
                "complaint": complaint,
                "mode": "mock"
            })

        row = get_complaints().find_one(
            {
                "id": complaint_id,
                "uni_roll_no": session.get("student_roll_no")
            },
            {"_id": 0}
        )

        if not row:
            return jsonify({
                "success": False,
                "error": "Complaint not found."
            }), 404

        complaint = {
            "id": row.get("id"),
            "category": row.get("category"),
            "department": row.get("department"),
            "location": row.get("location"),
            "severity": row.get("severity"),
            "priority": row.get("priority"),
            "issue": row.get("issue_group"),
            "recommended_action": row.get("recommended_action"),
            "status": row.get("status"),
            "created_at": (
                row["created_at"].strftime(
                    "%d %b %Y, %I:%M %p"
                )
                if row.get("created_at")
                else None
            )
        }

        return jsonify({
            "success": True,
            "complaint": complaint
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500