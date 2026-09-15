from routes.auth import auth_bp
from flask import Flask, jsonify, request, render_template, session, redirect, url_for
import os
from werkzeug.utils import secure_filename
from uuid import uuid4
import json
import hmac
from datetime import datetime
from mongodb import get_complaints, get_next_id
from services.ai import analyze_complaint
from routes.complaints import complaints_bp
from routes.admin import admin_bp
from routes.tracking import tracking_bp

from config import (
    DISABLE_DB,
    UPLOAD_FOLDER,
    ALLOWED_EXTENSIONS,
    FLASK_SECRET_KEY
)

app = Flask(__name__)
app.register_blueprint(auth_bp)
app.register_blueprint(complaints_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(tracking_bp)
app.secret_key = FLASK_SECRET_KEY

def admin_auth():
    if request.path == "/admin/login":
        return None

    if request.path == "/admin" or request.path.startswith("/api/admin/"):
        if not session.get("admin"):
            if request.path.startswith("/api/admin/"):
                return jsonify({
                    "success": False,
                    "error": "Admin authentication required."
                }), 401
            return redirect(url_for("admin.admin_login"))

    return None

@app.before_request
def check_admin_auth():
    return admin_auth()

mock_complaints = {}
mock_complaint_counter = 1

app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)

def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/student")
def student_portal():
    if not session.get("student_roll_no"):
        return redirect(url_for("auth.student_login"))

    return render_template("student.html")


# ============================================================
# AI CAMPUS BRIEFING
# ============================================================

@app.route("/api/admin/briefing")
def admin_briefing():

    conn = None
    cursor = None

    try:

        # =============================
        # MOCK MODE (DB DISABLED)
        # =============================
        
        if DISABLE_DB:
            return jsonify({
                "success": True,
                "briefing": {
                    "headline": "No complaints yet",
                    "summary": "No complaints have been submitted in mock mode.",
                    "top_issue": "N/A",
                    "affected_location": "N/A",
                    "affected_department": "N/A",
                    "recommended_action": "Monitor for incoming complaints.",
                    "urgency": "Low"
                },
                "mode": "mock"
            })


        # =============================
        # DATABASE MODE
        # =============================

        complaints_col = get_complaints()

        rows = complaints_col.find(
            {},
            {
                "_id": 0,
                "category": 1,
                "department": 1,
                "location": 1,
                "severity": 1,
                "priority": 1,
                "issue_group": 1,
                "status": 1
            }
        ).sort("created_at", -1).limit(30)

        rows = list(rows)

        if not rows:

            return jsonify({
                "success": True,
                "briefing": "No complaints have been submitted yet."
            })


        complaints = []

        for row in rows:

            complaints.append({
                "category": row.get("category"),
                "department": row.get("department"),
                "location": row.get("location"),
                "severity": row.get("severity"),
                "priority": row.get("priority"),
                "issue": row.get("issue_group"),
                "status": row.get("status")
            })


        briefing_prompt = f"""
You are the AI operations analyst for Campus Pulse,
a university complaint intelligence system.

Analyze these recent student complaints.

COMPLAINT DATA:

{json.dumps(complaints, indent=2)}

Create a concise operational briefing for a university administrator.

Identify:

1. The most important issue requiring attention.
2. The most affected location.
3. The most affected department.
4. Any recurring or related problems.
5. The recommended immediate action.

Rules:

- Base the briefing ONLY on the provided complaint data.
- Do not invent statistics.
- Do not invent locations.
- Do not invent departments.
- Prioritize Critical and High priority complaints.
- Consider complaint frequency and severity.
- Keep the briefing concise and actionable.

Return ONLY valid JSON in this format:

{{
    "headline": "...",
    "summary": "...",
    "top_issue": "...",
    "affected_location": "...",
    "affected_department": "...",
    "recommended_action": "...",
    "urgency": "Low | Medium | High | Critical"
}}
"""


        response = client.interactions.create(

            model="gemini-3.6-flash",

            input=briefing_prompt,

            response_format={
                "type": "text",
                "mime_type": "application/json",

                "schema": {

                    "type": "object",

                    "properties": {

                        "headline": {
                            "type": "string"
                        },

                        "summary": {
                            "type": "string"
                        },

                        "top_issue": {
                            "type": "string"
                        },

                        "affected_location": {
                            "type": "string"
                        },

                        "affected_department": {
                            "type": "string"
                        },

                        "recommended_action": {
                            "type": "string"
                        },

                        "urgency": {
                            "type": "string"
                        }

                    },

                    "required": [
                        "headline",
                        "summary",
                        "top_issue",
                        "affected_location",
                        "affected_department",
                        "recommended_action",
                        "urgency"
                    ]

                }
            }
        )


        briefing = json.loads(
            response.output_text
        )


        return jsonify({

            "success": True,

            "briefing": briefing

        })


    except Exception as e:

        return jsonify({

            "success": False,

            "error": str(e)

        }), 500


    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()

