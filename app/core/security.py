"""Compatibility shim for security helpers.

This module re-exports the hashing and JWT helper functions from
`app.core.passwords` and `app.core.jwt` so existing imports continue to work.
"""

from .passwords import hash_password, verify_password
from .jwt import create_access_token, decode_access_token

__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "decode_access_token",
]