# 🏛️ TaskFlixx Codebase Architecture & Structure

This document provides a detailed structural breakdown of the **TaskFlixx** repository.

---

## 📁 Repository Overview

```
TaskFlixx/
├── .github/                         # GitHub community templates
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md           # Bug report template
│   │   └── feature_request.md      # Feature proposal template
│   └── pull_request_template.md     # PR submission checklist
├── config/                          # Django core project configuration
│   ├── __init__.py
│   ├── asgi.py                      # ASGI entry point for async servers
│   ├── settings.py                  # Environment-aware Django settings & WhiteNoise
│   ├── urls.py                      # Global URL router (admin, /api/v1/, web app)
│   └── wsgi.py                      # Production WSGI entry point
├── static/                          # Static UI assets
│   └── todo/
│       ├── css/
│       │   ├── base.css             # Root variables, reset, zero-scrollbar engine
│       │   ├── style.css            # Dark mode tokens, headers, dropdown stacking
│       │   ├── my-tasks.css         # Task card styling & filter layout
│       │   ├── task-categories.css  # Project board cards & progress metrics
│       │   └── settings.css         # Profile & preferences forms
│       ├── js/
│       │   ├── script.js            # 60fps Wave canvas, modals, search, toasts
│       │   └── sw.js                # Service worker for offline caching
│       └── images/
│           └── logo.png             # Official TaskFlixx brand mark
├── templates/                       # Semantic HTML5 Django Templates
│   └── todo/
│       ├── base.html                # Master layout, navbar, ambient canvas, drawer
│       ├── index.html               # Main dashboard with live status grid & metrics
│       ├── kanban.html              # 6-column drag-and-drop Kanban board
│       ├── manage-tasks.html        # All tasks list, search, and template modal
│       ├── manage-projects.html     # Project management and modals
│       ├── ai_assistant.html        # ChatGPT-style AI Workspace
│       ├── settings.html            # Profile, notification switches, JSON/CSV export
│       ├── auth/                    # Dedicated OLED login, register, and Google SSO setup
│       └── components/              # Modular template components & modals
├── templates/emails/                # Responsive OLED Pitch-Black HTML Email Templates
│   ├── base_email.html              # Master layout with glowing CTA button
│   ├── task_assigned.html           # Task assignment alert
│   ├── task_comment.html            # Comment quote box
│   ├── task_due_soon.html           # Deadline reminder
│   ├── task_completed.html          # Task completed confirmation
│   ├── project_shared.html          # Project invite
│   └── welcome.html                 # Welcome onboarding guide
├── todo/                            # Core Django Application
│   ├── admin.py                     # Django admin model registrations
│   ├── apps.py                      # Application configuration
│   ├── autocorrect.py               # OpenHinglish multi-lingual spell correction pipeline
│   ├── context_processors.py        # Global template context injectors (forms, notifications)
│   ├── forms.py                     # ModelForms for Tasks, Projects, and Users
│   ├── google_auth.py               # RFC 6749 Google OAuth 2.0 & GIS handler
│   ├── middleware.py                # Authentication and demo middleware
│   ├── models.py                    # Task, TaskAttachment, TaskComment, Category, Notification, UserProfile
│   ├── notifications.py             # Enterprise Notification & Exponential Backoff Queue
│   ├── services.py                  # Domain business logic & data aggregation services
│   ├── serializers.py               # Django REST Framework serializers
│   ├── api_auth.py                  # JWT session bridge & token verification
│   ├── urls.py                      # Internal session/AJAX routes
│   ├── api/                         # REST API v1 Package (DRF ViewSets & Views)
│   ├── management/commands/         # Management CLI tools (process_notifications)
│   └── tests/                       # Comprehensive test suite (63 tests)
│       ├── test_models.py           # Model tests
│       ├── test_services.py         # Service layer tests
│       ├── test_views.py            # View & HTMX tests
│       └── test_api.py              # REST API v1 & JWT tests
├── .env.example                     # Environment variable blueprint
├── .gitignore                       # Git ignore list
├── API.md                           # Complete REST API v1 & AJAX reference
├── CODE_OF_CONDUCT.md               # Contributor Covenant Code of Conduct
├── CONTRIBUTING.md                  # Contribution and Pull Request workflow
├── LICENSE                          # MIT Open Source License
├── Procfile                         # Cloud deployment process file (Gunicorn)
├── README.md                        # Master project documentation
├── requirements.txt                 # Clean production dependencies
├── SECURITY.md                      # Security vulnerability disclosure policy
└── SETUP.md                         # Deployment and installation guide
```
