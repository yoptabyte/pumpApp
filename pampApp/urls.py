from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpRequest, HttpResponse
from django.urls import include, path, re_path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from pamp_app.views import GoogleLoginView, google_callback, index


def health_check(_request: HttpRequest) -> HttpResponse:
    return HttpResponse(status=200)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('pamp_app.urls')),
    path('api/v1/health/', health_check, name='health_check_v1'),
    path('api/v1/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/v1/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/v1/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('auth/', include('dj_rest_auth.urls')),
    path('auth/google/', include('allauth.socialaccount.urls')),
    path('auth/google/callback/', google_callback, name='google_callback'),
    path('auth/google/login/', GoogleLoginView.as_view(), name='google_login'),
    path('social-auth/', include('social_django.urls', namespace='social')),
    re_path(
        r'^(?!api/v1/|admin/|auth/|social-auth/|media/|static/|favicon\.ico$|manifest\.json$|robots\.txt$|logo192\.png$|logo512\.png$).*$',
        index,
        name='frontend',
    ),
]

if settings.DEBUG and not settings.USE_S3_MEDIA_STORAGE:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
