<div align="center">

# ⚡ TaskFlixx

### *Next-Generation Smart Task & Project Management Platform*

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.2+-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![OpenHinglish](https://img.shields.io/badge/OpenHinglish-Integrated-3b82f6?style=for-the-badge)](https://github.com/shankarmishra/openhinglish)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Theme: OLED Black](https://img.shields.io/badge/Theme-Pure_OLED_Black-000000?style=for-the-badge&logo=darkreader&logoColor=white)](#)
[![Aesthetics: Cool Wave](https://img.shields.io/badge/Canvas-Cool_Gradient_Wave-14b8a6?style=for-the-badge)](#)

<br>

<p align="center">
  <b>TaskFlixx</b> is an ultra-fast, visually stunning, OLED pure-black task and project orchestration platform built with <b>Django 5</b>, <b>OpenHinglish</b>, <b>Vanilla Modern CSS</b>, and <b>HTML5 Canvas</b>. Engineered for high productivity, real-time client-side updates, and zero clutter.
</p>

[✨ Live Features](#-key-features) • [🚀 Quick Start](#-quick-start) • [🚢 Deployment Guide](#-production-deployment) • [📡 API Reference](API.md)

</div>

---

## 🌟 Key Features

### ✨ Intelligent Auto-Correct & Spell-Check (OpenHinglish Engine)
- **Multi-Lingual Text Normalization**: Powered by [OpenHinglish](https://github.com/shankarmishra/openhinglish), normalizes shorthand (`intv` ➔ `interview`, `msg` ➔ `message`, `tmrw` ➔ `tomorrow`), typos (`krna` ➔ `karna`, `proejct` ➔ `project`, `taks` ➔ `task`), and transliterated Roman Hindi/Hinglish.
- **Configurable Settings**: Toggle auto-correction ON/OFF in Settings with a live interactive tester.
- **Uncluttered Seamless Experience**: Automatically runs on input blur and Enter key without clunky button labels everywhere.

### 📁 Manage Projects & Agile Kanban Workflows
- **Dedicated Project Workspaces**: Organize tasks by project with custom color accents and workflow templates:
  - ⚡ **Smart Work Management** (4 Lists: *To Do, In Progress, On Hold, Done*)
  - 🚀 **Super Work Management** (6 Lists: *Backlog, To Do, In Progress, On Hold, Done, Canceled*)
- **Direct Card Click-to-Edit**: Click any project card to open a spacious 600px settings modal with template switchers, color palettes, and description.

### 📋 Full-Featured Drag-and-Drop Kanban & Trello-Style Modal
- **Live Drag-and-Drop**: Reorder and move tasks smoothly across columns with HTML5 drag-and-drop.
- **Advanced Trello Task Modal**:
  - **Full-Width Topbar**: Direct project, status, and priority selection with clean close button.
  - **Task Attachments**: Upload PDFs, Word documents, Excel sheets, and images with automatic previews and download links.
  - **Direct Clipboard Paste (`Ctrl + V`)**: Instantly paste screenshots or copied documents directly into descriptions and comments.
  - **Interactive Checklists**: Editable checklist titles, auto-updating progress bar (`0-100%`), and inline item management.
  - **Activity & Comment Stream**: Real-time discussions with author avatars and inline editing.

### ⚡ Instant Client-Side SPA Experience (Zero Page Reloads)
- **Real-Time DOM Updates**: Creating, editing, moving across columns, or deleting tasks occurs instantly in the DOM without full page reloads.
- **Stacked Square Team Avatars**: Modern overlapping avatar stack on the Kanban topbar with instant assignee filtering.

### 🌊 Ambient Dynamic Cool-Gradient Wave Background
- **Interactive 60fps HTML5 Canvas**: Smooth continuous wave crests and troughs with a vivid cool gradient spectrum (Teal, Cyan, Sky Blue, Sapphire, Indigo, Violet) and interactive mouse ripple.

### 🔑 Google Single Sign-On (OAuth 2.0 & GIS)
- **RFC 6749 Compliant OAuth 2.0**: Direct one-click login with Google accounts (`/auth/google/login/` ➔ `/auth/google/callback/`) with state token CSRF protection.
- **Automatic Account Provisioning**: Auto-creates `UserProfile` and starter workspace upon first Google sign-in.
- **Local Developer Testing Mode**: Includes dedicated developer fallback screen for testing OAuth user flows without active cloud credentials.

### 📬 Enterprise Notification & Outbound Email Delivery Queue
- **Asynchronous Delivery Queue**: High-performance database queue (`Notification` model) for task assignments, comments, deadlines, and project invites.
- **Exponential Backoff Retries**: Automatic error recovery (`30s`, `2m`, `8m`, `30m`) for network/SMTP failures.
- **In-App Notification Bell**: Topbar alert hub with unread badge counter, relative timestamps, and one-click read actions.
- **Responsive OLED Email Templates**: 6 pitch-black email templates with glowing sapphire CTAs matching TaskFlixx aesthetics.

### 🤖 Intelligent AI Assistant & Side Drawer
- **ChatGPT-Style AI Workspace**: Interactive AI assistant that suggests comprehensive task breakdowns and one-click creates tasks and structured projects.

---

## 🏗️ Architecture & Tech Stack

```
TaskFlixx/
├── config/             # Django root configuration & WSGI/ASGI handlers
├── todo/               # Core application (models, views, forms, services)
│   ├── autocorrect.py  # OpenHinglish text normalization & spell check pipeline
│   ├── models.py       # Task, TaskAttachment, TaskComment, Category, UserProfile
│   ├── views.py        # Dashboard, Kanban, Projects, Attachments, Comments, AI & Auto-Correct APIs
│   ├── forms.py        # TaskForm, CategoryForm, UserUpdateForm, Preferences
│   └── tests/          # Comprehensive test suite (49+ tests)
├── templates/todo/     # Django HTML5 semantic templates
│   ├── base.html       # Global navigation, cool wave canvas, AI drawer, modals
│   ├── index.html      # Dashboard with live metrics & project toggle
│   ├── kanban.html     # Customizable Kanban board with stacked team avatars
│   ├── manage-projects.html # Manage Projects workspace & card container
│   ├── ai_assistant.html # ChatGPT-style AI Workspace
│   └── settings.html   # Profile, preferences, auto-correct toggle, data export
├── static/todo/        # Pure CSS and JavaScript assets
│   ├── css/            # base.css, style.css, settings.css
│   └── js/script.js    # Canvas wave engine, SPA DOM sync, Trello modal engine, toasts
└── requirements.txt    # Production dependencies including openhinglish
```

- **Backend**: Python 3.11+, Django 5.2+
- **NLP / Normalization**: OpenHinglish (`openhinglish`)
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
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run Migrations & Collect Static Files
```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

### 5. Run the Test Suite
```bash
python manage.py test
```

### 6. Start the Development Server
```bash
python manage.py runserver
```
Navigate to [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

---

## 🧪 Testing & Quality Assurance

TaskFlixx includes a comprehensive automated test suite covering models, views, API endpoints, OpenHinglish autocorrect, and security permissions.

```bash
python manage.py test
```
*Output: `Ran 36 tests in 33s ... OK`*

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
