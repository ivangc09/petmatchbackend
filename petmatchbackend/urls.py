from django.contrib import admin
from django.conf import settings
from django.urls import path, include
from django.conf.urls.static import static
from rest_framework.response import Response

def _ping(request):
    return Response({"ok": "true"}, status=200)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/_ping/', _ping),
    
    #path('api/auth/', include('dj_rest_auth.urls')),
    #path('api/auth/registration/', include('dj_rest_auth.registration.urls')),

    path('api/auth/social/', include('allauth.socialaccount.urls')),
    path('api/auth/', include('users.urls')),
    path('api/mascotas/', include('pets.urls')),
    path('api/chat/', include('chat.urls')),
]
