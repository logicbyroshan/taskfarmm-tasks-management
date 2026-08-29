"""
todo/notifications.py

Enterprise Notification & Outbound Email Delivery Queue Service for TaskFarmm.
Provides:
  1. In-App Notifications (Bell alert + real-time activity stream)
  2. Queue & Exponential Backoff Retry Engine (30s, 2m, 8m, 30m)
  3. Multi-part Responsive OLED HTML Email Dispatch
"""

import logging
from datetime import timedelta
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags

from .models import Notification

logger = logging.getLogger('todo')


class NotificationService:
    """
    Central orchestration service for in-app alerts and asynchronous queued email dispatch.
    """

    EVENT_TEMPLATE_MAP = {
        Notification.EventType.TASK_ASSIGNED: 'emails/task_assigned.html',
        Notification.EventType.TASK_COMMENT: 'emails/task_comment.html',
        Notification.EventType.TASK_DUE_SOON: 'emails/task_due_soon.html',
        Notification.EventType.TASK_COMPLETED: 'emails/task_completed.html',
        Notification.EventType.PROJECT_SHARED: 'emails/project_shared.html',
        Notification.EventType.WELCOME: 'emails/welcome.html',
    }

    @classmethod
    def should_send_email(cls, user, event_type):
        """Checks user notification preferences."""
        if not user or not user.email:
            return False

        profile = getattr(user, 'profile', None)
        if not profile:
            return True

        if event_type == Notification.EventType.TASK_DUE_SOON:
            return profile.notify_due_date_alerts
        if event_type == Notification.EventType.TASK_ASSIGNED:
            return profile.notify_task_reminders
        if event_type == Notification.EventType.SYSTEM:
            return profile.notify_app_updates

        return True

    @classmethod
    def queue_notification(cls, user, event_type, title, message, action_url='', context=None, send_email=True, immediate=True):
        """
        Creates an in-app notification record and optionally dispatches/queues an outbound HTML email.
        """
        if not user or not user.is_active:
            return None

        ctx = context or {}
        ctx.update({
            'title': title,
            'message': message,
            'action_url': action_url,
            'recipient_name': user.first_name or user.username,
            'recipient_email': user.email,
        })

        # Render HTML email if template exists
        template_name = cls.EVENT_TEMPLATE_MAP.get(event_type, 'emails/base_email.html')
        html_content = ""
        try:
            html_content = render_to_string(template_name, ctx)
        except Exception as e:
            logger.warning('Failed to render email template %s: %s', template_name, e)
            html_content = f"<p>{message}</p>"

        notif = Notification.objects.create(
            user=user,
            event_type=event_type,
            title=title,
            message=message,
            email=user.email or '',
            html_content=html_content,
            action_url=action_url or '',
            status=Notification.Status.PENDING,
            next_retry_at=timezone.now(),
        )

        # Attempt immediate dispatch if enabled and recipient wants emails
        if immediate and send_email and cls.should_send_email(user, event_type):
            cls._deliver_single(notif)

        return notif

    @classmethod
    def _deliver_single(cls, notif):
        """
        Attempts delivering a single notification email with error capture and backoff tracking.
        """
        if not notif.email:
            notif.status = Notification.Status.CANCELLED
            notif.last_error = "No recipient email address provided."
            notif.save(update_fields=['status', 'last_error'])
            return False

        try:
            notif.status = Notification.Status.SENDING
            notif.save(update_fields=['status'])

            plain_text = strip_tags(notif.html_content) or notif.message
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'TaskFarmm <noreply@taskfarmm.com>')

            email_msg = EmailMultiAlternatives(
                subject=f"[TaskFarmm] {notif.title}",
                body=plain_text,
                from_email=from_email,
                to=[notif.email],
            )
            if notif.html_content:
                email_msg.attach_alternative(notif.html_content, "text/html")

            email_msg.send(fail_silently=False)

            notif.status = Notification.Status.SENT
            notif.sent_at = timezone.now()
            notif.last_error = ""
            notif.save(update_fields=['status', 'sent_at', 'last_error'])
            logger.info('Notification email delivered: id=%s to=%s', notif.id, notif.email)
            return True

        except Exception as e:
            logger.error('Failed delivering notification id=%s: %s', notif.id, e)
            notif.retry_count += 1
            notif.last_error = str(e)

            if notif.retry_count >= notif.max_retries:
                notif.status = Notification.Status.FAILED
            else:
                notif.status = Notification.Status.PENDING
                # Exponential backoff: 30s * (2 ** retry_count) -> 60s, 120s, 240s...
                delay_sec = min(3600, 30 * (2 ** notif.retry_count))
                notif.next_retry_at = timezone.now() + timedelta(seconds=delay_sec)

            notif.save(update_fields=['status', 'retry_count', 'last_error', 'next_retry_at'])
            return False

    @classmethod
    def process_queue(cls, batch_size=50):
        """
        Processes pending and retry-eligible notifications in batch.
        """
        now = timezone.now()
        pending_items = list(
            Notification.objects.filter(
                status__in=[Notification.Status.PENDING, Notification.Status.FAILED],
                retry_count__lt=3,
                next_retry_at__lte=now
            ).exclude(email='').order_by('next_retry_at')[:batch_size]
        )

        succeeded = 0
        failed = 0

        for notif in pending_items:
            success = cls._deliver_single(notif)
            if success:
                succeeded += 1
            else:
                failed += 1

        return {
            'total_processed': len(pending_items),
            'succeeded': succeeded,
            'failed': failed,
        }

    @classmethod
    def get_unread(cls, user, limit=20):
        """Fetches latest unread in-app alerts for user."""
        return Notification.objects.filter(user=user, is_read=False).order_by('-created_at')[:limit]

    @classmethod
    def get_unread_count(cls, user):
        """Returns number of unread alerts."""
        if not user.is_authenticated:
            return 0
        return Notification.objects.filter(user=user, is_read=False).count()

    @classmethod
    def mark_as_read(cls, notification_id, user):
        """Marks single notification as read."""
        return Notification.objects.filter(id=notification_id, user=user).update(is_read=True)

    @classmethod
    def mark_all_as_read(cls, user):
        """Marks all user notifications as read."""
        return Notification.objects.filter(user=user, is_read=False).update(is_read=True)
