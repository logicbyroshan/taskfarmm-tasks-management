from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from todo.models import Category, Task, TaskComment, PreDefinedTask, UserProfile

User = get_user_model()


class ModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )

    def test_user_profile_signal_creation(self):
        """UserProfile is automatically created on User post_save."""
        self.assertTrue(hasattr(self.user, 'profile'))
        self.assertEqual(self.user.profile.theme, UserProfile.Theme.DARK)
        self.assertEqual(self.user.profile.default_task_priority, Task.Priority.MODERATE)
        self.assertEqual(str(self.user.profile), "testuser's Profile")

    def test_category_creation_and_str(self):
        category = Category.objects.create(
            user=self.user,
            name='Engineering',
            color='#3b82f6',
            description='Dev tasks'
        )
        self.assertEqual(str(category), 'Engineering')
        self.assertEqual(category.user, self.user)

    def test_task_creation_and_completed_at_auto_timestamp(self):
        category = Category.objects.create(user=self.user, name='Sprint 1')
        task = Task.objects.create(
            user=self.user,
            category=category,
            title='Write unit tests',
            status=Task.Status.TO_DO,
            priority=Task.Priority.HIGH
        )
        self.assertIsNone(task.completed_at)
        self.assertEqual(str(task), 'Write unit tests')

        # Marking status as DONE automatically sets completed_at
        task.status = Task.Status.DONE
        task.save()
        self.assertIsNotNone(task.completed_at)

        # Marking status back to IN_PROGRESS clears completed_at
        task.status = Task.Status.IN_PROGRESS
        task.save()
        self.assertIsNone(task.completed_at)

    def test_task_save_with_update_fields(self):
        task = Task.objects.create(
            user=self.user,
            title='Update fields test',
            status=Task.Status.TO_DO
        )
        task.status = Task.Status.DONE
        task.save(update_fields=['status'])
        task.refresh_from_db()
        self.assertIsNotNone(task.completed_at)

        task.status = Task.Status.IN_PROGRESS
        task.save(update_fields=['status'])
        task.refresh_from_db()
        self.assertIsNone(task.completed_at)

    def test_task_comment_creation_and_str(self):
        task = Task.objects.create(
            user=self.user,
            title='Refactor architecture'
        )
        comment = TaskComment.objects.create(
            task=task,
            user=self.user,
            content='Great progress so far!'
        )
        self.assertEqual(str(comment), f"Comment by {self.user.username} on {task.title}")
        self.assertEqual(task.comments.count(), 1)

    def test_predefined_task_creation_and_str(self):
        template = PreDefinedTask.objects.create(
            title='Configure CI/CD',
            category=PreDefinedTask.Category.DEVELOPMENT,
            suggested_priority=Task.Priority.HIGH,
            icon='fas fa-code-branch'
        )
        self.assertEqual(str(template), '[development] Configure CI/CD')
