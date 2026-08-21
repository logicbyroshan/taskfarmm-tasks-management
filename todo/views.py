# ----------------- Django Core Imports -----------------
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

# ----------------- Django Contrib Imports -----------------
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

# ----------------- Database and Querying Imports -----------------
from django.db.models import Count, Q
from django.utils import timezone
import json

# ----------------- Local Application Imports -----------------
from .models import Task, Category, UserProfile, PreDefinedTask
from .forms import TaskForm, CategoryForm, UserUpdateForm, UserProfileForm, PasswordUpdateForm


# ==============================================================================
#  HELPER: Get or create UserProfile
# ==============================================================================

def get_or_create_profile(user):
    profile, created = UserProfile.objects.get_or_create(user=user)
    return profile


# ==============================================================================
#  CORE PAGE VIEWS
# ==============================================================================

@login_required
def dashboard(request):
    """
    Displays the main dashboard for an authenticated user.
    """
    tasks = Task.objects.filter(user=request.user)

    # Calculate counts for all 6 task statuses
    backlog_count = tasks.filter(status='backlog').count()
    to_do_count = tasks.filter(status='not-started').count()
    in_progress_count = tasks.filter(status='in-progress').count()
    done_count = tasks.filter(status='completed').count()
    on_hold_count = tasks.filter(status='on-hold').count()
    canceled_count = tasks.filter(status='canceled').count()
    total_count = tasks.count()

    # Completion rate
    completion_rate = int((done_count / total_count) * 100) if total_count > 0 else 0

    # Get the 5 most recent non-completed tasks
    recent_tasks = tasks.exclude(status='completed').order_by('-created_at')[:5]

    # Get the 3 most recently completed tasks
    recently_completed_tasks = tasks.filter(status='completed').order_by('-completed_at')[:3]

    # Overdue tasks (due_date < today and not completed)
    today = timezone.now().date()
    overdue_count = tasks.filter(
        due_date__lt=today
    ).exclude(status__in=['completed', 'canceled']).count()

    # Tasks due today
    due_today_count = tasks.filter(
        due_date=today
    ).exclude(status__in=['completed', 'canceled']).count()

    # Projects overview with progress data
    projects = Category.objects.filter(user=request.user).annotate(
        task_count=Count('tasks'),
        completed_count=Count('tasks', filter=Q(tasks__status='completed'))
    )[:4]

    # Build project_progress list for the progress dropdown in the dashboard
    all_projects_progress = []
    all_projects_qs = Category.objects.filter(user=request.user).annotate(
        task_count=Count('tasks'),
        completed_count=Count('tasks', filter=Q(tasks__status='completed'))
    )
    for proj in all_projects_qs:
        prog = int((proj.completed_count / proj.task_count) * 100) if proj.task_count > 0 else 0
        all_projects_progress.append({
            'name': proj.name,
            'color': proj.color,
            'task_count': proj.task_count,
            'completed_count': proj.completed_count,
            'progress': prog,
        })

    context = {
        'backlog_count': backlog_count,
        'to_do_count': to_do_count,
        'in_progress_count': in_progress_count,
        'done_count': done_count,
        'on_hold_count': on_hold_count,
        'canceled_count': canceled_count,
        'total_count': total_count,
        'completion_rate': completion_rate,
        'overdue_count': overdue_count,
        'due_today_count': due_today_count,
        'recent_tasks': recent_tasks,
        'recently_completed_tasks': recently_completed_tasks,
        'projects': projects,
        'all_projects_progress': all_projects_progress,
        'active_page': 'dashboard',
    }
    return render(request, 'todo/index.html', context)


