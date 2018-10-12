from rest_framework import permissions, mixins, viewsets

from .models import User
from .serializers import UserCreationSerializer, UserSerializer
from .permissions import IsUser


class CreateUserViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin):
    permission_classes = (permissions.AllowAny,)
    serializer_class = UserCreationSerializer


class UserViewSet(mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  mixins.DestroyModelMixin,
                  viewsets.GenericViewSet):
    model_class = User
    serializer_class = UserSerializer
    permission_classes = (IsUser,)

    lookup_field = 'username'

    queryset = model_class.objects.all()
