from flask import Flask, jsonify, request, render_template
import psycopg2
import os
from werkzeug.utils import secure_filename
from pathlib import Path
from uuid import uuid4
import json
from dotenv import load_dotenv
from google import genai
from datetime import datetime
from mongodb import get_complaints, get_next_id
load_dotenv()

app = Flask(__name__)

# ============================================================
# DATABASE CONFIGURATION
# ============================================================

DISABLE_DB = os.getenv("DISABLE_DB", "false").lower() == "true"

# In-memory storage for mock data when DB is disabled
mock_complaints = {}
mock_complaint_counter = 1


import os
from pathlib import Path

if os.getenv("VERCEL"):
    UPLOAD_FOLDER = Path("/tmp/uploads")
else:
    UPLOAD_FOLDER = Path(__file__).resolve().parent / "uploads"

UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)

ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "webp",
    "pdf"
}


def allowed_file(filename):

    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )
# ============================================================
# GEMINI CLIENT
# ============================================================

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db_connection():
    if DISABLE_DB:
        raise Exception("Database is disabled for testing/deployment.")

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise Exception("DATABASE_URL is not configured.")

    return psycopg2.connect(database_url)


# ============================================================
# AI COMPLAINT ANALYSIS
# ============================================================

def analyze_complaint(description):

    prompt = f"""
        You are the AI complaint classification engine for Campus Pulse,
    a university student complaint management system.

    Analyze the following student complaint:

    {description}

    Return ONLY valid JSON.

    ============================================================
    CATEGORY AND DEPARTMENT RULES
    ============================================================

    Choose exactly ONE category and its matching department.

    1. Infrastructure
       Department: Facilities & Maintenance

       Examples:
       - Water leakage
       - Broken classroom equipment
       - Electrical problems
       - Damaged furniture
       - Classroom physical problems
       - AC problems
       - Ventilation problems

    2. IT & Network
       Department: IT & Network Services

       Examples:
       - Wi-Fi problems
       - Internet problems
       - Network outage
       - Computer problems
       - Software/system access problems

    3. Academics
       Department: Academic Affairs

       Examples:
       - Faculty issues
       - Timetable problems
       - Course issues
       - Examination issues
       - Academic records

    4. Hostel
       Department: Hostel Management

       Examples:
       - Hostel room problems
       - Water/hot water in hostel
       - Hostel cleanliness
       - Hostel maintenance

    5. Transport
       Department: Transport Services

       Examples:
       - Bus problems
       - Bus timings
       - Transportation availability

    6. Security
       Department: Campus Security

       Examples:
       - Security concerns
       - Suspicious activity
       - Security cameras
       - Access/security problems

    7. Library
       Department: Library Services

       Examples:
       - Library facilities
       - Library resources
       - Library access

    8. Food & Dining
       Department: Food Services

       Examples:
       - Canteen problems
       - Food quality
       - Mess problems
       - Dining facilities

    9. Finance
       Department: Finance Office

       Examples:
       - Fee issues
       - Payment problems
       - Refund issues

    10. Student Affairs
        Department: Student Affairs

        Examples:
        - General student services
        - Student support
        - Student activities

    11. Other
        Department: General Administration

        Use this only when the complaint does not clearly
        belong to any of the categories above.

    ============================================================
    PRIORITY
    ============================================================

    Critical:
    Immediate danger, fire, electrical danger, serious security
    threat, major flooding, or a severe issue affecting many students.

    High:
    Serious issue significantly affecting students, academics,
    campus operations, or essential services.

    Medium:
    Normal operational problem affecting some students.

    Low:
    Minor inconvenience or cosmetic issue.

    ============================================================
    SEVERITY
    ============================================================

    Give an integer from 1 to 10.

    1 = very minor inconvenience
    10 = extremely serious problem

    ============================================================
    LOCATION
    ============================================================

    Extract the exact location mentioned by the student.

    Examples:
    H1 13
    H0 06
    H2 14
    Block A
    Library
    Main Gate
    Hostel B

    If no specific location is mentioned, return:

    "Unknown"

    ============================================================
    ISSUE
    ============================================================

    Create a short and specific title for the actual problem.

    ============================================================
    RECOMMENDED ACTION
    ============================================================

    Give one practical action that the responsible department
    should take.

    ============================================================
    IMPORTANT
    ============================================================

    - Never invent a department.
    - Never invent a category.
    - Category and department MUST match the rules above.
    - Return ONLY JSON.
    - Do not return markdown.
    - Do not explain your answer.

    Return exactly:

    {{
        "category": "...",
        "department": "...",
        "issue": "...",
        "location": "...",
        "priority": "...",
        "severity": 1,
        "recommended_action": "..."
    }}
    """
    response = client.interactions.create(

        model="gemini-3.6-flash",

        input=prompt,

        response_format={
            "type": "text",
            "mime_type": "application/json",

            "schema": {

                "type": "object",

                "properties": {

                    "category": {
                        "type": "string"
                    },

                    "department": {
                        "type": "string"
                    },

                    "location": {
                        "type": "string"
                    },

                    "severity": {
                        "type": "integer"
                    },

                    "priority": {
                        "type": "string"
                    },

                    "issue": {
                        "type": "string"
                    },

                    "recommended_action": {
                        "type": "string"
                    }

                },

                "required": [

                    "category",
                    "department",
                    "location",
                    "severity",
                    "priority",
                    "issue",
                    "recommended_action"

                ]
            }
        }
    )

    analysis = json.loads(response.output_text)

    ALLOWED_CATEGORIES = {
        "Infrastructure",
        "IT & Network",
        "Academics",
        "Hostel",
        "Transport",
        "Security",
        "Library",
        "Food & Dining",
        "Finance",
        "Student Affairs",
        "Other"
    }

    ALLOWED_DEPARTMENTS = {
        "Facilities & Maintenance",
        "IT & Network Services",
        "Academic Affairs",
        "Hostel Management",
        "Transport Services",
        "Campus Security",
        "Library Services",
        "Food Services",
        "Finance Office",
        "Student Affairs",
        "General Administration"
    }

    if analysis.get("category") not in ALLOWED_CATEGORIES:
        analysis["category"] = "Other"

    if analysis.get("department") not in ALLOWED_DEPARTMENTS:
        analysis["department"] = "General Administration"

    return analysis

# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def home():

    return render_template("index.html")


# ============================================================
# SUBMIT COMPLAINT
# ============================================================

# ============================================================
# SUBMIT COMPLAINT
# ============================================================

@app.route("/api/complaints", methods=["POST"])
def create_complaint():

    saved_file = None
    global mock_complaint_counter

    try:

        # -----------------------------
        # Get form data
        # -----------------------------

        uni_roll_no = request.form.get("uni_roll_no")
        description = request.form.get("description")
        is_anonymous = (
            request.form.get("is_anonymous", "false").lower()
            == "true"
        )

        evidence = request.files.get("evidence")


        # -----------------------------
        # Validate input
        # -----------------------------

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


        # -----------------------------
        # Handle evidence file
        # -----------------------------

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


            original_name = secure_filename(
                evidence.filename
            )

            extension = (
                original_name.rsplit(".", 1)[1].lower()
            )


            unique_name = (
                f"{uuid4().hex}.{extension}"
            )


            saved_file = (
                UPLOAD_FOLDER / unique_name
            )


            evidence.save(saved_file)


            evidence_path = (
                f"uploads/{unique_name}"
            )


        # -----------------------------
        # AI ANALYSIS
               # -----------------------------
        # AI ANALYSIS
        # -----------------------------

        try:
            analysis = analyze_complaint(description)

        except Exception as ai_error:
            print("Gemini AI analysis failed:", ai_error)

            # Fallback analysis when Gemini quota/API is unavailable
            analysis = {
                "category": "Other",
                "department": "General Administration",
                "location": "Unknown",
                "severity": 5,
                "priority": "Medium",
                "issue": description[:100],
                "recommended_action": "Review and assign this complaint manually."
            }


        # -----------------------------
        # Extract AI fields
        # -----------------------------

        category = analysis["category"]
        department = analysis["department"]
        location = analysis["location"]
        severity = analysis["severity"]
        priority = analysis["priority"]
        issue = analysis["issue"]
        recommended_action = analysis[
            "recommended_action"
        ]


        # =============================
        # MOCK MODE (DB DISABLED)
        # =============================
        
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


        # =============================
        # DATABASE MODE
        # =============================

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


        # Remove uploaded file if database
        # insertion failed

        if saved_file and saved_file.exists():

            try:
                saved_file.unlink()
            except Exception:
                pass


        return jsonify({

            "success": False,

            "error": str(e)

        }), 500


# ============================================================
# ADMIN DASHBOARD
# ============================================================

@app.route("/admin")
def admin():

    return render_template("admin.html")