@login_required
def manage_tasks(request):
    """
    Displays a grid/list of ALL tasks belonging to the current user (Unorganized view).
    Supports search, filtering and sorting via GET params.
    """
    tasks = Task.objects.filter(user=request.user)

    # Search Query
    search_query = request.GET.get('search', '').strip()
    if search_query:
        tasks = tasks.filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query)
        )

    # Filtering
    status_filter = request.GET.get('status', 'all')
    priority_filter = request.GET.get('priority', 'all')
    project_filter = request.GET.get('project', 'all')
    sort_by = request.GET.get('sort', 'newest')

    if status_filter != 'all':
        tasks = tasks.filter(status=status_filter)
    if priority_filter != 'all':
        tasks = tasks.filter(priority=priority_filter)
    if project_filter != 'all':
        if project_filter == 'none':
            tasks = tasks.filter(category__isnull=True)
        else:
            tasks = tasks.filter(category_id=project_filter)

    # Sorting
    sort_map = {
        'newest': '-created_at',
        'oldest': 'created_at',
        'due_date': 'due_date',
        'priority': 'priority',
        'title': 'title',
    }
    tasks = tasks.order_by(sort_map.get(sort_by, '-created_at'))

    projects = Category.objects.filter(user=request.user)

    context = {
        'tasks': tasks,
        'projects': projects,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'project_filter': project_filter,
        'sort_by': sort_by,
        'search_query': search_query,
        'task_count': tasks.count(),
        'active_page': 'manage_tasks',
    }
    return render(request, 'todo/manage-tasks.html', context)


@login_required
def my_tasks(request):
    """
    Alias for manage_tasks (Unorganized task pool).
    """
    return manage_tasks(request)


@login_required
def task_categories(request):
    """
    Displays all projects created by the user (Manage Projects view).
    """
    categories = Category.objects.filter(user=request.user).annotate(
        task_count=Count('tasks'),
        completed_count=Count('tasks', filter=Q(tasks__status='completed'))
    )

    for category in categories:
        if category.task_count > 0:
            category.progress = int((category.completed_count / category.task_count) * 100)
        else:
            category.progress = 0

    form = CategoryForm()
    context = {
        'categories': categories,
        'form': form,
        'active_page': 'task_categories',
    }
    return render(request, 'todo/manage-projects.html', context)


@login_required
def manage_kanban(request):
    """
    Displays a Kanban board (Organized task view) with 6 columns.
    Supports filtering by Project.
    """
    all_projects = Category.objects.filter(user=request.user).annotate(
        task_count=Count('tasks')
    )

    tasks = Task.objects.filter(user=request.user)

    project_id = request.GET.get('project')
    selected_project = None
    if project_id:
        try:
            selected_project = all_projects.get(pk=project_id)
            tasks = tasks.filter(category=selected_project)
        except (Category.DoesNotExist, ValueError):
            project_id = None

    backlog_tasks = tasks.filter(status='backlog').order_by('-created_at')
    to_do_tasks = tasks.filter(status='not-started').order_by('-created_at')
    in_progress_tasks = tasks.filter(status='in-progress').order_by('-created_at')
    done_tasks = tasks.filter(status='completed').order_by('-created_at')
    on_hold_tasks = tasks.filter(status='on-hold').order_by('-created_at')
    canceled_tasks = tasks.filter(status='canceled').order_by('-created_at')

    context = {
        'all_projects': all_projects,
        'selected_project': selected_project,
        'selected_project_id': int(project_id) if project_id else None,
        'backlog_tasks': backlog_tasks,
        'to_do_tasks': to_do_tasks,
        'in_progress_tasks': in_progress_tasks,
        'done_tasks': done_tasks,
        'on_hold_tasks': on_hold_tasks,
        'canceled_tasks': canceled_tasks,
        'active_page': 'manage_kanban',
    }
    return render(request, 'todo/kanban.html', context)


