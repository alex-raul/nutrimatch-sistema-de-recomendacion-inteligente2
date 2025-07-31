# nutrimatch_project/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Personalizar títulos del admin
admin.site.site_header = "NutriMatch - Panel de Administración"
admin.site.site_title = "NutriMatch Admin"
admin.site.index_title = "Gestión del Sistema de Recomendación Nutricional"

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # APIs
    path('api/users/', include('users.urls')),
    path('api/nutrition/', include('nutrition.urls')),
    path('api/recommendations/', include('recommendations.urls')),
    
    # Autenticación
    path('auth/', include('authentication.urls')),
    
    # Páginas principales
    path('', include('core.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)