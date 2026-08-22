import datetime
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from todo.models import Category, Task, TaskComment, PreDefinedTask
from todo.services import (
    TaskService, CategoryService, ExportService,
    PreDefinedTaskService, StatsService,
)

User = get_user_model()


class ServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='serviceuser',
            email='service@example.com',
            password='password123'
        )
        self.project = Category.objects.create(
            user=self.user,
            name='Product Launch',
            color='#10b981'
        )
        self.task1 = Task.objects.create(
            user=self.user,
            category=self.project,
            title='Setup domain',
            status=Task.Status.DONE,
            priority=Task.Priority.HIGH,
            due_date=timezone.now().date()
        )
        self.task2 = Task.objects.create(
            user=self.user,
            category=self.project,
            title='Deploy to cloud',
            status=Task.Status.IN_PROGRESS,
            priority=Task.Priority.MODERATE,
            due_date=timezone.now().date() - datetime.timedelta(days=2)  # Overdue
        )
        self.task3 = Task.objects.create(
            user=self.user,
            title='General task',
            status=Task.Status.TO_DO,
            priority=Task.Priority.LOW,
            due_date=timezone.now().date()
        )

    def test_dashboard_stats_aggregation(self):
        stats = StatsService.get_stats(self.user)
        self.assertEqual(stats['total_count'], 3)
        self.assertEqual(stats['done_count'], 1)
        self.assertEqual(stats['in_progress_count'], 1)
        self.assertEqual(stats['to_do_count'], 1)
        self.assertEqual(stats['overdue_count'], 1)
        self.assertEqual(stats['due_today_count'], 1)
        self.assertEqual(stats['completion_rate'], 33)

    def test_filter_and_sort(self):
        # Search
        qs = TaskService.filter_and_sort(self.user, search='Setup')
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().title, 'Setup domain')

        # Status filter
        qs_done = TaskService.filter_and_sort(self.user, status=Task.Status.DONE)
        self.assertEqual(qs_done.count(), 1)

        # Priority filter
        qs_high = TaskService.filter_and_sort(self.user, priority=Task.Priority.HIGH)
        self.assertEqual(qs_high.count(), 1)

        # Project filter
        qs_proj = TaskService.filter_and_sort(self.user, project=str(self.project.id))
        self.assertEqual(qs_proj.count(), 2)

        qs_none = TaskService.filter_and_sort(self.user, project='none')
        self.assertEqual(qs_none.count(), 1)

    def test_kanban_columns_grouping(self):
        data = TaskService.get_kanban_columns(self.user, project_id=self.project.id)
        self.assertEqual(data['selected_project'].id, self.project.id)
        self.assertEqual(data['columns']['completed'].count(), 1)
        self.assertEqual(data['columns']['in-progress'].count(), 1)

    def test_task_operations(self):
        # Toggle
        TaskService.toggle_status(self.task3)
        self.task3.refresh_from_db()
        self.assertEqual(self.task3.status, Task.Status.DONE)

        TaskService.toggle_status(self.task3)
        self.task3.refresh_from_db()
        self.assertEqual(self.task3.status, Task.Status.TO_DO)

        # Checklist update
        checklist_items = [{'id': '1', 'text': 'Subtask 1', 'completed': True}]
        TaskService.update_checklist(self.task3, checklist_items)
        self.task3.refresh_from_db()
        self.assertEqual(self.task3.checklist, checklist_items)

        # Add comment
        comment = TaskService.add_comment(self.task3, self.user, 'Status update comment')
        self.assertEqual(comment.content, 'Status update comment')

    def test_category_service_and_progress(self):
        categories = CategoryService.get_with_stats(self.user)
        cat = categories[0]
        self.assertEqual(cat.task_count, 2)
        self.assertEqual(cat.completed_count, 1)
        self.assertEqual(cat.progress, 50)

        proj_progress = CategoryService.get_dashboard_project_progress(self.user)
        self.assertEqual(len(proj_progress), 1)
        self.assertEqual(proj_progress[0]['progress'], 50)

    def test_export_service(self):
        dict_list = ExportService.tasks_to_dict_list(self.user)
        self.assertEqual(len(dict_list), 3)

        header, rows = ExportService.tasks_to_csv_rows(self.user)
        self.assertIn('Title', header)
        self.assertEqual(len(rows), 3)

    def test_predefined_task_service(self):
        template = PreDefinedTask.objects.create(
            title='Setup SEO',
            category='marketing',
            suggested_priority='moderate',
            description='Meta tags and sitemap'
        )
        task = PreDefinedTaskService.add_to_user_tasks(
            user=self.user,
            predefined_id=template.id,
            category_id=self.project.id
        )
        self.assertEqual(task.title, 'Setup SEO')
        self.assertEqual(task.category, self.project)
        self.assertTrue(task.is_predefined)
