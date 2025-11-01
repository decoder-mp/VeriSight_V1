import hashlib
import os

def hash_passkey(passkey: str) -> str:
    """Hash a passkey using SHA-256 with a random salt."""
    salt = os.urandom(16).hex()
    hashed = hashlib.sha256((salt + passkey).encode("utf-8")).hexdigest()
    return f"{salt}${hashed}"

def verify_passkey(stored_hash: str, provided_passkey: str) -> bool:
    """Verify if the provided passkey matches the stored hash."""
    try:
        salt, hashed = stored_hash.split("$")
        check_hash = hashlib.sha256((salt + provided_passkey).encode("utf-8")).hexdigest()
        return check_hash == hashed
    except ValueError:
        return False
