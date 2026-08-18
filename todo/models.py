# todo/models.py

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Category(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=7, default='#2e86de') # Store hex color

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Categories'


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
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)  # Will store rich HTML content
    
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