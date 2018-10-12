import os
from unittest import TestCase

from jwt import encode, decode
from cryptography.hazmat.primitives import serialization

from utils.crypto import PemKeyCreator, PemKeyLoader


class TestJWTKeys(TestCase):
    ALGORITHMS = ['RS256']

    FIXTURES_DIR = 'fixtures'

    def setUp(self):
        if not os.path.isdir(self.FIXTURES_DIR):
            os.mkdir(self.FIXTURES_DIR)

    def tearDown(self):
        for filename in os.listdir(self.FIXTURES_DIR):
            if filename.endswith(".key"):
                os.remove(os.path.join(self.FIXTURES_DIR, filename))

    def test_crypto_creator(self):
        self.assertEqual(os.listdir(self.FIXTURES_DIR), [])
        private_key_path, public_key_path = PemKeyCreator.create_key_pair(self.FIXTURES_DIR)

        self.assertEqual(os.listdir(self.FIXTURES_DIR), [
            'private.key',
            'public.key'
        ])

        self.assertTrue(os.path.isfile(private_key_path))
        self.assertTrue(os.path.isfile(public_key_path))

    def test_crypto_loader_no_keys(self):
        private_key = PemKeyLoader.load_private_key('this_is_not_a_file.key')
        public_key = PemKeyLoader.load_public_key('this_is_not_a_file.key')

        self.assertIsNone(private_key)
        self.assertIsNone(public_key)

    def test_crypto_loader(self):
        private_key_path, public_key_path = PemKeyCreator.create_key_pair(self.FIXTURES_DIR)

        private_key = PemKeyLoader.load_private_key(private_key_path)
        public_key = PemKeyLoader.load_public_key(public_key_path)

        self.assertIsNotNone(private_key)
        self.assertTrue(public_key)

        public_key_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.PKCS1
        )

        private_key_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        )

        payload = {'user_id': 123}
        for algorithm in self.ALGORITHMS:
            token = encode(payload, private_key_bytes, algorithm=algorithm).decode('utf-8')
            decoded_payload = decode(token, public_key_bytes, algorithms=self.ALGORITHMS)
            self.assertEqual(payload, decoded_payload)
