<div align="center">
  <h1>TaskFlow</h1>
  <p><b>Role-based task & project management for teams — built with Flask + Bootstrap.</b></p>

  <p>
    <a href="https://taskflow-3p0i.onrender.com" target="_blank"><img alt="Live Demo" src="https://img.shields.io/badge/Live-Demo-009639?logo=render&logoColor=white"></a>
    <a href="#"><img alt="Python" src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white"></a>
    <a href="#"><img alt="Flask" src="https://img.shields.io/badge/Flask-3.x-000000?logo=flask&logoColor=white"></a>
    <a href="#"><img alt="SQLAlchemy" src="https://img.shields.io/badge/SQLAlchemy-2.x-D71F00?logo=sqlalchemy&logoColor=white"></a>
    <a href="#"><img alt="Bootstrap" src="https://img.shields.io/badge/Bootstrap-5-7952B3?logo=bootstrap&logoColor=white"></a>
    <a href="#"><img alt="AI" src="https://img.shields.io/badge/AI-Powered-FF6F00?logo=openai&logoColor=white"></a>
    <a href="#"><img alt="Tests" src="https://img.shields.io/badge/Tests-pytest-0A9EDC?logo=pytest&logoColor=white"></a>
  </p>
</div>

---

## What is TaskFlow?

TaskFlow is a professional task management web app designed for small teams:

- Admins can create projects, manage tasks, assign work, and control permissions.
- Members can focus on what they own: track assigned work, update status, add comments, and watch tasks.

