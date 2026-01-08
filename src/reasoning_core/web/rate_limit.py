"""Rate limiting for reasoning-core web API."""

import time
from typing import Dict, Optional
from collections import defaultdict
from fastapi import Request, HTTPException, status
from reasoning_core.web.config import (
    RATE_LIMIT_ENABLED,
    RATE_LIMIT_REQUESTS,
    RATE_LIMIT_WINDOW_SECONDS,
)

# In-memory rate limit storage (use Redis in production)
_rate_limit_store: Dict[str, list] = defaultdict(list)


def get_client_identifier(request: Request) -> str:
    """Get unique identifier for rate limiting.

    Args:
        request: FastAPI request object

    Returns:
        Client identifier (IP address or user ID)
    """
    # Try to get user ID from auth context if available
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"user:{user_id}"

    # Fall back to IP address
    client_host = request.client.host if request.client else "unknown"
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Get first IP in X-Forwarded-For chain
        client_host = forwarded_for.split(",")[0].strip()

    return f"ip:{client_host}"


def check_rate_limit(client_id: str) -> bool:
    """Check if client has exceeded rate limit.

    Args:
        client_id: Client identifier

    Returns:
        True if under limit, False if exceeded

    Raises:
        HTTPException: If rate limit exceeded
    """
    if not RATE_LIMIT_ENABLED:
        return True

    current_time = time.time()
    window_start = current_time - RATE_LIMIT_WINDOW_SECONDS

    # Get recent requests
    requests = _rate_limit_store[client_id]

    # Remove old requests outside window
    requests[:] = [req_time for req_time in requests if req_time > window_start]

    # Check if limit exceeded
    if len(requests) >= RATE_LIMIT_REQUESTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "rate_limit_exceeded",
                "message": f"Rate limit exceeded: {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW_SECONDS} seconds",
                "retry_after": RATE_LIMIT_WINDOW_SECONDS,
            },
        )

    # Add current request
    requests.append(current_time)

    return True


async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware.

    Args:
        request: FastAPI request
        call_next: Next middleware/handler

    Returns:
        Response
    """
    # Skip rate limiting for health check
    if request.url.path in ["/", "/api/health", "/docs", "/openapi.json", "/redoc"]:
        return await call_next(request)

    client_id = get_client_identifier(request)
    check_rate_limit(client_id)

    response = await call_next(request)

    # Add rate limit headers
    requests = _rate_limit_store[client_id]
    remaining = max(0, RATE_LIMIT_REQUESTS - len(requests))

    response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT_REQUESTS)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Window"] = str(RATE_LIMIT_WINDOW_SECONDS)

    return response


def cleanup_rate_limits():
    """Cleanup old rate limit entries."""
    current_time = time.time()
    window_start = current_time - RATE_LIMIT_WINDOW_SECONDS

    for client_id in list(_rate_limit_store.keys()):
        requests = _rate_limit_store[client_id]
        requests[:] = [req_time for req_time in requests if req_time > window_start]

        # Remove empty entries
        if not requests:
            del _rate_limit_store[client_id]