@login_required
def settings_page(request):
    """
    Handles the user settings page — profile, password, preferences, and danger zone.
    """
    profile = get_or_create_profile(request.user)

    if request.method == 'POST':
        action = request.POST.get('action', 'profile')

        if action == 'profile':
            u_form = UserUpdateForm(request.POST, instance=request.user)
            if u_form.is_valid():
                u_form.save()
                messages.success(request, 'Profile updated successfully!')
                return redirect('settings')
            else:
                p_form = UserProfileForm(instance=profile)
                pw_form = PasswordUpdateForm(request.user)

        elif action == 'preferences':
            p_form = UserProfileForm(request.POST, instance=profile)
            if p_form.is_valid():
                p_form.save()
                messages.success(request, 'Preferences saved successfully!')
                return redirect('settings')
            else:
                u_form = UserUpdateForm(instance=request.user)
                pw_form = PasswordUpdateForm(request.user)

        elif action == 'password':
            pw_form = PasswordUpdateForm(request.user, request.POST)
            if pw_form.is_valid():
                user = pw_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Password changed successfully!')
                return redirect('settings')
            else:
                u_form = UserUpdateForm(instance=request.user)
                p_form = UserProfileForm(instance=profile)

        elif action == 'clear_data':
            if request.POST.get('confirm_clear') == 'yes':
                Task.objects.filter(user=request.user).delete()
                Category.objects.filter(user=request.user).delete()
                messages.success(request, 'All data cleared successfully.')
                return redirect('settings')
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
    """Logs out the user and redirects to dashboard (demo mode will auto-login again)."""
    auth_logout(request)
    return redirect('dashboard')


# ==============================================================================
#  TASK CRUD
# ==============================================================================

@login_required
def task_detail(request, pk):
    """Returns task data as JSON for the edit modal."""
    task = get_object_or_404(Task, pk=pk, user=request.user)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        task_data = {
            'id': task.id,
            'title': task.title,
            'description': task.description or '',
            'category': task.category.id if task.category else '',
            'category_name': task.category.name if task.category else '',
            'priority': task.priority,
            'status': task.status,
            'due_date': task.due_date.strftime('%Y-%m-%d') if task.due_date else '',
            'created_at': task.created_at.strftime('%d %b %Y'),
        }
        return JsonResponse({'success': True, 'task': task_data})
    context = {
        'task': task,
        'active_page': 'manage_tasks',
    }
    return render(request, 'todo/task_detail.html', context)


@login_required
def task_create(request):
    """Handles task creation via AJAX POST request."""
    if request.method == 'POST':
        form = TaskForm(request.POST, user=request.user)
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
        else:
            return JsonResponse({'success': False, 'errors': form.errors})

    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)


@login_required
def task_update(request, pk):
    """Updates an existing task (full form or quick status update)."""
    task = get_object_or_404(Task, pk=pk, user=request.user)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        # Quick status-only update (e.g., from Kanban drag-drop or dashboard checkbox)
        if new_status and 'title' not in request.POST:
            if new_status in Task.Status.values:
                task.status = new_status
                task.save()
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': True, 'message': 'Status updated!'})
                return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

        # Full form update
        form = TaskForm(request.POST, instance=task, user=request.user)
        if form.is_valid():
            form.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Task updated successfully!'})
            return redirect(request.META.get('HTTP_REFERER', 'dashboard'))
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors})
            return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

    # GET request: return task data as JSON for populating edit modal
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        task_data = {
            'title': task.title,
            'description': task.description or '',
            'category': task.category.id if task.category else '',
            'priority': task.priority,
            'status': task.status,
            'due_date': task.due_date.strftime('%Y-%m-%d') if task.due_date else '',
        }
        return JsonResponse({'success': True, 'task': task_data})

    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)


@login_required
def task_delete(request, pk):
    """Deletes a task."""
    task = get_object_or_404(Task, pk=pk, user=request.user)
    if request.method == 'POST':
        task_title = task.title
        task.delete()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'Task "{task_title}" deleted.'})
        messages.success(request, f'Task "{task_title}" has been deleted.')
        return redirect('manage_tasks')

    return render(request, 'todo/confirm_delete.html', {'object': task, 'type': 'task'})


# ==============================================================================
#  CATEGORY CRUD
# ==============================================================================

@login_required
def category_create(request):
    """Handles new project/category creation."""
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = request.user
            category.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f'Project "{category.name}" created!',
                    'category': {
                        'id': category.id,
                        'name': category.name,
                        'color': category.color,
                    }
                })
            messages.success(request, f'Project "{category.name}" created.')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors})

    return redirect('task_categories')


@login_required
def category_update(request, pk):
    """Handles updating an existing category."""
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
        category_name = category.name
        category.delete()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'Project "{category_name}" deleted.'})
        messages.success(request, f'Project "{category_name}" has been deleted.')
        return redirect('task_categories')

    return render(request, 'todo/confirm_delete.html', {'object': category, 'type': 'project'})


