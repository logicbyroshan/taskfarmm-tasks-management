from django.urls import path
from . import views
from . import api_auth

urlpatterns = [
    # Main dashboard (default landing for authenticated users)
    path('', views.dashboard, name='dashboard'),
    
    # Page Views
    path('my-tasks/', views.my_tasks, name='my_tasks'),
    path('projects/', views.task_categories, name='manage_projects'),
    path('categories/', views.task_categories, name='task_categories'),
    path('kanban/', views.manage_kanban, name='manage_kanban'),
    path('settings/', views.settings_page, name='settings'),
    
    # Task CRUD
    path('task/<int:pk>/', views.task_detail, name='task_detail'),
    path('task/create/', views.task_create, name='task_create'),
    path('task/<int:pk>/update/', views.task_update, name='task_update'),
    path('task/<int:pk>/delete/', views.task_delete, name='task_delete'),
    
    # Project / Category CRUD
    path('projects/create/', views.category_create, name='project_create'),
    path('category/create/', views.category_create, name='category_create'),
    path('category/<int:pk>/update/', views.category_update, name='category_update'),
    path('category/<int:pk>/delete/', views.category_delete, name='category_delete'),
    
    # API Authentication & AI Assistant endpoints
    path('api/auth/verify-token/', api_auth.api_verify_token, name='api_verify_token'),
    path('api/auth/create-session/', api_auth.api_create_session, name='api_create_session'),
    path('api/auth/user-info/', api_auth.api_user_info, name='api_user_info'),
    path('api/ai/suggest/', views.api_ai_suggest, name='api_ai_suggest'),
]

# Removed: All authentication URLs (will be handled by another app)