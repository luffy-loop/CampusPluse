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
│   ├── admin-login.css
│   ├── admin.css
│   ├── admin.js
│   ├── landing.css
│   ├── script.js
│   ├── student-login.css
│   ├── style.css
│   ├── track.css
│   └── track.js
└── templates/
    ├── admin.html
    ├── admin_login.html
    ├── index.html
    ├── student.html
    ├── student_login.html
    └── track.html
```
## Environment Variables

Create a `.env` file in the project root:

```env
MONGODB_URI=your_mongodb_connection_string
MONGODB_DB=campuspluse
GEMINI_API_KEY=your_gemini_api_key
FLASK_SECRET_KEY=your_secret_key
ADMIN_USERNAME=your_admin_username
ADMIN_PASSWORD=your_admin_password
```

Do not commit your `.env` file or expose your actual credentials.

## Installation

```bash
git clone https://github.com/luffy-loop/CampusPluse.git
cd CampusPluse
python -m venv venv
```

Activate the virtual environment:

### Windows PowerShell

```powershell
.\venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the application:

```bash
python app.py
```

## Deployment

CampusPluse is deployed using Render.

**Live Demo:** https://campuspluse-z1ih.onrender.com/

## Status

CampusPluse is a project prototype demonstrating AI-assisted complaint management, MongoDB persistence, student access, and administrative monitoring.