It ships with a clean UI (Bootstrap 5), a real dashboard, in-app notifications, audit logs, and a small REST API for task operations.

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Default Login](#default-login)
- [Project Structure](#project-structure)
- [RBAC & Permissions](#rbac--permissions)
- [REST API](#rest-api)
- [AI Project Planning](#ai-project-planning)
- [Migrations](#migrations)
- [Tests](#tests)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

## Features

- Dashboard metrics (task totals, completion rate, overdue detection, workload, throughput).
- Role-based access control (RBAC) with:
  - Default role permissions
  - Admin UI to grant additional permissions
- Projects: create, edit, view, and organize tasks by project.
- Tasks:
  - Priority, due dates, assignees
  - Expanded workflow (Backlog → Review → Done)
  - Dependencies and watchers
  - Comments and activity timeline
- Governance:
  - Audit logs for important admin actions
  - Permission matrix screen
- Notifications:
  - In-app notification center
  - REST endpoint for acknowledging notifications
- REST API (session-authenticated) for listing tasks, transitions, and notifications.

## Tech Stack

- Backend: Python, Flask, Flask-Login
- Database: SQLite by default; supports PostgreSQL via `DATABASE_URL`
- ORM/Migrations: SQLAlchemy, Flask-SQLAlchemy, Alembic
- Frontend: Bootstrap 5, Jinja2 templates, vanilla JS
- Server: Gunicorn (production via Procfile)

## Quick Start

### Prerequisites

- Python 3.10+
- (Optional) PostgreSQL, if you want `DATABASE_URL` instead of SQLite

### Setup

```bash
git clone https://github.com/navadeep0508/TaskFlow.git
cd taskflow
python -m venv venv
```

Activate:

```bash
.\venv\Scripts\activate
```

Linux/macOS:

```bash
source venv/bin/activate
```

Install:

```bash
pip install -r requirements.txt
```

Create a `.env` (see [Configuration](#configuration)), then run:

```bash
python app.py
```

Open:

- http://127.0.0.1:5000

## Configuration

TaskFlow reads environment variables using `python-dotenv` (`load_dotenv()` in [app.py](app.py#L21)).

Create a local `.env` file (do not commit secrets):

```env
SECRET_KEY="replace-with-a-random-secret"
# Optional: defaults to sqlite:///taskflow.db if not set or invalid
DATABASE_URL="sqlite:///taskflow.db"

# Optional: enables Admin → AI Planning
OPENROUTER_API_KEY="replace-with-your-openrouter-key"
```

Generate a secure secret key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Default Login

On startup, TaskFlow ensures an admin user exists (see [_ensure_admin_user](app.py#L50-L77)).

- Email: `admin@taskflow.com`
- Password: `admin123`

Change these before deploying publicly.

## Project Structure

```text
taskflow/
  app.py                  # Flask app + blueprint registration
  database.py             # SQLAlchemy init
  models/                 # SQLAlchemy models (users, projects, tasks, governance)
  routes/                 # Blueprints (auth, tasks, projects, admin, API)
  services/               # Domain services (reporting, AI planning, notifications)
  templates/              # Jinja2 pages (dashboard, tasks, admin screens)
  static/                 # CSS/JS assets
  migrations/             # Alembic migrations
  tests/                  # pytest suite
  requirements.txt
  Procfile                # gunicorn entry for deployment
```

## RBAC & Permissions

Roles live in [models/user.py](models/user.py#L8-L35):

- Admin: full access (plus permission management & audit log viewing)
- Member: task transitions/comments/watch + API access

Default permission keys include:

- `project.manage`
- `task.create`, `task.edit`, `task.delete`, `task.assign`, `task.transition`
- `admin.permissions.manage`, `audit.view`
- `api.access`

Admins can grant extra permissions in:

- `/admin/permissions`

## REST API

API routes are registered at `/api/tasks` in [routes/api_tasks.py](routes/api_tasks.py#L10).

All endpoints require:

- An authenticated session (login via UI)
- The `api.access` permission

Endpoints:

- `GET /api/tasks` — list tasks (filters: `q`, `status`, `project_id`, `assignee_id`, `priority`, pagination)
- `POST /api/tasks/<task_id>/transition` — update status via workflow transition
- `GET /api/tasks/notifications` — list latest notifications (max 100)
- `POST /api/tasks/notifications/<notification_id>/ack` — mark notification as read

## AI Project Planning

TaskFlow includes an admin-only AI planning screen that leverages artificial intelligence to streamline project setup:

- **Route**: `/admin/ai-planning` (see [routes/ai_planning.py](routes/ai_planning.py#L12))
- **How it works**:
  1. Enter a project description or goal
  2. AI analyzes the requirements and breaks down the project into actionable tasks
  3. Each task includes suggested priority, estimated time, and dependencies
  4. Review and edit the generated tasks before creating the project
  5. One-click project creation with all tasks pre-populated

### Requirements

- `OPENROUTER_API_KEY` in `.env` (see [services/ai_service.py](services/ai_service.py#L6-L25))
- The `project.manage` permission
- Active internet connection for AI API calls

### Use Cases

- **New Projects**: Quickly bootstrap new projects with comprehensive task lists
- **Complex Initiatives**: Break down large, ambiguous projects into manageable tasks
- **Planning Efficiency**: Save hours of manual planning with AI-generated task breakdowns
- **Best Practices**: AI suggests industry-standard task structures and workflows

## Migrations

Alembic is configured in [alembic.ini](alembic.ini#L1-L5).

Apply migrations:

```bash
alembic upgrade head
```

## Tests

Run the suite:

```bash
pytest
```

## Deployment

The repo includes a [Procfile](Procfile) for platforms like Heroku/Render:

```text
web: gunicorn app:app
```

Minimum production env vars:

- `SECRET_KEY` (required)
- `DATABASE_URL` (recommended; defaults to local SQLite if not provided)
- `OPENROUTER_API_KEY` (optional, for AI planning feature)

### Deploy to Render

TaskFlow is configured for easy deployment on Render using the included `render.yaml` file.

**Prerequisites:**
- A Render account (free tier available)
- GitHub repository with your TaskFlow code

**Steps:**

1. **Push your code to GitHub** (if not already done)
   ```bash
   git add .
   git commit -m "Ready for Render deployment"
   git push origin main
   ```

2. **Create a new Web Service on Render:**
   - Go to [dashboard.render.com](https://dashboard.render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Render will automatically detect the `render.yaml` configuration

3. **Configure Environment Variables:**
   - `SECRET_KEY`: Render will auto-generate this (configured in render.yaml)
   - `DATABASE_URL`: Render will auto-connect to the PostgreSQL database (configured in render.yaml)
   - `OPENROUTER_API_KEY`: Add this manually if you want to use AI planning features

4. **Deploy:**
   - Click "Create Web Service"
   - Render will automatically:
     - Install dependencies from `requirements.txt`
     - Run database migrations (`alembic upgrade head`)
     - Start the application with Gunicorn

5. **Access your app:**
   - Once deployed, Render will provide a URL like `https://taskflow.onrender.com`
   - Log in with the default admin credentials (change these in production!)
     - Email: `admin@taskflow.com`
     - Password: `admin123`

**Note:** The `render.yaml` file creates a PostgreSQL database automatically. If you prefer to use your own database, you can modify the configuration and provide the `DATABASE_URL` manually.

### Manual Deployment (Alternative)

If you prefer manual configuration without `render.yaml`:

1. Create a Web Service on Render
2. Set these environment variables manually:
   - `SECRET_KEY`: Generate a secure random key
   - `DATABASE_URL`: Your PostgreSQL connection string
   - `OPENROUTER_API_KEY`: (optional) Your OpenRouter API key
3. Build command: `pip install -r requirements.txt && alembic upgrade head`
4. Start command: `gunicorn app:app`

## Troubleshooting

- Login loops back to `/login`: ensure `SECRET_KEY` is set and cookies are enabled.
- Using Supabase Postgres: TaskFlow auto-adds `sslmode=require` when host ends with `.supabase.co` (see [_normalize_database_url](app.py#L25-L33)).
- AI planning shows an error: add `OPENROUTER_API_KEY` and restart the server.

---

Made for building calm, consistent team delivery.
## Troubleshooting

- Login loops back to `/login`: ensure `SECRET_KEY` is set and cookies are enabled.
- Using Supabase Postgres: TaskFlow auto-adds `sslmode=require` when host ends with `.supabase.co` (see [_normalize_database_url](app.py#L25-L33)).
- AI planning shows an error: add `OPENROUTER_API_KEY` and restart the server.

---

Made for building calm, consistent team delivery.
