from django.contrib import admin
from .models import APIToken, APIRequest, APILog, APIConfiguration, APIVersion

@admin.register(APIToken)
class APITokenAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'is_active', 'created_at', 'last_used', 'expires_at']
    list_filter = ['is_active', 'created_at', 'expires_at']
    search_fields = ['name', 'user__username', 'user__email']
    readonly_fields = ['token', 'created_at', 'last_used']
    ordering = ['-created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

@admin.register(APIRequest)
class APIRequestAdmin(admin.ModelAdmin):
    list_display = ['method', 'endpoint', 'status_code', 'response_time', 'ip_address', 'created_at']
    list_filter = ['method', 'status_code', 'created_at']
    search_fields = ['endpoint', 'ip_address', 'user_agent']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'token')

@admin.register(APILog)
class APILogAdmin(admin.ModelAdmin):
    list_display = ['level', 'message_short', 'request', 'created_at']
    list_filter = ['level', 'created_at']
    search_fields = ['message', 'data']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    def message_short(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_short.short_description = 'Message'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('request')

@admin.register(APIConfiguration)
class APIConfigurationAdmin(admin.ModelAdmin):
    list_display = ['name', 'value_short', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['name']
    
    def value_short(self, obj):
        return obj.value[:50] + '...' if len(obj.value) > 50 else obj.value
    value_short.short_description = 'Value'

@admin.register(APIVersion)
class APIVersionAdmin(admin.ModelAdmin):
    list_display = ['version', 'is_current', 'is_deprecated', 'deprecation_date', 'created_at']
    list_filter = ['is_current', 'is_deprecated', 'created_at']
    search_fields = ['version', 'changelog']
    readonly_fields = ['created_at']
    ordering = ['-created_at']