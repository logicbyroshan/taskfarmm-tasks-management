"""
todo/services.py

Business logic layer for TaskFlixx.

All database queries and domain logic live here — views and API viewsets
stay thin by delegating to these service functions. This prevents duplication,
makes the code testable in isolation, and keeps HTTP concerns out of the
business layer.
"""

import logging
from collections import defaultdict
from django.db.models import Count, Q
from django.utils import timezone
from django.utils.timesince import timesince

from django.contrib.auth.models import User
from .models import Task, Category, TaskComment, PreDefinedTask, Notification, UserProfile
from .notifications import NotificationService

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

        projects_count = CategoryService.get_categories(user).count()

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
            'projects_count': projects_count,
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
        Optimized with a single database round-trip.
        """
        all_projects = (
            Category.objects
            .filter(Q(user=user) | Q(members=user))
            .distinct()
            .annotate(task_count=Count('tasks', distinct=True))
            .prefetch_related('members')
        )

        selected_project = None
        if project_id and str(project_id).isdigit():
            selected_project = all_projects.filter(pk=int(project_id)).first()
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

        all_board_tasks = list(qs.order_by('-created_at'))
        tasks_by_status = defaultdict(list)
        for t in all_board_tasks:
            tasks_by_status[t.status].append(t)

        columns = {
            'backlog': tasks_by_status['backlog'],
            'not-started': tasks_by_status['not-started'],
            'in-progress': tasks_by_status['in-progress'],
            'completed': tasks_by_status['completed'],
            'on-hold': tasks_by_status['on-hold'],
            'canceled': tasks_by_status['canceled'],
        }

        active_columns = []
        if selected_project:
            for col_def in selected_project.get_board_columns():
                col = dict(col_def)
                col['tasks'] = columns.get(col['key'], [])
                col['count'] = len(col['tasks'])
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
                old_assignee_ids = set(task.assignees.values_list('id', flat=True))
                new_users = list(AuthUser.objects.filter(id__in=assignee_ids))
                task.assignees.set(new_users)
                for nu in new_users:
                    if nu.id not in old_assignee_ids and nu.id != user.id:
                        try:
                            NotificationService.queue_notification(
                                user=nu,
                                event_type=Notification.EventType.TASK_ASSIGNED,
                                title=f"Assigned to task: {task.title}",
                                message=f"{user.get_full_name() or user.username} assigned you to task '{task.title}'",
                                action_url=f"/kanban/?project={task.category_id}&task={task.id}" if task.category_id else f"/kanban/?task={task.id}",
                                context={
                                    'task_title': task.title,
                                    'assigner_name': user.get_full_name() or user.username,
                                    'project_name': task.category.name if task.category else 'General Tasks',
                                }
                            )
                        except Exception as e:
                            logger.warning('Failed to queue assignment notification: %s', e)

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
            # Queue task completed notification to task owner if exists
            if task.user:
                try:
                    NotificationService.queue_notification(
                        user=task.user,
                        event_type=Notification.EventType.TASK_COMPLETED,
                        title=f"Task completed: {task.title}",
                        message=f"Task '{task.title}' has been marked as completed.",
                        action_url=f"/kanban/?project={task.category_id}" if task.category_id else "/kanban/",
                        context={
                            'task_title': task.title,
                            'project_name': task.category.name if task.category else 'General Tasks',
                        }
                    )
                except Exception as e:
                    logger.warning('Failed to queue completion notification: %s', e)

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
        """Creates a new comment on a task and notifies stakeholders."""
        if not content or not content.strip():
            raise ValueError('Comment content cannot be empty.')
        comment = TaskComment.objects.create(
            task=task,
            user=user,
            content=content.strip()
        )

        # Notify task creator and assignees (excluding author)
        recipients = set()
        if task.user and task.user != user:
            recipients.add(task.user)
        for assignee in task.assignees.exclude(id=user.id):
            recipients.add(assignee)

        for r in recipients:
            try:
                NotificationService.queue_notification(
                    user=r,
                    event_type=Notification.EventType.TASK_COMMENT,
                    title=f"New comment on: {task.title}",
                    message=f"{user.get_full_name() or user.username} commented on '{task.title}'",
                    action_url=f"/kanban/?project={task.category_id}" if task.category_id else "/kanban/",
                    context={
                        'task_title': task.title,
                        'comment_text': comment.content,
                        'author_name': user.get_full_name() or user.username,
                        'project_name': task.category.name if task.category else 'General Tasks',
                    }
                )
            except Exception as e:
                logger.warning('Failed to queue comment notification: %s', e)

        return comment


# ============================================================
#  CATEGORY / PROJECT SERVICE
# ============================================================

class CategoryService:
    """Encapsulates all Category/Project-related business logic."""

    @staticmethod
    def get_categories(user):
        """Returns categories owned by or shared with a user."""
        return Category.objects.filter(Q(user=user) | Q(members=user)).distinct()

    @staticmethod
    def get_with_stats(user):
        """
        Returns all categories owned by or shared with a user annotated with task counts,
        status breakdowns (backlog, in-progress, completed, todo), member lists,
        and a computed progress percentage.
        """
        categories = list(
            Category.objects
            .filter(Q(user=user) | Q(members=user))
            .distinct()
            .annotate(
                task_count=Count('tasks', distinct=True),
                completed_count=Count('tasks', filter=Q(tasks__status='completed'), distinct=True),
                in_progress_count=Count('tasks', filter=Q(tasks__status='in-progress'), distinct=True),
                todo_count=Count('tasks', filter=Q(tasks__status='not-started'), distinct=True),
                backlog_count=Count('tasks', filter=Q(tasks__status='backlog'), distinct=True),
            )
            .prefetch_related('members', 'user')
        )
        for cat in categories:
            cat.progress = (
                int((cat.completed_count / cat.task_count) * 100)
                if cat.task_count > 0 else 0
            )
            cat.is_owner = (cat.user_id == user.id)
            cat.ensure_share_token()
            members = []
            if cat.user:
                members.append({
                    'id': cat.user.id,
                    'name': cat.user.get_full_name() or cat.user.username,
                    'username': cat.user.username,
                    'initials': cat.user.username[:2].upper(),
                    'is_owner': True,
                })
            for m in cat.members.all():
                if cat.user_id != m.id:
                    members.append({
                        'id': m.id,
                        'name': m.get_full_name() or m.username,
                        'username': m.username,
                        'initials': m.username[:2].upper(),
                        'is_owner': False,
                    })
            cat.member_list = members
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
    def create_category(user, name, color='#3b82f6', description='', board_template=Category.BoardTemplate.SMART):
        """Creates a new project/category for the user."""
        import re
        if not re.match(r'^#[0-9A-Fa-f]{6}$', color):
            color = '#3b82f6'
        if board_template not in Category.BoardTemplate.values:
            board_template = Category.BoardTemplate.SMART
        category = Category.objects.create(
            user=user,
            name=name,
            color=color,
            description=description,
            board_template=board_template,
        )
        logger.info('Category created: id=%d user=%s template=%s', category.id, user.username, board_template)
        return category


    @staticmethod
    def get_recent_projects_for_dashboard(user, limit=8):
        """
        Returns recent projects with enriched statistics (total tasks, backlog, in-progress, completed,
        members count, assigned member list, progress percentage) for the main dashboard display.
        """
        categories = list(
            Category.objects
            .filter(Q(user=user) | Q(members=user))
            .distinct()
            .annotate(
                task_count=Count('tasks', distinct=True),
                completed_count=Count('tasks', filter=Q(tasks__status='completed'), distinct=True),
                in_progress_count=Count('tasks', filter=Q(tasks__status='in-progress'), distinct=True),
                todo_count=Count('tasks', filter=Q(tasks__status='not-started'), distinct=True),
                backlog_count=Count('tasks', filter=Q(tasks__status='backlog'), distinct=True),
            )
            .prefetch_related('members', 'user')
            .order_by('-created_at')[:limit]
        )
        for cat in categories:
            cat.progress = (
                int((cat.completed_count / cat.task_count) * 100)
                if cat.task_count > 0 else 0
            )
            cat.is_owner = (cat.user_id == user.id)
            cat.ensure_share_token()
            cat.member_list = [
                {
                    'id': m.id,
                    'username': m.username,
                    'name': m.get_full_name() or m.username,
                    'initials': m.username[:2].upper()
                }
                for m in cat.members.all()
            ]
        return categories


# ============================================================
#  SUB-USER / TEAM MANAGEMENT SERVICE (Max 99 per account)
# ============================================================

class SubUserService:
    """Encapsulates all Sub-User and Team Member business logic."""

    MAX_SUBUSERS = 99

    @classmethod
    def get_subusers(cls, owner):
        """Returns all sub-users belonging to the owner account."""
        if hasattr(owner, 'profile') and owner.profile.is_subuser:
            return User.objects.none()

        return (
            User.objects
            .filter(profile__parent_user=owner, profile__is_subuser=True)
            .select_related('profile')
            .prefetch_related('shared_categories', 'assigned_tasks')
            .order_by('-date_joined')
        )

    @classmethod
    def get_subusers_data(cls, owner):
        """Returns detailed serializable data list of all sub-users."""
        subusers = cls.get_subusers(owner)
        data = []
        for u in subusers:
            prof = getattr(u, 'profile', None)
            assigned_projects = [
                {'id': c.id, 'name': c.name, 'color': c.color}
                for c in u.shared_categories.all()
            ]
            data.append({
                'id': u.id,
                'username': u.username,
                'name': u.get_full_name() or u.username,
                'first_name': u.first_name,
                'email': u.email,
                'role': prof.role if prof else 'member',
                'role_display': prof.get_role_display() if prof else 'Member',
                'is_active': u.is_active,
                'assigned_projects': assigned_projects,
                'assigned_project_ids': [p['id'] for p in assigned_projects],
                'assigned_tasks_count': u.assigned_tasks.count(),
                'date_joined': u.date_joined.strftime('%d %b %Y, %H:%M'),
                'last_login': u.last_login.strftime('%d %b %Y, %H:%M') if u.last_login else 'Never',
            })
        return data

    @classmethod
    def create_subuser(cls, owner, username, password, display_name='', role='member', assigned_project_ids=None):
        """
        Creates a sub-user under the owner account.
        Enforces maximum 99 sub-users limit.
        Does not require unique email.
        """
        owner_profile = getattr(owner, 'profile', None)
        if owner_profile is None or not hasattr(owner_profile, 'is_subuser'):
            owner_profile = UserProfile.objects.filter(user=owner).first()

        if owner_profile and owner_profile.is_subuser:
            raise ValueError("Sub-users cannot create other sub-users.")

        current_count = cls.get_subusers(owner).count()
        if current_count >= cls.MAX_SUBUSERS:
            raise ValueError(f"Account limit reached. Maximum {cls.MAX_SUBUSERS} sub-users allowed.")

        username = (username or '').strip().lower()
        if not username:
            raise ValueError("Username is required.")
        if len(username) < 3:
            raise ValueError("Username must be at least 3 characters long.")
        if not password or len(password) < 4:
            raise ValueError("Password must be at least 4 characters long.")

        if User.objects.filter(username__iexact=username).exists():
            raise ValueError(f'Username "{username}" is already taken. Please choose another username.')

        # Dummy email scoped to parent account so uniqueness isn't required
        dummy_email = f"{username}@{owner.username}.taskflixx.local"

        subuser = User.objects.create_user(
            username=username,
            password=password,
            email=dummy_email,
            first_name=display_name.strip() if display_name else username
        )

        profile, _ = UserProfile.objects.get_or_create(user=subuser)
        profile.is_subuser = True
        profile.parent_user = owner
        profile.role = role if role in UserProfile.Role.values else UserProfile.Role.MEMBER
        profile.can_manage_tasks = True
        profile.save()
        subuser.profile = profile

        # Assign projects if provided
        if assigned_project_ids:
            projects = Category.objects.filter(id__in=assigned_project_ids, user=owner)
            for p in projects:
                p.members.add(subuser)

        logger.info("Sub-user created: %s (under owner %s, role=%s)", subuser.username, owner.username, profile.role)
        return subuser

    @classmethod
    def update_subuser(cls, owner, subuser_id, username=None, password=None, display_name=None, role=None, is_active=None, assigned_project_ids=None):
        """Updates an existing sub-user."""
        subuser = User.objects.filter(id=subuser_id, profile__parent_user=owner, profile__is_subuser=True).first()
        if not subuser:
            raise ValueError("Sub-user not found or access denied.")

        if username:
            username = username.strip().lower()
            if username != subuser.username:
                if User.objects.filter(username__iexact=username).exclude(id=subuser.id).exists():
                    raise ValueError(f'Username "{username}" is already taken.')
                subuser.username = username

        if display_name is not None:
            subuser.first_name = display_name.strip()

        if password:
            if len(password) < 4:
                raise ValueError("Password must be at least 4 characters long.")
            subuser.set_password(password)

        if is_active is not None:
            subuser.is_active = bool(is_active)

        subuser.save()

        profile = getattr(subuser, 'profile', None)
        if profile and role and role in UserProfile.Role.values:
            profile.role = role
            profile.save(update_fields=['role'])

        if assigned_project_ids is not None:
            # Update member projects for this subuser
            owner_projects = Category.objects.filter(user=owner)
            for p in owner_projects:
                if p.id in assigned_project_ids or str(p.id) in assigned_project_ids:
                    p.members.add(subuser)
                else:
                    p.members.remove(subuser)

        logger.info("Sub-user updated: id=%s username=%s by owner %s", subuser.id, subuser.username, owner.username)
        return subuser

    @classmethod
    def delete_subuser(cls, owner, subuser_id):
        """Deletes a sub-user account."""
        subuser = User.objects.filter(id=subuser_id, profile__parent_user=owner, profile__is_subuser=True).first()
        if not subuser:
            raise ValueError("Sub-user not found or access denied.")

        username = subuser.username
        # Remove from projects
        for p in subuser.shared_categories.all():
            p.members.remove(subuser)
        # Unassign tasks
        subuser.assigned_tasks.clear()
        subuser.delete()
        logger.info("Sub-user deleted: username=%s by owner %s", username, owner.username)
        return True


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

