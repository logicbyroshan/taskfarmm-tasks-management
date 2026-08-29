# todo/middleware.py
import logging
from django.conf import settings
from django.contrib.auth import get_user_model, login

User = get_user_model()
logger = logging.getLogger('todo')

class DemoAuthMiddleware:
    """
    Authentication Middleware for TaskFarmm.
    All pages strictly enforce authentication via @login_required.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

