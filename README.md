# CampusPluse

AI-powered campus complaint management and intelligence system built with Flask, MongoDB, and Gemini.

## Overview

CampusPluse helps students report campus issues, track complaint progress, and allows administrators to monitor and manage complaints through a centralized dashboard.

The system uses AI to analyze complaints and assist with:

- Complaint categorization
- Department routing
- Priority assessment
- Severity scoring
- Location extraction
- Recommended actions
- Campus-level pattern detection
- Administrative insights

## Features

### Student Portal
- Submit campus complaints
- Attach supporting evidence
- Track complaint status
- View complaint history

### Admin Dashboard
- View complaint statistics
- Monitor recent complaints
- Filter complaints
- Update complaint status
- Monitor department workload
- View high-priority complaints
- Generate AI-powered campus briefings
- Detect recurring campus issues

### AI Complaint Intelligence
Gemini analyzes submitted complaints and determines:
- Category
- Responsible department
- Location
- Severity
- Priority
- Issue summary
- Recommended action

## Tech Stack

- Python
- Flask
- MongoDB
- PyMongo
- Google Gemini
- HTML
- CSS
- JavaScript
- Gunicorn

## Project Structure

```text
CampusPluse/
├── app.py
├── mongodb.py
├── requirements.txt
├── static/
│   ├── admin.css
│   ├── admin.js
│   ├── landing.css
│   ├── script.js
│   ├── style.css
│   ├── student-login.css
│   ├── track.css
│   └── track.js
└── templates/
    ├── admin.html
    ├── admin_login.html
    ├── index.html
    ├── student.html
    ├── student_login.html
    └── track.html
