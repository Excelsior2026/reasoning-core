"""Caching functionality for performance optimization."""

import hashlib
import json
import time
from typing import Dict, Any, Optional
from functools import wraps
from datetime import datetime, timedelta


class MemoryCache:
    """In-memory cache with TTL support."""

    def __init__(self, default_ttl: int = 3600):
        """Initialize cache.

        Args:
            default_ttl: Default time-to-live in seconds (default: 1 hour)
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl

    def _make_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments.

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Cache key string
        """
        key_data = json.dumps({'args': args, 'kwargs': kwargs}, sort_keys=True)
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if expired/not found
        """
        if key not in self.cache:
            return None

        entry = self.cache[key]
        
        # Check expiration
        if entry['expires_at'] < time.time():
            del self.cache[key]
            return None

        return entry['value']

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        ttl = ttl or self.default_ttl
        expires_at = time.time() + ttl
        
        self.cache[key] = {
            'value': value,
            'expires_at': expires_at,
            'created_at': time.time(),
        }

    def delete(self, key: str) -> None:
        """Delete key from cache.

        Args:
            key: Cache key
        """
        self.cache.pop(key, None)

    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()

    def cleanup_expired(self) -> int:
        """Remove expired entries.

        Returns:
            Number of entries removed
        """
        now = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if entry['expires_at'] < now
        ]
        
        for key in expired_keys:
            del self.cache[key]

        return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Statistics dictionary
        """
        now = time.time()
        active_entries = sum(
            1 for entry in self.cache.values()
            if entry['expires_at'] >= now
        )
        expired_entries = len(self.cache) - active_entries

        return {
            'total_entries': len(self.cache),
            'active_entries': active_entries,
            'expired_entries': expired_entries,
            'default_ttl': self.default_ttl,
        }


# Global cache instance
_analysis_cache = MemoryCache(default_ttl=7200)  # 2 hours default
_result_cache = MemoryCache(default_ttl=86400)  # 24 hours for completed results


def cache_analysis_result(ttl: Optional[int] = None):
    """Decorator to cache analysis results.

    Args:
        ttl: Cache TTL in seconds

    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = f"{func.__name__}:{_analysis_cache._make_key(*args, **kwargs)}"
            
            # Try to get from cache
            cached_result = _analysis_cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Call function and cache result
            result = await func(*args, **kwargs)
            
            # Only cache successful results
            if result and isinstance(result, dict):
                if result.get('status') == 'completed':
                    _analysis_cache.set(cache_key, result, ttl)

            return result

        return wrapper
    return decorator


def get_cache_key_for_text(text: str, domain: str, use_llm: bool = False) -> str:
    """Generate cache key for text analysis.

    Args:
        text: Input text
        domain: Domain type
        use_llm: Whether LLM was used

    Returns:
        Cache key
    """
    # Use text hash for cache key (first 1000 chars to avoid huge keys)
    text_sample = text[:1000] if len(text) > 1000 else text
    key_data = {
        'text_hash': hashlib.sha256(text_sample.encode()).hexdigest(),
        'text_length': len(text),
        'domain': domain,
        'use_llm': use_llm,
    }
    key_string = json.dumps(key_data, sort_keys=True)
    return hashlib.md5(key_string.encode()).hexdigest()


def cache_text_analysis(text: str, domain: str, result: Dict[str, Any], use_llm: bool = False, ttl: int = 7200) -> None:
    """Cache text analysis result.

    Args:
        text: Input text
        domain: Domain type
        result: Analysis result
        use_llm: Whether LLM was used
        ttl: Cache TTL in seconds
    """
    cache_key = f"text_analysis:{get_cache_key_for_text(text, domain, use_llm)}"
    _analysis_cache.set(cache_key, result, ttl)


def get_cached_text_analysis(text: str, domain: str, use_llm: bool = False) -> Optional[Dict[str, Any]]:
    """Get cached text analysis result.

    Args:
        text: Input text
        domain: Domain type
        use_llm: Whether LLM was used

    Returns:
        Cached result or None
    """
    cache_key = f"text_analysis:{get_cache_key_for_text(text, domain, use_llm)}"
    return _analysis_cache.get(cache_key)


def clear_cache() -> None:
    """Clear all caches."""
    _analysis_cache.clear()
    _result_cache.clear()


def cleanup_caches() -> Dict[str, int]:
    """Cleanup expired cache entries.

    Returns:
        Dictionary with cleanup statistics
    """
    analysis_cleaned = _analysis_cache.cleanup_expired()
    result_cleaned = _result_cache.cleanup_expired()
    
    return {
        'analysis_cache_cleaned': analysis_cleaned,
        'result_cache_cleaned': result_cleaned,
        'total_cleaned': analysis_cleaned + result_cleaned,
    }


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics.

    Returns:
        Statistics for all caches
    """
    return {
        'analysis_cache': _analysis_cache.get_stats(),
        'result_cache': _result_cache.get_stats(),
    }