# ==============================================================================
#  PREDEFINED TASKS (Task Template Library)
# ==============================================================================

@login_required
def predefined_tasks_api(request):
    """
    Returns a list of pre-defined task templates, optionally filtered by category.
    Used by the frontend to display a task library picker.
    """
    category = request.GET.get('category', 'all')
    tasks_qs = PreDefinedTask.objects.all()
    if category != 'all':
        tasks_qs = tasks_qs.filter(category=category)

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

    return JsonResponse({
        'success': True,
        'tasks': tasks_data,
        'categories': categories,
    })


@login_required
def add_predefined_task(request):
    """
    Quickly adds a pre-defined task to the user's task pool.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            predefined_id = data.get('predefined_id')
            category_id = data.get('category_id')

            predefined = get_object_or_404(PreDefinedTask, pk=predefined_id)

            category = None
            if category_id:
                try:
                    category = Category.objects.get(pk=category_id, user=request.user)
                except Category.DoesNotExist:
                    pass

            task = Task.objects.create(
                user=request.user,
                title=predefined.title,
                description=predefined.description or '',
                priority=predefined.suggested_priority,
                category=category,
                status=Task.Status.TO_DO,
                is_predefined=True,
            )

            return JsonResponse({
                'success': True,
                'message': f'Task "{task.title}" added!',
                'task_id': task.id,
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    return JsonResponse({'success': False, 'error': 'POST required'}, status=405)


# ==============================================================================
#  STATS API
# ==============================================================================

@login_required
def stats_api(request):
    """Returns aggregated task stats for charts and widgets."""
    tasks = Task.objects.filter(user=request.user)
    total = tasks.count()
    done = tasks.filter(status='completed').count()
    in_progress = tasks.filter(status='in-progress').count()
    backlog = tasks.filter(status='backlog').count()
    on_hold = tasks.filter(status='on-hold').count()
    canceled = tasks.filter(status='canceled').count()
    to_do = tasks.filter(status='not-started').count()

    today = timezone.now().date()
    overdue = tasks.filter(
        due_date__lt=today
    ).exclude(status__in=['completed', 'canceled']).count()

    return JsonResponse({
        'success': True,
        'stats': {
            'total': total,
            'done': done,
            'in_progress': in_progress,
            'backlog': backlog,
            'on_hold': on_hold,
            'canceled': canceled,
            'to_do': to_do,
            'overdue': overdue,
            'completion_rate': int((done / total) * 100) if total > 0 else 0,
        }
    })


@login_required
def tasks_export_api(request):
    """Exports all user tasks and projects data as JSON or CSV."""
    tasks = Task.objects.filter(user=request.user).select_related('category')
    format_type = request.GET.get('format', 'json').lower()

    if format_type == 'csv':
        import csv
        from django.http import HttpResponse
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="taskflixx_tasks_export.csv"'
        writer = csv.writer(response)
        writer.writerow(['ID', 'Title', 'Description', 'Project', 'Priority', 'Status', 'Due Date', 'Created At', 'Completed At'])
        for t in tasks:
            writer.writerow([
                t.id,
                t.title,
                t.description or '',
                t.category.name if t.category else 'General',
                t.get_priority_display(),
                t.get_status_display(),
                t.due_date.strftime('%Y-%m-%d') if t.due_date else '',
                t.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                t.completed_at.strftime('%Y-%m-%d %H:%M:%S') if t.completed_at else '',
            ])
        return response

    tasks_data = [
        {
            'id': t.id,
            'title': t.title,
            'description': t.description or '',
            'project': t.category.name if t.category else 'General',
            'priority': t.priority,
            'priority_display': t.get_priority_display(),
            'status': t.status,
            'status_display': t.get_status_display(),
            'due_date': t.due_date.strftime('%Y-%m-%d') if t.due_date else None,
            'created_at': t.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'completed_at': t.completed_at.strftime('%Y-%m-%d %H:%M:%S') if t.completed_at else None,
        }
        for t in tasks
    ]
    return JsonResponse({'success': True, 'tasks': tasks_data, 'total': len(tasks_data)})


# ==============================================================================
#  AI ASSISTANT API
# ==============================================================================

@csrf_exempt
@login_required
def api_ai_suggest(request):
    """
    AI Task & Project Assistant endpoint.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            prompt = data.get('prompt', '').strip()

            if not prompt:
                return JsonResponse({'success': False, 'error': 'Empty prompt'}, status=400)

            prompt_lower = prompt.lower()
            if 'website' in prompt_lower or 'launch' in prompt_lower or 'app' in prompt_lower:
                title = "Launch Strategy & Production Readiness"
                suggestion = (
                    "1. Finalize DNS records & SSL certificate configuration.\n"
                    "2. Run cross-browser compatibility and lighthouse performance audit.\n"
                    "3. Execute production database migrations.\n"
                    "4. Verify exception logging & error reporting setup.\n"
                    "5. Set up monitoring & uptime alerts."
                )
            elif 'subtask' in prompt_lower or 'breakdown' in prompt_lower or 'feature' in prompt_lower:
                title = f"Task Breakdown: {prompt[:30]}..."
                suggestion = (
                    "Recommended Subtasks:\n"
                    "- API Endpoint setup with request validation\n"
                    "- Database schema migrations & indexing\n"
                    "- Frontend UI component integration\n"
                    "- Write unit and integration tests\n"
                    "- Code review and deployment"
                )
            elif 'marketing' in prompt_lower or 'campaign' in prompt_lower:
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
                'prompt': prompt
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'POST method required'}, status=405)


