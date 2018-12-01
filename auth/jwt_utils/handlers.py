from typing import Dict
from datetime import datetime

from rest_framework_jwt.settings import api_settings

from users.models import User
from users.serializers import UserJwtPayloadSerializer


def jwt_payload_handler(user: User) -> Dict[str, str]:
    return {
        **UserJwtPayloadSerializer(user).data,
        'exp': datetime.utcnow() + api_settings.JWT_EXPIRATION_DELTA
    }


def jwt_response_payload_handler(token, user=None, request=None):
    return {
        'token': token,
        'user': UserJwtPayloadSerializer(user).data
    }
