from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import Tenant, TenantFile, TenantModel, TenantUser
from .middleware import get_current_tenant, set_current_tenant
import pandas as pd
import joblib
import os
import json

@login_required
def tenant_dashboard(request):
    """Main tenant dashboard"""
    tenant = get_current_tenant()
    if not tenant:
        return redirect('tenants:select_tenant')
    
    # Get tenant statistics
    files_count = TenantFile.objects.filter(tenant=tenant).count()
    users_count = TenantUser.objects.filter(tenant=tenant, is_active=True).count()
    
    # Only show model info to admins
    models_count = 0
    recent_models = []
    if request.user.is_staff:
        models_count = TenantModel.objects.filter(tenant=tenant, is_active=True).count()
        recent_models = TenantModel.objects.filter(tenant=tenant, is_active=True).order_by('-created_at')[:5]
    
    context = {
        'tenant': tenant,
        'files_count': files_count,
        'models_count': models_count,
        'users_count': users_count,
        'recent_files': TenantFile.objects.filter(tenant=tenant).order_by('-uploaded_at')[:5],
        'recent_models': recent_models,
        'is_admin': request.user.is_staff,
    }
    return render(request, 'tenants/dashboard.html', context)

@login_required
def select_tenant(request):
    """Tenant selection page"""
    user_tenants = TenantUser.objects.filter(user=request.user, is_active=True).select_related('tenant')
    owned_tenants = Tenant.objects.filter(owner=request.user, is_active=True)
    
    context = {
        'user_tenants': user_tenants,
        'owned_tenants': owned_tenants,
    }
    return render(request, 'tenants/select_tenant.html', context)

@login_required
def switch_tenant(request, tenant_id):
    """Switch to a specific tenant"""
    tenant = get_object_or_404(Tenant, id=tenant_id, is_active=True)
    
    # Check if user has access to this tenant
    if not TenantUser.objects.filter(tenant=tenant, user=request.user, is_active=True).exists():
        if tenant.owner != request.user:
            messages.error(request, 'You do not have access to this tenant.')
            return redirect('tenants:select_tenant')
    
    # Set tenant in session
    request.session['tenant_id'] = str(tenant.id)
    set_current_tenant(tenant)
    
    messages.success(request, f'Switched to tenant: {tenant.name}')
    return redirect('tenants:dashboard')

@login_required
def tenant_files(request):
    """Manage tenant files"""
    tenant = get_current_tenant()
    if not tenant:
        return redirect('tenants:select_tenant')
    
    files = TenantFile.objects.filter(tenant=tenant).order_by('-uploaded_at')
    
    context = {
        'tenant': tenant,
        'files': files,
    }
    return render(request, 'tenants/files.html', context)

@login_required
def upload_file(request):
    """Upload a new file for the tenant"""
    tenant = get_current_tenant()
    if not tenant:
        return redirect('tenants:select_tenant')
    
    if request.method == 'POST':
        file = request.FILES.get('file')
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        
        if file and name:
            # Determine file type
            file_extension = os.path.splitext(file.name)[1].lower()
            if file_extension == '.csv':
                file_type = 'csv'
            elif file_extension in ['.xlsx', '.xls']:
                file_type = 'excel'
            elif file_extension == '.json':
                file_type = 'json'
            elif file_extension == '.txt':
                file_type = 'txt'
            else:
                file_type = 'other'
            
            # Create tenant file
            tenant_file = TenantFile.objects.create(
                tenant=tenant,
                name=name,
                file_type=file_type,
                file=file,
                description=description,
                uploaded_by=request.user
            )
            
            messages.success(request, f'File "{name}" uploaded successfully!')
            return redirect('tenants:files')
        else:
            messages.error(request, 'Please provide both file and name.')
    
    return render(request, 'tenants/upload_file.html', {'tenant': tenant})

