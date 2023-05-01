from django.contrib import admin
from django.urls import path, include
from rest_framework.authtoken import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('LittleLemonAPI.urls')),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('api-auth-token/', views.obtain_auth_token),
]
