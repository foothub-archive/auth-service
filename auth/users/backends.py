from django.contrib.auth import get_user_model


User = get_user_model()


class UsernameEmailModelBackend:
    def authenticate(self, request, username=None, password=None):
        authenticated_user = None

        if username is not None:
            if '@' in username:
                query_args = {'email': username}
            else:
                query_args = {'username': username}
            try:
                user = User.objects.get(**query_args)
                if user.check_password(password):
                    authenticated_user = user
            except User.DoesNotExist:
                User().set_password(password)

        return authenticated_user
