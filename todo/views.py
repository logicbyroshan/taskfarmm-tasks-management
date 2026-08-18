# ----------------- Django Core Imports -----------------
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import JsonResponse

# ----------------- Django Contrib Imports -----------------
from django.contrib import messages
from django.contrib.auth.decorators import login_required

# ----------------- Database and Querying Imports -----------------
from django.db.models import Count, Q

# ----------------- Local Application Imports -----------------
from .models import Task, Category
from .forms import TaskForm, CategoryForm, UserUpdateForm


# ==============================================================================
#  CORE PAGE VIEWS
# ==============================================================================

@login_required
def dashboard(request):
    """
    Displays the main dashboard for an authenticated user.
    It gathers various statistics (task counts) and lists of recent tasks
    to provide a summary of the user's activity.
    """
    tasks = Task.objects.filter(user=request.user)

    # Calculate counts for all 6 task statuses in 2x3 overview grid
    backlog_count = tasks.filter(status='backlog').count()
    to_do_count = tasks.filter(status='not-started').count()
    in_progress_count = tasks.filter(status='in-progress').count()
    done_count = tasks.filter(status='completed').count()
    on_hold_count = tasks.filter(status='on-hold').count()
    canceled_count = tasks.filter(status='canceled').count()

    # Get the 5 most recent tasks that are not yet completed
    recent_tasks = tasks.exclude(status='completed').order_by('-created_at')[:5]

    # Get the 3 most recently completed tasks
    recently_completed_tasks = tasks.filter(status='completed').order_by('-completed_at')[:3]

    context = {
        'backlog_count': backlog_count,
        'to_do_count': to_do_count,
        'in_progress_count': in_progress_count,
        'done_count': done_count,
        'on_hold_count': on_hold_count,
        'canceled_count': canceled_count,
        'recent_tasks': recent_tasks,
        'recently_completed_tasks': recently_completed_tasks,
        'active_page': 'dashboard',
    }
    return render(request, 'todo/index.html', context)


@login_required
def my_tasks(request):
    """
    Displays a grid of all tasks belonging to the current user (Manage Tasks view).
    """
    tasks = Task.objects.filter(user=request.user).order_by('-created_at')
    context = {
        'tasks': tasks,
        'active_page': 'my_tasks',
    }
    return render(request, 'todo/manage-tasks.html', context)