@app.route("/api/admin/dashboard")
def admin_dashboard():

    try:

        # =============================
        # MOCK MODE (DB DISABLED)
        # =============================
        
        if DISABLE_DB:
            complaints = list(mock_complaints.values())
            
            total = len(complaints)
            pending = sum(1 for c in complaints if c.get("status") == "Pending")
            high_priority = sum(1 for c in complaints if c.get("priority") in ("High", "Critical"))
            resolved = sum(1 for c in complaints if c.get("status") == "Resolved")
            
            # Department distribution
            dept_count = {}
            for c in complaints:
                dept = c.get("department", "Unassigned")
                dept_count[dept] = dept_count.get(dept, 0) + 1
            
            departments = [
                {"department": dept, "count": count}
                for dept, count in sorted(dept_count.items(), key=lambda x: x[1], reverse=True)
            ]
            
            # Format complaints
            formatted_complaints = []
            for c in complaints:
                formatted_complaints.append({
                    "id": c["id"],
                    "uni_roll_no": c["uni_roll_no"],
                    "description": c["description"],
                    "category": c["category"],
                    "department": c["department"],
                    "location": c["location"],
                    "severity": c["severity"],
                    "priority": c["priority"],
                    "status": c["status"],
                    "created_at": c["created_at"].strftime("%d %b %Y, %I:%M %p") if c["created_at"] else None,
                    "evidence_path": c["evidence_path"]
                })
            
            return jsonify({
                "success": True,
                "stats": {
                    "total": total,
                    "pending": pending,
                    "high_priority": high_priority,
                    "resolved": resolved
                },
                "departments": departments,
                "complaints": formatted_complaints,
                "mode": "mock"
            })


        # =============================
        # DATABASE MODE
        # =============================

        complaints_col = get_complaints()

        total = complaints_col.count_documents({})

        pending = complaints_col.count_documents({
            "status": "Pending"
        })

        high_priority = complaints_col.count_documents({
            "priority": {
                "$in": ["High", "Critical"]
            }
        })

        resolved = complaints_col.count_documents({
            "status": "Resolved"
        })

        departments = [
            {
                "department": row["_id"] or "Unassigned",
                "count": row["count"]
            }
            for row in complaints_col.aggregate([
                {
                    "$group": {
                        "_id": "$department",
                        "count": {"$sum": 1}
                    }
                },
                {
                    "$sort": {
                        "count": -1
                    }
                }
            ])
        ]

        rows = complaints_col.find(
            {},
            {
                "_id": 0,
                "id": 1,
                "uni_roll_no": 1,
                "description": 1,
                "category": 1,
                "department": 1,
                "location": 1,
                "severity": 1,
                "priority": 1,
                "status": 1,
                "created_at": 1,
                "evidence_path": 1
            }
        ).sort("created_at", -1).limit(20)

        complaints = []

        for row in rows:
            complaints.append({
                "id": row.get("id"),
                "uni_roll_no": row.get("uni_roll_no"),
                "description": row.get("description"),
                "category": row.get("category"),
                "department": row.get("department"),
                "location": row.get("location"),
                "severity": row.get("severity"),
                "priority": row.get("priority"),
                "status": row.get("status"),
                "created_at": (
                    row["created_at"].strftime(
                        "%d %b %Y, %I:%M %p"
                    )
                    if row.get("created_at")
                    else None
                ),
                "evidence_path": row.get("evidence_path")
            })

        return jsonify({
            "success": True,
            "stats": {
                "total": total,
                "pending": pending,
                "high_priority": high_priority,
                "resolved": resolved
            },
            "departments": departments,
            "complaints": complaints
        })

    except Exception as e:

        return jsonify({

            "success": False,

            "error": str(e)

        }), 500


# ============================================================
# UPDATE COMPLAINT STATUS
# ============================================================

