"""
todo/api/views.py

DRF ViewSets and API Views for the TaskFlixx REST API (v1).

Authentication:
  - Session auth for browser-based users (same Django session cookie)
  - JWT Bearer token for external consumers (portfolio sites, admin dashboards, etc.)

All endpoints are under /api/v1/ prefix and use the DRF router.
"""

import csv
import logging

from django.contrib.auth.models import User
from django.http import HttpResponse
from django.db.models import Count, Q
from django.utils import timezone

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django_filters.rest_framework import DjangoFilterBackend

from ..models import Task, Category, TaskComment, PreDefinedTask, UserProfile
from ..serializers import (
    TaskSerializer, TaskListSerializer, TaskWriteSerializer,
    CategorySerializer, TaskCommentSerializer,
    UserStatsSerializer, PreDefinedTaskSerializer, UserProfileSerializer,
)
from ..services import (
    TaskService, CategoryService, SubUserService, ExportService,
    PreDefinedTaskService, StatsService,
)

logger = logging.getLogger('todo')


# ============================================================
#  TASK VIEWSET  /api/v1/tasks/
# ============================================================

class TaskViewSet(viewsets.ModelViewSet):
    """
    Full CRUD for Tasks.

    List:   GET  /api/v1/tasks/?status=&priority=&project=&search=&sort=
    Detail: GET  /api/v1/tasks/{id}/
    Create: POST /api/v1/tasks/
    Update: PUT/PATCH /api/v1/tasks/{id}/
    Delete: DELETE /api/v1/tasks/{id}/

    Custom actions:
      POST /api/v1/tasks/{id}/toggle/      — toggle completion status
      POST /api/v1/tasks/{id}/comment/     — add activity comment
      POST /api/v1/tasks/{id}/checklist/   — replace checklist
      GET  /api/v1/tasks/export/?format=json|csv
    """

    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'priority']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'updated_at', 'due_date', 'title', 'priority']
    ordering = ['-created_at']

    def get_queryset(self):
        """Only return tasks belonging to the authenticated user."""
        qs = TaskService.filter_and_sort(
            user=self.request.user,
            search=self.request.query_params.get('search', ''),
            status=self.request.query_params.get('status', 'all'),
            priority=self.request.query_params.get('priority', 'all'),
            project=self.request.query_params.get('project', 'all'),
            sort=self.request.query_params.get('sort', 'newest'),
        )
        return qs

    def get_serializer_class(self):
        if self.action == 'list':
            return TaskListSerializer
        if self.action in ('create', 'update', 'partial_update'):
            return TaskWriteSerializer
        return TaskSerializer

    def perform_create(self, serializer):
        """Attach the current user and handle category_id resolution with permission checks."""
        if not SubUserService.can_manage_tasks(self.request.user):
            raise PermissionDenied('Permission denied. Viewers cannot create tasks.')

        data = serializer.validated_data.copy()
        category_id = data.pop('category_id', None)
        category = None
        if category_id:
            category = Category.objects.filter(
                Q(pk=category_id) & (Q(user=self.request.user) | Q(members=self.request.user))
            ).first()
            if not category:
                raise ValidationError({'category_id': 'Project not found or you do not have permission to access it.'})
        serializer.save(user=self.request.user, category=category)

    def perform_update(self, serializer):
        """Handle category_id resolution on update with permission checks."""
        if not SubUserService.can_manage_tasks(self.request.user):
            raise PermissionDenied('Permission denied. Viewers cannot update tasks.')

        data = serializer.validated_data.copy()
        category_id = data.pop('category_id', None)

        if 'category_id' in self.request.data:
            category = None
            if category_id:
                category = Category.objects.filter(
                    Q(pk=category_id) & (Q(user=self.request.user) | Q(members=self.request.user))
                ).first()
                if not category:
                    raise ValidationError({'category_id': 'Project not found or you do not have permission to access it.'})
            serializer.save(category=category)
        else:
            serializer.save()

    def perform_destroy(self, instance):
        if not SubUserService.can_manage_tasks(self.request.user):
            raise PermissionDenied('Permission denied. Viewers cannot delete tasks.')
        instance.delete()

    def get_object(self):
        """Ensure users can only access tasks they own, collaborate on, or are assigned to."""
        obj = super().get_object()
        user = self.request.user
        is_owner = (obj.user == user)
        is_project_owner = bool(obj.category and obj.category.user == user)
        is_project_member = bool(obj.category and obj.category.members.filter(pk=user.pk).exists())
        is_assignee = obj.assignees.filter(pk=user.pk).exists()

        if not (is_owner or is_project_owner or is_project_member or is_assignee):
            raise PermissionDenied('You do not have permission to access this task.')
        return obj

    @action(detail=True, methods=['post'], url_path='toggle')
    def toggle(self, request, pk=None):
        """Toggle a task between Done and To Do."""
        if not SubUserService.can_manage_tasks(request.user):
            raise PermissionDenied('Permission denied. Viewers cannot modify tasks.')
        task = self.get_object()
        task = TaskService.toggle_status(task)
        serializer = TaskSerializer(task, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='comment')
    def comment(self, request, pk=None):
        """Post a new activity comment on a task."""
        if not SubUserService.can_manage_tasks(request.user):
            raise PermissionDenied('Permission denied. Viewers cannot post comments.')
        task = self.get_object()
        content = request.data.get('content', '')
        try:
            comment = TaskService.add_comment(task, request.user, content)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = TaskCommentSerializer(comment, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='checklist')
    def checklist(self, request, pk=None):
        """Replace the task checklist with a new list of items."""
        if not SubUserService.can_manage_tasks(request.user):
            raise PermissionDenied('Permission denied. Viewers cannot modify checklists.')
        task = self.get_object()
        checklist = request.data.get('checklist', [])
        if not isinstance(checklist, list):
            return Response(
                {'error': 'checklist must be a list.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        task = TaskService.update_checklist(task, checklist)
        return Response({'checklist': task.checklist, 'success': True})

    @action(detail=False, methods=['get'], url_path='export')
    def export(self, request):
        """
        Export all tasks as JSON or CSV.
        GET /api/v1/tasks/export/?format=json|csv
        """
        fmt = request.query_params.get('format', 'json').lower()
        if fmt == 'csv':
            header, rows = ExportService.tasks_to_csv_rows(request.user)
            response = HttpResponse(content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = 'attachment; filename="taskflixx_export.csv"'
            writer = csv.writer(response)
            writer.writerow(header)
            writer.writerows(rows)
            return response

        data = ExportService.tasks_to_dict_list(request.user)
        return Response({'success': True, 'tasks': data, 'total': len(data)})


# ============================================================
#  CATEGORY VIEWSET  /api/v1/projects/
# ============================================================

class CategoryViewSet(viewsets.ModelViewSet):
    """
    Full CRUD for Projects (Categories).

    List:   GET  /api/v1/projects/
    Detail: GET  /api/v1/projects/{id}/
    Create: POST /api/v1/projects/
    Update: PUT/PATCH /api/v1/projects/{id}/
    Delete: DELETE /api/v1/projects/{id}/
    """

    permission_classes = [IsAuthenticated]
    serializer_class = CategorySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        return (
            Category.objects
            .filter(Q(user=self.request.user) | Q(members=self.request.user))
            .distinct()
            .annotate(
                task_count=Count('tasks', distinct=True),
                completed_count=Count('tasks', filter=Q(tasks__status='completed'), distinct=True)
            )
            .prefetch_related('members')
        )

    def perform_create(self, serializer):
        if not SubUserService.can_create_projects(self.request.user):
            raise PermissionDenied('Permission denied. You do not have permission to create projects.')
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        obj = self.get_object()
        if obj.user != self.request.user:
            raise PermissionDenied('Only the project owner can update project settings.')
        serializer.save()

    def perform_destroy(self, instance):
        if instance.user != self.request.user:
            raise PermissionDenied('Only the project owner can delete this project.')
        instance.delete()

    def get_object(self):
        obj = super().get_object()
        user = self.request.user
        if obj.user != user and not obj.members.filter(pk=user.pk).exists():
            raise PermissionDenied('You do not have permission to access this project.')
        return obj


# ============================================================
#  STATS  /api/v1/stats/
# ============================================================

class StatsAPIView(APIView):
    """
    Returns aggregated task statistics for the authenticated user.

    GET /api/v1/stats/

    Useful for portfolio pages, dashboards, and admin widgets that want
    to display a user's productivity metrics without full task data.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        stats = StatsService.get_stats(request.user)
        serializer = UserStatsSerializer(stats)
        return Response({'success': True, 'stats': serializer.data})


# ============================================================
#  TASK TEMPLATES  /api/v1/templates/
# ============================================================

class PreDefinedTaskViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for the task template library.

    List:   GET /api/v1/templates/?category=website|development|...
    Detail: GET /api/v1/templates/{id}/

    POST /api/v1/templates/{id}/add/ — add a template to user's task pool
    """

    permission_classes = [IsAuthenticated]
    serializer_class = PreDefinedTaskSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category', 'suggested_priority']
    search_fields = ['title']

    def get_queryset(self):
        return PreDefinedTask.objects.all()

    @action(detail=True, methods=['post'], url_path='add')
    def add(self, request, pk=None):
        """Add a predefined task template to the user's task pool."""
        category_id = request.data.get('category_id')
        try:
            task = PreDefinedTaskService.add_to_user_tasks(
                user=request.user,
                predefined_id=pk,
                category_id=category_id,
            )
        except PreDefinedTask.DoesNotExist:
            return Response(
                {'error': 'Template not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = TaskListSerializer(task, context={'request': request})
        return Response({
            'success': True,
            'message': f'Task "{task.title}" added to your tasks.',
            'task': serializer.data,
        }, status=status.HTTP_201_CREATED)


# ============================================================
#  USER PROFILE  /api/v1/profile/
# ============================================================

class UserProfileAPIView(APIView):
    """
    GET/PATCH the authenticated user's profile settings.

    GET   /api/v1/profile/
    PATCH /api/v1/profile/
    """

    permission_classes = [IsAuthenticated]

    def _get_profile(self, user):
        profile, _ = UserProfile.objects.get_or_create(user=user)
        return profile

    def get(self, request):
        profile = self._get_profile(request.user)
        serializer = UserProfileSerializer(profile)
        return Response({
            'username': request.user.username,
            'email': request.user.email,
            'profile': serializer.data,
        })

    def patch(self, request):
        profile = self._get_profile(request.user)
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'success': True, 'profile': serializer.data})


# ============================================================
#  COMMENTS  /api/v1/comments/{id}/
# ============================================================

class TaskCommentDeleteView(APIView):
    """
    DELETE /api/v1/comments/{id}/ — remove a comment (author, task owner, or project owner).
    """

    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            comment = TaskComment.objects.select_related('task', 'task__category').get(pk=pk)
        except TaskComment.DoesNotExist:
            return Response({'error': 'Comment not found.'}, status=status.HTTP_404_NOT_FOUND)

        user = request.user
        is_author = (comment.user == user)
        is_task_owner = (comment.task.user == user)
        is_proj_owner = bool(comment.task.category and comment.task.category.user == user)

        if not (is_author or is_task_owner or is_proj_owner):
            raise PermissionDenied('You do not have permission to delete this comment.')

        comment.delete()
        return Response({'success': True}, status=status.HTTP_204_NO_CONTENT)
