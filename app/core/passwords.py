from passlib.context import CryptContext
import hashlib

# Use Argon2 via passlib for new hashes. Keep a bcrypt context as a fallback
# so existing accounts hashed with the previous pre-hash+bcrypt strategy
# continue to authenticate without requiring an immediate DB migration.
argon_context = CryptContext(schemes=["argon2"], deprecated="auto")
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _pre_hash(password: str) -> str:
    if password is None:
        password = ""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def hash_password(password: str) -> str:
    """Hash a password using Argon2 (via passlib)."""
    if password is None:
        password = ""
    return argon_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against the stored hash.

    Tries Argon2 first (new hashes). If that fails and the stored hash looks
    like a bcrypt hash, attempts the legacy pre-hash (SHA-256) + bcrypt
    verification. This ensures existing users can still log in.
    """
    if plain_password is None:
        plain_password = ""
    if not hashed_password:
        return False

    # Try Argon2
    try:
        if argon_context.verify(plain_password, hashed_password):
            return True
    except Exception:
        # argon verify may raise on malformed hashes; ignore and try fallback
        pass

    # Fallback: if stored hash is bcrypt, verify against pre-hash
    try:
        if bcrypt_context.identify(hashed_password):
            pre = _pre_hash(plain_password)
            return bcrypt_context.verify(pre, hashed_password)
    except Exception:
        return False

    return False