@app.route("/api/admin/complaints/<int:complaint_id>/status", methods=["PUT"])
def update_complaint_status(complaint_id):

    try:
        data = request.get_json()
        new_status = data.get("status")

        allowed_statuses = {
            "Pending",
            "In Progress",
            "Resolved"
        }

        if new_status not in allowed_statuses:
            return jsonify({
                "success": False,
                "error": "Invalid status."
            }), 400

        # =============================
        # MOCK MODE (DB DISABLED)
        # =============================
        
        if DISABLE_DB:
            if complaint_id not in mock_complaints:
                return jsonify({
                    "success": False,
                    "error": "Complaint not found."
                }), 404
            
            mock_complaints[complaint_id]["status"] = new_status
            mock_complaints[complaint_id]["updated_at"] = datetime.now()
            
            return jsonify({
                "success": True,
                "id": complaint_id,
                "status": new_status,
                "message": "Complaint status updated successfully.",
                "mode": "mock"
            })


        # =============================
        # DATABASE MODE
        # =============================

        result = get_complaints().update_one(
            {"id": complaint_id},
            {
                "$set": {
                    "status": new_status,
                    "updated_at": datetime.now()
                }
            }
        )

        if result.matched_count == 0:
            return jsonify({
                "success": False,
                "error": "Complaint not found."
            }), 404

        return jsonify({
            "success": True,
            "id": complaint_id,
            "status": new_status,
            "message": "Complaint status updated successfully."
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

        # ============================================================
# STUDENT COMPLAINT TRACKING
# ============================================================

@app.route("/track")
def track():

    return render_template("track.html")

# ============================================================
# STUDENT COMPLAINTS BY ROLL NUMBER
# ============================================================

@app.route("/api/complaints", methods=["GET"])
def get_student_complaints():

    try:

        uni_roll_no = request.args.get("uni_roll_no")

        if not uni_roll_no:

            return jsonify({
                "success": False,
                "error": "University roll number is required."
            }), 400


        # =============================
        # MOCK MODE (DB DISABLED)
        # =============================
        
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
                    "created_at": c["created_at"].strftime("%d %b %Y, %I:%M %p") if c["created_at"] else None,
                    "updated_at": c["updated_at"].strftime("%d %b %Y, %I:%M %p") if c["updated_at"] else None
                })
            
            return jsonify({
                "success": True,
                "complaints": formatted_complaints,
                "count": len(formatted_complaints),
                "mode": "mock"
            })


        # =============================
        # DATABASE MODE
        # =============================

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
                    row["created_at"].strftime("%d %b %Y, %I:%M %p")
                    if row.get("created_at")
                    else None
                ),
                "updated_at": (
                    row["updated_at"].strftime("%d %b %Y, %I:%M %p")
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




@app.route("/api/complaints/<int:complaint_id>")
def get_complaint(complaint_id):

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
                "created_at": c["created_at"].strftime("%d %b %Y, %I:%M %p") if c["created_at"] else None
            }
            
            return jsonify({
                "success": True,
                "complaint": complaint,
                "mode": "mock"
            })


        # =============================
        # DATABASE MODE
        # =============================

        row = get_complaints().find_one(
            {"id": complaint_id},
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
                row["created_at"].strftime("%d %b %Y, %I:%M %p")
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

# ============================================================
# CAMPUS SIGNALS
# ============================================================

@app.route("/api/admin/signals")
def campus_signals():

    try:

        # =============================
        # MOCK MODE (DB DISABLED)
        # =============================
        
        if DISABLE_DB:
            return jsonify({
                "success": True,
                "signals": [],
                "mode": "mock"
            })


        # =============================
        # DATABASE MODE
        # =============================

        complaints_col = get_complaints()

        priority_map = {
            4: "Critical",
            3: "High",
            2: "Medium",
            1: "Low",
            0: "Unknown"
        }

        rows = complaints_col.aggregate([
            {
                "$match": {
                    "location": {
                        "$nin": [None, "Unknown"]
                    }
                }
            },
            {
                "$group": {
                    "_id": {
                        "category": "$category",
                        "department": "$department",
                        "location": "$location"
                    },
                    "complaint_count": {
                        "$sum": 1
                    },
                    "average_severity": {
                        "$avg": "$severity"
                    },
                    "priority_level": {
                        "$max": {
                            "$switch": {
                                "branches": [
                                    {
                                        "case": {"$eq": ["$priority", "Critical"]},
                                        "then": 4
                                    },
                                    {
                                        "case": {"$eq": ["$priority", "High"]},
                                        "then": 3
                                    },
                                    {
                                        "case": {"$eq": ["$priority", "Medium"]},
                                        "then": 2
                                    },
                                    {
                                        "case": {"$eq": ["$priority", "Low"]},
                                        "then": 1
                                    }
                                ],
                                "default": 0
                            }
                        }
                    }
                }
            },
            {
                "$match": {
                    "complaint_count": {
                        "$gte": 2
                    }
                }
            },
            {
                "$sort": {
                    "complaint_count": -1,
                    "average_severity": -1
                }
            },
            {
                "$limit": 10
            }
        ])

        signals = []

        for row in rows:
            signals.append({
                "category": row["_id"].get("category"),
                "department": row["_id"].get("department"),
                "location": row["_id"].get("location"),
                "complaint_count": row["complaint_count"],
                "average_severity": round(
                    float(row["average_severity"]),
                    1
                ) if row["average_severity"] is not None else 0,
                "priority": priority_map.get(
                    row["priority_level"],
                    "Unknown"
                )
            })

        return jsonify({
            "success": True,
            "signals": signals
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

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