from django.contrib import admin
from .models import Task, Category, UserProfile, PreDefinedTask


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'status', 'priority', 'category', 'due_date', 'created_at']
    list_filter = ['status', 'priority', 'category']
    search_fields = ['title', 'description']
    ordering = ['-created_at']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'color', 'created_at']
    search_fields = ['name']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'theme', 'default_task_priority']


@admin.register(PreDefinedTask)
class PreDefinedTaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'suggested_priority']
    list_filter = ['category', 'suggested_priority']
    search_fields = ['title', 'description']
