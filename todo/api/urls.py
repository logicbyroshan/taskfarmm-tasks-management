"""
todo/api/urls.py

URL routing for the TaskFlixx REST API v1.

All routes are under the /api/v1/ prefix (set in config/urls.py).

Authentication:
  POST /api/v1/auth/token/         — obtain JWT access + refresh tokens
  POST /api/v1/auth/token/refresh/ — refresh an access token

Resources:
  /api/v1/tasks/           — Task CRUD + export, toggle, comment, checklist actions
  /api/v1/projects/        — Project (Category) CRUD
  /api/v1/stats/           — Aggregated user stats
  /api/v1/templates/       — Predefined task template library
  /api/v1/profile/         — User profile settings
  /api/v1/comments/{id}/   — Delete a specific comment
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    TaskViewSet,
    CategoryViewSet,
    StatsAPIView,
    PreDefinedTaskViewSet,
    UserProfileAPIView,
    TaskCommentDeleteView,
)

# DRF router — auto-generates standard CRUD routes for ViewSets
router = DefaultRouter()
router.register(r'tasks', TaskViewSet, basename='api-task')
router.register(r'projects', CategoryViewSet, basename='api-project')
router.register(r'templates', PreDefinedTaskViewSet, basename='api-template')

urlpatterns = [
    # JWT authentication
    path('auth/token/', TokenObtainPairView.as_view(), name='api-token-obtain'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='api-token-refresh'),

    # Aggregated stats
    path('stats/', StatsAPIView.as_view(), name='api-stats'),

    # User profile
    path('profile/', UserProfileAPIView.as_view(), name='api-profile'),

    # Comment management
    path('comments/<int:pk>/', TaskCommentDeleteView.as_view(), name='api-comment-delete'),

    # Router-generated routes (tasks, projects, templates)
    path('', include(router.urls)),
]
