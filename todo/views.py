"""
todo/views.py

Template-rendering views for the TaskFlixx web application.

This file is intentionally thin — all business logic lives in services.py.
Views here are responsible only for:
  1. Authentication/permission checking
  2. Calling the appropriate service method
  3. Rendering the correct template with the returned context

JSON/AJAX endpoints for the HTMX frontend are kept here (not in the DRF API)
because they use Django's session auth and return task-specific HTML fragments.
External consumers should use the REST API (/api/v1/).
"""

import csv
import json
import logging

# Django core
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.utils.timesince import timesince

# Local models, forms, and services
from .models import Task, Category, UserProfile, TaskComment
from .forms import TaskForm, CategoryForm, UserUpdateForm, UserProfileForm, PasswordUpdateForm
from .services import (
    TaskService, CategoryService, ExportService,
    PreDefinedTaskService, StatsService,
)

logger = logging.getLogger('todo')


# ============================================================
#  HELPERS
# ============================================================

def get_or_create_profile(user):
    """Returns or creates the UserProfile for a user."""
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


def get_accessible_task(user, pk):
    """Returns a task accessible by user (owned, shared project, or assigned)."""
    return get_object_or_404(
        Task.objects.filter(
            Q(user=user) | 
            Q(category__members=user) | 
            Q(category__user=user) | 
            Q(assignees=user)
        ).distinct(),
        pk=pk
    )


# ============================================================
#  PAGE VIEWS
# ============================================================

@login_required
def dashboard(request):
    """Displays the main dashboard for an authenticated user."""
    stats = StatsService.get_stats(request.user)
    recent_tasks = TaskService.get_recent_tasks(request.user)
    recently_completed = TaskService.get_recently_completed(request.user)
    category_stats = CategoryService.get_with_stats(request.user)
    all_projects_progress = CategoryService.get_dashboard_project_progress(request.user)

    context = {
        # Stats (single DB aggregation)
        'total_tasks': stats['total_count'],
        'total_count': stats['total_count'],
        'backlog_count': stats['backlog_count'],
        'to_do_count': stats['to_do_count'],
        'in_progress_count': stats['in_progress_count'],
        'done_count': stats['done_count'],
        'on_hold_count': stats['on_hold_count'],
        'canceled_count': stats['canceled_count'],
        'completion_rate': stats['completion_rate'],
        'overdue_count': stats['overdue_count'],
        'due_today_count': stats['due_today_count'],
        # Lists
        'recent_tasks': recent_tasks,
        'recently_completed': recently_completed,
        'recently_completed_tasks': recently_completed,
        'category_stats': category_stats,
        'projects': category_stats,
        'all_projects_progress': all_projects_progress,
        'active_page': 'dashboard',
    }
    return render(request, 'todo/index.html', context)


@login_required
def manage_tasks(request):
    """
    Displays a grid/list of all tasks with live HTMX search, filtering, and sorting.
    """
    tasks = TaskService.filter_and_sort(
        user=request.user,
        search=request.GET.get('search', '').strip(),
        status=request.GET.get('status', 'all'),
        priority=request.GET.get('priority', 'all'),
        project=request.GET.get('project', 'all'),
        sort=request.GET.get('sort', 'newest'),
    )
    projects = Category.objects.filter(user=request.user)

    context = {
        'tasks': tasks,
        'projects': projects,
        'status_filter': request.GET.get('status', 'all'),
        'priority_filter': request.GET.get('priority', 'all'),
        'project_filter': request.GET.get('project', 'all'),
        'sort_by': request.GET.get('sort', 'newest'),
        'search_query': request.GET.get('search', '').strip(),
        'task_count': tasks.count(),
        'active_page': 'manage_tasks',
    }

    if request.headers.get('HX-Request'):
        return render(request, 'todo/components/task_list_partial.html', context)

    return render(request, 'todo/manage-tasks.html', context)


@login_required
def task_categories(request):
    """Displays all projects/categories for the current user."""
    categories = CategoryService.get_with_stats(request.user)
    form = CategoryForm()
    context = {
        'categories': categories,
        'form': form,
        'active_page': 'task_categories',
    }
    return render(request, 'todo/manage-projects.html', context)


