"""
todo/tests/test_notifications.py

Comprehensive tests for TaskFarmm Enterprise Notification & Email Delivery System:
- Model properties & state machine
- Service queuing & email template rendering
- Exponential backoff & retry mechanics
- In-app notification bell & AJAX endpoints
- Management command processing
"""

from unittest.mock import patch
from django.contrib.auth.models import User
from django.core import mail
from django.core.management import call_command
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from todo.models import Task, Category, TaskComment, Notification, UserProfile
from todo.notifications import NotificationService
from todo.services import TaskService


class NotificationSystemTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='alex_coder',
            email='alex@taskfarmm.dev',
            password='TestPassword123!',
            first_name='Alex'
        )
        self.teammate = User.objects.create_user(
            username='sarah_pm',
            email='sarah@taskfarmm.dev',
            password='TestPassword123!',
            first_name='Sarah'
        )
        self.category = Category.objects.create(
            user=self.user,
            name='Alpha Project',
            color='#3b82f6'
        )

    def test_queue_notification_creates_db_record(self):
        notif = NotificationService.queue_notification(
            user=self.user,
            event_type=Notification.EventType.TASK_ASSIGNED,
            title='Assigned to Sprint 12',
            message='You have been assigned to Sprint 12 task',
            action_url='/kanban/',
            context={'task_title': 'Sprint 12', 'project_name': 'Alpha Project'}
        )
        self.assertIsNotNone(notif)
        self.assertEqual(notif.user, self.user)
        self.assertEqual(notif.event_type, Notification.EventType.TASK_ASSIGNED)
        self.assertIn('Sprint 12', notif.html_content)
        self.assertEqual(notif.status, Notification.Status.SENT)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('[TaskFarmm] Assigned to Sprint 12', mail.outbox[0].subject)

    def test_email_delivery_failure_triggers_exponential_backoff(self):
        with patch('django.core.mail.EmailMultiAlternatives.send', side_effect=Exception('SMTP connection timeout')):
            notif = NotificationService.queue_notification(
                user=self.user,
                event_type=Notification.EventType.TASK_DUE_SOON,
                title='Task Due Soon: Release MVP',
                message='MVP is due in 2 hours',
                action_url='/kanban/',
                context={'task_title': 'Release MVP', 'due_date': 'Today'}
            )
            self.assertEqual(notif.status, Notification.Status.PENDING)
            self.assertEqual(notif.retry_count, 1)
            self.assertIn('SMTP connection timeout', notif.last_error)
            self.assertGreater(notif.next_retry_at, timezone.now())

    def test_process_queue_retries_and_succeeds(self):
        # Create a pending failed notification
        notif = Notification.objects.create(
            user=self.user,
            event_type=Notification.EventType.TASK_COMMENT,
            title='New comment on Task',
            message='Great progress!',
            email='alex@taskfarmm.dev',
            html_content='<p>Great progress!</p>',
            status=Notification.Status.FAILED,
            retry_count=1,
            next_retry_at=timezone.now() - timezone.timedelta(minutes=5),
        )

        result = NotificationService.process_queue(batch_size=10)
        self.assertEqual(result['total_processed'], 1)
        self.assertEqual(result['succeeded'], 1)

        notif.refresh_from_db()
        self.assertEqual(notif.status, Notification.Status.SENT)
        self.assertIsNotNone(notif.sent_at)

    def test_in_app_notification_read_toggle(self):
        notif1 = Notification.objects.create(
            user=self.user,
            title='Notice 1',
            message='First notice',
            status=Notification.Status.SENT,
            is_read=False
        )
        notif2 = Notification.objects.create(
            user=self.user,
            title='Notice 2',
            message='Second notice',
            status=Notification.Status.SENT,
            is_read=False
        )

        self.assertEqual(NotificationService.get_unread_count(self.user), 2)

        # Mark single read
        NotificationService.mark_as_read(notif1.id, self.user)
        self.assertEqual(NotificationService.get_unread_count(self.user), 1)

        # Mark all read
        NotificationService.mark_all_as_read(self.user)
        self.assertEqual(NotificationService.get_unread_count(self.user), 0)

    def test_task_comment_queues_notification_to_owner(self):
        task = Task.objects.create(
            user=self.user,
            category=self.category,
            title='Review Architecture',
            priority=Task.Priority.HIGH,
            status=Task.Status.IN_PROGRESS
        )

        # Sarah comments on Alex's task
        TaskService.add_comment(task, self.teammate, 'I reviewed the database schema, looks solid!')

        alex_notifs = Notification.objects.filter(user=self.user, event_type=Notification.EventType.TASK_COMMENT)
        self.assertEqual(alex_notifs.count(), 1)
        self.assertIn('Review Architecture', alex_notifs.first().title)

    def test_task_completion_queues_notification(self):
        task = Task.objects.create(
            user=self.user,
            category=self.category,
            title='Implement Cache Layer',
            status=Task.Status.IN_PROGRESS
        )
        TaskService.toggle_status(task)
        self.assertEqual(task.status, Task.Status.DONE)

        completion_notifs = Notification.objects.filter(user=self.user, event_type=Notification.EventType.TASK_COMPLETED)
        self.assertEqual(completion_notifs.count(), 1)

    def test_api_notification_endpoints(self):
        self.client.force_login(self.user)
        notif = Notification.objects.create(
            user=self.user,
            title='Test Alert',
            message='System maintenance in 1 hour',
            status=Notification.Status.SENT,
            is_read=False
        )

        # List API
        response = self.client.get(reverse('api_notifications_list'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['unread_count'], 1)
        self.assertEqual(len(data['notifications']), 1)

        # Mark Read API
        read_response = self.client.post(reverse('api_notification_mark_read', kwargs={'pk': notif.id}))
        self.assertEqual(read_response.status_code, 200)
        self.assertEqual(read_response.json()['unread_count'], 0)

        # Mark All Read API
        all_read_response = self.client.post(reverse('api_notification_mark_all_read'))
        self.assertEqual(all_read_response.status_code, 200)
        self.assertEqual(all_read_response.json()['unread_count'], 0)

    def test_process_notifications_management_command(self):
        call_command('process_notifications', batch_size=20)
