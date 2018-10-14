from django.urls import path, include


urlpatterns = [
    path('jwt/', include('jwt_utils.urls')),
    path('', include('users.urls'))
]
