# todo/api_auth.py
"""
API Authentication for TaskFlix
This module will handle token/session-based authentication from external auth service.
Currently using demo middleware - replace with real API integration later.
"""

from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

User = get_user_model()


@csrf_exempt
def api_verify_token(request):
    """
    API endpoint to verify external auth token.
    
    Expected flow:
    1. External auth service provides token/session
    2. This endpoint validates the token
    3. Returns user info or creates user if needed
    
    TODO: Implement actual token verification with external auth service
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            token = data.get('token')
            
            # TODO: Verify token with external auth service
            # For now, just return demo response
            
            return JsonResponse({
                'success': True,
                'user': {
                    'id': 1,
                    'username': 'demo_user',
                    'email': 'demo@taskflix.com',
                    'first_name': 'Demo',
                    'last_name': 'User'
                }
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    return JsonResponse({
        'success': False,
        'error': 'Method not allowed'
    }, status=405)


@csrf_exempt
def api_create_session(request):
    """
    API endpoint to create session from external auth.
    
    Expected payload:
    {
        "token": "external_auth_token",
        "user_data": {
            "username": "...",
            "email": "...",
            "first_name": "...",
            "last_name": "..."
        }
    }
    
    TODO: Implement proper session creation with external auth validation
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            token = data.get('token')
            user_data = data.get('user_data', {})
            
            # TODO: Verify token with external auth service
            
            # Create or update user
            username = user_data.get('username', 'demo_user')
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': user_data.get('email', ''),
                    'first_name': user_data.get('first_name', ''),
                    'last_name': user_data.get('last_name', '')
                }
            )
            
            # Create session
            from django.contrib.auth import login
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            
            return JsonResponse({
                'success': True,
                'session_id': request.session.session_key,
                'user_id': user.id
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    return JsonResponse({
        'success': False,
        'error': 'Method not allowed'
    }, status=405)


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