# ==============================================================================
#  AI ASSISTANT PAGE
# ==============================================================================

@login_required
def ai_assistant_page(request):
    """
    Renders the dedicated AI Assistant page.
    """
    projects = Category.objects.filter(user=request.user).annotate(
        task_count=Count('tasks')
    )
    recent_tasks = Task.objects.filter(user=request.user).order_by('-created_at')[:10]
    context = {
        'active_page': 'ai_assistant',
        'projects': projects,
        'recent_tasks': recent_tasks,
    }
    return render(request, 'todo/ai_assistant.html', context)


@login_required
def ai_create_task(request):
    """
    Creates a task directly from AI suggestion data posted from the AI assistant page.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            title = data.get('title', '').strip()
            description = data.get('description', '').strip()
            priority = data.get('priority', 'moderate')
            status = data.get('status', 'not-started')
            category_id = data.get('category_id')

            if not title:
                return JsonResponse({'success': False, 'error': 'Title is required'}, status=400)

            category = None
            if category_id:
                try:
                    category = Category.objects.get(pk=category_id, user=request.user)
                except Category.DoesNotExist:
                    pass

            task = Task.objects.create(
                user=request.user,
                title=title,
                description=description,
                priority=priority if priority in ['high', 'moderate', 'low'] else 'moderate',
                status=status if status in Task.Status.values else 'not-started',
                category=category,
            )
            return JsonResponse({
                'success': True,
                'message': f'Task "{task.title}" created successfully!',
                'task_id': task.id,
                'task_title': task.title,
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'POST required'}, status=405)


@login_required
def ai_create_project(request):
    """
    Creates a project/category directly from AI suggestion data.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name', '').strip()
            description = data.get('description', '').strip()
            color = data.get('color', '#3b82f6')
            tasks_to_create = data.get('tasks', [])  # List of task titles/dicts

            if not name:
                return JsonResponse({'success': False, 'error': 'Project name is required'}, status=400)

            # Validate hex color
            import re
            if not re.match(r'^#[0-9A-Fa-f]{6}$', color):
                color = '#3b82f6'

            project = Category.objects.create(
                user=request.user,
                name=name,
                description=description,
                color=color,
            )

            created_tasks = []
            for task_data in tasks_to_create[:10]:  # Max 10 tasks at a time
                if isinstance(task_data, str):
                    task_title = task_data
                    task_priority = 'moderate'
                else:
                    task_title = task_data.get('title', '')
                    task_priority = task_data.get('priority', 'moderate')

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
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'POST required'}, status=405)