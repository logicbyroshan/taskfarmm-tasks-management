import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Category(models.Model):

    class BoardTemplate(models.TextChoices):
        SMART = 'smart', 'Smart Work Management (4 Lists)'
        SUPER = 'super', 'Super Work Management (6 Lists)'

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='categories', db_index=True
    )
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=7, default='#2e86de')  # Store hex color
    description = models.TextField(blank=True, null=True)
    board_template = models.CharField(
        max_length=50,
        choices=BoardTemplate.choices,
        default=BoardTemplate.SMART,
    )
    column_names = models.JSONField(default=dict, blank=True)
    members = models.ManyToManyField(
        User, related_name='shared_categories', blank=True
    )
    share_token = models.CharField(
        max_length=64, blank=True, null=True, unique=True, db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    DEFAULT_COLUMN_CONFIGS = {
        'backlog': {'key': 'backlog', 'title': 'Backlog', 'dot_class': 'dot-backlog', 'color': '#8b5cf6'},
        'not-started': {'key': 'not-started', 'title': 'To Do', 'dot_class': 'dot-to-do', 'color': '#ef4444'},
        'in-progress': {'key': 'in-progress', 'title': 'In Progress', 'dot_class': 'dot-in-progress', 'color': '#3b82f6'},
        'on-hold': {'key': 'on-hold', 'title': 'On Hold', 'dot_class': 'dot-on-hold', 'color': '#f59e0b'},
        'completed': {'key': 'completed', 'title': 'Done', 'dot_class': 'dot-done', 'color': '#10b981'},
        'canceled': {'key': 'canceled', 'title': 'Canceled', 'dot_class': 'dot-canceled', 'color': '#6b7280'},
    }

    SMART_KEYS = ['not-started', 'in-progress', 'on-hold', 'completed']
    SUPER_KEYS = ['backlog', 'not-started', 'in-progress', 'on-hold', 'completed', 'canceled']

    def __str__(self):
        return self.name

    def ensure_share_token(self):
        if not self.share_token:
            self.share_token = uuid.uuid4().hex
            self.save(update_fields=['share_token'])
        return self.share_token

    def get_column_title(self, key):
        if self.column_names and isinstance(self.column_names, dict) and key in self.column_names and self.column_names[key]:
            return self.column_names[key]
        default_cfg = self.DEFAULT_COLUMN_CONFIGS.get(key, {})
        return default_cfg.get('title', key.replace('-', ' ').title())

    def get_board_columns(self):
        keys = self.SUPER_KEYS if self.board_template == self.BoardTemplate.SUPER else self.SMART_KEYS
        columns = []
        for k in keys:
            cfg = dict(self.DEFAULT_COLUMN_CONFIGS.get(k, {'key': k, 'title': k, 'dot_class': '', 'color': '#8c9bab'}))
            cfg['title'] = self.get_column_title(k)
            columns.append(cfg)
        return columns

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'name'], name='category_user_name_idx'),
        ]


class Task(models.Model):

    class Priority(models.TextChoices):
        HIGH = 'high', 'High'
        MODERATE = 'moderate', 'Moderate'
        LOW = 'low', 'Low'

    class Status(models.TextChoices):
        BACKLOG = 'backlog', 'Backlog'
        TO_DO = 'not-started', 'To Do'
        IN_PROGRESS = 'in-progress', 'In Progress'
        DONE = 'completed', 'Done'
        ON_HOLD = 'on-hold', 'On Hold'
        CANCELED = 'canceled', 'Canceled'

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='tasks', db_index=True
    )
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='tasks', db_index=True
    )
    assignees = models.ManyToManyField(
        User, related_name='assigned_tasks', blank=True
    )

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    is_predefined = models.BooleanField(default=False)
    checklist_title = models.CharField(max_length=100, default='Checklist', blank=True)
    checklist = models.JSONField(default=list, blank=True)  # [{id, text, completed}]

    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.MODERATE,
        db_index=True,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.TO_DO,
        db_index=True,
    )

    due_date = models.DateField(blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Automatically set completed_at when status changes to completed/done
        if self.status == self.Status.DONE and not self.completed_at:
            self.completed_at = timezone.now()
            if 'update_fields' in kwargs and kwargs['update_fields'] is not None:
                kwargs['update_fields'] = set(kwargs['update_fields']) | {'completed_at'}
        elif self.status != self.Status.DONE and self.completed_at is not None:
            self.completed_at = None
            if 'update_fields' in kwargs and kwargs['update_fields'] is not None:
                kwargs['update_fields'] = set(kwargs['update_fields']) | {'completed_at'}
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            # Most common filter: user + status (dashboard, kanban)
            models.Index(fields=['user', 'status'], name='task_user_status_idx'),
            # Overdue detection: user + due_date
            models.Index(fields=['user', 'due_date'], name='task_user_due_date_idx'),
            # Priority filter
            models.Index(fields=['user', 'priority'], name='task_user_priority_idx'),
            # Category (project) filter
            models.Index(fields=['user', 'category'], name='task_user_category_idx'),
        ]


class TaskComment(models.Model):
    """
    Activity stream comments for Trello-style card discussions.
    """
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='task_comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['task', 'created_at'], name='comment_task_created_idx'),
        ]

    def __str__(self):
        return f"Comment by {self.user.username} on {self.task.title}"


