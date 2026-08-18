# todo/middleware.py
from django.contrib.auth import get_user_model
from django.contrib.auth import login

User = get_user_model()

class DemoAuthMiddleware:
    """
    Temporary middleware to auto-login a demo user.
    This will be replaced by API token/session auth later.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        # Create or get demo user on startup
        self.demo_user = self._get_or_create_demo_user()

    def _get_or_create_demo_user(self):
        """Create a demo user for testing"""
        username = 'demo_user'
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = User.objects.create_user(
                username=username,
                email='demo@taskflix.com',
                password='demo123',  # This won't be used
                first_name='Demo',
                last_name='User'
            )
        return user

    def __call__(self, request):
        # Auto-login demo user if not authenticated
        if not request.user.is_authenticated:
            # Manually set the user in the session
            request.user = self.demo_user
            login(request, self.demo_user, backend='django.contrib.auth.backends.ModelBackend')
        
        response = self.get_response(request)
        return response
