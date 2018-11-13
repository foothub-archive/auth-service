from rest_framework import mixins, viewsets, response, status

from .models import User
from .serializers import UserSerializer
from .permissions import UserPermissions
from .tasks import on_create


class UserViewSet(mixins.ListModelMixin,
                  mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.DestroyModelMixin,
                  viewsets.GenericViewSet):

    model_class = User
    serializer_class = UserSerializer
    permission_classes = (UserPermissions,)

    lookup_field = 'username'

    queryset = model_class.objects.all()

    def list(self, request, *args, **kwargs) -> response.Response:
        return response.Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def perform_create(self, serializer):
        user = serializer.save()
        on_create(user)
