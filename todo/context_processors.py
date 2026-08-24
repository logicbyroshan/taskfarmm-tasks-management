# todo/context_processors.py
from .forms import TaskForm
from .models import Notification

def add_task_form_to_context(request):
    """
    Makes the TaskForm and unread notifications available in the context of every template.
    """
    if request.user.is_authenticated:
        form = TaskForm(user=request.user)
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
        latest_notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:8]
        return {
            'task_create_form': form,
            'unread_notifications_count': unread_count,
            'latest_notifications': latest_notifications,
        }
    return {}