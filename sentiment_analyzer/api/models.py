from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

class APIToken(models.Model):
    """Model for API authentication tokens"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_tokens')
    name = models.CharField(max_length=100, help_text="Token name for identification")
    token = models.CharField(max_length=64, unique=True, help_text="API token")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True, help_text="Token expiration date")
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.name}"
    
    def is_expired(self):
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False

class APIRequest(models.Model):
    """Model for tracking API requests"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token = models.ForeignKey(APIToken, on_delete=models.CASCADE, related_name='requests', null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    endpoint = models.CharField(max_length=200, help_text="API endpoint called")
    method = models.CharField(max_length=10, help_text="HTTP method")
    status_code = models.PositiveIntegerField(help_text="HTTP status code")
    response_time = models.FloatField(help_text="Response time in milliseconds")
    ip_address = models.GenericIPAddressField(help_text="Client IP address")
    user_agent = models.TextField(blank=True, help_text="User agent string")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.method} {self.endpoint} - {self.status_code}"

class APILog(models.Model):
    """Model for detailed API logging"""
    LOG_LEVELS = [
        ('debug', 'Debug'),
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request = models.ForeignKey(APIRequest, on_delete=models.CASCADE, related_name='logs')
    level = models.CharField(max_length=10, choices=LOG_LEVELS)
    message = models.TextField(help_text="Log message")
    data = models.JSONField(null=True, blank=True, help_text="Additional log data")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.level.upper()}: {self.message[:50]}..."

class APIConfiguration(models.Model):
    """Model for API configuration settings"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True, help_text="Configuration name")
    value = models.TextField(help_text="Configuration value")
    description = models.TextField(blank=True, help_text="Configuration description")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name}: {self.value[:50]}..."

class APIVersion(models.Model):
    """Model for API version management"""
    version = models.CharField(max_length=20, unique=True, help_text="API version (e.g., v1.0.0)")
    is_current = models.BooleanField(default=False, help_text="Is this the current API version?")
    is_deprecated = models.BooleanField(default=False, help_text="Is this version deprecated?")
    deprecation_date = models.DateTimeField(null=True, blank=True, help_text="Deprecation date")
    end_of_life_date = models.DateTimeField(null=True, blank=True, help_text="End of life date")
    changelog = models.TextField(blank=True, help_text="Version changelog")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"API {self.version}"
    
    def save(self, *args, **kwargs):
        # Ensure only one version is current
        if self.is_current:
            APIVersion.objects.filter(is_current=True).update(is_current=False)
        super().save(*args, **kwargs)