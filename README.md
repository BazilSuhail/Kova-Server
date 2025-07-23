# Task Management API

A Flask-based REST API for task management with MongoDB and JWT authentication.

## Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Set up MongoDB and update `.env` with `MONGO_URI`.
3. Run: `python run.py`

## Endpoints
- `/api/auth/signup`: Create a user.
- `/api/auth/login`: Authenticate user.
- `/api/users/profile`: Manage user profile.
- `/api/tasks`: Manage tasks.
- `/api/subtasks/task/<task_id>`: Manage subtasks.
- `/api/notifications`: Manage notifications.
- `/api/planner`: Manage planners.
- `/api/summaries`: Manage summaries.

## Testing
Use `pytest` in the `tests` folder.