class TaskAttachment(models.Model):
    """
    Uploaded files and paste-to-upload attachments (PDFs, images, documents) associated with a Task.
    """
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='attachments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='task_attachments')
    file = models.FileField(upload_to='task_attachments/%Y/%m/')
    filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField(default=0)  # bytes
    file_type = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['task', 'created_at'], name='task_attach_created_idx'),
        ]

    def __str__(self):
        return f"{self.filename} ({self.task.title})"

    def is_image(self):
        ext = self.filename.split('.')[-1].lower() if '.' in self.filename else ''
        return ext in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'] or self.file_type.startswith('image/')


class PreDefinedTask(models.Model):
    """
    A library of pre-defined task templates that users can pick from
    to quickly populate their task list for a project.
    """
    class Category(models.TextChoices):
        WEBSITE = 'website', 'Website / App Launch'
        MARKETING = 'marketing', 'Marketing'
        DESIGN = 'design', 'Design'
        DEVELOPMENT = 'development', 'Development'
        OPERATIONS = 'operations', 'Operations'
        FINANCE = 'finance', 'Finance'
        HR = 'hr', 'HR / Hiring'
        GENERAL = 'general', 'General'

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(
        max_length=30,
        choices=Category.choices,
        default=Category.GENERAL,
        db_index=True,
    )
    suggested_priority = models.CharField(
        max_length=10,
        choices=Task.Priority.choices,
        default=Task.Priority.MODERATE
    )
    icon = models.CharField(max_length=50, default='fas fa-tasks')

    def __str__(self):
        return f"[{self.category}] {self.title}"

    class Meta:
        ordering = ['category', 'title']


class UserProfile(models.Model):
    """
    Extended user settings and preferences stored per-user.
    """
    class Theme(models.TextChoices):
        DARK = 'dark', 'Dark'
        LIGHT = 'light', 'Light'
        SYSTEM = 'system', 'System'

    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin (Full Task & Project Access)'
        MEMBER = 'member', 'Member (Assigned Projects & Tasks)'
        VIEWER = 'viewer', 'Viewer (Read Only)'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    theme = models.CharField(max_length=10, choices=Theme.choices, default=Theme.DARK)
    notify_task_reminders = models.BooleanField(default=True)
    notify_due_date_alerts = models.BooleanField(default=True)
    notify_app_updates = models.BooleanField(default=False)
    default_task_priority = models.CharField(
        max_length=10,
        choices=Task.Priority.choices,
        default=Task.Priority.MODERATE
    )
    default_task_status = models.CharField(
        max_length=20,
        choices=Task.Status.choices,
        default=Task.Status.TO_DO
    )

    # Sub-user / Team Member Hierarchy (Max 99 per parent account)
    is_subuser = models.BooleanField(default=False, db_index=True)
    parent_user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True,
        related_name='subusers', db_index=True
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)
    can_manage_tasks = models.BooleanField(default=True)
    can_create_projects = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_owner(self):
        return not self.is_subuser

    @property
    def effective_owner(self):
        return self.parent_user if (self.is_subuser and self.parent_user) else self.user

    def get_subuser_count(self):
        if self.is_subuser:
            return 0
        return self.user.subusers.count()

    def __str__(self):
        if self.is_subuser and self.parent_user:
            return f"{self.user.username} (Sub-user of {self.parent_user.username})"
        return f"{self.user.username}'s Profile"



class Notification(models.Model):
    """
    Enterprise Notification & Email Queue Model.
    Tracks in-app notification alerts and outbound email deliveries with retry queue.
    """
    class EventType(models.TextChoices):
        TASK_ASSIGNED = 'task_assigned', 'Task Assigned'
        TASK_COMMENT = 'task_comment', 'Task Comment Added'
        TASK_DUE_SOON = 'task_due_soon', 'Task Due Soon'
        TASK_COMPLETED = 'task_completed', 'Task Completed'
        PROJECT_SHARED = 'project_shared', 'Project Shared'
        WELCOME = 'welcome', 'Welcome to TaskFlixx'
        SYSTEM = 'system', 'System Notification'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SENDING = 'sending', 'Sending'
        SENT = 'sent', 'Sent'
        FAILED = 'failed', 'Failed'
        CANCELLED = 'cancelled', 'Cancelled'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    event_type = models.CharField(max_length=30, choices=EventType.choices, default=EventType.SYSTEM, db_index=True)
    title = models.CharField(max_length=255)
    message = models.TextField()
    email = models.EmailField(blank=True)
    html_content = models.TextField(blank=True)
    action_url = models.CharField(max_length=500, blank=True)
    
    # Delivery Queue & Retry state
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    retry_count = models.PositiveIntegerField(default=0)
    max_retries = models.PositiveIntegerField(default=3)
    last_error = models.TextField(blank=True)
    next_retry_at = models.DateTimeField(default=timezone.now, db_index=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    # In-app bell status
    is_read = models.BooleanField(default=False, db_index=True)
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'next_retry_at']),
            models.Index(fields=['user', 'is_read', '-created_at']),
        ]

    def __str__(self):
        return f"[{self.get_event_type_display()}] {self.title} -> {self.user.username} ({self.status})"


# Auto-create UserProfile when User is created
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)