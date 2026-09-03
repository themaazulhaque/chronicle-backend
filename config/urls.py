from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)


def root_view(request):
    return JsonResponse({
        "status": "success",
        "message": "Chronicle Backend API is running",
        "service": "chronicle-backend"
    })


def health_view(request):
    return JsonResponse({"status": "healthy"})


urlpatterns = [
    path('', root_view, name='root'),
    path('health/', health_view, name='health'),
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('apps.users.urls')),
    path('api/v1/devices/', include('apps.devices.urls')),
    path('api/v1/apps/', include('apps.usage.urls')),
    path('api/v1/usage/', include('apps.usage.usage_urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
