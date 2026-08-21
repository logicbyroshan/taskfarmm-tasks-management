# 📡 TaskFlixx API Documentation

TaskFlixx provides internal RESTful and AJAX API endpoints designed for real-time frontend interaction, stats aggregation, AI assistance, template management, and full data export.

**Base URL**: `http://127.0.0.1:8000/` (or your production deployment domain)

---

## 🔒 Authentication & Headers

All AJAX mutation endpoints require:
- `X-CSRFToken`: Valid Django CSRF token.
- `X-Requested-With: XMLHttpRequest` header.
- Authenticated user session.

---

## 📋 Task Endpoints

### 1. Create Task
- **Endpoint**: `POST /task/create/`
- **Body**: Form data or JSON (`title`, `description`, `priority`, `status`, `category`, `due_date`)
- **Response**:
```json
{
  "success": true,
  "message": "Task created successfully!",
  "task": {
    "id": 21,
    "title": "Build user onboarding tour",
    "status": "not-started",
    "priority": "high"
  }
}
```

### 2. Update Task
- **Endpoint**: `POST /task/<int:pk>/update/`
- **Body**: Form data or JSON (`status`, `priority`, `title`, `description`, `category`, `due_date`)
- **Response**:
```json
{
  "success": true,
  "message": "Task updated successfully!"
}
```

### 3. Delete Task
- **Endpoint**: `POST /task/<int:pk>/delete/`
- **Response**:
```json
{
  "success": true,
  "message": "Task deleted successfully."
}
```

---

## 📁 Project / Category Endpoints

### 1. Create Project
- **Endpoint**: `POST /projects/create/` or `POST /category/create/`
- **Body**: `name`, `color` (Hex, e.g. `#3b82f6`)
- **Response**:
```json
{
  "success": true,
  "message": "Project created successfully!",
  "category": {
    "id": 8,
    "name": "Mobile App Launch",
    "color": "#3b82f6"
  }
}
```

### 2. Update Project
- **Endpoint**: `POST /category/<int:pk>/update/`
- **Body**: `name`, `color`
- **Response**: `302 Redirect` or JSON confirmation.

### 3. Delete Project
- **Endpoint**: `POST /category/<int:pk>/delete/`
- **Response**:
```json
{
  "success": true,
  "message": "Project deleted successfully."
}
```

---

## 📊 Analytics & Export APIs

### 1. Real-Time Stats API
- **Endpoint**: `GET /api/stats/`
- **Response**:
```json
{
  "success": true,
  "stats": {
    "total": 19,
    "done": 7,
    "in_progress": 4,
    "backlog": 3,
    "on_hold": 1,
    "canceled": 1,
    "to_do": 3,
    "overdue": 0,
    "completion_rate": 36
  }
}
```

### 2. Full Task Export API
- **Endpoint**: `GET /api/export/tasks/?format=json` or `GET /api/export/tasks/?format=csv`
- **JSON Response**:
```json
{
  "success": true,
  "total": 19,
  "tasks": [
    {
      "id": 1,
      "title": "Design Figma Mockups",
      "description": "Create high fidelity dark mode UI screens",
      "project": "Design System",
      "priority": "high",
      "priority_display": "High",
      "status": "completed",
      "status_display": "Done",
      "due_date": "2026-09-01",
      "created_at": "2026-08-20 14:30:00",
      "completed_at": "2026-08-21 09:15:00"
    }
  ]
}
```
- **CSV Response**: Generates `taskflixx_tasks_export.csv` file download with complete columns.

---

## 🤖 AI Assistant APIs

### 1. AI Task & Project Suggestion
- **Endpoint**: `POST /api/ai/suggest/`
- **Body**: `{"prompt": "Launch an ecommerce mobile app"}`
- **Response**:
```json
{
  "success": true,
  "title": "E-Commerce Mobile App Launch Plan",
  "suggestion": "1. Configure push notification services...\n2. Set up payment gateway...\n3. Run App Store review audit...",
  "description": "Step-by-step launch sequence",
  "prompt": "Launch an ecommerce mobile app"
}
```

### 2. AI Create Task
- **Endpoint**: `POST /api/ai/create-task/`
- **Body**: `{"title": "Implement Stripe checkout", "priority": "high", "description": "Add Stripe Elements"}`
- **Response**:
```json
{
  "success": true,
  "message": "Task 'Implement Stripe checkout' created successfully!",
  "task_id": 25,
  "task_title": "Implement Stripe checkout"
}
```

### 3. AI Create Project with Batch Tasks
- **Endpoint**: `POST /api/ai/create-project/`
- **Body**: `{"name": "Q3 Sprint", "description": "Sprint tasks", "tasks": ["Task A", "Task B", "Task C"]}`
- **Response**:
```json
{
  "success": true,
  "message": "Project 'Q3 Sprint' created with 3 tasks!",
  "project_id": 9,
  "project_name": "Q3 Sprint",
  "tasks_created": [
    { "id": 26, "title": "Task A" },
    { "id": 27, "title": "Task B" },
    { "id": 28, "title": "Task C" }
  ]
}
```

---

## 🪄 Template Library APIs

### 1. Get Predefined Templates
- **Endpoint**: `GET /api/predefined-tasks/?category=all|website|marketing|design|development|operations|finance|hr|general`
- **Response**:
```json
{
  "success": true,
  "tasks": [
    {
      "id": 1,
      "title": "Conduct UX audit and usability review",
      "description": "Evaluate current user flow and identify drop-off points.",
      "category": "design",
      "suggested_priority": "high",
      "icon": "fas fa-search"
    }
  ]
}
```

### 2. Add Template to Active Tasks
- **Endpoint**: `POST /api/predefined-tasks/add/`
- **Body**: `{"predefined_id": 1}`
- **Response**:
```json
{
  "success": true,
  "message": "Task 'Conduct UX audit and usability review' added!",
  "task_id": 29
}
```
