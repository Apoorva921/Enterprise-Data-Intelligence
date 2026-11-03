"""
Security and JWT Authentication Provider.
"""
import time
import hmac
import hashlib
import json
import base64
from typing import Optional, Dict, Any
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from backend.app.core.config import settings

security = HTTPBearer(auto_error=False)


def _b64_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64_decode(data: str) -> bytes:
    padding = "=" * (4 - (len(data) % 4))
    return base64.urlsafe_b64decode(data + padding)


def create_access_token(data: Dict[str, Any], expires_in_seconds: int = 86400) -> str:
    """Creates a signed HMAC-SHA256 JWT token."""
    header = {"alg": "HS256", "typ": "JWT"}
    payload = data.copy()
    payload["exp"] = int(time.time()) + expires_in_seconds
    payload["iat"] = int(time.time())

    h_str = _b64_encode(json.dumps(header).encode("utf-8"))
    p_str = _b64_encode(json.dumps(payload).encode("utf-8"))
    msg = f"{h_str}.{p_str}".encode("utf-8")

    sig = hmac.new(settings.secret_key.encode("utf-8"), msg, hashlib.sha256).digest()
    sig_str = _b64_encode(sig)
    return f"{h_str}.{p_str}.{sig_str}"


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decodes and validates HMAC-SHA256 JWT token."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Malformed token")
        h_str, p_str, sig_str = parts

        msg = f"{h_str}.{p_str}".encode("utf-8")
        expected_sig = hmac.new(settings.secret_key.encode("utf-8"), msg, hashlib.sha256).digest()
        actual_sig = _b64_decode(sig_str)

        if not hmac.compare_digest(expected_sig, actual_sig):
            raise ValueError("Invalid signature")

        payload = json.loads(_b64_decode(p_str).decode("utf-8"))
        if payload.get("exp", 0) < time.time():
            raise ValueError("Token expired")
        return payload
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def verify_admin_token(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)) -> Dict[str, Any]:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required for protected administrative endpoints",
        )
    return decode_access_token(credentials.credentials)

