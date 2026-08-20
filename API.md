# TaskMitra API Documentation

Base URL: `http://127.0.0.1:8000/`

All AJAX endpoints require the `X-CSRFToken` header and `X-Requested-With: XMLHttpRequest`.

---

## Authentication

TaskMitra uses Django session authentication. In development, `DemoAuthMiddleware` auto-creates a session for a demo user. For production, replace with standard Django login.

---

## Task Endpoints

### GET/POST `/task/<id>/update/`

**GET** — Fetch task data for edit modal.

Response:
```json
{
  "success": true,
  "task": {
    "id": 1,
    "title": "My Task",
    "description": "...",
    "priority": "high",
    "status": "in-progress",
    "category": 2,
    "due_date": "2026-09-01"
  }
}
```

**POST** — Update task fields. Accepts `multipart/form-data` or JSON.

Body fields: `title`, `description`, `priority`, `status`, `category`, `due_date`

Response:
```json
{ "success": true }
```

---

### POST `/task/<id>/delete/`

Delete a task.

Response:
```json
{ "success": true }
```

---

### POST `/task/create/`

Create a new task via form submission. Returns redirect on success.

---

## Stats API

### GET `/api/stats/`

Returns aggregated task statistics for the current user.

Response:
```json
{
  "success": true,
  "total": 10,
  "completed": 3,
  "in_progress": 4,
  "backlog": 1,
  "on_hold": 0,
  "canceled": 0,
  "overdue": 2,
  "completion_rate": 30
}
```

---

## Predefined Task Templates

### GET `/api/predefined-tasks/`

Returns the list of all predefined task templates. Supports optional `?category=` query filter.

Response:
```json
{
  "success": true,
  "tasks": [
    {
      "id": 1,
      "title": "Set Up Domain & Hosting",
      "description": "...",
      "category": "Website Launch",
      "priority": "high",
      "icon": "fas fa-globe"
    }
  ]
}
```

---

### POST `/api/predefined-tasks/add/`

Add a predefined task template to the user's task list.

Body (JSON):
```json
{
  "task_id": 1,
  "category_id": 3
}
```

Response:
```json
{
  "success": true,
  "message": "Task added successfully",
  "task_id": 42
}
```

---

## AI Assistant Endpoints

### POST `/api/ai/suggest/`

Generate an AI suggestion/plan for a text prompt.

Body (JSON):
```json
{ "prompt": "Create a website launch plan" }
```

Response:
```json
{
  "success": true,
  "title": "Launch Strategy & Production Readiness",
  "suggestion": "1. Finalize DNS...\n2. Cross-browser QA...",
  "description": "...",
  "prompt": "Create a website launch plan"
}
```

---

### POST `/api/ai/create-task/`

Create a single task directly from AI suggestion data.

Body (JSON):
```json
{
  "title": "Configure DNS & SSL",
  "description": "Set up domain records and SSL certificate",
  "priority": "high",
  "status": "not-started",
  "category_id": 2
}
```

Response:
```json
{
  "success": true,
  "message": "Task \"Configure DNS & SSL\" created successfully!",
  "task_id": 45,
  "task_title": "Configure DNS & SSL"
}
```

---

### POST `/api/ai/create-project/`

Create a project (category) and optionally populate it with tasks in one call.

Body (JSON):
```json
{
  "name": "Website Launch Project",
  "description": "Full website launch plan",
  "color": "#3b82f6",
  "tasks": [
    { "title": "Configure DNS", "priority": "high" },
    { "title": "Run Lighthouse Audit", "priority": "moderate" },
    "Write post-launch report"
  ]
}
```

- `tasks` can be an array of strings (title only) or objects with `title` and `priority`.
- Maximum 10 tasks per call.

Response:
```json
{
  "success": true,
  "message": "Project \"Website Launch Project\" created with 3 tasks!",
  "project_id": 7,
  "project_name": "Website Launch Project",
  "tasks_created": [
    { "id": 46, "title": "Configure DNS" },
    { "id": 47, "title": "Run Lighthouse Audit" },
    { "id": 48, "title": "Write post-launch report" }
  ]
}
```

---

## Settings Endpoints

### POST `/settings/`

Handles multiple form actions via the `action` field:

| `action` value | Effect |
|---|---|
| `update_profile` | Update first name, last name, email |
| `change_password` | Change current user password |
| `update_preferences` | Save theme, default priority/status to UserProfile |
| `update_notifications` | Save notification toggle preferences |
| `export_tasks_json` | Returns tasks as JSON file download |
| `export_tasks_csv` | Returns tasks as CSV file download |
| `clear_tasks` | Delete all tasks (keeps projects) |
| `clear_all_data` | Delete all tasks AND projects |

---

## Error Format

All API endpoints return errors in this format:

```json
{
  "success": false,
  "error": "Human-readable error message"
}
```

HTTP status codes: `400` (bad request), `403` (forbidden), `404` (not found), `405` (wrong method), `500` (server error).
