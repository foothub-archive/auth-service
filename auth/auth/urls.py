from django.urls import path, include


urlpatterns = [
    path('jwt/', include('jwt_views')),
    path('', include('users.routers'))
]
