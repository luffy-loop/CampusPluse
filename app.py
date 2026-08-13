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
load_dotenv()

app = Flask(__name__)

UPLOAD_FOLDER = Path(app.root_path) / "uploads"

UPLOAD_FOLDER.mkdir(
    parents=True,
    exist_ok=True
)

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

    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )


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

    conn = None
    cursor = None
    saved_file = None

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

        analysis = analyze_complaint(
            description
        )


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


        # -----------------------------
        # Connect to PostgreSQL
        # -----------------------------

        conn = get_db_connection()
        cursor = conn.cursor()


        # -----------------------------
        # Insert everything
        # -----------------------------

        query = """

            INSERT INTO complaints (

                uni_roll_no,
                description,
                category,
                department,
                location,
                severity,
                priority,
                issue_group,
                recommended_action,
                is_anonymous,
                evidence_path

            )

            VALUES (

                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s

            )

            RETURNING id;

        """


        cursor.execute(

            query,

            (

                uni_roll_no,
                description,
                category,
                department,
                location,
                severity,
                priority,
                issue,
                recommended_action,
                is_anonymous,
                evidence_path

            )

        )


        complaint_id = cursor.fetchone()[0]


        conn.commit()


        # -----------------------------
        # Response
        # -----------------------------

        return jsonify({

            "success": True,

            "id": complaint_id,

            "message": (
                "Complaint analyzed and "
                "submitted successfully."
            ),

            "analysis": analysis,

            "evidence_uploaded": (
                evidence_path is not None
            )

        })


    except Exception as e:

        if conn:
            conn.rollback()


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


    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()

# ============================================================
# ADMIN DASHBOARD
# ============================================================

@app.route("/admin")
def admin():

    return render_template("admin.html")


