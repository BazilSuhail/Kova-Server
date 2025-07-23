# Task Management API

A Flask-based REST API for task management with MongoDB and JWT authentication.

***

## 🚀 Setup Instructions

1. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   .\venv\Scripts\Activate   # On Windows
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Export dependencies to `requirements.txt`:**
   ```bash
   pip freeze > requirements.txt
   ```

4. **Set up your environment variables:**
   - Create a `.env` file.
   - Add your MongoDB URI:
     ```env
     MONGO_URI=your_mongo_connection_string
     ```

5. **Run the server:**
   ```bash
   python run.py
   ```

***

## 🗂️ Project Structure


```
    zenflow-server/
    │
    ├── app/
    │   ├── __pycache__/              # Python bytecode cache
    │   ├── api/                      # All route/controller logic
    │   │   ├── __init__.py
    │   │   ├── auth.py               # User authentication routes
    │   │   ├── notifications.py      # Notifications routes
    │   │   ├── planner.py            # Planner routes
    │   │   ├── subtasks.py           # Subtask-related routes
    │   │   ├── summaries.py          # Summary generation routes
    │   │   ├── tasks.py              # Task CRUD routes
    │   │   └── users.py              # User profile routes
    │   │
    │   ├── middleware/               # Middleware for things like auth checks
    │   │   ├── __init__.py
    │   │   └── auth.py               # Auth-related middleware
    │   │
    │   ├── models/                   # MongoDB models/schemas
    │   │   ├── __init__.py
    │   │   ├── notification.py       # Notification schema
    │   │   ├── planner.py            # Planner schema
    │   │   ├── subtask.py            # Subtask schema
    │   │   ├── summary.py            # Summary schema
    │   │   ├── task.py               # Task schema
    │   │   └── user.py               # User schema
    │   │
    │   └── services/                 # Business logic/services
    │       ├── __init__.py
    │       ├── config.py             # App configuration (e.g., DB, env)
    │       └── utils.py              # Utility/helper functions
    │
    ├── venv/                         # Python virtual environment
    │
    ├── .env                          # Environment variables
    ├── .gitignore                    # Git ignore rules
    ├── README.md                     # This file
    ├── requirements.txt              # Python package dependencies
    └── run.py                        # Entry point of the application

```

</details>

***

## 📚 API Endpoints

### Auth
- `POST /api/auth/signup` – Create a new user
- `POST /api/auth/login` – Authenticate a user

### User
- `GET /api/users/profile` – Get or update user profile

### Tasks
- `GET/POST /api/tasks` – List or create tasks
- `PUT/DELETE /api/tasks/<id>` – Update or delete task

### Subtasks
- `GET/POST /api/subtasks/task/<task_id>` – Manage subtasks for a task

### Notifications
- `GET/POST /api/notifications` – Manage notifications

### Planner
- `GET/POST /api/planner` – Daily/weekly planner management

### Summaries
- `GET /api/summaries` – View task summaries

***

## 🧪 Testing

You can run tests using:

```bash
pytest tests/
```

> (Note: Add test cases inside a `tests/` directory.)

***

## 📌 Notes

- Make sure MongoDB is running and accessible via the URI in `.env`.
- All routes are prefixed with `/api`.

***
