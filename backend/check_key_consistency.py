import base64
import hashlib
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

# Values from .env
env_private_key = "a8DzdwYdmcsQ26H/8c7BgjN1aVq2PlOHO3JvGRsvVGg="
env_device_id = "c285dd8574830ead5fb1b8b7e1052dcc4b9461d1f8f8af27a2717b93d702f7f7"

print(f"Checking consistency...")
print(f"ENV Private Key: {env_private_key}")
print(f"ENV Device ID:   {env_device_id}")

try:
    # Decode private key
    priv_raw = base64.b64decode(env_private_key)
    print(f"Private key length: {len(priv_raw)} bytes")

    if len(priv_raw) != 32:
        print("ERROR: Private key must be 32 bytes!")
    
    # Derive public key
    priv_key = Ed25519PrivateKey.from_private_bytes(priv_raw)
    pub_raw = priv_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    
    # Calculate Device ID (SHA256 of public key)
    derived_id = hashlib.sha256(pub_raw).hexdigest()
    
    print(f"Derived ID:      {derived_id}")
    
    if derived_id == env_device_id:
        print("SUCCESS: Private key matches Device ID.")
    else:
        print("FAILURE: Private key DOES NOT match Device ID!")
        print(f"The private key corresponds to device ID: {derived_id}")

except Exception as e:
    print(f"Error: {e}")