# ============================================================
# COMPLAINT SLA
# ============================================================

@app.route("/api/admin/complaints/<int:complaint_id>/sla")
def complaint_sla(complaint_id):

    try:

        # =============================
        # MOCK MODE (DB DISABLED)
        # =============================
        
        if DISABLE_DB:
            if complaint_id not in mock_complaints:
                return jsonify({
                    "success": False,
                    "error": "Complaint not found."
                }), 404
            
            c = mock_complaints[complaint_id]
            priority = c.get("priority", "Medium")
            status = c.get("status", "Pending")
            created_at = c.get("created_at", datetime.now())
            updated_at = c.get("updated_at", datetime.now())
            
            sla_hours = {
                "Critical": 2,
                "High": 4,
                "Medium": 12,
                "Low": 24
            }
            
            target_hours = sla_hours.get(priority, 12)
            
            if status == "Resolved":
                end_time = updated_at
            else:
                end_time = datetime.now()
            
            elapsed_seconds = (end_time - created_at).total_seconds()
            elapsed_hours = elapsed_seconds / 3600
            remaining_hours = target_hours - elapsed_hours
            
            if status == "Resolved":
                sla_status = "Resolved"
            elif remaining_hours <= 0:
                sla_status = "Breached"
            elif remaining_hours <= (target_hours * 0.25):
                sla_status = "At Risk"
            else:
                sla_status = "On Track"
            
            progress = min(100, max(0, (elapsed_hours / target_hours) * 100))
            
            return jsonify({
                "success": True,
                "complaint_id": complaint_id,
                "priority": priority,
                "status": status,
                "target_hours": target_hours,
                "elapsed_hours": round(elapsed_hours, 1),
                "remaining_hours": round(max(0, remaining_hours), 1),
                "progress": round(progress, 1),
                "sla_status": sla_status,
                "mode": "mock"
            })


        # =============================
        # DATABASE MODE
        # =============================

        row = get_complaints().find_one(
            {"id": complaint_id},
            {
                "_id": 0,
                "id": 1,
                "priority": 1,
                "status": 1,
                "created_at": 1,
                "updated_at": 1
            }
        )

        if not row:

            return jsonify({
                "success": False,
                "error": "Complaint not found."
            }), 404


        priority = row.get("priority") or "Medium"
        status = row.get("status") or "Pending"
        created_at = row.get("created_at")


        # SLA TARGET

        sla_hours = {

            "Critical": 2,

            "High": 4,

            "Medium": 12,

            "Low": 24

        }


        target_hours = sla_hours.get(
            priority,
            12
        )


        # RESOLVED COMPLAINT

        if status == "Resolved":

            end_time = row.get("updated_at") or datetime.now()

        else:

            end_time = datetime.now()


        # ELAPSED TIME

        elapsed_seconds = (
            end_time - created_at
        ).total_seconds()

        elapsed_hours = (
            elapsed_seconds / 3600
        )


        remaining_hours = (
            target_hours - elapsed_hours
        )


        # SLA STATUS

        if status == "Resolved":

            sla_status = "Resolved"

        elif remaining_hours <= 0:

            sla_status = "Breached"

        elif remaining_hours <= (
            target_hours * 0.25
        ):

            sla_status = "At Risk"

        else:

            sla_status = "On Track"


        progress = min(
            100,
            max(
                0,
                (elapsed_hours / target_hours) * 100
            )
        )


        return jsonify({

            "success": True,

            "complaint_id": complaint_id,

            "priority": priority,

            "status": status,

            "target_hours": target_hours,

            "elapsed_hours": round(
                elapsed_hours,
                1
            ),

            "remaining_hours": round(
                max(0, remaining_hours),
                1
            ),

            "progress": round(
                progress,
                1
            ),

            "sla_status": sla_status

        })


    except Exception as e:

        return jsonify({

            "success": False,

            "error": str(e)

        }), 500


                           
# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    app.run(debug=True)
