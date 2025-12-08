from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from frontend import views as frontend_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('tenants/', include('tenants.urls')),
    path('api/', include('api.urls')),
    path('', include('frontend.urls')),
    # path('ml/', include('ml_analysis.urls')),  # Legacy dashboard disabled
    
    # Catch-all for React frontend (SPA routing) - Must be last
    re_path(r'^.*$', frontend_views.home, name='react_fallback'),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
