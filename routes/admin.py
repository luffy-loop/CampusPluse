from flask import Blueprint, request, render_template, session, redirect, url_for, jsonify
import os
import hmac
from datetime import datetime
from mongodb import get_complaints
from config import DISABLE_DB

admin_bp = Blueprint("admin", __name__)

mock_complaints = {}
mock_complaint_counter = 1


@admin_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "GET":
        return render_template("admin_login.html")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    admin_username = os.getenv("ADMIN_USERNAME", "").strip()
    admin_password = os.getenv("ADMIN_PASSWORD", "")

    if (
        admin_username
        and admin_password
        and hmac.compare_digest(username, admin_username)
        and hmac.compare_digest(password, admin_password)
    ):
        session["admin"] = True
        return redirect(url_for("admin"))

    return render_template(
        "admin_login.html",
        error="Invalid username or password."
    ), 401


@admin_bp.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin.admin_login"))


@admin_bp.route("/admin")
def admin():
    return render_template("admin.html")


@admin_bp.route("/api/admin/dashboard")
def admin_dashboard():
    try:
        if DISABLE_DB:
            complaints = list(mock_complaints.values())

            total = len(complaints)
            pending = sum(
                1 for c in complaints
                if c.get("status") == "Pending"
            )
            high_priority = sum(
                1 for c in complaints
                if c.get("priority") in ("High", "Critical")
            )
            resolved = sum(
                1 for c in complaints
                if c.get("status") == "Resolved"
            )

            dept_count = {}

            for c in complaints:
                dept = c.get("department", "Unassigned")
                dept_count[dept] = dept_count.get(dept, 0) + 1

            departments = [
                {
                    "department": dept,
                    "count": count
                }
                for dept, count in sorted(
                    dept_count.items(),
                    key=lambda x: x[1],
                    reverse=True
                )
            ]

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
                    "created_at": (
                        c["created_at"].strftime(
                            "%d %b %Y, %I:%M %p"
                        )
                        if c["created_at"]
                        else None
                    ),
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

        complaints_col = get_complaints()
        total = complaints_col.count_documents({})
        pending = complaints_col.count_documents({"status": "Pending"})
        high_priority = complaints_col.count_documents({
            "priority": {"$in": ["High", "Critical"]}
        })
        resolved = complaints_col.count_documents({"status": "Resolved"})

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
                {"$sort": {"count": -1}}
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


@admin_bp.route(
    "/api/admin/complaints/<int:complaint_id>/status",
    methods=["PUT"]
)
def update_complaint_status(complaint_id):
    try:
        data = request.get_json() or {}
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


@admin_bp.route("/api/admin/signals")
def campus_signals():
    try:
        if DISABLE_DB:
            return jsonify({
                "success": True,
                "signals": [],
                "mode": "mock"
            })

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
                                        "case": {
                                            "$eq": [
                                                "$priority",
                                                "Critical"
                                            ]
                                        },
                                        "then": 4
                                    },
                                    {
                                        "case": {
                                            "$eq": [
                                                "$priority",
                                                "High"
                                            ]
                                        },
                                        "then": 3
                                    },
                                    {
                                        "case": {
                                            "$eq": [
                                                "$priority",
                                                "Medium"
                                            ]
                                        },
                                        "then": 2
                                    },
                                    {
                                        "case": {
                                            "$eq": [
                                                "$priority",
                                                "Low"
                                            ]
                                        },
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
                "average_severity": (
                    round(
                        float(row["average_severity"]),
                        1
                    )
                    if row["average_severity"] is not None
                    else 0
                ),
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
