<div align="center">
  <h1>TaskFlow</h1>
  <p><b>Role-based task & project management for teams — built with Flask + Bootstrap.</b></p>

  <p>
    <a href="#"><img alt="Python" src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white"></a>
    <a href="#"><img alt="Flask" src="https://img.shields.io/badge/Flask-3.x-000000?logo=flask&logoColor=white"></a>
    <a href="#"><img alt="SQLAlchemy" src="https://img.shields.io/badge/SQLAlchemy-2.x-D71F00?logo=sqlalchemy&logoColor=white"></a>
    <a href="#"><img alt="Bootstrap" src="https://img.shields.io/badge/Bootstrap-5-7952B3?logo=bootstrap&logoColor=white"></a>
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
git clone <your-repo-url>
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

TaskFlow includes an admin-only AI planning screen:

- `/admin/ai-planning` (see [routes/ai_planning.py](routes/ai_planning.py#L12))

It requires:

- `OPENROUTER_API_KEY` in `.env` (see [services/ai_service.py](services/ai_service.py#L6-L25))
- The `project.manage` permission

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

## Troubleshooting

- Login loops back to `/login`: ensure `SECRET_KEY` is set and cookies are enabled.
- Using Supabase Postgres: TaskFlow auto-adds `sslmode=require` when host ends with `.supabase.co` (see [_normalize_database_url](app.py#L25-L33)).
- AI planning shows an error: add `OPENROUTER_API_KEY` and restart the server.

---

Made for building calm, consistent team delivery.
