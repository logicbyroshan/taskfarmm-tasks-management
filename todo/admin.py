from django.contrib import admin
from .models import Task, Category, UserProfile, PreDefinedTask, TaskComment, TaskAttachment, Notification


class TaskCommentInline(admin.TabularInline):
    model = TaskComment
    extra = 0
    readonly_fields = ['created_at']


class TaskAttachmentInline(admin.TabularInline):
    model = TaskAttachment
    extra = 0
    readonly_fields = ['file_size', 'created_at']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'status', 'priority', 'category', 'due_date', 'created_at']
    list_filter = ['status', 'priority', 'category']
    search_fields = ['title', 'description']
    ordering = ['-created_at']
    inlines = [TaskCommentInline, TaskAttachmentInline]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'board_template', 'color', 'created_at']
    list_filter = ['board_template']
    search_fields = ['name']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_subuser', 'parent_user', 'role', 'can_manage_tasks', 'can_create_projects', 'theme', 'default_task_priority']
    list_filter = ['is_subuser', 'role', 'theme']
    search_fields = ['user__username', 'user__email', 'parent_user__username']


@admin.register(PreDefinedTask)
class PreDefinedTaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'suggested_priority']
    list_filter = ['category', 'suggested_priority']
    search_fields = ['title', 'description']


@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    list_display = ['task', 'user', 'created_at']
    search_fields = ['content', 'task__title', 'user__username']
    list_filter = ['created_at']


@admin.register(TaskAttachment)
class TaskAttachmentAdmin(admin.ModelAdmin):
    list_display = ['filename', 'task', 'user', 'file_size', 'created_at']
    search_fields = ['filename', 'task__title', 'user__username']
    list_filter = ['created_at']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'event_type', 'status', 'is_read', 'retry_count', 'created_at']
    list_filter = ['event_type', 'status', 'is_read', 'created_at']
    search_fields = ['title', 'message', 'user__username', 'email']
    ordering = ['-created_at']
