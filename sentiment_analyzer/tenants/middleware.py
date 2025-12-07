from django.http import Http404
from django.shortcuts import get_object_or_404
from .models import Tenant, TenantUser
import threading

# Thread-local storage for tenant context
_thread_locals = threading.local()

class TenantMiddleware:
    """Middleware to identify and set tenant context"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Extract tenant from subdomain or URL parameter
        tenant = self.get_tenant_from_request(request)
        
        if tenant:
            # Set tenant in thread-local storage
            set_current_tenant(tenant)
            request.tenant = tenant
        else:
            # Set default tenant or handle no tenant case
            request.tenant = None
        
        response = self.get_response(request)
        return response
    
    def get_tenant_from_request(self, request):
        """Extract tenant from request (subdomain, URL param, or header)"""
        # Method 1: Subdomain (e.g., tenant1.yourdomain.com)
        host = request.get_host().split(':')[0]
        if '.' in host:
            subdomain = host.split('.')[0]
            if subdomain != 'www':
                try:
                    return Tenant.objects.get(slug=subdomain, is_active=True)
                except Tenant.DoesNotExist:
                    pass
        
        # Method 2: URL parameter (?tenant=slug)
        tenant_slug = request.GET.get('tenant')
        if tenant_slug:
            try:
                return Tenant.objects.get(slug=tenant_slug, is_active=True)
            except Tenant.DoesNotExist:
                pass
        
        # Method 3: Header (X-Tenant-ID)
        tenant_id = request.headers.get('X-Tenant-ID')
        if tenant_id:
            try:
                return Tenant.objects.get(id=tenant_id, is_active=True)
            except Tenant.DoesNotExist:
                pass
        
        # Method 4: Session
        tenant_id = request.session.get('tenant_id')
        if tenant_id:
            try:
                return Tenant.objects.get(id=tenant_id, is_active=True)
            except Tenant.DoesNotExist:
                pass
        
        return None

def get_current_tenant():
    """Get current tenant from thread-local storage"""
    return getattr(_thread_locals, 'tenant', None)

def set_current_tenant(tenant):
    """Set current tenant in thread-local storage"""
    _thread_locals.tenant = tenant

def clear_current_tenant():
    """Clear current tenant from thread-local storage"""
    if hasattr(_thread_locals, 'tenant'):
        delattr(_thread_locals, 'tenant')
