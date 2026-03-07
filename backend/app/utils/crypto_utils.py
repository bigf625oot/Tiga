import base64
import os
from typing import Optional
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
from app.core.config import settings

def _get_key() -> bytes:
    if not settings.MASTER_KEY:
        # Fallback for dev/test if not set, but strictly should raise
        # For this task, I will raise to enforce requirement
        if settings.LOG_LEVEL == "DEBUG": # Allow a default for testing if absolutely needed, but better to fail secure
             pass
        raise ValueError("MASTER_KEY environment variable is not set")
    try:
        key = base64.b64decode(settings.MASTER_KEY)
        if len(key) != 32:
             raise ValueError(f"MASTER_KEY must be 32 bytes (256 bits) when decoded, got {len(key)}")
        return key
    except Exception as e:
        raise ValueError(f"Invalid MASTER_KEY: {e}")

def encrypt_field(plaintext: str) -> str:
    """
    Encrypts a string using AES-256-CBC.
    IV is generated randomly and prepended to the ciphertext.
    Output is base64 encoded.
    """
    if not plaintext:
        return plaintext
    
    try:
        key = _get_key()
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        
        # PKCS7 padding
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(plaintext.encode('utf-8')) + padder.finalize()
        
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        
        # Return base64(iv + ciphertext)
        return base64.b64encode(iv + ciphertext).decode('utf-8')
    except Exception as e:
        # In production, log this securely
        raise ValueError(f"Encryption failed: {str(e)}")

def decrypt_field(ciphertext: str) -> str:
    """
    Decrypts a base64 encoded string (iv + ciphertext) using AES-256-CBC.
    """
    if not ciphertext:
        return ciphertext
        
    try:
        data = base64.b64decode(ciphertext)
        if len(data) < 16:
            raise ValueError("Invalid ciphertext length")
            
        iv = data[:16]
        actual_ciphertext = data[16:]
        
        key = _get_key()
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        
        padded_plaintext = decryptor.update(actual_ciphertext) + decryptor.finalize()
        
        unpadder = padding.PKCS7(128).unpadder()
        plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()
        
        return plaintext.decode('utf-8')
    except Exception as e:
        raise ValueError(f"Decryption failed: {str(e)}")
