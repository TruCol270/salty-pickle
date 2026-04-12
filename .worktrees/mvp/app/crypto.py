"""Symmetric encryption helpers for OAuth tokens stored at rest.

Uses Fernet (AES-128-CBC with HMAC) keyed from the app SECRET_KEY.
"""

import base64
import hashlib
import logging
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

from app.config import get_settings

logger = logging.getLogger(__name__)


def _fernet() -> Fernet:
    key_material = get_settings().secret_key.encode()
    derived = hashlib.sha256(key_material).digest()
    fernet_key = base64.urlsafe_b64encode(derived)
    return Fernet(fernet_key)


def encrypt_token(plaintext: Optional[str]) -> Optional[str]:
    if not plaintext:
        return plaintext
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt_token(ciphertext: Optional[str]) -> Optional[str]:
    if not ciphertext:
        return ciphertext
    try:
        return _fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken:
        logger.warning("Failed to decrypt token — returning raw value (legacy unencrypted data)")
        return ciphertext
