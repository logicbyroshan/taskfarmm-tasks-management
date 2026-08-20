# TaskMitra — Smart Task Management Platform

> A premium, full-stack Django task manager with AI-powered automation, Kanban boards, project tracking, and real-time progress dashboards.

![Python](https://img.shields.io/badge/Python-3.10%2B-3b82f6?style=flat-square&logo=python)
![Django](https://img.shields.io/badge/Django-4.2-green?style=flat-square&logo=django)
![License](https://img.shields.io/badge/License-MIT-a78bfa?style=flat-square)

---

## ✨ Features

### 🏠 Dashboard
- Live stats: Total / In Progress / Completed / Overdue task counts
- **Overall Progress** bar with **By-Project toggle** — see per-project completion %
- Recent tasks list with inline check-to-complete
- Clickable Task Status grid (Backlog → Canceled) linking to filtered views
- Recently Completed tasks panel
- Projects quick-access cards

### 📋 All Tasks (Manage Tasks)
- Server-side filtering: Status / Priority / Project / Sort
- Task count badge
- **Predefined Task Template Library** — 39+ curated templates across 8 categories
- Inline edit & delete via AJAX modal

### 📌 Kanban Board
- 6-column Kanban: Backlog · To Do · In Progress · Done · On Hold · Canceled
- Project filter dropdown
- Drag-and-drop ready card layout
- Move-to-status quick actions

### 🤖 AI Assistant
- **Floating AI button** on every page opens a **slide-in side drawer**
  - Quick-action chips (Launch Plan, Breakdown, Marketing, Dev Setup)
  - Free-form prompt input
  - "Add as Task" — pre-fills the New Task modal with AI output
  - Deep-link to the full AI page
- **Dedicated AI Assistant Page** (`/ai-assistant/`)
  - 4 action cards: Create Project, Generate Tasks, Break Down Work, Launch Plan
  - Output modes: Suggest → view first, Auto-Create Tasks, Auto-Create Project + Tasks
  - 8 quick-prompt chips for common workflows
  - Bulk task creation (up to 8 tasks at once)
  - Project auto-creation with task list

### ⚙️ Settings
- Profile edit (name, email)
- Password change
- Theme & default priority/status preferences (saved to DB)
- Notification toggles (Task Reminders, Due Date Alerts, App Updates)
- Stats overview (Total, Completed, In Progress, Overdue)
- Data Export: JSON / CSV
- Danger Zone: Clear All Tasks, Clear All Data

### 🗂️ Projects
- Create, edit, delete projects with custom color
- Task counts and progress per project

---

## 🛠 Tech Stack

| Layer       | Technology |
|-------------|------------|
| Backend     | Django 4.2 + SQLite (dev) |
| Frontend    | Vanilla HTML/CSS/JS — no frameworks |
| Fonts       | Plus Jakarta Sans (Google Fonts) |
| Icons       | Font Awesome 6 |
| Background  | Vanta.js Dots |
| Auth        | DemoAuthMiddleware (dev) → swap for `django.contrib.auth` in prod |

---

## 🚀 Quick Start

```bash
# 1. Clone
git clone https://github.com/logicbyroshan/smart-tasks-manager.git
cd smart-tasks-manager

# 2. Virtual environment
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # macOS/Linux

# 3. Install dependencies
pip install django

# 4. Migrate database
python manage.py migrate

# 5. Seed pre-defined task templates
python manage.py seed_predefined_tasks

# 6. Run development server
python manage.py runserver
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) — logged in automatically as **Demo User**.

---

## 📁 Project Structure

```
TaskMitra/
├── config/               # Django settings, urls, wsgi
├── todo/                 # Core app
│   ├── models.py         # Task, Category, UserProfile, PreDefinedTask
│   ├── views.py          # All page + API views
│   ├── urls.py           # URL routing
│   ├── forms.py          # Task, Category, User forms
│   ├── admin.py          # Admin registrations
│   └── management/commands/seed_predefined_tasks.py
├── templates/todo/
│   ├── base.html         # Global layout + AI side drawer
│   ├── index.html        # Dashboard
│   ├── manage-tasks.html # All Tasks + Template Library
│   ├── kanban.html       # Kanban board
│   ├── ai_assistant.html # Full AI assistant page
│   └── settings.html     # Settings page
└── static/todo/
    ├── css/              # base.css, style.css, settings.css, my-tasks.css
    └── js/               # script.js
```

---

## 🔌 Key API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET`  | `/api/stats/` | Task statistics JSON |
| `GET`  | `/api/predefined-tasks/` | List task templates |
| `POST` | `/api/predefined-tasks/add/` | Add template as task |
| `POST` | `/api/ai/suggest/` | AI suggestion for a prompt |
| `POST` | `/api/ai/create-task/` | Create task from AI output |
| `POST` | `/api/ai/create-project/` | Create project + tasks from AI |
| `GET/POST` | `/task/<id>/update/` | AJAX task edit |
| `POST` | `/task/<id>/delete/` | AJAX task delete |

See [API.md](./API.md) for full documentation.

---

## 📝 License

MIT © [logicbyroshan](https://github.com/logicbyroshan)