@login_required
def manage_kanban(request):
    """Displays the Kanban board with single-project view."""
    project_id = request.GET.get('project')
    data = TaskService.get_kanban_columns(request.user, project_id)

    context = {
        'all_projects': data['all_projects'],
        'selected_project': data['selected_project'],
        'selected_project_id': data['selected_project_id'],
        'backlog_tasks': data['columns']['backlog'],
        'to_do_tasks': data['columns']['not-started'],
        'in_progress_tasks': data['columns']['in-progress'],
        'done_tasks': data['columns']['completed'],
        'on_hold_tasks': data['columns']['on-hold'],
        'canceled_tasks': data['columns']['canceled'],
        'active_page': 'manage_kanban',
    }
    return render(request, 'todo/kanban.html', context)


@login_required
def settings_page(request):
    """Handles the user settings page — profile, password, preferences, and danger zone."""
    profile = get_or_create_profile(request.user)

    if request.method == 'POST':
        action = request.POST.get('action', 'profile')

        if action == 'profile':
            u_form = UserUpdateForm(request.POST, instance=request.user)
            if u_form.is_valid():
                u_form.save()
                messages.success(request, 'Profile updated successfully!')
                return redirect('settings')
            p_form = UserProfileForm(instance=profile)
            pw_form = PasswordUpdateForm(request.user)

        elif action == 'preferences':
            p_form = UserProfileForm(request.POST, instance=profile)
            if p_form.is_valid():
                p_form.save()
                messages.success(request, 'Preferences saved successfully!')
                return redirect('settings')
            u_form = UserUpdateForm(instance=request.user)
            pw_form = PasswordUpdateForm(request.user)

        elif action == 'password':
            pw_form = PasswordUpdateForm(request.user, request.POST)
            if pw_form.is_valid():
                user = pw_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Password changed successfully!')
                return redirect('settings')
            u_form = UserUpdateForm(instance=request.user)
            p_form = UserProfileForm(instance=profile)

        elif action == 'clear_tasks':
            if request.POST.get('confirm_clear') == 'yes':
                Task.objects.filter(user=request.user).delete()
                messages.success(request, 'All tasks cleared successfully. Projects remain intact.')
            else:
                messages.error(request, 'Confirmation not provided. No tasks were deleted.')
            return redirect('settings')

        elif action in ('clear_all', 'clear_data'):
            if request.POST.get('confirm_clear') == 'yes':
                Task.objects.filter(user=request.user).delete()
                Category.objects.filter(user=request.user).delete()
                messages.success(request, 'All data (tasks and projects) cleared successfully.')
            else:
                messages.error(request, 'Confirmation not provided. No data was deleted.')
            return redirect('settings')

        else:
            u_form = UserUpdateForm(instance=request.user)
            p_form = UserProfileForm(instance=profile)
            pw_form = PasswordUpdateForm(request.user)
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = UserProfileForm(instance=profile)
        pw_form = PasswordUpdateForm(request.user)

    context = {
        'active_page': 'settings',
        'u_form': u_form,
        'p_form': p_form,
        'pw_form': pw_form,
        'profile': profile,
    }
    return render(request, 'todo/settings.html', context)


@login_required
def logout_view(request):
    """Logs out the user and redirects to the login page."""
    auth_logout(request)
    return redirect('dashboard')


@login_required
def ai_assistant_page(request):
    """Renders the AI Assistant page."""
    projects = CategoryService.get_with_stats(request.user)
    recent_tasks = TaskService.get_recent_tasks(request.user, limit=10)
    context = {
        'active_page': 'ai_assistant',
        'projects': projects,
        'recent_tasks': recent_tasks,
    }
    return render(request, 'todo/ai_assistant.html', context)


# ============================================================
#  TASK CRUD (HTMX / AJAX — session auth)
# ============================================================

@login_required
def task_detail(request, pk):
    """Returns task detail as JSON for the Trello modal."""
    task = get_object_or_404(Task, pk=pk, user=request.user)

    is_ajax = (
        request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        or request.GET.get('format') == 'json'
    )
    if is_ajax:
        data = TaskService.get_task_detail_data(task)
        return JsonResponse({'success': True, 'task': data})
    return render(request, 'todo/task_detail.html', {'task': task})


