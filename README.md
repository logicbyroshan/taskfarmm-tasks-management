# TaskFlixx — Smart Task Management Platform

> A premium, full-stack Django task management platform featuring an ambient fluid wave background, pure black OLED theme, Kanban boards, AI assistant, project tracking, and live productivity metrics.

![Python](https://img.shields.io/badge/Python-3.11%2B-3b82f6?style=flat-square&logo=python)
![Django](https://img.shields.io/badge/Django-5.2-green?style=flat-square&logo=django)
![License](https://img.shields.io/badge/License-MIT-a78bfa?style=flat-square)

---

## ✨ Key Features & Architecture

### 🌌 Dynamic Ambient Wave Background
- **60fps Fluid Wave Canvas Engine (`#bg-wave-canvas`)**: Mathematically animated multi-harmonic travelling wave harmonics across a fixed matrix of dots with interactive cursor ripples and luminous cyan-blue wave crests.

### 🖤 Pure Pitch-Black OLED Aesthetic
- Pure `#000000` background across all cards, containers, headers, sidebars, and modals with crisp, high-contrast borders and zero mismatched color tints.

### 🚫 Zero-Vertical-Scrollbar Design
- Clean, scrollbar-free interface globally across all pages, sidebars, and columns, with horizontal scrolling exclusively on the 6-column Kanban board.

### 🔝 Unified Header Bars & Floating Dropdowns
- Standardized `.page-header-bar` across All Tasks, Manage Projects, and Kanban with quick action buttons (`Add Project`, `Kanban`, `Add Task`).
- High `z-index` floating dropdowns that open seamlessly on top of cards and tables without clipping.

### 🏠 Live Dashboard
- Real-time counters: Backlog / To Do / In Progress / Done / On Hold / Canceled.
- Completion progress bars with per-project toggles.
- Recent and completed task feeds with instant 1-click status updates.

### 📋 All Tasks (Manage Tasks)
- Multi-parameter filtering: Status, Priority, Project, and Sort Order.
- **Predefined Task Template Library**: 39+ curated templates across 8 categories.
- Inline edit and delete modal workflows.

### 📌 6-Column Kanban Board
- Columns: Backlog · To Do · In Progress · Done · On Hold · Canceled.
- Project switcher and drag-and-drop card interaction.

### 🤖 AI Assistant & Slide-In Drawer
- Global floating AI drawer on every page for instant task planning.
- Dedicated AI Assistant page (`/ai-assistant/`) with bulk project and task creation.

### ⚙️ Settings & Data Portability
- Profile management, theme modes, notifications, data export (JSON/CSV), and database reset utilities.

---

## 🛠 Tech Stack

| Layer       | Technology |
|-------------|------------|
| **Backend** | Python 3.11 + Django 5.2 (SQLite dev DB) |
| **Frontend**| Vanilla HTML5 / CSS3 / JavaScript (No framework overhead) |
| **Fonts**   | Plus Jakarta Sans & Inter (Google Fonts) |
| **Icons**   | Font Awesome 6 |
| **Visuals** | High-performance HTML5 2D Canvas Wave Mesh |
| **Auth**    | DemoAuthMiddleware (Local dev) + External Auth API ready |

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
