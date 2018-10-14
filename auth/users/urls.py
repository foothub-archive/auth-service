from rest_framework import routers
from .views import CreateUserViewSet, UserViewSet


router = routers.SimpleRouter(trailing_slash=False)
router.register(r'create-user', CreateUserViewSet, 'create-user')
router.register(r'users', UserViewSet, 'users')

urlpatterns = router.urls
