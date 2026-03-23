"""
apps/users/otp.py

OTP generation and verification.
OTPs are stored in Redis (not DB) with a 5-minute TTL.
Key format:  otp:{email}
Value:       bcrypt hash of the 6-digit code
"""
from __future__ import annotations

import hashlib
import random
import string

from django.core.cache import cache

OTP_TTL = 300  # 5 minutes
OTP_KEY_PREFIX = "otp:"


def _otp_key(email: str) -> str:
    return f"{OTP_KEY_PREFIX}{email.lower()}"


def generate_and_store(email: str) -> str:
    """
    Generate a 6-digit OTP, store its SHA-256 hash in Redis, and
    return the plaintext code (to be sent via email).
    """
    code = "".join(random.choices(string.digits, k=6))
    hashed = _hash(code)
    cache.set(_otp_key(email), hashed, timeout=OTP_TTL)
    return code


def verify(email: str, code: str) -> bool:
    """
    Verify a submitted OTP code against the stored hash.
    Returns True on match and deletes the key (one-time use).
    Returns False if not found or hash mismatch.
    """
    key = _otp_key(email)
    stored_hash = cache.get(key)
    if stored_hash is None:
        return False
    if stored_hash == _hash(code):
        cache.delete(key)
        return True
    return False


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()
