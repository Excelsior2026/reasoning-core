# Security and Code Quality Fixes

> **Status note (2026-10-15):** Written against a web layer that could not
> previously be imported (fixed in the P0 pull request). Treat the "✅" marks
> below as intended controls that still require verification, not as a
> verified security posture.
>
> **Update (2026-10-16):** The authentication, SSRF, path-traversal, and
> local-first-default controls below are now enforced in code with regression
> tests (see the `Security` section in `CHANGELOG.md`). Authentication is off
> by default for local use; enable `REASONING_CORE_AUTH_ENABLED=true` and set
> `REASONING_CORE_API_KEYS` before exposing the server beyond localhost.

This document summarizes all the security and code quality fixes implemented in the reasoning-core web API.

## Critical Security Fixes

### 1. Authentication & Authorization ✅
- **File**: `src/reasoning_core/web/auth.py`
- **Changes**:
  - JWT token authentication (PyJWT) and API key authentication
  - State-changing endpoints require credentials when authentication is
    enabled; read-only endpoints use optional authentication
  - Configurable via `REASONING_CORE_AUTH_ENABLED` (default: `false`, a
    local-mode default; enable it before exposing the server)

### 2. File Size Limits & Validation ✅
- **Files**: `src/reasoning_core/web/validation.py`, `src/reasoning_core/web/config.py`
- **Changes**:
  - Maximum file size: 50MB (configurable via `REASONING_CORE_MAX_FILE_SIZE_MB`)
  - Maximum text length: 1MB (configurable via `REASONING_CORE_MAX_TEXT_LENGTH`)
  - File size validation checks in chunks to prevent memory exhaustion
  - Proper HTTP 413 errors for oversized files

### 3. SSRF Protection ✅
- **File**: `src/reasoning_core/web/scraper.py`
- **Changes**:
  - URL validation before fetching
  - Blocks private/internal IP addresses by default
  - Blocks localhost unless explicitly allowed
  - Domain whitelisting support via `REASONING_CORE_ALLOWED_DOMAINS`
  - Configurable via `REASONING_CORE_ALLOW_PRIVATE_IPS`
  - Hostnames are resolved and every resolved address is validated
    (DNS-rebinding style names pointing at private addresses are rejected)
  - Redirect targets are re-validated before being followed
  - Alternate IP encodings (decimal, hex, octal, shortened forms) are
    normalized before validation

### 4. Memory Leak Prevention ✅
- **File**: `src/reasoning_core/web/server.py`
- **Changes**:
  - Task expiration: 1 hour (configurable via `REASONING_CORE_TASK_EXPIRY_SECONDS`)
  - Automatic cleanup of expired tasks
  - File cleanup with configurable max age (1 hour default)
  - Periodic cleanup tasks run in background
  - Rate limit store cleanup

### 5. Path Traversal Protection ✅
- **File**: `src/reasoning_core/web/validation.py`
- **Changes**:
  - Filename sanitization using `os.path.basename()`
  - Removes dangerous characters
  - Limits filename length
  - Validates file extensions against whitelist
  - Prevents directory traversal attacks

## High Priority Fixes

### 6. Comprehensive Input Validation ✅
- **File**: `src/reasoning_core/web/validation.py`
- **Changes**:
  - Pydantic models for request validation
  - Text length validation
  - URL format validation
  - Domain name validation
  - File type validation
  - MIME type checking

### 7. Error Logging ✅
- **Files**: `src/reasoning_core/web/server.py`, all web modules
- **Changes**:
  - Structured logging throughout
  - Log levels configurable via `REASONING_CORE_LOG_LEVEL`
  - File logging support via `REASONING_CORE_LOG_FILE`
  - Exception logging with full tracebacks
  - Request/response logging

### 8. File Cleanup Mechanism ✅
- **File**: `src/reasoning_core/web/server.py`
- **Changes**:
  - Automatic cleanup of old uploaded files
  - Configurable file max age (1 hour default)
  - Periodic cleanup runs every hour
  - Cleanup on server shutdown

### 9. Production Code Cleanup ✅
- **File**: `web/src/components/KnowledgeGraphViewer.jsx`
- **Changes**:
  - Removed `console.log` from production code
  - Conditional logging only in development mode

### 10. Rate Limiting ✅
- **File**: `src/reasoning_core/web/rate_limit.py`
- **Changes**:
  - In-memory rate limiting (configurable, can use Redis in production)
  - Default: 10 requests per 60 seconds per IP/user
  - Configurable via `REASONING_CORE_RATE_LIMIT_REQUESTS` and `REASONING_CORE_RATE_LIMIT_WINDOW`
  - Rate limit headers in responses
  - Client identification by IP or user ID

