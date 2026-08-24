# todo/middleware.py
import logging
from django.conf import settings
from django.contrib.auth import get_user_model, login

User = get_user_model()
logger = logging.getLogger('todo')

class DemoAuthMiddleware:
    """
    Middleware to auto-login a demo user for seamless interactive testing.
    Can be enabled/disabled via ENABLE_DEMO_AUTH in settings or environment.
    Runs lazily without executing DB queries during server initialization.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def _get_or_create_demo_user(self):
        """Lazily create or get a demo user with safe database exception handling."""
        username = 'demo_user'
        try:
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': 'demo@taskflix.com',
                    'first_name': 'Demo',
                    'last_name': 'User'
                }
            )
            return user
        except Exception as e:
            logger.debug('DemoAuthMiddleware could not get or create demo user: %s', e)
            return None

    def __call__(self, request):
        enable_demo = getattr(settings, 'ENABLE_DEMO_AUTH', False)
        
        # Don't auto-login on admin, auth pages (login/register), logout, or explicit API auth paths
        exempt_prefixes = ('/admin/', '/login/', '/register/', '/signup/', '/logout/', '/api/v1/auth/', '/api/auth/')
        is_exempt_path = any(request.path.startswith(prefix) for prefix in exempt_prefixes)

        if enable_demo and not is_exempt_path and not request.user.is_authenticated:
            demo_user = self._get_or_create_demo_user()
            if demo_user:
                request.user = demo_user
                login(request, demo_user, backend='django.contrib.auth.backends.ModelBackend')

        return self.get_response(request)
