from rest_framework import mixins, viewsets, response, status, decorators, permissions

from rest_framework_jwt.serializers import VerifyJSONWebTokenSerializer

from .models import User
from .serializers import UserSerializer, EmailConfirmationSerializer
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

    @decorators.action(methods=['post'], detail=False,
                       permission_classes=(permissions.AllowAny,), serializer_class=VerifyJSONWebTokenSerializer)
    def confirm_email(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.query_params)

        if not serializer.is_valid():
            return response.Response(
                data={'token': ["This field is missing or not valid."]}, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.object.get('user')
        user.email_confirmed = True
        user.save()
        return response.Response(status=status.HTTP_204_NO_CONTENT)

