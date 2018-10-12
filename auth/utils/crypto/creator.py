import os
from typing import Tuple
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend


class PemKeyCreator:
    PUBLIC_EXPONENT = 65537

    PRIVATE_KEY_STR = 'private.key'
    PUBLIC_KEY_STR = 'public.key'

    @staticmethod
    def _save_key(key, filepath: str) -> None:
        with open(filepath, 'wb') as fp:
            fp.write(key)

    @classmethod
    def create_key_pair(cls, path: str='') -> Tuple[str, str]:
        key = rsa.generate_private_key(
            backend=default_backend(),
            public_exponent=cls.PUBLIC_EXPONENT,
            key_size=2048
        )

        # get private key (RSA PRIVATE KEY)
        private_key = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        )

        # get public key (RSA PUBLIC KEY)
        public_key = key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.PKCS1
        )

        private_key_path = os.path.join(path, cls.PRIVATE_KEY_STR)
        cls._save_key(private_key, private_key_path)
        public_key_path = os.path.join(path, cls.PUBLIC_KEY_STR)
        cls._save_key(public_key, public_key_path)

        return private_key_path, public_key_path
