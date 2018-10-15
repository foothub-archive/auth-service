from django.urls import path, include

from auth.views import status_view

urlpatterns = [
    path('', status_view),
    path('jwt/', include('jwt_utils.urls')),
    path('', include('users.urls'))
]
