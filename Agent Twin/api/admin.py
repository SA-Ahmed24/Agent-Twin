"""
Django Admin Configuration
"""
from django.contrib import admin
from .models import WritingStyle, Experience, PersonalInfo, DocumentMemory, UserProfile, VoiceProfile, VoiceShareToken


@admin.register(WritingStyle)
class WritingStyleAdmin(admin.ModelAdmin):
    list_display = ['user_id', 'tone_formality', 'average_sentence_length', 'last_updated']
    list_filter = ['tone_formality', 'last_updated']
    search_fields = ['user_id']


@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    list_display = ['title', 'company', 'user_id', 'memory_type', 'created_at']
    list_filter = ['memory_type', 'detected_from_sample', 'created_at']
    search_fields = ['title', 'company', 'user_id']
    date_hierarchy = 'created_at'


@admin.register(PersonalInfo)
class PersonalInfoAdmin(admin.ModelAdmin):
    list_display = ['user_id', 'key', 'value', 'confidence', 'source', 'updated_at']
    list_filter = ['key', 'source', 'updated_at']
    search_fields = ['user_id', 'key', 'value']


@admin.register(DocumentMemory)
class DocumentMemoryAdmin(admin.ModelAdmin):
    list_display = ['user_id', 'content_type', 'created_at']
    list_filter = ['content_type', 'created_at']
    search_fields = ['user_id']
    date_hierarchy = 'created_at'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'onboarding_completed', 'created_at']
    list_filter = ['onboarding_completed', 'created_at']
    search_fields = ['user__username']


@admin.register(VoiceProfile)
class VoiceProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'tts_service', 'is_active', 'created_at']
    list_filter = ['tts_service', 'is_active', 'created_at']
    search_fields = ['user__username']


@admin.register(VoiceShareToken)
class VoiceShareTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'token', 'name', 'is_active', 'requests_today', 'max_requests_per_day', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['user__username', 'token', 'name']
    readonly_fields = ['token', 'created_at', 'updated_at']
