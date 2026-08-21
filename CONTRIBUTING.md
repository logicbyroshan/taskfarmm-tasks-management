# 🤝 Contributing to TaskFlixx

Thank you for your interest in contributing to **TaskFlixx**! We love pull requests, feature suggestions, bug reports, and code reviews from the community.

---

## 📜 Table of Contents
1. [Code of Conduct](#code-of-conduct)
2. [How Can I Contribute?](#how-can-i-contribute)
   - [Reporting Bugs](#reporting-bugs)
   - [Suggesting Enhancements](#suggesting-enhancements)
   - [Pull Requests](#pull-requests)
3. [Local Development Setup](#local-development-setup)
4. [Coding & Design Standards](#coding--design-standards)
5. [Git Commit Guidelines](#git-commit-guidelines)

---

## 📜 Code of Conduct
Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md) to keep our community safe, inclusive, and welcoming.

---

## 🛠️ How Can I Contribute?

### 🐛 Reporting Bugs
Before submitting an issue, please search existing issues to avoid duplicates. When opening a bug report, use the [Bug Report Template](.github/ISSUE_TEMPLATE/bug_report.md) and include:
- A clear, descriptive title.
- Step-by-step reproduction instructions.
- Expected vs. actual behavior.
- Browser, OS, and Python/Django versions.
- Screenshots or console logs if applicable.

### 💡 Suggesting Enhancements
We welcome ideas to make TaskFlixx even better! Use the [Feature Request Template](.github/ISSUE_TEMPLATE/feature_request.md) and explain:
- The problem you want to solve.
- Your proposed solution or user workflow.
- Any alternative solutions considered.

### 🚀 Pull Requests (PRs)
1. **Fork the repository** on GitHub.
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/taskflixx-tasks-management.git
   cd taskflixx-tasks-management
   ```
3. **Create a new branch** with a descriptive name:
   ```bash
   git checkout -b feature/kanban-keyboard-shortcuts
   # or
   git checkout -b fix/dropdown-stacking-context
   ```
4. **Make your changes** following the project standards.
5. **Test thoroughly**:
   ```bash
   python manage.py check
   python manage.py test
   ```
6. **Commit your changes** using conventional commit messages.
7. **Push to your fork** and **open a Pull Request** against `main`.

---

## 💻 Local Development Setup

1. **Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Or `venv\Scripts\activate` on Windows
   ```
2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Run Migrations**:
   ```bash
   python manage.py migrate
   ```
4. **Start Development Server**:
   ```bash
   python manage.py runserver
   ```

---

## 🎨 Coding & Design Standards

### 🖤 Pure Pitch-Black OLED Aesthetic
- All container backgrounds, cards, modals, and dropdowns must use **pure black (`#000000`)**.
- Borders use subtle `#27272a` or `#1f2937` dividers.
- Avoid mixed slate/gray muddy backgrounds.

### 🚫 Zero-Vertical-Scrollbars Rule
- The UI is designed to fit modern viewports without vertical page scrollbars.
- Horizontal scrolling is strictly allowed only on the 6-column Kanban board.

### 🐍 Python / Django Guidelines
- Follow **PEP 8** style guidelines.
- Always use `get_object_or_404` for lookup endpoints.
- Keep business logic in `views.py` and `models.py`.
- Always pass `request.user` to queries to ensure strict multi-tenant user isolation.

### ⚡ JavaScript Guidelines
- Write clean, modular ES6+ code in `static/todo/js/script.js`.
- Always include `X-CSRFToken` header for AJAX `POST` requests.
- Use `window.showToast(message, type)` for dynamic user feedback.

---

## 📝 Git Commit Guidelines

We recommend [Conventional Commits](https://www.conventionalcommits.org/):
- `feat: add task due date reminder notification`
- `fix: resolve dropdown z-index clipping on mobile view`
- `docs: update API documentation for export endpoints`
- `style: optimize OLED dark theme border contrast`
- `refactor: clean up unused modal handler functions`

---

Thank you for making TaskFlixx better for everyone! 🚀
