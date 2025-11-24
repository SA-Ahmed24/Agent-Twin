"""
API URL Configuration
"""
from django.urls import path
from . import views
from . import auth_views

urlpatterns = [
    # Authentication
    path('auth/signup/', auth_views.signup, name='signup'),
    path('auth/login/', auth_views.login_view, name='login'),
    path('auth/logout/', auth_views.logout_view, name='logout'),
    path('auth/user/', auth_views.current_user, name='current_user'),
    
    # Onboarding
    path('onboarding/upload/', views.onboarding_upload, name='onboarding_upload'),
    path('onboarding/status/', views.onboarding_status, name='onboarding_status'),
    
    # Main API
    path('upload-sample/', views.upload_sample, name='upload_sample'),
    path('generate/', views.generate_content, name='generate'),
    path('memory/view/', views.view_memory, name='view_memory'),
    path('memory/reset/', views.reset_memory, name='reset_memory'),
    
    # Voice Agent
    path('voice/upload-sample/', views.upload_voice_sample, name='upload_voice_sample'),
    path('voice/ask/', views.voice_ask, name='voice_ask'),
    path('voice/profile/', views.voice_profile, name='voice_profile'),
    
    # Public Voice Agent (shareable)
    path('voice/public/<str:token>/ask/', views.public_voice_ask, name='public_voice_ask'),
    path('voice/public/<str:token>/status/', views.public_voice_status, name='public_voice_status'),
    
    # Share Token Management
    path('voice/share/create/', views.create_share_token, name='create_share_token'),
    path('voice/share/list/', views.list_share_tokens, name='list_share_tokens'),
]

