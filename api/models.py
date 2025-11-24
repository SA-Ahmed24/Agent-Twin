"""
Database Models for Agent Twin
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class UserProfile(models.Model):
    """Extended user profile with onboarding status"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    onboarding_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile for {self.user.username}"


class WritingStyle(models.Model):
    """Stores user's writing style characteristics"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='writing_styles')
    average_sentence_length = models.FloatField(default=15.0)
    tone_formality = models.CharField(
        max_length=50,
        choices=[
            ('formal', 'Formal'),
            ('casual', 'Casual'),
            ('professional', 'Professional'),
            ('academic', 'Academic'),
        ],
        default='professional'
    )
    vocabulary_keywords = models.JSONField(default=list, blank=True)  # List of distinctive words/phrases
    signature_phrases = models.JSONField(default=list, blank=True)  # List of unique phrases
    sentence_structure_patterns = models.JSONField(default=dict, blank=True)  # Additional patterns
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user']  # One style per user
        ordering = ['-last_updated']

    def __str__(self):
        return f"WritingStyle for user: {self.user.username}"


class Experience(models.Model):
    """Stores user's experiences, internships, projects, roles"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='experiences')
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255, null=True, blank=True)
    position = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(blank=True)
    achievements = models.JSONField(default=list, blank=True)  # List of achievements
    tech_stack = models.JSONField(default=list, blank=True)  # List of technologies
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    detected_from_sample = models.BooleanField(default=True)
    memory_type = models.CharField(
        max_length=20,
        choices=[
            ('text', 'Text'),
            ('image', 'Image'),
            ('audio', 'Audio'),
        ],
        default='text'
    )
    source_document = models.ForeignKey(
        'DocumentMemory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='experiences'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f"{self.title} - {self.user.username}"


class PersonalInfo(models.Model):
    """Stores personal information as key-value pairs"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='personal_info')
    key = models.CharField(max_length=100)  # e.g., "name", "university", "major", "interests"
    value = models.TextField()  # Can be string or JSON string
    confidence = models.FloatField(default=1.0)  # How certain we are (0.0 to 1.0)
    source = models.CharField(
        max_length=50,
        choices=[
            ('upload', 'Upload'),
            ('generated', 'Generated'),
            ('inferred', 'Inferred'),
        ],
        default='upload'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'key']  # One value per key per user
        ordering = ['key']
        indexes = [
            models.Index(fields=['user', 'key']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.key}: {self.value[:50]}"


class DocumentMemory(models.Model):
    """Stores uploaded documents and their analysis"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='document_memories')
    content_type = models.CharField(
        max_length=20,
        choices=[
            ('text', 'Text'),
            ('image', 'Image'),
            ('audio', 'Audio'),
            ('pdf', 'PDF'),
        ],
        default='text'
    )
    raw_text = models.TextField(null=True, blank=True)  # Extracted text content
    file_path = models.CharField(max_length=500, null=True, blank=True)  # Local file path
    file_url = models.URLField(null=True, blank=True)  # Cloud storage URL (optional)
    gemini_analysis = models.JSONField(default=dict, blank=True)  # Full Gemini response
    extracted_style_signals = models.JSONField(default=dict, blank=True)  # Style extraction results
    extracted_facts = models.JSONField(default=dict, blank=True)  # Facts/experiences extraction results
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f"{self.content_type} document for {self.user.username} - {self.created_at}"


class VoiceProfile(models.Model):
    """Stores user voice samples and voice cloning configuration"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='voice_profile')
    voice_sample_file = models.FileField(upload_to='voice_samples/', null=True, blank=True)
    voice_sample_url = models.URLField(null=True, blank=True)  # For cloud storage
    voice_clone_id = models.CharField(max_length=255, null=True, blank=True)  # ID from TTS service (e.g., ElevenLabs)
    tts_service = models.CharField(
        max_length=50,
        choices=[
            ('web_speech', 'Web Speech API'),
            ('elevenlabs', 'ElevenLabs'),
            ('azure', 'Azure Speech'),
            ('google', 'Google Cloud TTS'),
        ],
        default='web_speech'
    )
    is_active = models.BooleanField(default=False)  # Whether voice cloning is set up
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Voice profile for {self.user.username}"


class VoiceShareToken(models.Model):
    """Shareable token for public voice agent access"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='voice_share_tokens')
    token = models.CharField(max_length=64, unique=True)  # Unique shareable token
    name = models.CharField(max_length=100, blank=True)  # Optional name for the share link
    max_requests_per_day = models.IntegerField(default=50)  # Daily rate limit
    requests_today = models.IntegerField(default=0)  # Current day's request count
    last_reset_date = models.DateField(auto_now_add=True)  # Date when requests_today was last reset
    is_active = models.BooleanField(default=True)  # Can disable without deleting
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['user', 'is_active']),
        ]

    def __str__(self):
        return f"Share token for {self.user.username} - {self.token[:8]}..."

    def can_make_request(self):
        """Check if token can make a request (within rate limit)"""
        from django.utils import timezone
        today = timezone.now().date()
        
        # Reset counter if it's a new day
        if self.last_reset_date < today:
            self.requests_today = 0
            self.last_reset_date = today
            self.save()
        
        return self.is_active and self.requests_today < self.max_requests_per_day

    def increment_request(self):
        """Increment request counter"""
        from django.utils import timezone
        today = timezone.now().date()
        
        # Reset counter if it's a new day
        if self.last_reset_date < today:
            self.requests_today = 0
            self.last_reset_date = today
        
        self.requests_today += 1
        self.save()

    def get_remaining_requests(self):
        """Get remaining requests for today"""
        from django.utils import timezone
        today = timezone.now().date()
        
        # Reset counter if it's a new day
        if self.last_reset_date < today:
            return self.max_requests_per_day
        
        return max(0, self.max_requests_per_day - self.requests_today)