### 11. Configuration Management ✅
- **File**: `src/reasoning_core/web/config.py`
- **Changes**:
  - Centralized configuration via environment variables
  - Sensible defaults for all settings
  - Type conversions and validation
  - Separate configs for file uploads, security, CORS, rate limiting, etc.

### 12. Improved Error Handling ✅
- **File**: `src/reasoning_core/web/server.py`
- **Changes**:
  - Global exception handlers
  - Proper HTTP status codes
  - User-friendly error messages
  - Detailed error logging
  - Graceful error recovery

## New Dependencies

The following new dependencies were added to the project's `[web]` extra in `pyproject.toml` (installed with `pip install -e ".[web]"`; these were originally tracked in `requirements-web.txt`, since removed):

- `aiofiles>=23.0.0` - Async file operations
- `pyjwt>=2.8.0` - JWT token handling (the single JWT implementation)
- `pypdf>=4.0.0` - PDF text extraction (replaces the deprecated `PyPDF2`)

## Environment Variables

All configuration can be done via environment variables:

### Security
- `REASONING_CORE_AUTH_ENABLED` - Enable/disable authentication (default:
  false; local mode — set to true before exposing the server)
- `REASONING_CORE_API_KEYS` - Comma-separated list of API keys
- `REASONING_CORE_JWT_SECRET` - JWT secret key
- `REASONING_CORE_ALLOW_PRIVATE_IPS` - Allow private IPs in URLs (default: false)
- `REASONING_CORE_ALLOWED_DOMAINS` - Comma-separated whitelist of allowed domains
- `REASONING_CORE_HOST` - Server bind address (default: 127.0.0.1)
- `REASONING_CORE_PORT` - Server bind port (default: 8000)

### File Upload
- `REASONING_CORE_MAX_FILE_SIZE_MB` - Max file size in MB (default: 50)
- `REASONING_CORE_MAX_TEXT_LENGTH` - Max text length in bytes (default: 1000000)
- `REASONING_CORE_UPLOAD_DIR` - Upload directory path (default: temp dir)
- `REASONING_CORE_FILE_MAX_AGE` - File max age in seconds (default: 3600)

### Task Management
- `REASONING_CORE_TASK_EXPIRY_SECONDS` - Task expiration time (default: 3600)
- `REASONING_CORE_MAX_TASKS_PER_USER` - Max tasks per user (default: 100)

### Rate Limiting
- `REASONING_CORE_RATE_LIMIT_ENABLED` - Enable rate limiting (default: true)
- `REASONING_CORE_RATE_LIMIT_REQUESTS` - Requests per window (default: 10)
- `REASONING_CORE_RATE_LIMIT_WINDOW` - Window size in seconds (default: 60)

### CORS
- `REASONING_CORE_CORS_ORIGINS` - Comma-separated list of allowed origins

### Logging
- `REASONING_CORE_LOG_LEVEL` - Log level (default: INFO)
- `REASONING_CORE_LOG_FILE` - Log file path (optional)

## Testing Recommendations

1. Test file upload with files > 50MB (should fail with 413)
2. Test SSRF protection with private IPs (should be blocked)
3. Test rate limiting by making > 10 requests in 60 seconds
4. Test authentication with invalid API keys (should fail)
5. Test path traversal with malicious filenames (should be sanitized)
6. Test task expiration (tasks should be removed after 1 hour)
7. Test file cleanup (files should be removed after 1 hour)

## Production Deployment Notes

1. **Enable authentication**: `export REASONING_CORE_AUTH_ENABLED=true`
2. **Set strong API keys**: `export REASONING_CORE_API_KEYS="key1,key2,key3"`
3. **Set JWT secret**: `export REASONING_CORE_JWT_SECRET="your-secret-key"`
4. **Configure CORS**: `export REASONING_CORE_CORS_ORIGINS="https://yourdomain.com"`
5. **Set log file**: `export REASONING_CORE_LOG_FILE="/var/log/reasoning-core.log"`
6. **Use Redis for rate limiting** (currently in-memory, replace with Redis in production)
7. **Use database for task storage** (currently in-memory, replace with DB in production)
8. **Set up file cleanup cron job** (or rely on periodic cleanup)

## Migration Guide

If you have existing deployments:

1. Install new dependencies: `pip install -e ".[web]"`
2. Set environment variables (see above)
3. Restart the server
4. Existing tasks will expire after 1 hour
5. Old uploaded files will be cleaned up after 1 hour
