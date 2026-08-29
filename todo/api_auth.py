# todo/api_auth.py
"""
API Authentication for TaskFarmm
Handles token/session-based authentication and bridges JWT auth with Django session login.
"""

import json
import logging
from django.conf import settings
from django.contrib.auth import get_user_model, login, authenticate
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

User = get_user_model()
logger = logging.getLogger('todo')


@csrf_exempt
def api_verify_token(request):
    """
    API endpoint to verify a JWT access token.
    Decodes the token using SimpleJWT, retrieves the corresponding User,
    and returns their profile details.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        token_str = data.get('token', '').strip()
        if not token_str:
            return JsonResponse({'success': False, 'error': 'Token is required'}, status=400)

        # Decode and validate JWT
        try:
            token = AccessToken(token_str)
            user_id = token['user_id']
            user = User.objects.get(id=user_id)
        except (InvalidToken, TokenError, User.DoesNotExist) as e:
            if settings.DEBUG and getattr(settings, 'ENABLE_DEMO_AUTH', False) and token_str == 'demo-token':
                user, _ = User.objects.get_or_create(username='demo_user', defaults={'email': 'demo@taskfarm.com'})
            else:
                return JsonResponse({'success': False, 'error': 'Invalid or expired token'}, status=401)

        if not user.is_active:
            return JsonResponse({'success': False, 'error': 'Account is disabled.'}, status=401)

        return JsonResponse({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }
        })
    except Exception as e:
        logger.warning('Token verification error: %s', e)
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
def api_create_session(request):
    """
    API endpoint to create a Django session from a valid JWT access token.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        token_str = data.get('token', '').strip()
        user_data = data.get('user_data', {})

        if not token_str:
            return JsonResponse({'success': False, 'error': 'Token is required'}, status=400)

        try:
            token = AccessToken(token_str)
            user_id = token['user_id']
            user = User.objects.get(id=user_id)
        except (InvalidToken, TokenError, User.DoesNotExist):
            if settings.DEBUG and getattr(settings, 'ENABLE_DEMO_AUTH', False) and token_str == 'demo-token':
                username = user_data.get('username', 'demo_user')
                user, _ = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'email': user_data.get('email', ''),
                        'first_name': user_data.get('first_name', ''),
                        'last_name': user_data.get('last_name', '')
                    }
                )
            else:
                return JsonResponse({'success': False, 'error': 'Invalid or expired token'}, status=401)

        if not user.is_active:
            return JsonResponse({'success': False, 'error': 'Account is disabled.'}, status=401)

        login(request, user, backend='django.contrib.auth.backends.ModelBackend')

        if not request.session.session_key:
            request.session.save()

        return JsonResponse({
            'success': True,
            'session_id': request.session.session_key,
            'user_id': user.id,
            'username': user.username
        })
    except Exception as e:
        logger.warning('Session creation error: %s', e)
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


def api_user_info(request):
    """
    Get current user information from session.
    """
    if request.user.is_authenticated:
        return JsonResponse({
            'success': True,
            'user': {
                'id': request.user.id,
                'username': request.user.username,
                'email': request.user.email,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name
            }
        })

    return JsonResponse({
        'success': False,
        'error': 'Not authenticated'
    }, status=401)


@csrf_exempt
def api_auth_login(request):
    """
    Direct API login endpoint accepting JSON credentials.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
    try:
        data = json.loads(request.body) if request.body else request.POST
        login_input = data.get('username') or data.get('email', '').strip()
        password = data.get('password', '').strip()

        if not login_input or not password:
            return JsonResponse({'success': False, 'error': 'Username/Email and password required'}, status=400)

        # Authenticate by username or email
        user = None
        if '@' in login_input:
            user_obj = User.objects.filter(email__iexact=login_input).first()
            if user_obj:
                user = authenticate(request, username=user_obj.username, password=password)
        if not user:
            user = authenticate(request, username=login_input, password=password)

        if user is None:
            return JsonResponse({'success': False, 'error': 'Invalid credentials'}, status=401)

        if not user.is_active:
            return JsonResponse({'success': False, 'error': 'Account is inactive'}, status=403)

        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        return JsonResponse({
            'success': True,
            'message': 'Logged in successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'name': user.get_full_name() or user.username
            }
        })
    except Exception as e:
        logger.error('API login error: %s', e)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def api_auth_csrf(request):
    """Returns CSRF token for API clients."""
    from django.middleware.csrf import get_token
    token = get_token(request)
    return JsonResponse({'csrfToken': token, 'success': True})


def api_health_check(request):
    """Health check endpoint for monitoring."""
    return JsonResponse({
        'status': 'healthy',
        'app': 'TaskFarmm',
        'version': '2.0.0',
    })
