"""
Authentication Views for Agent Twin
"""
import json
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import UserProfile


@csrf_exempt
@require_http_methods(["POST"])
def signup(request):
    """
    User signup endpoint.
    
    Accepts:
    - POST with JSON: {"username": "...", "email": "...", "password": "..."}
    
    Returns:
    - JSON with user info and onboarding status
    """
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = {
                'username': request.POST.get('username'),
                'email': request.POST.get('email'),
                'password': request.POST.get('password')
            }
        
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        # Validation
        if not username or not password:
            return JsonResponse({
                'error': 'Username and password are required'
            }, status=400)
        
        if User.objects.filter(username=username).exists():
            return JsonResponse({
                'error': 'Username already exists'
            }, status=400)
        
        if email and User.objects.filter(email=email).exists():
            return JsonResponse({
                'error': 'Email already exists'
            }, status=400)
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        
        # Create profile
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        # Auto-login
        login(request, user)
        
        return JsonResponse({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            },
            'onboarding_completed': profile.onboarding_completed
        })
    
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def login_view(request):
    """
    User login endpoint.
    
    Accepts:
    - POST with JSON: {"username": "...", "password": "..."}
    
    Returns:
    - JSON with user info
    """
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = {
                'username': request.POST.get('username'),
                'password': request.POST.get('password')
            }
        
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return JsonResponse({
                'error': 'Username and password are required'
            }, status=400)
        
        # Authenticate
        user = authenticate(request, username=username, password=password)
        
        if user is None:
            return JsonResponse({
                'error': 'Invalid username or password'
            }, status=401)
        
        # Login
        login(request, user)
        
        # Get profile
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        return JsonResponse({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            },
            'onboarding_completed': profile.onboarding_completed
        })
    
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def logout_view(request):
    """Logout endpoint"""
    logout(request)
    return JsonResponse({
        'success': True,
        'message': 'Logged out successfully'
    })


@require_http_methods(["GET"])
def current_user(request):
    """
    Get current authenticated user.
    
    Returns:
    - JSON with user info or 401 if not authenticated
    """
    if not request.user.is_authenticated:
        return JsonResponse({
            'authenticated': False
        }, status=401)
    
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    return JsonResponse({
        'authenticated': True,
        'user': {
            'id': request.user.id,
            'username': request.user.username,
            'email': request.user.email
        },
        'onboarding_completed': profile.onboarding_completed
    })

