import os
from typing import Callable
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key
from cryptography.hazmat.backends import default_backend


class PemKeyLoader:

    @staticmethod
    def _load_key(filepath: str, load_function: Callable, **kwargs):
        key = None
        if os.path.isfile(filepath):
            with open(filepath, 'rb') as fp:
                key = load_function(fp.read(), **kwargs)

        return key

    @classmethod
    def load_private_key(cls, filepath: str):
        return cls._load_key(filepath, load_pem_private_key, password=None, backend=default_backend())

    @classmethod
    def load_public_key(cls, filepath: str):
        return cls._load_key(filepath, load_pem_public_key, backend=default_backend())
