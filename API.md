# 📡 TaskFarmm API Documentation

TaskFarmm provides a dual API surface:
1. **REST API v1 (`/api/v1/`)**: Production-ready RESTful API powered by Django REST Framework (DRF) with JWT Bearer Token authentication, filtering, pagination, search, and throttling.
2. **Internal Session / AJAX Endpoints**: High-performance JSON/HTMX endpoints optimized for web frontend interactions.

**Base URL**: `http://127.0.0.1:8000/` (or your production deployment domain)

---

# 🚀 REST API v1 (`/api/v1/`)

## 🔑 Authentication (JWT)

Include the JWT access token in the `Authorization` header for all requests:
```http
Authorization: Bearer <your_access_token>
```

### 1. Obtain JWT Token Pair
- **Endpoint**: `POST /api/v1/auth/token/`
- **Body**:
```json
{
  "username": "demo_user",
  "password": "your_password"
}
```
- **Response**:
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsIn...",
  "access": "eyJhbGciOiJIUzI1NiIsIn..."
}
```

### 2. Refresh Access Token
- **Endpoint**: `POST /api/v1/auth/token/refresh/`
- **Body**:
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsIn..."
}
```
- **Response**:
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsIn..."
}
```

---

## 📋 Tasks API (`/api/v1/tasks/`)

### 1. List Tasks
- **Endpoint**: `GET /api/v1/tasks/`
- **Query Parameters**:
  - `status`: Filter by status (`backlog`, `not-started`, `in-progress`, `completed`, `on-hold`, `canceled`, `all`)
  - `priority`: Filter by priority (`high`, `moderate`, `low`, `all`)
  - `project`: Filter by project ID or `none`
  - `search`: Search task titles and descriptions
  - `sort`: Order by `newest`, `oldest`, `due_date`, `priority`, `title`, `updated`
  - `page`: Page number (default: 1, page size: 20)
- **Response (Paginated)**:
```json
{
  "count": 42,
  "next": "http://127.0.0.1:8000/api/v1/tasks/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Design Figma Design Tokens",
      "priority": "high",
      "priority_display": "High",
      "status": "in-progress",
      "status_display": "In Progress",
      "due_date": "2026-09-01",
      "category": {
        "id": 2,
        "name": "Design System",
        "color": "#8b5cf6"
      },
      "created_at": "2026-08-20T14:30:00Z",
      "updated_at": "2026-08-21T09:15:00Z"
    }
  ]
}
```

### 2. Retrieve Task Detail
- **Endpoint**: `GET /api/v1/tasks/{id}/`
- **Response**:
```json
{
  "id": 1,
  "title": "Design Figma Design Tokens",
  "description": "Establish typography and color variables in Figma.",
  "checklist": [
    {"id": "chk_1", "text": "Colors palette", "completed": true},
    {"id": "chk_2", "text": "Typography scale", "completed": false}
  ],
  "checklist_progress": {
    "total": 2,
    "completed": 1,
    "percentage": 50
  },
  "priority": "high",
  "priority_display": "High",
  "status": "in-progress",
  "status_display": "In Progress",
  "due_date": "2026-09-01",
  "is_predefined": false,
  "category": {
    "id": 2,
    "name": "Design System",
    "color": "#8b5cf6"
  },
  "comments": [
    {
      "id": 4,
      "user": "demo_user",
      "content": "Tokens imported successfully.",
      "time_ago": "2 hours ago",
      "created_at_display": "22 Aug 2026, 14:00",
      "created_at": "2026-08-22T14:00:00Z"
    }
  ],
  "comment_count": 1,
  "created_at": "2026-08-20T14:30:00Z",
  "updated_at": "2026-08-21T09:15:00Z",
  "completed_at": null
}
```

### 3. Create Task
- **Endpoint**: `POST /api/v1/tasks/`
- **Body**:
```json
{
  "title": "Build user onboarding tour",
  "description": "Interactive walk-through modal.",
  "priority": "high",
  "status": "not-started",
  "category_id": 2,
  "due_date": "2026-09-15",
  "checklist": [
    {"id": "chk_1", "text": "Step 1 UI", "completed": false}
  ]
}
```

### 4. Update / Partial Update Task
- **Endpoint**: `PUT /api/v1/tasks/{id}/` or `PATCH /api/v1/tasks/{id}/`
- **Body**: Key-value pairs of fields to update.

### 5. Delete Task
- **Endpoint**: `DELETE /api/v1/tasks/{id}/`
- **Response**: `204 No Content`

### 6. Toggle Task Status
- **Endpoint**: `POST /api/v1/tasks/{id}/toggle/`
- **Response**: Full updated task object with new status.

### 7. Add Comment to Task
- **Endpoint**: `POST /api/v1/tasks/{id}/comment/`
- **Body**: `{"content": "Discussing implementation details."}`

### 8. Update Checklist
- **Endpoint**: `POST /api/v1/tasks/{id}/checklist/`
- **Body**:
```json
{
  "checklist": [
    {"id": "chk_1", "text": "Item 1", "completed": true},
    {"id": "chk_2", "text": "Item 2", "completed": false}
  ]
}
```

### 9. Export Tasks
- **Endpoint**: `GET /api/v1/tasks/export/?format=json|csv`

---

## 📁 Projects API (`/api/v1/projects/`)

### 1. List Projects
- **Endpoint**: `GET /api/v1/projects/`

### 2. Create Project
- **Endpoint**: `POST /api/v1/projects/`
- **Body**:
```json
{
  "name": "Mobile Application",
  "color": "#10b981",
  "description": "iOS and Android apps"
}
```

### 3. Update / Delete Project
- `PATCH /api/v1/projects/{id}/`
- `DELETE /api/v1/projects/{id}/`

---

## 📊 Analytics API (`/api/v1/stats/`)

- **Endpoint**: `GET /api/v1/stats/`
- **Response**:
```json
{
  "success": true,
  "stats": {
    "total_count": 25,
    "done_count": 10,
    "in_progress_count": 6,
    "backlog_count": 4,
    "to_do_count": 3,
    "on_hold_count": 1,
    "canceled_count": 1,
    "overdue_count": 0,
    "due_today_count": 2,
    "completion_rate": 40
  }
}
```

---

## 🪄 Task Templates API (`/api/v1/templates/`)

### 1. List Templates
- **Endpoint**: `GET /api/v1/templates/?category=website|development|marketing|design|operations|finance|hr|general`

### 2. Add Template to User Tasks
- **Endpoint**: `POST /api/v1/templates/{id}/add/`
- **Body**: `{"category_id": 1}`

---

## 👤 User Profile API (`/api/v1/profile/`)

- **GET /api/v1/profile/**: Retrieve current user profile settings.
- **PATCH /api/v1/profile/**: Update preferences (`theme`, `notify_task_reminders`, `default_task_priority`, etc.).

---

# 🌐 Internal Session / AJAX Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/task/create/` | Create task via session form |
| `POST` | `/task/<id>/update/` | Inline update task (Trello modal live save / drag-and-drop) |
| `POST` | `/task/<id>/delete/` | Delete task |
| `POST` | `/task/<id>/toggle/` | Toggle Done / To Do status |
| `POST` | `/task/<id>/attachment/` | Upload file(s) or clipboard base64 pasted images to task |
| `POST`/`DELETE` | `/task/attachment/<id>/delete/` | Delete task attachment |
| `POST` | `/task/<id>/comment/` | Add activity comment |
| `POST` | `/task/comment/<id>/edit/` | Edit activity comment inline |
| `POST`/`DELETE` | `/task/comment/<id>/delete/` | Delete activity comment |
| `POST` | `/task/<id>/checklist/` | Replace / sync task checklist items |
| `POST` | `/projects/create/` | Create new project |
| `POST` | `/category/<id>/update/` | Edit project |
| `POST` | `/category/<id>/delete/` | Delete project |
| `POST` | `/project/<id>/share/` | Generate collaboration share token |
| `GET` | `/project/join/<token>/` | Join shared project board |
| `GET` | `/api/stats/` | Fetch aggregated user stats |
| `GET` | `/api/export/tasks/?format=json\|csv` | Export all tasks |
| `POST` | `/api/ai/suggest/` | AI Action Plan assistant |
| `POST` | `/api/ai/create-task/` | Instant task creation from AI |
| `POST` | `/api/ai/create-project/` | Instant project + tasks batch creation |

