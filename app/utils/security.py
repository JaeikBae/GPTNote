"""Security-related helper functions."""

import hashlib
import hmac
import os


def hash_password(password: str, salt: str | None = None) -> str:
    """Return a salted SHA256 password hash."""

    salt_bytes = bytes.fromhex(salt) if salt else os.urandom(16)
    salt_hex = salt or salt_bytes.hex()
    pwd_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt_bytes,
        390000,
    )
    return f"{salt_hex}${pwd_hash.hex()}"


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against a salted hash."""

    try:
        salt_hex, hash_hex = hashed_password.split("$")
    except ValueError:
        return False
    test_hash = hash_password(password, salt=salt_hex).split("$")[1]
    return hmac.compare_digest(test_hash, hash_hex)

