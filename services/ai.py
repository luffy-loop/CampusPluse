import os
import json
from google import genai
from dotenv import load_dotenv
load_dotenv()

client = None


def analyze_complaint(description):

    global client

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

    if client is None:
        client = genai.Client(
            api_key=os.getenv("GEMINI_API_KEY")
        )

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

    try:
        analysis = json.loads(response.output_text)
    except (json.JSONDecodeError, TypeError):
        return {
            "category": "Other",
            "department": "General Administration",
            "location": "Unknown",
            "severity": 5,
            "priority": "Medium",
            "issue": description[:100],
            "recommended_action": "Review and assign this complaint manually."
        }

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

    allowed_priorities = {
        "Low",
        "Medium",
        "High",
        "Critical"
    }

    if analysis.get("priority") not in allowed_priorities:
        analysis["priority"] = "Medium"

    severity = analysis.get("severity")

    if not isinstance(severity, int) or not 1 <= severity <= 10:
        analysis["severity"] = 5

    return analysis