@app.route("/api/admin/dashboard")
def admin_dashboard():

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        # ----------------------------------------
        # Total complaints
        # ----------------------------------------

        cursor.execute("""
            SELECT COUNT(*)
            FROM complaints;
        """)

        total = cursor.fetchone()[0]


        # ----------------------------------------
        # Pending complaints
        # ----------------------------------------

        cursor.execute("""
            SELECT COUNT(*)
            FROM complaints
            WHERE status = 'Pending';
        """)

        pending = cursor.fetchone()[0]


        # ----------------------------------------
        # High / Critical complaints
        # ----------------------------------------

        cursor.execute("""
            SELECT COUNT(*)
            FROM complaints
            WHERE priority IN ('High', 'Critical');
        """)

        high_priority = cursor.fetchone()[0]


        # ----------------------------------------
        # Resolved complaints
        # ----------------------------------------

        cursor.execute("""
            SELECT COUNT(*)
            FROM complaints
            WHERE status = 'Resolved';
        """)

        resolved = cursor.fetchone()[0]


        # ----------------------------------------
        # Department distribution
        # ----------------------------------------

        cursor.execute("""
            SELECT
                COALESCE(department, 'Unassigned') AS department,
                COUNT(*) AS count
            FROM complaints
            GROUP BY department
            ORDER BY count DESC;
        """)

        departments = [

            {
                "department": row[0],
                "count": row[1]
            }

            for row in cursor.fetchall()

        ]


                # ----------------------------------------
        # Recent complaints
        # ----------------------------------------

        cursor.execute("""
            SELECT
                id,
                uni_roll_no,
                description,
                category,
                department,
                location,
                severity,
                priority,
                status,
                created_at,
                evidence_path
            FROM complaints
            ORDER BY created_at DESC
            LIMIT 20;
        """)

        rows = cursor.fetchall()

        complaints = []

        for row in rows:

            complaints.append({

                "id": row[0],

                "uni_roll_no": row[1],

                "description": row[2],

                "category": row[3],

                "department": row[4],

                "location": row[5],

                "severity": row[6],

                "priority": row[7],

                "status": row[8],

                "created_at": (
                    row[9].strftime("%d %b %Y, %I:%M %p")
                    if row[9]
                    else None
                ),

                "evidence_path": row[10]

            })

        rows = cursor.fetchall()


        complaints = []

        for row in rows:

            complaints.append({

                "id": row[0],

                "uni_roll_no": row[1],

                "description": row[2],

                "category": row[3],

                "department": row[4],

                "location": row[5],

                "severity": row[6],

                "priority": row[7],

                "status": row[8],

"created_at": (
    row[9].strftime("%d %b %Y, %I:%M %p")
    if row[9]
    else None
),

"evidence_path": row[10]

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


    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()

# ============================================================
# UPDATE COMPLAINT STATUS
# ============================================================

@app.route("/api/admin/complaints/<int:complaint_id>/status", methods=["PUT"])
def update_complaint_status(complaint_id):

    conn = None
    cursor = None

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

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE complaints
            SET status = %s
            WHERE id = %s
            RETURNING id, status;
        """, (new_status, complaint_id))

        result = cursor.fetchone()

        if not result:
            conn.rollback()

            return jsonify({
                "success": False,
                "error": "Complaint not found."
            }), 404

        conn.commit()

        return jsonify({
            "success": True,
            "id": result[0],
            "status": result[1],
            "message": "Complaint status updated successfully."
        })

    except Exception as e:

        if conn:
            conn.rollback()

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
# STUDENT COMPLAINT TRACKING
# ============================================================

@app.route("/track")
def track():

    return render_template("track.html")


@app.route("/api/complaints/<int:complaint_id>")
def get_complaint(complaint_id):

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id,
                category,
                department,
                location,
                severity,
                priority,
                issue_group,
                recommended_action,
                status,
                created_at
            FROM complaints
            WHERE id = %s;
        """, (complaint_id,))

        row = cursor.fetchone()

        if not row:

            return jsonify({
                "success": False,
                "error": "Complaint not found."
            }), 404

        complaint = {
            "id": row[0],
            "category": row[1],
            "department": row[2],
            "location": row[3],
            "severity": row[4],
            "priority": row[5],
            "issue": row[6],
            "recommended_action": row[7],
            "status": row[8],
            "created_at": (
                row[9].strftime("%d %b %Y, %I:%M %p")
                if row[9]
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

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()

# ============================================================
# CAMPUS SIGNALS
# ============================================================

@app.route("/api/admin/signals")
def campus_signals():

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                category,
                department,
                location,
                COUNT(*) AS complaint_count,
ROUND(AVG(severity)::numeric, 1) AS average_severity,                MAX(
                    CASE
                        WHEN priority = 'Critical' THEN 4
                        WHEN priority = 'High' THEN 3
                        WHEN priority = 'Medium' THEN 2
                        WHEN priority = 'Low' THEN 1
                        ELSE 0
                    END
                ) AS priority_level
            FROM complaints
            WHERE location IS NOT NULL
              AND location <> 'Unknown'
            GROUP BY
                category,
                department,
                location
            HAVING COUNT(*) >= 2
            ORDER BY
                complaint_count DESC,
                average_severity DESC
            LIMIT 10;
        """)

        rows = cursor.fetchall()

        signals = []

        for row in rows:

            priority_map = {
                4: "Critical",
                3: "High",
                2: "Medium",
                1: "Low",
                0: "Unknown"
            }

            signals.append({
                "category": row[0],
                "department": row[1],
                "location": row[2],
                "complaint_count": row[3],
                "average_severity": float(row[4])
                    if row[4] is not None
                    else 0,
                "priority": priority_map.get(
                    row[5],
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

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()

# ============================================================
# AI CAMPUS BRIEFING
# ============================================================

@app.route("/api/admin/briefing")
def admin_briefing():

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        # Get recent complaints
        cursor.execute("""
            SELECT
                category,
                department,
                location,
                severity,
                priority,
                issue_group,
                status
            FROM complaints
            ORDER BY created_at DESC
            LIMIT 30;
        """)

        rows = cursor.fetchall()

        if not rows:

            return jsonify({
                "success": True,
                "briefing": "No complaints have been submitted yet."
            })


        complaints = []

        for row in rows:

            complaints.append({
                "category": row[0],
                "department": row[1],
                "location": row[2],
                "severity": row[3],
                "priority": row[4],
                "issue": row[5],
                "status": row[6]
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

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id,
                priority,
                status,
                created_at,
                updated_at
            FROM complaints
            WHERE id = %s;
        """, (complaint_id,))

        row = cursor.fetchone()

        if not row:

            return jsonify({
                "success": False,
                "error": "Complaint not found."
            }), 404


        priority = row[1] or "Medium"
        status = row[2] or "Pending"
        created_at = row[3]


        # --------------------------------
        # SLA TARGET
        # --------------------------------

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


        # --------------------------------
        # RESOLVED COMPLAINT
        # --------------------------------

        if status == "Resolved":

            end_time = row[4] or datetime.now()

        else:

            end_time = datetime.now()


        # --------------------------------
        # ELAPSED TIME
        # --------------------------------

        elapsed_seconds = (
            end_time - created_at
        ).total_seconds()

        elapsed_hours = (
            elapsed_seconds / 3600
        )


        remaining_hours = (
            target_hours - elapsed_hours
        )


        # --------------------------------
        # SLA STATUS
        # --------------------------------

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


    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()

                           
# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    app.run(debug=True)