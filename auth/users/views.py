from rest_framework import permissions, mixins, viewsets, response, status

from .models import User
from .serializers import UserCreationSerializer, UserSerializer
from .permissions import IsUser


class CreateUserViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin):
    permission_classes = (permissions.AllowAny,)
    serializer_class = UserCreationSerializer


class UserViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    model_class = User
    serializer_class = UserSerializer
    permission_classes = (IsUser,)

    lookup_field = 'username'

    queryset = model_class.objects.all()

    def list(self, request, *args, **kwargs) -> response.Response:
        return response.Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
