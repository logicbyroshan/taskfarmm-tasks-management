# todo/models.py

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Category(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=7, default='#2e86de')  # Store hex color
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['-created_at']


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

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks'
    )

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)  # Will store rich HTML content
    is_predefined = models.BooleanField(default=False)  # Tracks if task came from a template
    checklist = models.JSONField(default=list, blank=True)  # Trello-style subtasks [{id, text, completed}]

    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.MODERATE
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.TO_DO
    )

    due_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Automatically set completed_at when status is changed to completed/done
        if self.status == self.Status.DONE and not self.completed_at:
            self.completed_at = timezone.now()
        elif self.status != self.Status.DONE:
            self.completed_at = None
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_at']


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

    def __str__(self):
        return f"Comment by {self.user.username} on {self.task.title}"


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
        default=Category.GENERAL
    )
    suggested_priority = models.CharField(
        max_length=10,
        choices=Task.Priority.choices,
        default=Task.Priority.MODERATE
    )
    icon = models.CharField(max_length=50, default='fas fa-tasks')  # FontAwesome icon class

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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


# Auto-create UserProfile when User is created
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)