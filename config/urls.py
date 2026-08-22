from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse

urlpatterns = [
    path('admin/', admin.site.urls),
    path('robots.txt', lambda r: HttpResponse("User-agent: *\nAllow: /\n", content_type="text/plain")),
    # REST API v1
    path('api/v1/', include('todo.api.urls')),
    # Main web application
    path('', include('todo.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)