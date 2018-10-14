import uuid
from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.contrib.auth.base_user import AbstractBaseUser
from django.utils.deconstruct import deconstructible

from .managers import UserManager


@deconstructible
class UnicodeUsernameValidator(RegexValidator):
    regex = r'^[\w.+-]+$'
    message = 'Enter a valid username. This value may contain only letters, numbers, and ./+/-/_ characters.'
    flags = 0


@deconstructible
class BlackListValidator:
    MESSAGE = 'Username not allowed.'
    CODE = 'invalid'

    def __init__(self, black_list=None):
        self.black_list = black_list if black_list is not None else []

    def __call__(self, value):
        if value in self.black_list:
            raise ValidationError(self.MESSAGE, self.CODE)


UUID4HEX_LEN = 32


def get_default_uuid():
    return uuid.uuid4().hex


class User(AbstractBaseUser):
    USERNAME_FIELD = 'username'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['email']

    BLACKLISTED_USERNAMES = ['me']

    USERNAME_MAX_LEN = 30

    uuid = models.CharField(
        max_length=UUID4HEX_LEN,
        editable=False,
        null=False,
        blank=False,
        unique=True,
        default=get_default_uuid
    )

    email = models.EmailField(
        blank=False,
        null=False,
        unique=True
    )

    username_validator = UnicodeUsernameValidator()
    blacklist_validator = BlackListValidator(BLACKLISTED_USERNAMES)
    username = models.CharField(
        validators=[username_validator, blacklist_validator],
        max_length=USERNAME_MAX_LEN,
        blank=False,
        null=False,
        unique=True,
    )

    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()


class PhoneNumber(models.Model):
    NUMBER_MAX_LEN = 16

    phone_regex = RegexValidator(regex='^\+\d{8,15}$',
                                 message="Phone number format: '+99999999'. Up to 16 digits.")
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=NUMBER_MAX_LEN,
        blank=True,
        unique=True
    )

    user = models.ForeignKey(
        to='users.User',
        on_delete=models.CASCADE,
        related_name='phone_numbers',
        null=False
    )

    class Meta:
        ordering = ['-id']
