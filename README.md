# CampusPluse

[![Tests](https://github.com/luffy-loop/CampusPluse/actions/workflows/tests.yml/badge.svg)](https://github.com/luffy-loop/CampusPluse/actions/workflows/tests.yml)

AI-powered campus complaint management and intelligence system built with Flask, MongoDB, and Gemini.

## Live Demo

**Live Application:**  
https://campuspluse-z1ih.onrender.com/

CampusPluse provides separate student and administrator workflows for reporting, tracking, and managing campus complaints.

## Quality Signals

- **Tests:** 31 automated tests
- **Test Coverage:** 76%
- **CI:** GitHub Actions
- **Dependency Security:** `pip-audit`
- **Deployment Health:** `/health` endpoint with scheduled production checks
- **API Documentation:** `openapi.yaml`

## Overview

CampusPluse is a web-based campus complaint management system designed to make issue reporting and administrative response more organized and data-driven.

Students can submit campus complaints with supporting evidence and track complaint progress. Administrators can monitor complaints through a centralized dashboard, update complaint status, analyze department workload, and generate AI-assisted operational insights.

The system uses Google Gemini to analyze complaint descriptions and assist with:

- Complaint categorization
- Department routing
- Priority assessment
- Severity scoring
- Location extraction
- Issue summarization
- Recommended actions
- Recurring campus issue detection
- Administrative briefings

## Core Workflow

```text
Student
   ↓
Submit Complaint
   ↓
Gemini AI Analysis
   ↓
Category + Department + Priority + Severity
   ↓
MongoDB Persistence
   ↓
Admin Dashboard
   ↓
Status Updates + Campus Intelligence
   ↓
Student Complaint Tracking
```

## Features

### Student Portal

- Student login using university roll number
- Submit campus complaints
- Attach supporting evidence
- Anonymous complaint option
- AI-assisted complaint analysis
- Track complaint status
- View complaint history
- View complaint details

### Admin Dashboard

- Secure administrator login
- Complaint statistics
- Recent complaint monitoring
- Complaint filtering
- Complaint status updates
- Department workload monitoring
- High-priority complaint monitoring
- Campus signal detection
- AI-powered campus briefings
- Complaint SLA monitoring

### AI Complaint Intelligence

Gemini analyzes complaint descriptions and determines:

- Category
- Responsible department
- Location
- Severity
- Priority
- Issue summary
- Recommended action

Example:

```text
Complaint:
"The Wi-Fi in H1 13 has stopped working since morning."

AI Analysis:
Category: IT & Network
Department: IT & Network Services
Location: H1 13
Priority: High
Severity: 7
Recommended Action:
Inspect network connectivity and restore service.
```

## Screenshots

### CampusPluse Landing Page

![CampusPluse Landing Page](screenshots/Screenshot%202026-09-15%20193537.png)

### Student Portal

![CampusPluse Student Portal](screenshots/Screenshot%202026-09-15%20193558.png)

### Complaint Submission

![CampusPluse Complaint Submission](screenshots/Screenshot%202026-09-15%20193632.png)

### Complaint Tracking

![CampusPluse Complaint Tracking](screenshots/Screenshot%202026-09-15%20193729.png)

### Student Complaint History

![CampusPluse Complaint History](screenshots/Screenshot%202026-09-15%20193745.png)

### Admin Dashboard

![CampusPluse Admin Dashboard](screenshots/Screenshot%202026-09-15%20193835.png)

### Admin Complaint Management

![CampusPluse Admin Complaint Management](screenshots/Screenshot%202026-09-15%20193847.png)

## Tech Stack

### Backend

- Python
- Flask
- PyMongo
- Gunicorn

### Database

- MongoDB

### AI

- Google Gemini

### Frontend

- HTML
- CSS
- JavaScript

### Testing

- Pytest
- pytest-cov
- mongomock

### Deployment

- Render

## Project Structure

```text
CampusPluse/
├── app.py
├── config.py
├── mongodb.py
├── routes/
│   ├── __init__.py
│   ├── admin.py
│   ├── auth.py
│   ├── complaints.py
│   └── tracking.py
├── services/
│   └── ai.py
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
├── templates/
│   ├── admin.html
│   ├── admin_login.html
│   ├── index.html
│   ├── student.html
│   ├── student_login.html
│   └── track.html
├── tests/
│   ├── test_admin.py
│   ├── test_ai.py
│   ├── test_auth.py
│   ├── test_complaints.py
│   ├── test_health.py
│   ├── test_mongodb.py
│   └── test_tracking.py
├── openapi.yaml
├── requirements.txt
└── .gitignore
```

## Architecture

CampusPluse uses a modular Flask structure to separate major application responsibilities.

```text
app.py
 │
 ├── Flask application setup
 ├── Blueprint registration
 └── shared application configuration
        │
        ├── routes/
        │   ├── auth.py
        │   ├── complaints.py
        │   ├── admin.py
        │   └── tracking.py
        │
        ├── services/
        │   └── ai.py
        │
        └── mongodb.py
            └── MongoDB access
```

This structure keeps authentication, complaint handling, administration, tracking, and AI processing organized into separate modules.

## API Documentation

The complete API specification is available in [`openapi.yaml`](openapi.yaml) and can be imported into Swagger UI, Postman, or other OpenAPI-compatible tools.

### API Overview

### Student Authentication

```text
GET  /student/login
POST /student/login
GET  /student/logout
```

### Complaint Management

```text
POST /api/complaints
GET  /api/complaints
GET  /api/complaints/<complaint_id>
```

### Student Tracking

```text
GET /track
```

### Administration

```text
GET  /admin/login
POST /admin/login
GET  /admin/logout
GET  /admin

GET  /api/admin/dashboard
GET  /api/admin/signals
GET  /api/admin/briefing

PUT  /api/admin/complaints/<complaint_id>/status
GET  /api/admin/complaints/<complaint_id>/sla
```

## Testing

Run the full test suite locally:

```bash
python -m pytest -v
```

Run tests with coverage:

```bash
python -m pytest -v --cov=. --cov-report=term-missing
```

GitHub Actions runs the test suite with coverage on pushes and pull requests to `main`. Dependency vulnerabilities are checked separately with `pip-audit`.

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

Never commit `.env` or expose real credentials.

## Installation

Clone the repository:

```bash
git clone https://github.com/luffy-loop/CampusPluse.git
cd CampusPluse
```

Create a virtual environment:

```bash
python -m venv venv
```

### Windows PowerShell

Activate the environment:

```powershell
.\venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure the required environment variables in `.env`.

Start the application:

```bash
python app.py
```

The application will be available at:

```text
http://127.0.0.1:5000/
```

## Deployment

CampusPluse is deployed using Render.

**Live Demo:**  
https://campuspluse-z1ih.onrender.com/

The deployment exposes `/health` for application/database health checks. Production health is checked automatically by GitHub Actions on a scheduled basis.

Production deployment requires the appropriate environment variables to be configured in the hosting platform.

## Security

The project includes:

- Environment-based secret configuration
- Session-based student access
- Session-based administrator authentication
- Protected administrator routes
- File extension validation for uploaded evidence
- Secure filename handling
- Constant-time comparison for administrator credentials
- Automated dependency vulnerability scanning

## Current Status

CampusPluse is a working project prototype demonstrating:

- AI-assisted complaint classification
- MongoDB persistence
- Student complaint submission
- Complaint tracking
- Administrative monitoring
- Campus-level signals
- AI-generated administrative briefings
- Complaint SLA monitoring
- Modular Flask route organization
- Automated testing and CI
- Deployment health monitoring
- OpenAPI API documentation

## Roadmap

Planned improvements include:

- Stronger AI response validation
- Improved production security controls
- Further authentication hardening
- Improved observability and error monitoring

## License

This project is licensed under the MIT License.
