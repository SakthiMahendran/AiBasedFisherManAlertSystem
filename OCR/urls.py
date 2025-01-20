from django.contrib import admin
from django.urls import path, include  # Import 'include' for including app-specific URLs

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('auth_app.urls')),  # Include the URLs of auth_app
    path('api/ai/', include('ai_app.urls')),         # Include the URLs of ai app
]
