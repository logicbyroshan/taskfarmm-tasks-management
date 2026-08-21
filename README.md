<div align="center">

# ⚡ TaskFlixx

### *Next-Generation Smart Task & Project Management Platform*

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.2+-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=for-the-badge)](CONTRIBUTING.md)
[![Theme: OLED Black](https://img.shields.io/badge/Theme-Pure_OLED_Black-000000?style=for-the-badge&logo=darkreader&logoColor=white)](#)
[![Aesthetics: 60FPS Waves](https://img.shields.io/badge/Canvas-60FPS_Ambient_Waves-6366f1?style=for-the-badge)](#)

<br>

<p align="center">
  <b>TaskFlixx</b> is an ultra-fast, visually stunning, OLED pure-black task and project orchestration platform built with <b>Django 5</b>, <b>Vanilla Modern CSS</b>, and <b>HTML5 Canvas</b>. Engineered for high productivity, real-time feedback, and zero clutter.
</p>

[✨ Live Features](#-key-features) • [🚀 Quick Start](#-quick-start) • [🚢 Deployment Guide](#-production-deployment) • [📡 API Reference](API.md) • [🤝 Contributing](CONTRIBUTING.md)

</div>

---

## 🌟 Key Features

### 🌊 Ambient Dynamic Wave Background
- **Interactive 60fps HTML5 Canvas**: Smooth continuous wave crests and troughs rippling across an OLED matrix with cursor wave dynamics.

### 🖤 Pure Pitch-Black OLED Aesthetic
- **True `#000000` Dark Theme**: Curated high-contrast interface designed for OLED screens, featuring crisp borders (`#27272a`), neon accents, and zero slate/gray muddiness.

### 📋 6-Column Drag-and-Drop Kanban Board
- **Live Visual Workflow**: Seamless HTML5 drag-and-drop across `Backlog`, `To Do`, `In Progress`, `Done`, `On Hold`, and `Canceled`.
- **Dynamic Counters**: Instant numeric badge updates, auto-strike-through on completion, and project switcher filter.

### 🤖 Intelligent AI Assistant & Side Drawer
- **ChatGPT-Style AI Workspace**: Interactive AI assistant that suggests comprehensive task breakdowns and one-click creates tasks and structured projects.
- **Global Drawer Access**: Summon the AI copilot from any page with persistent history in `localStorage`.

### ⚡ Comprehensive Task Management & Filter Engine
- **Multi-Parameter Filtering**: Filter by Status, Priority, Project, and Sort Order with instant live counts.
- **Global Navbar Search**: Deep case-insensitive search across task titles and descriptions.
- **Template Library**: 39+ pre-defined task templates across 8 domains (Website Launch, Dev, Marketing, Design, Operations, Finance, HR, General).

### 📦 Complete Data Export
- **One-Click Export**: Export full user task and project data into formatted **JSON** or **CSV** spreadsheets.

### 🚫 Global Zero-Vertical-Scrollbar Architecture
- **Clean Viewport Layout**: Optimized fixed viewports with zero vertical scrollbars; horizontal panning is strictly reserved for the 6-column Kanban board.

---

## 🏗️ Architecture & Tech Stack

```
TaskFlixx/
├── config/             # Django root configuration & WSGI/ASGI handlers
├── todo/               # Core application (models, views, forms, context processors)
│   ├── models.py       # Task, Category, PreDefinedTask, UserProfile
│   ├── views.py        # Dashboard, Kanban, All Tasks, Projects, AI & Export APIs
│   └── forms.py        # TaskForm, CategoryForm, UserUpdateForm, Preferences
├── templates/todo/     # Django HTML5 semantic templates
│   ├── base.html       # Global navigation, ambient canvas, AI drawer, modals
│   ├── index.html      # Dashboard with live metrics & project toggle
│   ├── kanban.html     # 6-Column drag-and-drop Kanban workflow
│   ├── manage-tasks.html # All Tasks grid, search, and template library
│   ├── manage-projects.html # Project cards & modal management
│   ├── ai_assistant.html # ChatGPT-style AI Workspace
│   └── settings.html   # Profile, preferences, and data export
├── static/todo/        # Pure CSS and JavaScript assets
│   ├── css/            # base.css, style.css, my-tasks.css, settings.css
│   └── js/script.js    # Canvas engine, modal handlers, global search, toasts
└── requirements.txt    # Production dependencies
```

- **Backend**: Python 3.11+, Django 5.2+
- **Frontend**: Vanilla Modern CSS (No Tailwind dependency), HTML5 Canvas, ES6+ JavaScript
- **Database**: SQLite (Development) / PostgreSQL / MySQL (Production via `DATABASE_URL`)
- **Static Asset Serving**: WhiteNoise with compressed manifest caching
- **Production Server**: Gunicorn WSGI

---

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/logicbyroshan/taskflixx-tasks-management.git
cd taskflixx-tasks-management
```

### 2. Create and Activate a Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy the example environment file and customize as needed:
```bash
cp .env.example .env
```

### 5. Apply Database Migrations
```bash
python manage.py migrate
```

### 6. Create Superuser (Optional)
```bash
python manage.py createsuperuser
```

### 7. Run Development Server
```bash
python manage.py runserver
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser!

---

## 🚢 Production Deployment

TaskFlixx is pre-configured with **WhiteNoise** and **Gunicorn** for instant cloud deployment.

### Deploy on Render / Railway / Heroku

1. **Set Environment Variables in your hosting dashboard**:
   - `SECRET_KEY`: A strong random string (e.g. 50+ characters).
   - `DEBUG`: `False`
   - `ALLOWED_HOSTS`: `your-app-name.onrender.com,yourdomain.com`
   - `DATABASE_URL`: `postgres://user:password@host:5432/dbname` (Optional, defaults to SQLite)
2. **Build Command**:
   ```bash
   pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput
   ```
3. **Start Command**:
   ```bash
   gunicorn config.wsgi --log-file -
   ```

### Deploy with Docker or Linux VPS (Systemd + Nginx)
For detailed step-by-step instructions on deploying via Ubuntu VPS, Nginx reverse proxy, SSL certificates, and Gunicorn systemd service, see [SETUP.md](SETUP.md).

---

## 🔑 Environment Variables Reference

| Variable | Required | Default | Description |
| :--- | :---: | :---: | :--- |
| `SECRET_KEY` | **Yes (Prod)** | *Insecure dev key* | Django cryptographic secret key |
| `DEBUG` | No | `True` | Debug mode (`True`/`False`) |
| `ALLOWED_HOSTS` | **Yes (Prod)** | `*` | Comma-separated allowed hostnames/domains |
| `DATABASE_URL` | No | `sqlite:///db.sqlite3` | PostgreSQL/MySQL connection string |
| `EMAIL_BACKEND` | No | `console.EmailBackend` | Email backend class for alerts |
| `EMAIL_HOST` | No | `smtp.gmail.com` | SMTP host for email delivery |
| `EMAIL_PORT` | No | `587` | SMTP port |
| `EMAIL_HOST_USER` | No | `""` | SMTP username/email |
| `EMAIL_HOST_PASSWORD`| No | `""` | SMTP password / App Password |

---

## 📡 API Endpoints

TaskFlixx provides robust internal REST and AJAX endpoints. Full documentation available in [API.md](API.md).

- `GET /api/stats/` — Real-time task metrics and completion rate.
- `GET /api/export/tasks/?format=json|csv` — Full user task and project export.
- `GET /api/predefined-tasks/` — Template library items by category.
- `POST /api/predefined-tasks/add/` — Add template to active tasks.
- `POST /api/ai/suggest/` — AI workflow planner.
- `POST /api/ai/create-task/` — Instant task creation via AI.
- `POST /api/ai/create-project/` — Instant project + subtask generation via AI.

---

## 🤝 Contributing

We welcome contributions from developers worldwide! Whether fixing a bug, adding a new feature, or polishing the UI:

1. **Fork the Repository** on GitHub.
2. **Create a Feature Branch** (`git checkout -b feature/amazing-feature`).
3. **Commit your Changes** (`git commit -m 'feat: add amazing feature'`).
4. **Push to the Branch** (`git push origin feature/amazing-feature`).
5. **Open a Pull Request**!

Please check [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for full guidelines.

---

## 📄 License

Distributed under the **MIT License**. See [LICENSE](LICENSE) for more information.

---

<div align="center">
  <b>Built with ❤️ by <a href="https://github.com/logicbyroshan">Roshan Damor</a> & the Open Source Community</b>
</div>
