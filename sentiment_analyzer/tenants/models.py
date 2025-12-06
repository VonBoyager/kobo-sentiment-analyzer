from django.db import models
from django.contrib.auth.models import User
import uuid
import os

def tenant_file_path(instance, filename):
    """Generate file path for tenant-specific files"""
    return f'tenants/{instance.tenant.slug}/files/{filename}'

def tenant_model_path(instance, filename):
    """Generate file path for tenant-specific model files"""
    return f'tenants/{instance.tenant.slug}/models/{filename}'

class Tenant(models.Model):
    """Tenant model for multi-tenancy"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_tenants')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    # Database configuration for this tenant
    database_name = models.CharField(max_length=100, unique=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.name.lower().replace(' ', '-')
        if not self.database_name:
            self.database_name = f"tenant_{self.slug}"
        super().save(*args, **kwargs)

class TenantFile(models.Model):
    """Model for storing tenant-specific files (CSV, Excel, etc.)"""
    FILE_TYPES = [
        ('csv', 'CSV'),
        ('excel', 'Excel'),
        ('json', 'JSON'),
        ('txt', 'Text'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='files')
    name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=10, choices=FILE_TYPES)
    file = models.FileField(upload_to=tenant_file_path)
    description = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_size = models.BigIntegerField(default=0)
    
    class Meta:
        ordering = ['-uploaded_at']
        unique_together = ['tenant', 'name']
    
    def __str__(self):
        return f"{self.tenant.name} - {self.name}"
    
    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size
        super().save(*args, **kwargs)
    
    @property
    def file_extension(self):
        return os.path.splitext(self.file.name)[1].lower()

class TenantModel(models.Model):
    """Model for storing tenant-specific ML models (.joblib files)"""
    MODEL_TYPES = [
        ('sentiment', 'Sentiment Analysis'),
        ('classification', 'Classification'),
        ('regression', 'Regression'),
        ('clustering', 'Clustering'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='models')
    name = models.CharField(max_length=255)
    model_type = models.CharField(max_length=20, choices=MODEL_TYPES)
    model_file = models.FileField(upload_to=tenant_model_path)
    description = models.TextField(blank=True)
    version = models.CharField(max_length=50, default='1.0')
    accuracy = models.FloatField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    # Model metadata
    training_data_size = models.IntegerField(null=True, blank=True)
    features_count = models.IntegerField(null=True, blank=True)
    last_trained = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['tenant', 'name', 'version']
    
    def __str__(self):
        return f"{self.tenant.name} - {self.name} v{self.version}"

class TenantUser(models.Model):
    """Model for managing users within tenants"""
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('user', 'User'),
        ('viewer', 'Viewer'),
    ]
    
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='tenant_users')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tenant_memberships')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['tenant', 'user']
    
    def __str__(self):
        return f"{self.user.username} in {self.tenant.name} ({self.role})"