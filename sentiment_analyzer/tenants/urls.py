from django.urls import path
from . import views

app_name = 'tenants'

urlpatterns = [
    # Tenant management
    path('', views.select_tenant, name='select_tenant'),
    path('create/', views.create_tenant, name='create_tenant'),
    path('switch/<uuid:tenant_id>/', views.switch_tenant, name='switch_tenant'),
    path('dashboard/', views.tenant_dashboard, name='dashboard'),
    
    # File management
    path('files/', views.tenant_files, name='files'),
    path('upload-file/', views.upload_file, name='upload_file'),
    
    # Model management
    path('models/', views.tenant_models, name='models'),
    path('upload-model/', views.upload_model, name='upload_model'),
    
    # Analysis
    path('analyze/', views.analyze_data, name='analyze'),
]
