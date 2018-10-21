from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(min_length=8, write_only=True)

    def create(self, validated_data):
        return User.objects.create_user(validated_data['email'],
                                        validated_data['username'],
                                        validated_data['password'])

    class Meta:
        model = User
        fields = ('uuid', 'username', 'email', 'password')


UserJwtPayloadSerializer = UserSerializer
