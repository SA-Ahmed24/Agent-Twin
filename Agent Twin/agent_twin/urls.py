"""
URL configuration for agent_twin project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from api.views import index, login_page, signup_page, onboarding_page, timeline_page, voice_page, public_voice_page

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('login/', login_page, name='login'),
    path('signup/', signup_page, name='signup'),
    path('onboarding/', onboarding_page, name='onboarding'),
    path('timeline/', timeline_page, name='timeline'),
    path('voice/', voice_page, name='voice'),
    path('voice/public/<str:token>/', public_voice_page, name='public_voice'),
    path('', index, name='index'),  # Frontend (chat)
]

# Serve static files and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / 'frontend' / 'static')
    # Also serve static files from frontend/static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()
