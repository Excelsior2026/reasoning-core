"""Configuration for reasoning-core web server."""

import os
from typing import List
from pathlib import Path

# File upload settings
MAX_FILE_SIZE_MB = int(os.getenv("REASONING_CORE_MAX_FILE_SIZE_MB", "50"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
MAX_TEXT_LENGTH = int(os.getenv("REASONING_CORE_MAX_TEXT_LENGTH", "1000000"))  # 1MB
ALLOWED_FILE_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".html", ".htm", ".md", ".markdown"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "text/plain",
    "text/html",
    "text/markdown",
}

# Task management
TASK_EXPIRY_SECONDS = int(os.getenv("REASONING_CORE_TASK_EXPIRY_SECONDS", "3600"))  # 1 hour
MAX_TASKS_PER_USER = int(os.getenv("REASONING_CORE_MAX_TASKS_PER_USER", "100"))

# Request settings
REQUEST_TIMEOUT_SECONDS = int(os.getenv("REASONING_CORE_REQUEST_TIMEOUT", "30"))
URL_SCRAPE_TIMEOUT = int(os.getenv("REASONING_CORE_URL_TIMEOUT", "30"))

# Security settings
AUTH_ENABLED = os.getenv("REASONING_CORE_AUTH_ENABLED", "true").lower() in ("true", "1", "yes")
API_KEY_HEADER = "X-API-Key"
JWT_SECRET_KEY = os.getenv("REASONING_CORE_JWT_SECRET", os.getenv("REASONING_CORE_SECRET_KEY", ""))
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = int(os.getenv("REASONING_CORE_JWT_EXPIRE_HOURS", "24"))

# CORS settings
CORS_ALLOW_ORIGINS = os.getenv(
    "REASONING_CORE_CORS_ORIGINS", "http://localhost:3000,http://localhost:5173"
).split(",")
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["GET", "POST"]
CORS_ALLOW_HEADERS = ["Content-Type", "Authorization", "X-API-Key"]

# Rate limiting
RATE_LIMIT_ENABLED = os.getenv("REASONING_CORE_RATE_LIMIT_ENABLED", "true").lower() in ("true", "1", "yes")
RATE_LIMIT_REQUESTS = int(os.getenv("REASONING_CORE_RATE_LIMIT_REQUESTS", "10"))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("REASONING_CORE_RATE_LIMIT_WINDOW", "60"))

# SSRF protection
ALLOW_PRIVATE_IPS = os.getenv("REASONING_CORE_ALLOW_PRIVATE_IPS", "false").lower() in ("true", "1", "yes")
ALLOWED_URL_DOMAINS: List[str] = os.getenv("REASONING_CORE_ALLOWED_DOMAINS", "").split(",")
ALLOWED_URL_DOMAINS = [d.strip() for d in ALLOWED_URL_DOMAINS if d.strip()]

# Logging
LOG_LEVEL = os.getenv("REASONING_CORE_LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("REASONING_CORE_LOG_FILE", "")

# File storage
UPLOAD_DIR = Path(os.getenv("REASONING_CORE_UPLOAD_DIR", ""))
if not UPLOAD_DIR:
    import tempfile
    UPLOAD_DIR = Path(tempfile.gettempdir()) / "reasoning_core_uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

FILE_CLEANUP_INTERVAL_SECONDS = int(os.getenv("REASONING_CORE_FILE_CLEANUP_INTERVAL", "3600"))  # 1 hour
FILE_MAX_AGE_SECONDS = int(os.getenv("REASONING_CORE_FILE_MAX_AGE", "3600"))  # 1 hour

# LLM settings
LLM_ENABLED = os.getenv("REASONING_CORE_LLM_ENABLED", "false").lower() in ("true", "1", "yes")
LLM_MODEL = os.getenv("REASONING_CORE_LLM_MODEL", "llama3.2:3b")
LLM_BASE_URL = os.getenv("REASONING_CORE_LLM_URL", "http://localhost:11434")
LLM_USE_GPU = os.getenv("REASONING_CORE_LLM_USE_GPU", "true").lower() in ("true", "1", "yes")
LLM_TIMEOUT = int(os.getenv("REASONING_CORE_LLM_TIMEOUT", "120"))  # 2 minutes
