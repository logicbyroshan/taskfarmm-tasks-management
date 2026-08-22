"""
todo/services.py

Business logic layer for TaskFlixx.

All database queries and domain logic live here — views and API viewsets
stay thin by delegating to these service functions. This prevents duplication,
makes the code testable in isolation, and keeps HTTP concerns out of the
business layer.
"""

import logging
from django.db.models import Count, Q
from django.utils import timezone
from django.utils.timesince import timesince

from .models import Task, Category, TaskComment, PreDefinedTask

logger = logging.getLogger('todo')


# ============================================================
#  TASK SERVICE
# ============================================================

class TaskService:
    """Encapsulates all Task-related business logic."""

    # Mapping from sort param → ORM ordering expression
    SORT_MAP = {
        'newest': '-created_at',
        'oldest': 'created_at',
        'due_date': 'due_date',
        'priority': 'priority',
        'title': 'title',
        'updated': '-updated_at',
    }

    @staticmethod
    def get_base_queryset(user):
        """
        Returns tasks accessible by user:
        - Project owners see all tasks in their projects.
        - Collaborators only see tasks assigned to them or created by them.
        """
        return (
            Task.objects
            .filter(
                Q(user=user) | 
                Q(category__user=user) |
                Q(assignees=user)
            )
            .distinct()
            .select_related('category', 'user')
            .prefetch_related('assignees', 'category__members')
        )

    @staticmethod
    def get_dashboard_stats(user):
        """
        Returns aggregated dashboard statistics for a user.

        Uses a single DB aggregation query instead of multiple .count() calls,
        reducing round-trips from 8 → 1.
        """
        tasks = TaskService.get_base_queryset(user)
        today = timezone.now().date()

        # Single aggregation pass for all status counts
        status_counts = dict(
            tasks.values('status')
                 .annotate(n=Count('id'))
                 .values_list('status', 'n')
        )

        total = sum(status_counts.values())
        done = status_counts.get('completed', 0)
        in_progress = status_counts.get('in-progress', 0)

        overdue = tasks.filter(
            due_date__lt=today
        ).exclude(status__in=['completed', 'canceled']).count()

        due_today = tasks.filter(
            due_date=today
        ).exclude(status__in=['completed', 'canceled']).count()

        completion_rate = int((done / total) * 100) if total > 0 else 0

        return {
            'total_count': total,
            'done_count': done,
            'in_progress_count': in_progress,
            'backlog_count': status_counts.get('backlog', 0),
            'to_do_count': status_counts.get('not-started', 0),
            'on_hold_count': status_counts.get('on-hold', 0),
            'canceled_count': status_counts.get('canceled', 0),
            'overdue_count': overdue,
            'due_today_count': due_today,
            'completion_rate': completion_rate,
        }

    @staticmethod
    def get_recent_tasks(user, limit=6):
        """Returns the most recently created tasks accessible by the user."""
        return (
            TaskService.get_base_queryset(user)
            .order_by('-created_at')[:limit]
        )

    @staticmethod
    def get_recently_completed(user, limit=6):
        """Returns recently completed tasks for the dashboard."""
        return (
            TaskService.get_base_queryset(user)
            .filter(status='completed')
            .order_by('-completed_at')[:limit]
        )

    @staticmethod
    def filter_and_sort(user, search='', status='all', priority='all',
                        project='all', sort='newest'):
        """
        Returns a filtered and sorted queryset for the manage-tasks view and REST API.
        """
        qs = TaskService.get_base_queryset(user)

        if search:
            qs = qs.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )

        if status != 'all' and status:
            qs = qs.filter(status=status)

        if priority != 'all' and priority:
            qs = qs.filter(priority=priority)

        if project == 'none':
            qs = qs.filter(category__isnull=True)
        elif project not in ('all', '', None):
            qs = qs.filter(category_id=project)

        ordering = TaskService.SORT_MAP.get(sort, '-created_at')
        return qs.order_by(ordering)

    @staticmethod
    def filter_and_sort_tasks(user, category=None, priority=None, status=None,
                              sort='newest', query=None):
        return TaskService.filter_and_sort(
            user=user, search=query or '', status=status or 'all',
            priority=priority or 'all', project=category or 'all', sort=sort
        )

    @staticmethod
    def get_kanban_columns(user, project_id=None):
        """
        Returns tasks split by status for the Kanban board.
        Supports shared projects where user is owner or member.
        """
        all_projects = (
            Category.objects
            .filter(Q(user=user) | Q(members=user))
            .distinct()
            .annotate(task_count=Count('tasks', distinct=True))
            .prefetch_related('members')
        )

        selected_project = None
        if project_id:
            selected_project = all_projects.filter(pk=project_id).first()
        if not selected_project and all_projects.exists():
            selected_project = all_projects.first()

        if selected_project:
            selected_project_id = selected_project.id
            selected_project.ensure_share_token()
            if selected_project.user == user:
                # Main user / owner sees all tasks across the project
                qs = Task.objects.filter(category=selected_project).select_related('category', 'user').prefetch_related('assignees')
            else:
                # Collaborator only sees tasks assigned to them or created by them
                qs = Task.objects.filter(
                    Q(category=selected_project) & (Q(assignees=user) | Q(user=user))
                ).distinct().select_related('category', 'user').prefetch_related('assignees')
        else:
            selected_project_id = None
            # If no project selected, show user's accessible tasks
            qs = TaskService.get_base_queryset(user)

        columns = {
            'backlog': qs.filter(status='backlog').order_by('-created_at'),
            'not-started': qs.filter(status='not-started').order_by('-created_at'),
            'in-progress': qs.filter(status='in-progress').order_by('-created_at'),
            'completed': qs.filter(status='completed').order_by('-created_at'),
            'on-hold': qs.filter(status='on-hold').order_by('-created_at'),
            'canceled': qs.filter(status='canceled').order_by('-created_at'),
        }

        active_columns = []
        if selected_project:
            for col_def in selected_project.get_board_columns():
                col = dict(col_def)
                col['tasks'] = columns.get(col['key'], qs.none())
                col['count'] = col['tasks'].count()
                active_columns.append(col)

        return {
            'all_projects': all_projects,
            'selected_project': selected_project,
            'selected_project_id': selected_project_id,
            'columns': columns,
            'active_columns': active_columns,
            'has_projects': all_projects.exists(),
        }

    @staticmethod
    def update_project_column_name(project, column_key, new_name):
        """Renames a Kanban column title for a project."""
        if not isinstance(project.column_names, dict):
            project.column_names = {}
        project.column_names[column_key] = new_name.strip()
        project.save(update_fields=['column_names'])
        return project

    @staticmethod
    def get_task_detail_data(task):
        """
        Returns a complete task data dict for the Trello modal / API response.
        Includes comments and checklist. Called by both views and serializers.
        """
        comments = (
            task.comments
            .select_related('user')
            .order_by('-created_at')
        )
        comments_data = [
            {
                'id': c.id,
                'user': c.user.username,
                'content': c.content,
                'created_at': c.created_at.strftime('%d %b %Y, %H:%M'),
                'time_ago': timesince(c.created_at) + ' ago',
            }
            for c in comments
        ]
        assignees_data = [
            {
                'id': u.id,
                'username': u.username,
                'initials': u.username[:2].upper()
            }
            for u in task.assignees.all()
        ]
        attachments = (
            task.attachments
            .select_related('user')
            .order_by('-created_at')
        )
        attachments_data = [
            {
                'id': a.id,
                'filename': a.filename,
                'file_url': a.file.url if a.file else '',
                'file_size': a.file_size,
                'file_size_display': f"{a.file_size / 1024:.1f} KB" if a.file_size < 1048576 else f"{a.file_size / 1048576:.1f} MB",
                'file_type': a.file_type,
                'is_image': a.is_image(),
                'user': a.user.username,
                'created_at': a.created_at.strftime('%d %b %Y, %H:%M'),
            }
            for a in attachments
        ]
        return {
            'id': task.id,
            'title': task.title,
            'user': task.user.username if task.user else '',
            'description': task.description or '',
            'category': task.category_id,
            'category_name': task.category.name if task.category else 'General',
            'category_color': task.category.color if task.category else '#71717a',
            'priority': task.priority,
            'priority_display': task.get_priority_display(),
            'status': task.status,
            'status_display': task.get_status_display(),
            'due_date': task.due_date.strftime('%Y-%m-%d') if task.due_date else '',
            'created_at': task.created_at.strftime('%d %b %Y, %H:%M'),
            'checklist_title': getattr(task, 'checklist_title', 'Checklist') or 'Checklist',
            'checklist': task.checklist or [],
            'comments': comments_data,
            'assignees': assignees_data,
            'attachments': attachments_data,
        }

    @staticmethod
    def add_attachment(task, user, uploaded_file):
        """Creates a TaskAttachment for the task."""
        from .models import TaskAttachment
        attachment = TaskAttachment.objects.create(
            task=task,
            user=user,
            file=uploaded_file,
            filename=uploaded_file.name,
            file_size=uploaded_file.size,
            file_type=getattr(uploaded_file, 'content_type', '')
        )
        return attachment

    @staticmethod
    def create_task(user, validated_data):
        """Creates a new task for the given user, supporting shared categories."""
        category_id = validated_data.pop('category_id', None)
        category = None
        if category_id:
            category = Category.objects.filter(
                Q(pk=category_id) & (Q(user=user) | Q(members=user))
            ).distinct().first()

        task = Task.objects.create(
            user=user,
            category=category,
            **validated_data
        )
        logger.info('Task created: id=%d user=%s', task.id, user.username)
        return task

    @staticmethod
    def partial_update_task(task, data, user):
        """
        Applies a partial update to a task from a dict of fields.
        Handles category lookup and status validation.
        Returns the updated task instance.
        """
        if 'title' in data and data['title'].strip():
            task.title = data['title'].strip()

        if 'description' in data:
            task.description = data['description']

        if 'status' in data and data['status'] in Task.Status.values:
            task.status = data['status']

        if 'priority' in data and data['priority'] in Task.Priority.values:
            task.priority = data['priority']

        if 'due_date' in data:
            task.due_date = data['due_date'] if data['due_date'] else None

        if 'category' in data:
            cat_id = data['category']
            if cat_id:
                task.category = Category.objects.filter(
                    Q(pk=cat_id) & (Q(user=user) | Q(members=user))
                ).distinct().first()
            else:
                task.category = None

        if 'checklist' in data:
            task.checklist = data['checklist']

        if 'checklist_title' in data:
            task.checklist_title = data['checklist_title'] or 'Checklist'

        if 'assignees' in data:
            assignee_ids = data['assignees']
            if isinstance(assignee_ids, list):
                from django.contrib.auth.models import User as AuthUser
                task.assignees.set(AuthUser.objects.filter(id__in=assignee_ids))

        task.save()
        logger.info('Task updated: id=%d user=%s fields=%s', task.id, user.username, list(data.keys()))
        return task

    @staticmethod
    def toggle_status(task):
        """Toggles a task between DONE and TO_DO."""
        if task.status == Task.Status.DONE:
            task.status = Task.Status.TO_DO
            task.completed_at = None
        else:
            task.status = Task.Status.DONE
            task.completed_at = timezone.now()
        task.save(update_fields=['status', 'completed_at', 'updated_at'])
        return task

    @staticmethod
    def update_checklist(task, checklist):
        """Replaces the task checklist with the provided list."""
        task.checklist = checklist
        task.save(update_fields=['checklist', 'updated_at'])
        return task

    @staticmethod
    def add_comment(task, user, content):
        """Creates a new comment on a task."""
        if not content or not content.strip():
            raise ValueError('Comment content cannot be empty.')
        comment = TaskComment.objects.create(
            task=task,
            user=user,
            content=content.strip()
        )
        return comment


