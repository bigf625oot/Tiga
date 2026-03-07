import pytest
import base64
from app.utils.crypto_utils import encrypt_field, decrypt_field
from app.core.config import settings

def test_encryption_decryption():
    # Setup mock key for testing
    # Ensure it's 32 bytes base64 encoded
    mock_key = base64.b64encode(b'0'*32).decode()
    settings.MASTER_KEY = mock_key
    
    plaintext = "SensitiveData123"
    encrypted = encrypt_field(plaintext)
    
    # Check if encrypted string is not empty and not equal to plaintext
    assert encrypted
    assert encrypted != plaintext
    
    # Decrypt and verify
    decrypted = decrypt_field(encrypted)
    assert decrypted == plaintext

def test_encryption_randomness():
    settings.MASTER_KEY = base64.b64encode(b'0'*32).decode()
    plaintext = "SameData"
    
    # Encrypt same data twice, should be different due to random IV
    enc1 = encrypt_field(plaintext)
    enc2 = encrypt_field(plaintext)
    
    assert enc1 != enc2
    
    # Both should decrypt to same plaintext
    assert decrypt_field(enc1) == plaintext
    assert decrypt_field(enc2) == plaintext

def test_empty_input():
    assert encrypt_field(None) is None
    assert encrypt_field("") == ""
    assert decrypt_field(None) is None
    assert decrypt_field("") == ""
