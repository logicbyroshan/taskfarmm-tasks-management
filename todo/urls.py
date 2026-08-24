from django.urls import path
from django.http import JsonResponse
from . import views
from . import api_auth
from . import google_auth

urlpatterns = [
    # Main dashboard
    path('', views.dashboard, name='dashboard'),

    # Page Views
    path('my-tasks/', views.manage_tasks, name='my_tasks'),
    path('manage-tasks/', views.manage_tasks, name='manage_tasks'),
    path('projects/', views.task_categories, name='manage_projects'),
    path('categories/', views.task_categories, name='task_categories'),
    path('kanban/', views.manage_kanban, name='manage_kanban'),
    path('ai-assistant/', views.ai_assistant_page, name='ai_assistant'),
    path('settings/', views.settings_page, name='settings'),
    # Authentication
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('signup/', views.register_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),

    # Google SSO (OAuth2 & GIS)
    path('auth/google/login/', google_auth.google_login, name='google_login'),
    path('auth/google/callback/', google_auth.google_callback, name='google_callback'),
    path('auth/google/credential/', google_auth.google_credential_callback, name='google_credential'),
    path('auth/google/dev-login/', google_auth.google_dev_demo_login, name='google_dev_login'),

    # Task CRUD
    path('task/<int:pk>/', views.task_detail, name='task_detail'),
    path('task/create/', views.task_create, name='task_create'),
    path('task/<int:pk>/update/', views.task_update, name='task_update'),
    path('task/<int:pk>/delete/', views.task_delete, name='task_delete'),
    path('task/<int:pk>/toggle/', views.task_toggle_status, name='task_toggle_status'),
    path('task/<int:pk>/comment/', views.task_add_comment, name='task_add_comment'),
    path('task/comment/<int:pk>/edit/', views.task_comment_edit, name='task_comment_edit'),
    path('task/comment/<int:pk>/delete/', views.task_comment_delete, name='task_comment_delete'),
    path('task/<int:pk>/checklist/', views.task_update_checklist, name='task_update_checklist'),
    path('task/<int:pk>/attachment/', views.task_upload_attachment, name='task_upload_attachment'),
    path('task/attachment/<int:pk>/delete/', views.task_delete_attachment, name='task_delete_attachment'),

    # Project / Category CRUD & Collaboration
    path('projects/create/', views.category_create, name='project_create'),
    path('category/create/', views.category_create, name='category_create'),
    path('category/<int:pk>/update/', views.category_update, name='category_update'),
    path('category/<int:pk>/delete/', views.category_delete, name='category_delete'),
    path('category/<int:pk>/column/rename/', views.category_rename_column, name='category_rename_column'),
    path('project/<int:pk>/share/', views.project_share, name='project_share'),
    path('project/join/<str:token>/', views.project_join, name='project_join'),

    # Predefined Tasks (Template Library)
    path('api/predefined-tasks/', views.predefined_tasks_api, name='predefined_tasks_api'),
    path('api/predefined-tasks/add/', views.add_predefined_task, name='add_predefined_task'),

    # Stats & Export API
    path('api/stats/', views.stats_api, name='stats_api'),
    path('api/export/tasks/', views.tasks_export_api, name='tasks_export_api'),

    # Auth & Health endpoints
    path('api/health/', api_auth.api_health_check, name='api_health'),
    path('api/v1/health/', api_auth.api_health_check, name='api_v1_health'),
    path('api/auth/login/', api_auth.api_auth_login, name='api_auth_login'),
    path('api/auth/me/', api_auth.api_user_info, name='api_auth_me'),
    path('api/auth/csrf/', api_auth.api_auth_csrf, name='api_auth_csrf'),
    path('api/auth/switch-user/', views.switch_user, name='switch_user'),
    path('api/auth/verify-token/', api_auth.api_verify_token, name='api_verify_token'),
    path('api/auth/create-session/', api_auth.api_create_session, name='api_create_session'),
    path('api/auth/user-info/', api_auth.api_user_info, name='api_user_info'),
    path('api/ai/suggest/', views.api_ai_suggest, name='api_ai_suggest'),
    path('api/ai/create-task/', views.ai_create_task, name='ai_create_task'),
    path('api/ai/create-project/', views.ai_create_project, name='ai_create_project'),
    path('api/autocorrect/', views.api_autocorrect, name='api_autocorrect'),

    # In-App Notifications API
    path('api/notifications/', views.api_notifications_list, name='api_notifications_list'),
    path('api/notifications/unread-count/', lambda r: JsonResponse({'unread_count': views.NotificationService.get_unread_count(r.user)}), name='api_notifications_unread_count'),
    path('api/notifications/<int:pk>/read/', views.api_notification_mark_read, name='api_notification_mark_read'),
    path('api/notifications/read-all/', views.api_notification_mark_all_read, name='api_notification_mark_all_read'),
]