# ============================================================
#  CATEGORY / PROJECT SERVICE
# ============================================================

class CategoryService:
    """Encapsulates all Category/Project-related business logic."""

    @staticmethod
    def get_with_stats(user):
        """
        Returns all categories owned by or shared with a user annotated with task counts
        and a computed progress percentage.
        """
        categories = list(
            Category.objects
            .filter(Q(user=user) | Q(members=user))
            .distinct()
            .annotate(
                task_count=Count('tasks', distinct=True),
                completed_count=Count('tasks', filter=Q(tasks__status='completed'), distinct=True)
            )
            .prefetch_related('members')
        )
        for cat in categories:
            cat.progress = (
                int((cat.completed_count / cat.task_count) * 100)
                if cat.task_count > 0 else 0
            )
            cat.is_owner = (cat.user_id == user.id)
            cat.ensure_share_token()
        return categories

    @staticmethod
    def get_dashboard_project_progress(user):
        """
        Returns project progress data for the dashboard sidebar toggle.
        """
        categories = (
            Category.objects
            .filter(Q(user=user) | Q(members=user))
            .distinct()
            .annotate(
                task_count=Count('tasks', distinct=True),
                completed_count=Count('tasks', filter=Q(tasks__status='completed'), distinct=True)
            )
            .order_by('name')
        )
        result = []
        for cat in categories:
            progress = (
                int((cat.completed_count / cat.task_count) * 100)
                if cat.task_count > 0 else 0
            )
            result.append({
                'id': cat.id,
                'name': cat.name,
                'color': cat.color,
                'task_count': cat.task_count,
                'completed_count': cat.completed_count,
                'progress': progress,
            })
        return result

    @staticmethod
    def create_category(user, name, color='#3b82f6', description=''):
        """Creates a new project/category for the user."""
        import re
        if not re.match(r'^#[0-9A-Fa-f]{6}$', color):
            color = '#3b82f6'
        category = Category.objects.create(
            user=user,
            name=name,
            color=color,
            description=description,
        )
        logger.info('Category created: id=%d user=%s', category.id, user.username)
        return category