@login_required
def task_categories(request):
    """
    Displays all projects created by the user (Manage Projects view).
    Calculates total task count and completion percentage for each project.
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
    Displays a Kanban board page with 6 columns matching Dashboard status overview:
    Backlog, To Do, In Progress, Done, On Hold, Canceled.
    Supports filtering by specific Project.
    """
    all_projects = Category.objects.filter(user=request.user)
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
    Handles the user settings page for profile updates only.
    Password change removed as auth will be handled by another app.
    """
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        if u_form.is_valid():
            u_form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('settings')

    # For GET requests
    u_form = UserUpdateForm(instance=request.user)

    context = {
        'active_page': 'settings',
        'u_form': u_form,
    }
    return render(request, 'todo/settings.html', context)


# ==============================================================================
#  TASK CRUD (Create, Read, Update, Delete) VIEWS
# ==============================================================================

@login_required
def task_detail(request, pk):
    """
    Displays full task details on a dedicated page.
    Shows all task information including rich text description.
    """
    task = get_object_or_404(Task, pk=pk, user=request.user)
    context = {
        'task': task,
        'active_page': 'my_tasks',
    }
    return render(request, 'todo/task_detail.html', context)


@login_required
def task_create(request):
    """
    Handles the creation of a new task via an AJAX POST request from a modal.
    Returns a JSON response indicating success or failure.
    """
    # This view should only accept POST requests now
    if request.method == 'POST':
        form = TaskForm(request.POST, user=request.user)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()
            return JsonResponse({'success': True, 'message': 'Task created successfully!'})
        else:
            # If the form is invalid, return the errors as JSON
            return JsonResponse({'success': False, 'errors': form.errors})
    
    # If it's a GET request, it's not a valid way to use this endpoint anymore
    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)


@login_required
def task_update(request, pk):
    """
    Handles updating an existing task via POST request.
    Supports quick status updates as well as full form updates.
    """
    task = get_object_or_404(Task, pk=pk, user=request.user)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        # If only status is passed (e.g. from Kanban move buttons or task checkboxes)
        if new_status and 'title' not in request.POST:
            if new_status in Task.Status.values:
                task.status = new_status
                task.save()
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': True, 'message': 'Task status updated!'})
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
    
    # If it's a GET request, return task data as JSON for populating the edit form
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        task_data = {
            'title': task.title,
            'description': task.description,
            'category': task.category.id if task.category else '',
            'priority': task.priority,
            'status': task.status,
            'due_date': task.due_date.strftime('%Y-%m-%d') if task.due_date else '',
        }
        return JsonResponse({'success': True, 'task': task_data})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)


@login_required
def task_delete(request, pk):
    """
    Handles the deletion of a task.
    On GET, it shows a confirmation page.
    On POST, it deletes the task and redirects to the task list.
    """
    task = get_object_or_404(Task, pk=pk, user=request.user)
    if request.method == 'POST':
        task_title = task.title
        task.delete()
        messages.success(request, f'Task "{task_title}" has been deleted.')
        return redirect('my_tasks')
        
    return render(request, 'todo/confirm_delete.html', {'object': task})


# ==============================================================================
#  CATEGORY CRUD (Create, Read, Update, Delete) VIEWS
# ==============================================================================

@login_required
def category_create(request):
    """
    Handles the creation of a new category via a POST request,
    typically from a modal form. Redirects back to the categories page.
    """
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = request.user
            category.save()
            messages.success(request, f'Category "{category.name}" created.')
    
    return redirect('task_categories')


@login_required
def category_update(request, pk):
    """
    Handles updating an existing category via a POST request.
    This would be used if you implement an "edit category" modal.
    """
    category = get_object_or_404(Category, pk=pk, user=request.user)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, f'Category "{category.name}" updated.')
            
    return redirect('task_categories')


@login_required
def category_delete(request, pk):
    """
    Handles the deletion of a category.
    It's recommended to handle this with a POST request for security.
    """
    category = get_object_or_404(Category, pk=pk, user=request.user)
    if request.method == 'POST':
        category_name = category.name
        category.delete()
        messages.success(request, f'Category "{category_name}" has been deleted.')
        return redirect('task_categories')
        
    return render(request, 'todo/confirm_delete.html', {'object': category})


# ==============================================================================
#  AI ASSISTANT API ENDPOINTS (Stubs ready for LLM / OpenAI API Integration)
# ==============================================================================

from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
@login_required
def api_ai_suggest(request):
    """
    AI Task & Project Assistant endpoint.
    Accepts user prompts and returns AI task breakdowns, smart priority recommendations,
    and task descriptions. Prepared for OpenAI / Gemini / Claude API key integration.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            prompt = data.get('prompt', '').strip()

            if not prompt:
                return JsonResponse({'success': False, 'error': 'Empty prompt'}, status=400)

            # Smart AI Suggestion Generator Logic
            prompt_lower = prompt.lower()
            if 'website' in prompt_lower or 'launch' in prompt_lower or 'app' in prompt_lower:
                title = "Launch Strategy & Production Readiness"
                suggestion = (
                    "1. Finalize DNS records & SSL certificate configuration.\n"
                    "2. Run cross-browser compatibility and lighthouse performance audit.\n"
                    "3. Execute production database migrations.\n"
                    "4. Verify exception logging & error reporting setup."
                )
            elif 'subtask' in prompt_lower or 'breakdown' in prompt_lower or 'feature' in prompt_lower:
                title = f"Task Breakdown: {prompt[:30]}..."
                suggestion = (
                    "Recommended Subtasks:\n"
                    "- API Endpoint setup with request validation\n"
                    "- Database schema migrations & indexing\n"
                    "- Frontend UI component integration with glassmorphism styling\n"
                    "- Comprehensive unit and integration test coverage"
                )
            else:
                title = f"AI Workflow Task: {prompt[:35]}"
                suggestion = (
                    f"AI Action Plan for '{prompt}':\n"
                    "- Priority: High\n"
                    "- Recommended Timeline: Complete within 48 hours\n"
                    "- Suggested Action: Create task, assign project category, and review progress."
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