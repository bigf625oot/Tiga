import base64
import hashlib

from cryptography.fernet import Fernet

from app.core.config import settings


def get_cipher_suite():
    # Derive a 32-byte key from the SECRET_KEY
    key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    key_b64 = base64.urlsafe_b64encode(key)
    return Fernet(key_b64)


def encrypt_password(password: str) -> str:
    cipher = get_cipher_suite()
    return cipher.encrypt(password.encode()).decode()


def decrypt_password(encrypted_password: str) -> str:
    cipher = get_cipher_suite()
    return cipher.decrypt(encrypted_password.encode()).decode()