# ============================================================
#  EXPORT SERVICE
# ============================================================

class ExportService:
    """Handles exporting tasks to JSON or CSV."""

    @staticmethod
    def tasks_to_dict_list(user):
        """Returns all tasks as a list of dicts for JSON export."""
        tasks = (
            Task.objects
            .filter(user=user)
            .select_related('category')
            .order_by('-created_at')
        )
        return [
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

    @staticmethod
    def tasks_to_csv_rows(user):
        """Returns header + rows for CSV export."""
        header = ['ID', 'Title', 'Description', 'Project', 'Priority',
                  'Status', 'Due Date', 'Created At', 'Completed At']
        tasks = (
            Task.objects
            .filter(user=user)
            .select_related('category')
            .order_by('-created_at')
        )
        rows = [
            [
                t.id, t.title, t.description or '',
                t.category.name if t.category else 'General',
                t.get_priority_display(), t.get_status_display(),
                t.due_date.strftime('%Y-%m-%d') if t.due_date else '',
                t.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                t.completed_at.strftime('%Y-%m-%d %H:%M:%S') if t.completed_at else '',
            ]
            for t in tasks
        ]
        return header, rows


# ============================================================
#  PREDEFINED TASK SERVICE
# ============================================================

class PreDefinedTaskService:
    """Handles task template library operations."""

    @staticmethod
    def get_templates(category='all'):
        """Returns predefined task templates, optionally filtered by category."""
        qs = PreDefinedTask.objects.all()
        if category and category != 'all':
            qs = qs.filter(category=category)
        return qs

    @staticmethod
    def add_to_user_tasks(user, predefined_id, category_id=None):
        """
        Adds a predefined task template to the user's task pool.
        Returns the newly created Task instance.
        """
        predefined = PreDefinedTask.objects.get(pk=predefined_id)
        category = None
        if category_id:
            category = Category.objects.filter(pk=category_id, user=user).first()

        task = Task.objects.create(
            user=user,
            title=predefined.title,
            description=predefined.description or '',
            priority=predefined.suggested_priority,
            category=category,
            status=Task.Status.TO_DO,
            is_predefined=True,
        )
        logger.info('Predefined task added: predefined_id=%s task_id=%d user=%s',
                    predefined_id, task.id, user.username)
        return task


# ============================================================
#  STATS SERVICE
# ============================================================

class StatsService:
    """Aggregate stats used by both HTML views and the REST API."""

    @staticmethod
    def get_stats(user):
        """Full stats dict — reused by dashboard view and /api/v1/stats/ endpoint."""
        stats = TaskService.get_dashboard_stats(user)
        total = stats['total_count']
        done = stats['done_count']
        stats['completion_rate'] = int((done / total) * 100) if total > 0 else 0
        return stats
