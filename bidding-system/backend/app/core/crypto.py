"""민감 데이터 암호화 (AES-256-GCM)

키 생성:
  python -c "import os, base64; print(base64.urlsafe_b64encode(os.urandom(32)).decode())"
"""
import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from app.core.config import settings

_aesgcm: AESGCM | None = None


def _get_aesgcm() -> AESGCM:
    global _aesgcm
    if _aesgcm is None:
        key_b64 = settings.ENCRYPTION_KEY
        if not key_b64:
            raise ValueError(
                "ENCRYPTION_KEY not set. Generate with: "
                "python -c \"import os, base64; print(base64.urlsafe_b64encode(os.urandom(32)).decode())\""
            )
        key = base64.urlsafe_b64decode(key_b64 + "=" * ((4 - len(key_b64) % 4) % 4))
        if len(key) != 32:
            raise ValueError("ENCRYPTION_KEY must be 32 bytes (256-bit) base64url-encoded")
        _aesgcm = AESGCM(key)
    return _aesgcm


def encrypt(value: str) -> str:
    """AES-256-GCM 암호화. 반환 형식: base64url(12-byte nonce || ciphertext+tag)"""
    if not value:
        return value
    nonce = os.urandom(12)
    ciphertext = _get_aesgcm().encrypt(nonce, value.encode(), None)
    return base64.urlsafe_b64encode(nonce + ciphertext).decode()


def decrypt(value: str) -> str:
    """AES-256-GCM 복호화"""
    if not value:
        return value
    raw = base64.urlsafe_b64decode(value + "==")
    nonce, ciphertext = raw[:12], raw[12:]
    return _get_aesgcm().decrypt(nonce, ciphertext, None).decode()