@login_required
def tenant_models(request):
    """Manage tenant ML models - Admin only"""
    if not request.user.is_staff:
        messages.error(request, 'Access denied. This feature is only available to administrators.')
        return redirect('tenants:dashboard')
    
    tenant = get_current_tenant()
    if not tenant:
        return redirect('tenants:select_tenant')
    
    models = TenantModel.objects.filter(tenant=tenant, is_active=True).order_by('-created_at')
    
    context = {
        'tenant': tenant,
        'models': models,
    }
    return render(request, 'tenants/admin_models.html', context)

@login_required
def upload_model(request):
    """Upload a new ML model for the tenant - Admin only"""
    if not request.user.is_staff:
        messages.error(request, 'Access denied. This feature is only available to administrators.')
        return redirect('tenants:dashboard')
    
    tenant = get_current_tenant()
    if not tenant:
        return redirect('tenants:select_tenant')
    
    if request.method == 'POST':
        model_file = request.FILES.get('model_file')
        name = request.POST.get('name')
        model_type = request.POST.get('model_type')
        description = request.POST.get('description', '')
        version = request.POST.get('version', '1.0')
        
        if model_file and name and model_type:
            # Create tenant model
            tenant_model = TenantModel.objects.create(
                tenant=tenant,
                name=name,
                model_type=model_type,
                model_file=model_file,
                description=description,
                version=version,
                created_by=request.user
            )
            
            messages.success(request, f'Model "{name}" uploaded successfully!')
            return redirect('tenants:models')
        else:
            messages.error(request, 'Please provide model file, name, and type.')
    
    context = {
        'tenant': tenant,
        'model_types': TenantModel.MODEL_TYPES,
    }
    return render(request, 'tenants/upload_model.html', context)

@login_required
def analyze_data(request):
    """Analyze tenant data using their models - Admin only"""
    if not request.user.is_staff:
        messages.error(request, 'Access denied. This feature is only available to administrators.')
        return redirect('tenants:dashboard')
    
    tenant = get_current_tenant()
    if not tenant:
        return redirect('tenants:select_tenant')
    
    if request.method == 'POST':
        file_id = request.POST.get('file_id')
        model_id = request.POST.get('model_id')
        text_data = request.POST.get('text_data', '')
        
        try:
            # Get the file and model
            tenant_file = get_object_or_404(TenantFile, id=file_id, tenant=tenant)
            tenant_model = get_object_or_404(TenantModel, id=model_id, tenant=tenant, is_active=True)
            
            # Load the model
            model_path = tenant_model.model_file.path
            model = joblib.load(model_path)
            
            # Process data based on file type
            if tenant_file.file_type == 'csv':
                df = pd.read_csv(tenant_file.file.path)
                # Add your analysis logic here
                results = {'message': 'CSV analysis completed', 'rows': len(df)}
            elif text_data:
                # Analyze text data
                prediction = model.predict([text_data])
                results = {'prediction': prediction[0], 'text': text_data}
            else:
                results = {'error': 'No data provided for analysis'}
            
            return JsonResponse(results)
            
        except Exception as e:
            return JsonResponse({'error': str(e)})
    
    # Get available files and models
    files = TenantFile.objects.filter(tenant=tenant)
    models = TenantModel.objects.filter(tenant=tenant, is_active=True)
    
    context = {
        'tenant': tenant,
        'files': files,
        'models': models,
    }
    return render(request, 'tenants/analyze.html', context)

@login_required
def create_tenant(request):
    """Create a new tenant"""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        
        if name:
            try:
                tenant = Tenant.objects.create(
                    name=name,
                    description=description,
                    owner=request.user
                )
                
                # Add owner as tenant user
                TenantUser.objects.create(
                    tenant=tenant,
                    user=request.user,
                    role='owner'
                )
                
                messages.success(request, f'Tenant "{name}" created successfully!')
                return redirect('tenants:select_tenant')
            except Exception as e:
                messages.error(request, f'Error creating tenant: {str(e)}')
        else:
            messages.error(request, 'Please provide a tenant name.')
    
    return render(request, 'tenants/create_tenant.html')