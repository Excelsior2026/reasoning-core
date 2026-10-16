"""Authentication and authorization for reasoning-core web API."""

import os
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

from reasoning_core.web.config import API_KEY_HEADER, AUTH_ENABLED, JWT_ALGORITHM, JWT_EXPIRE_HOURS, JWT_SECRET_KEY

# Security schemes
bearer_scheme = HTTPBearer(auto_error=False)
api_key_scheme = APIKeyHeader(name=API_KEY_HEADER, auto_error=False)

# API keys (load from environment). When authentication is explicitly enabled
# but no keys are configured, fall back to a generated development key so that
# local authenticated testing is possible; the key is printed once so the
# operator can use it, and it changes on every restart.
API_KEYS: set = set()
api_keys_env = os.getenv("REASONING_CORE_API_KEYS", "")
if api_keys_env:
    API_KEYS = set(key.strip() for key in api_keys_env.split(",") if key.strip())
elif AUTH_ENABLED:
    dev_key = os.getenv("REASONING_CORE_DEV_KEY")
    if not dev_key:
        dev_key = secrets.token_urlsafe(32)
        print("⚠️  Authentication is enabled but no API keys are configured.")
        print(f"⚠️  Generated development key: {dev_key}")
        print("⚠️  This key changes on every restart; set REASONING_CORE_API_KEYS for a stable key.")
    API_KEYS.add(dev_key)


class AuthenticationError(HTTPException):
    """Authentication error exception."""

    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class AuthorizationError(HTTPException):
    """Authorization error exception."""

    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def verify_api_key(api_key: Optional[str]) -> bool:
    """Verify if API key is valid.

    Args:
        api_key: API key to verify

    Returns:
        True if valid, False otherwise
    """
    if not AUTH_ENABLED:
        return True

    if not api_key:
        return False

    return api_key in API_KEYS


def verify_jwt_token(token: str) -> Dict:
    """Verify JWT token and return payload.

    Args:
        token: JWT token string

    Returns:
        Token payload dictionary

    Raises:
        AuthenticationError: If token is invalid or expired
    """
    if not AUTH_ENABLED:
        return {"user_id": "anonymous", "username": "anonymous"}

    if not JWT_SECRET_KEY:
        raise AuthenticationError("JWT secret key not configured")

    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired")
    except Exception:
        raise AuthenticationError("Invalid token")


def create_jwt_token(user_id: str, username: str, email: Optional[str] = None) -> str:
    """Create a JWT token.

    Args:
        user_id: User identifier
        username: Username
        email: Optional email address

    Returns:
        JWT token string
    """
    if not JWT_SECRET_KEY:
        raise ValueError("JWT secret key not configured")

    payload = {
        "user_id": user_id,
        "username": username,
        "email": email,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS),
    }

    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


async def authenticate(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    api_key: Optional[str] = Depends(api_key_scheme),
) -> Dict:
    """Authenticate request using JWT or API key.

    Args:
        credentials: HTTP Bearer credentials (JWT)
        api_key: API key from header

    Returns:
        Authentication information dictionary

    Raises:
        AuthenticationError: If authentication fails
    """
    if not AUTH_ENABLED:
        return {"user_id": "anonymous", "username": "anonymous", "auth_type": "disabled"}

    # Try JWT token first
    if credentials:
        try:
            payload = verify_jwt_token(credentials.credentials)
            payload["auth_type"] = "jwt"
            return payload
        except AuthenticationError:
            pass  # Try API key if JWT fails

    # Try API key
    if api_key:
        if verify_api_key(api_key):
            return {"user_id": "api_user", "username": "api", "auth_type": "api_key"}

    # No valid authentication found
    raise AuthenticationError("Authentication required. Provide either a Bearer token or X-API-Key header.")


async def optional_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    api_key: Optional[str] = Depends(api_key_scheme),
) -> Optional[Dict]:
    """Optional authentication (doesn't fail if not provided).

    Args:
        credentials: HTTP Bearer credentials
        api_key: API key from header

    Returns:
        Authentication info or None if not authenticated
    """
    if not AUTH_ENABLED:
        return None

    try:
        return await authenticate(credentials, api_key)
    except AuthenticationError:
        return None