@login_required
def task_create(request):
    """Creates a task via AJAX POST or JSON payload."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'POST required.'}, status=405)

    post_data = request.POST
    if request.content_type and 'application/json' in request.content_type:
        try:
            post_data = json.loads(request.body)
        except Exception:
            post_data = request.POST

    form = TaskForm(post_data, user=request.user)
    if form.is_valid():
        task = form.save(commit=False)
        task.user = request.user
        task.save()
        return JsonResponse({
            'success': True,
            'message': 'Task created successfully!',
            'task': {
                'id': task.id,
                'title': task.title,
                'status': task.status,
                'priority': task.priority,
            }
        })
    return JsonResponse({'success': False, 'errors': form.errors}, status=400)


@login_required
def task_update(request, pk):
    """
    Updates a task via JSON body (Trello modal) or form POST (kanban drag-drop).
    GET: returns task JSON for Trello modal population.
    POST (JSON body): partial update for live editing.
    POST (form): quick status update or full form update.
    """
    task = get_accessible_task(request.user, pk)

    if request.method == 'GET':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            data = TaskService.get_task_detail_data(task)
            return JsonResponse({'success': True, 'task': data})
        return JsonResponse({'success': False, 'message': 'Ajax GET only.'}, status=400)

    if request.method == 'POST':
        # JSON body from Trello modal live edits
        if request.content_type and 'application/json' in request.content_type:
            try:
                data = json.loads(request.body)
                task = TaskService.partial_update_task(task, data, request.user)
                return JsonResponse({'success': True, 'message': 'Task updated!'})
            except Exception as e:
                logger.warning('Task update failed: pk=%d error=%s', pk, e)
                return JsonResponse({'success': False, 'error': str(e)}, status=400)

        # Quick status update (kanban drag-drop)
        new_status = request.POST.get('status')
        if new_status and new_status in Task.Status.values and 'title' not in request.POST:
            task.status = new_status
            task.save(update_fields=['status', 'updated_at'])
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Status updated!'})
            return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

        # Full form update
        form = TaskForm(request.POST, instance=task, user=request.user)
        if form.is_valid():
            form.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Task updated!'})
            return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
        return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

    return JsonResponse({'success': False, 'message': 'Invalid method.'}, status=405)


@login_required
@require_http_methods(['POST'])
def task_add_comment(request, pk):
    """Adds a new activity comment to a task."""
    task = get_accessible_task(request.user, pk)
    try:
        data = json.loads(request.body)
        content = data.get('content', '').strip()
    except (json.JSONDecodeError, AttributeError):
        content = request.POST.get('content', '').strip()

    try:
        comment = TaskService.add_comment(task, request.user, content)
    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

    return JsonResponse({
        'success': True,
        'comment': {
            'id': comment.id,
            'user': comment.user.username,
            'content': comment.content,
            'created_at': comment.created_at.strftime('%d %b %Y, %H:%M'),
            'time_ago': 'Just now',
        }
    })


@login_required
@require_http_methods(['POST', 'DELETE'])
def task_comment_delete(request, pk):
    """Deletes a task comment (comment author or task owner)."""
    comment = get_object_or_404(
        TaskComment.objects.filter(
            Q(user=request.user) | 
            Q(task__user=request.user) | 
            Q(task__category__user=request.user)
        ).distinct(),
        pk=pk
    )
    comment.delete()
    return JsonResponse({'success': True, 'message': 'Comment deleted.'})


@login_required
@require_http_methods(['POST'])
def task_update_checklist(request, pk):
    """Replaces task checklist."""
    task = get_accessible_task(request.user, pk)
    try:
        data = json.loads(request.body)
        checklist = data.get('checklist', [])
    except (json.JSONDecodeError, AttributeError):
        checklist = []
    TaskService.update_checklist(task, checklist)
    return JsonResponse({'success': True, 'message': 'Checklist updated!'})


@login_required
@require_http_methods(['POST'])
def task_toggle_status(request, pk):
    """Toggles task status between DONE and TO_DO."""
    task = get_accessible_task(request.user, pk)
    TaskService.toggle_status(task)
    if request.headers.get('HX-Request'):
        return render(request, 'todo/components/task_card.html', {'task': task})

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'task': {
                'id': task.id,
                'status': task.status,
                'is_completed': task.status == Task.Status.DONE,
            }
        })
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))


@login_required
def task_delete(request, pk):
    """Deletes a task."""
    task = get_object_or_404(
        Task.objects.filter(Q(user=request.user) | Q(category__user=request.user)).distinct(),
        pk=pk
    )
    if request.method == 'POST':
        title = task.title
        task.delete()
        if request.headers.get('HX-Request'):
            return HttpResponse('', status=200)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'Task "{title}" deleted.'})
        messages.success(request, f'Task "{title}" deleted.')
        return redirect('manage_tasks')
    return render(request, 'todo/confirm_delete.html', {'object': task, 'type': 'task'})


# ============================================================
#  CATEGORY / PROJECT CRUD & SHARING
# ============================================================

@login_required
def category_create(request):
    """Creates a new project/category."""
    if request.method == 'POST':
        post_data = request.POST
        if request.content_type and 'application/json' in request.content_type:
            try:
                post_data = json.loads(request.body)
            except Exception:
                post_data = request.POST

        form = CategoryForm(post_data)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = request.user
            category.save()
            category.ensure_share_token()
            is_ajax_or_json = (
                request.headers.get('X-Requested-With') == 'XMLHttpRequest'
                or (request.content_type and 'application/json' in request.content_type)
            )
            if is_ajax_or_json:
                return JsonResponse({
                    'success': True,
                    'message': f'Project "{category.name}" created!',
                    'category': {
                        'id': category.id,
                        'name': category.name,
                        'color': category.color,
                        'share_token': category.share_token,
                    }
                })
            messages.success(request, f'Project "{category.name}" created.')
        else:
            is_ajax_or_json = (
                request.headers.get('X-Requested-With') == 'XMLHttpRequest'
                or (request.content_type and 'application/json' in request.content_type)
            )
            if is_ajax_or_json:
                return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    return redirect('task_categories')


@login_required
def category_update(request, pk):
    """Updates an existing category."""
    category = get_object_or_404(Category, pk=pk, user=request.user)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': f'Project "{category.name}" updated.'})
            messages.success(request, f'Project "{category.name}" updated.')
    return redirect('task_categories')


@login_required
def category_delete(request, pk):
    """Deletes a category."""
    category = get_object_or_404(Category, pk=pk, user=request.user)
    if request.method == 'POST':
        name = category.name
        category.delete()
        if request.headers.get('HX-Request'):
            return HttpResponse('', status=200)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'Project "{name}" deleted.'})
        messages.success(request, f'Project "{name}" deleted.')
        return redirect('task_categories')
    return render(request, 'todo/confirm_delete.html', {'object': category, 'type': 'project'})


@login_required
def project_share(request, pk):
    """
    GET: Returns project sharing info (share URL, members, is_owner).
    POST: Adds or removes project members by username/email.
    """
    from django.contrib.auth.models import User as AuthUser
    category = get_object_or_404(
        Category.objects.filter(Q(user=request.user) | Q(members=request.user)).distinct(),
        pk=pk
    )
    token = category.ensure_share_token()
    share_url = request.build_absolute_uri(f"/project/join/{token}/")
    is_owner = (category.user_id == request.user.id)

    if request.method == 'POST':
        if not is_owner:
            return JsonResponse({'success': False, 'message': 'Only project owner can manage members.'}, status=403)
        try:
            data = json.loads(request.body)
        except Exception:
            data = request.POST

        action = data.get('action')
        if action == 'add_member':
            query = data.get('username', '').strip()
            user_to_add = AuthUser.objects.filter(Q(username__iexact=query) | Q(email__iexact=query)).first()
            if not user_to_add:
                return JsonResponse({'success': False, 'message': f'User "{query}" not found.'}, status=404)
            if user_to_add.id == category.user_id:
                return JsonResponse({'success': False, 'message': 'User is already the project owner.'}, status=400)
            category.members.add(user_to_add)
            return JsonResponse({
                'success': True,
                'message': f'{user_to_add.username} added to project!',
                'member': {
                    'id': user_to_add.id,
                    'username': user_to_add.username,
                    'initials': user_to_add.username[:2].upper()
                }
            })
        elif action == 'remove_member':
            member_id = data.get('member_id')
            user_to_remove = AuthUser.objects.filter(pk=member_id).first()
            if user_to_remove:
                category.members.remove(user_to_remove)
                return JsonResponse({'success': True, 'message': f'{user_to_remove.username} removed from project.'})
            return JsonResponse({'success': False, 'message': 'Member not found.'}, status=404)

    members = [
        {
            'id': m.id,
            'username': m.username,
            'initials': m.username[:2].upper(),
            'is_owner': False
        }
        for m in category.members.all()
    ]
    owner_info = {
        'id': category.user.id,
        'username': category.user.username,
        'initials': category.user.username[:2].upper(),
        'is_owner': True
    }

    return JsonResponse({
        'success': True,
        'project_id': category.id,
        'project_name': category.name,
        'share_url': share_url,
        'is_owner': is_owner,
        'owner': owner_info,
        'members': members
    })


@login_required
def project_join(request, token):
    """
    Allows a user with an invite/share link to join a shared project.
    """
    category = get_object_or_404(Category, share_token=token)
    if category.user != request.user and not category.members.filter(pk=request.user.pk).exists():
        category.members.add(request.user)
        messages.success(request, f'🎉 You have joined project "{category.name}"!')
    else:
        messages.info(request, f'You are currently viewing project "{category.name}".')

    return redirect(f"/kanban/?project={category.id}")


# ============================================================
#  PREDEFINED TASK TEMPLATES
# ============================================================

@login_required
def predefined_tasks_api(request):
    """Returns predefined task templates filtered by category."""
    from .models import PreDefinedTask
    category = request.GET.get('category', 'all')
    tasks_qs = PreDefinedTaskService.get_templates(category)

    tasks_data = [
        {
            'id': t.id,
            'title': t.title,
            'description': t.description or '',
            'category': t.category,
            'category_display': t.get_category_display(),
            'suggested_priority': t.suggested_priority,
            'icon': t.icon,
        }
        for t in tasks_qs
    ]
    categories = [
        {'value': c[0], 'label': c[1]}
        for c in PreDefinedTask.Category.choices
    ]
    return JsonResponse({'success': True, 'tasks': tasks_data, 'categories': categories})


@login_required
def add_predefined_task(request):
    """Adds a predefined task template to the user's task pool."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
    try:
        data = json.loads(request.body)
        task = PreDefinedTaskService.add_to_user_tasks(
            user=request.user,
            predefined_id=data.get('predefined_id'),
            category_id=data.get('category_id'),
        )
        return JsonResponse({
            'success': True,
            'message': f'Task "{task.title}" added!',
            'task_id': task.id,
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ============================================================
#  STATS & EXPORT (legacy session-auth endpoints, kept for HTMX widgets)
# ============================================================

@login_required
def stats_api(request):
    """Returns aggregated stats. Also available at /api/v1/stats/ with JWT auth."""
    stats = StatsService.get_stats(request.user)
    return JsonResponse({'success': True, 'stats': stats})


@login_required
def tasks_export_api(request):
    """Exports all tasks as JSON or CSV."""
    fmt = request.GET.get('format', 'json').lower()
    if fmt == 'csv':
        header, rows = ExportService.tasks_to_csv_rows(request.user)
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="taskflixx_export.csv"'
        writer = csv.writer(response)
        writer.writerow(header)
        writer.writerows(rows)
        return response

    data = ExportService.tasks_to_dict_list(request.user)
    return JsonResponse({'success': True, 'tasks': data, 'total': len(data)})


# ============================================================
#  AI ASSISTANT ENDPOINTS
# ============================================================

@login_required
def api_ai_suggest(request):
    """
    AI Task & Project Assistant endpoint.
    Generates a suggested action plan from a user prompt.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST method required'}, status=405)

    try:
        data = json.loads(request.body)
        prompt = data.get('prompt', '').strip()

        if not prompt:
            return JsonResponse({'success': False, 'error': 'Empty prompt'}, status=400)

        prompt_lower = prompt.lower()

        if any(kw in prompt_lower for kw in ['website', 'launch', 'app']):
            title = "Launch Strategy & Production Readiness"
            suggestion = (
                "1. Finalize DNS records & SSL certificate configuration.\n"
                "2. Run cross-browser compatibility and lighthouse performance audit.\n"
                "3. Execute production database migrations.\n"
                "4. Verify exception logging & error reporting setup.\n"
                "5. Set up monitoring & uptime alerts."
            )
        elif any(kw in prompt_lower for kw in ['subtask', 'breakdown', 'feature']):
            title = f"Task Breakdown: {prompt[:30]}..."
            suggestion = (
                "Recommended Subtasks:\n"
                "- API Endpoint setup with request validation\n"
                "- Database schema migrations & indexing\n"
                "- Frontend UI component integration\n"
                "- Write unit and integration tests\n"
                "- Code review and deployment"
            )
        elif any(kw in prompt_lower for kw in ['marketing', 'campaign']):
            title = "Marketing Campaign Execution Plan"
            suggestion = (
                "1. Define target audience and campaign objectives.\n"
                "2. Create content calendar and asset list.\n"
                "3. Set up ad creatives and A/B tests.\n"
                "4. Launch campaign and monitor metrics.\n"
                "5. Analyze results and optimize."
            )
        else:
            title = f"AI Workflow Task: {prompt[:35]}"
            suggestion = (
                f"AI Action Plan for '{prompt}':\n"
                "- Priority: High\n"
                "- Recommended Timeline: Complete within 48 hours\n"
                "- Suggested Action: Create task, assign project category, and review progress.\n"
                "- Next Step: Break into subtasks if the scope is large."
            )

        return JsonResponse({
            'success': True,
            'title': title,
            'suggestion': suggestion,
            'description': suggestion,
            'prompt': prompt,
        })
    except (json.JSONDecodeError, Exception) as e:
        logger.error('AI suggest error: %s', e)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def ai_create_task(request):
    """Creates a task from AI suggestion data."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
    try:
        data = json.loads(request.body)
        title = data.get('title', '').strip()
        if not title:
            return JsonResponse({'success': False, 'error': 'Title is required'}, status=400)

        category = None
        if data.get('category_id'):
            category = Category.objects.filter(pk=data['category_id'], user=request.user).first()

        task = Task.objects.create(
            user=request.user,
            title=title,
            description=data.get('description', '').strip(),
            priority=data.get('priority', 'moderate') if data.get('priority') in Task.Priority.values else 'moderate',
            status=data.get('status', 'not-started') if data.get('status') in Task.Status.values else 'not-started',
            category=category,
        )
        return JsonResponse({
            'success': True,
            'message': f'Task "{task.title}" created!',
            'task_id': task.id,
            'task_title': task.title,
        })
    except Exception as e:
        logger.error('AI create task error: %s', e)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def ai_create_project(request):
    """Creates a project with optional tasks from AI suggestion data."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        if not name:
            return JsonResponse({'success': False, 'error': 'Project name is required'}, status=400)

        project = CategoryService.create_category(
            user=request.user,
            name=name,
            color=data.get('color', '#3b82f6'),
            description=data.get('description', ''),
        )

        created_tasks = []
        for task_data in data.get('tasks', [])[:10]:  # Max 10 tasks
            task_title = task_data if isinstance(task_data, str) else task_data.get('title', '')
            task_priority = 'moderate' if isinstance(task_data, str) else task_data.get('priority', 'moderate')
            if task_title:
                t = Task.objects.create(
                    user=request.user,
                    title=task_title,
                    priority=task_priority,
                    status='not-started',
                    category=project,
                )
                created_tasks.append({'id': t.id, 'title': t.title})

        return JsonResponse({
            'success': True,
            'message': f'Project "{project.name}" created with {len(created_tasks)} tasks!',
            'project_id': project.id,
            'project_name': project.name,
            'tasks_created': created_tasks,
        })
    except Exception as e:
        logger.error('AI create project error: %s', e)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)