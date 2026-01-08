# Functionality & Code Review: reasoning-core

**Date:** 2026-01-XX  
**Reviewer:** AI Code Reviewer  
**Version:** 0.1.0  
**Scope:** Full codebase including web UI and installers

## Executive Summary

Reasoning Core has evolved into a comprehensive reasoning extraction engine with a web UI and cross-platform installers. The codebase demonstrates good structure and functionality, but there are **critical security and functionality issues** that need immediate attention before production deployment.

**Overall Assessment:** ⚠️ **Needs Improvement** - Good foundation with security and functionality gaps

**Key Strengths:**
- Well-structured plugin architecture
- Good error handling in core API
- Comprehensive domain support
- Modern web UI with React
- Cross-platform installer support

**Critical Issues:**
- **No authentication/authorization in web API**
- **No file size limits or rate limiting**
- **Memory leaks in task storage**
- **Security vulnerabilities in file upload**
- **Missing input validation in web API**
- **No request logging/auditing**

---

## 1. Security Issues 🔴 **CRITICAL**

### 1.1 Missing Authentication ⚠️ **CRITICAL VULNERABILITY**

**Location:** `src/reasoning_core/web/server.py`

**Issue:**
```python:51:57:src/reasoning_core/web/server.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ Allows all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Problems:**
- **No authentication** on any endpoints
- CORS allows all origins (`allow_origins=["*"]`)
- Anyone can upload files, scrape websites, analyze text
- No rate limiting or abuse prevention
- Comment says "In production, specify allowed origins" but no enforcement

**Impact:** 
- Security vulnerability - open to abuse
- DoS potential - unlimited resource consumption
- No user accountability

**Recommendation:**
```python
# Add authentication middleware
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_token(token: str = Depends(security)):
    # Verify JWT or API key
    if not is_valid_token(token.credentials):
        raise HTTPException(status_code=401, detail="Invalid token")
    return token

# Apply to routes
@app.post("/api/analyze/text", dependencies=[Depends(verify_token)])
async def analyze_text(...):
    ...

# Restrict CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourdomain.com"],  # Specific origins
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)
```

### 1.2 File Upload Security ⚠️ **CRITICAL VULNERABILITY**

**Location:** `src/reasoning_core/web/server.py:129-165`

**Issues:**

#### No File Size Limits
```python:148:150:src/reasoning_core/web/server.py
with open(file_path, "wb") as f:
    content = await file.read()  # ⚠️ Reads entire file into memory
    f.write(content)
```

**Problems:**
- No maximum file size validation
- Entire file loaded into memory (DoS risk)
- No file type validation beyond filename
- No virus/malware scanning
- Path traversal possible in filename

**Impact:**
- Memory exhaustion from large files
- Disk space exhaustion
- Potential malicious file uploads

**Recommendation:**
```python
from fastapi import File, UploadFile, Form
import aiofiles

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".html", ".md"}

@app.post("/api/analyze/file")
async def analyze_file(
    file: UploadFile = File(...),
    domain: str = Form(default="generic"),
):
    # Validate file size
    file_size = 0
    async with aiofiles.open(temp_path, "wb") as f:
        while chunk := await file.read(8192):  # Stream in chunks
            file_size += len(chunk)
            if file_size > MAX_FILE_SIZE:
                raise HTTPException(413, "File too large")
            await f.write(chunk)
    
    # Validate file extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, "Invalid file type")
    
    # Validate file signature (magic numbers)
    # ... check actual file content, not just extension
```

#### Path Traversal Vulnerability
```python:146:146:src/reasoning_core/web/server.py
file_path = UPLOAD_DIR / f"{task_id}_{file.filename}"  # ⚠️ Uses unsanitized filename
```

**Problem:** Filename could contain `../` or other path components

**Recommendation:**
```python
from pathlib import Path
import re

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal."""
    # Remove path components
    filename = Path(filename).name
    # Remove dangerous characters
    filename = re.sub(r'[^\w\s.-]', '', filename)
    # Limit length
    return filename[:255]

file_path = UPLOAD_DIR / f"{task_id}_{sanitize_filename(file.filename)}"
```

### 1.3 URL Scraping Security ⚠️ **HIGH RISK**

**Location:** `src/reasoning_core/web/scraper.py:44-53`

**Issues:**
- No SSRF (Server-Side Request Forgery) protection
- Can access internal/localhost URLs
- No URL whitelist/blacklist
- No timeout enforcement validation
- User-Agent spoofing

**Problems:**
```python:52:52:src/reasoning_core/web/scraper.py
response = requests.get(url, headers=headers, timeout=timeout)
```

**Impact:**
- Could access internal services (SSRF)
- Could scan local network
- Could trigger requests to internal APIs

**Recommendation:**
```python
import ipaddress
from urllib.parse import urlparse

def is_safe_url(url: str) -> bool:
    """Check if URL is safe to fetch (prevent SSRF)."""
    parsed = urlparse(url)
    hostname = parsed.hostname
    
    # Block private/localhost IPs
    try:
        ip = ipaddress.ip_address(hostname)
        if ip.is_private or ip.is_loopback:
            return False
    except ValueError:
        pass  # Hostname, not IP
    
    # Block localhost hostnames
    if hostname in ["localhost", "127.0.0.1", "0.0.0.0"]:
        return False
    
    # Optional: whitelist domains
    ALLOWED_DOMAINS = ["example.com", "example.org"]  # Configure
    if hostname not in ALLOWED_DOMAINS:
        return False
    
    return True
```

### 1.4 In-Memory Task Storage ⚠️ **MEMORY LEAK**

**Location:** `src/reasoning_core/web/server.py:60`

**Issue:**
```python:60:60:src/reasoning_core/web/server.py
tasks: dict = {}  # ⚠️ Never cleaned up
```

**Problems:**
- Tasks stored in-memory indefinitely
- No expiration/cleanup mechanism
- Memory leak over time
- No persistent storage (lost on restart)
- Race conditions in concurrent access

**Impact:**
- Memory exhaustion over time
- Data loss on server restart
- No task history/audit trail

**Recommendation:**
```python
import time
from collections import OrderedDict

# Task storage with expiration
tasks: OrderedDict = OrderedDict()
TASK_EXPIRY_SECONDS = 3600  # 1 hour

def cleanup_expired_tasks():
    """Remove expired tasks."""
    current_time = time.time()
    expired = [
        task_id for task_id, task in tasks.items()
        if current_time - task.get("created_at", 0) > TASK_EXPIRY_SECONDS
    ]
    for task_id in expired:
        tasks.pop(task_id, None)

# Use Redis or database in production
# tasks = redis_client  # Or database connection
```

### 1.5 Sensitive Data Exposure ⚠️ **MEDIUM RISK**

**Location:** Multiple files

**Issues:**
- Error messages expose internal details
- Stack traces returned to clients
- File paths exposed in responses

**Example:**
```python:125:126:src/reasoning_core/web/server.py
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))  # ⚠️ Exposes internal errors
```

**Recommendation:**
```python
import logging
logger = logging.getLogger(__name__)

except Exception as e:
    logger.exception("Error processing request")
    # Don't expose internal errors to client
    raise HTTPException(
        status_code=500,
        detail="An error occurred processing your request. Please try again."
    )
```

---

## 2. Functionality Issues

### 2.1 Missing Input Validation ⚠️ **HIGH PRIORITY**

**Location:** `src/reasoning_core/web/server.py`

**Issue:**
```python:100:109:src/reasoning_core/web/server.py
@app.post("/api/analyze/text", response_model=AnalysisResponse)
async def analyze_text(request: AnalysisRequest):
    """Analyze text directly."""
    try:
        # Get domain
        domain = get_domain(request.domain)
        api = ReasoningAPI(domain=domain)
        
        # Process text
        result = api.process_text(request.text, include_graph=True)
```

**Problems:**
- No text length validation (could be huge)
- No content validation (could be malicious)
- Domain validation missing (silent failure if invalid)
- No rate limiting per user/IP

**Recommendation:**
```python
from pydantic import Field, validator

class AnalysisRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1_000_000)  # 1MB max
    domain: str = Field(default="generic", pattern="^(generic|medical|business|meeting)$")
    
    @validator('text')
    def validate_text(cls, v):
        if not v.strip():
            raise ValueError('Text cannot be empty')
        if len(v.encode('utf-8')) > 1_000_000:
            raise ValueError('Text too large')
        return v
```

### 2.2 Background Task Error Handling ⚠️ **MEDIUM PRIORITY**

**Location:** `src/reasoning_core/web/server.py:168-209`

**Issue:**
```python:204:209:src/reasoning_core/web/server.py
except Exception as e:
    tasks[task_id] = {
        "status": "error",
        "error": str(e),  # ⚠️ Error message stored but not logged
        "domain": domain,
    }
```

**Problems:**
- Errors not logged
- No retry mechanism
- No notification of failures
- Silent failures

**Recommendation:**
```python
import logging

logger = logging.getLogger(__name__)

def process_file_task(task_id: str, file_path: str, domain: str):
    """Process file in background."""
    try:
        # ... processing ...
    except DocumentParserError as e:
        logger.error(f"Document parsing failed for task {task_id}: {e}")
        tasks[task_id] = {
            "status": "error",
            "error": "Failed to parse document. Please check file format.",
            "domain": domain,
        }
    except Exception as e:
        logger.exception(f"Unexpected error processing task {task_id}")
        tasks[task_id] = {
            "status": "error",
            "error": "An unexpected error occurred. Please try again.",
            "domain": domain,
        }
```

### 2.3 Missing File Cleanup ⚠️ **MEDIUM PRIORITY**

**Location:** `src/reasoning_core/web/server.py:195-196`

**Issue:**
```python:195:196:src/reasoning_core/web/server.py
# Cleanup file
if os.path.exists(file_path):
    os.unlink(file_path)
```

**Problems:**
- Files not cleaned up on error
- No cleanup on server shutdown
- Temp directory grows indefinitely
- No cleanup of orphaned files

**Recommendation:**
```python
import atexit
import shutil

# Periodic cleanup
def cleanup_old_files():
    """Remove files older than 1 hour."""
    current_time = time.time()
    for file_path in UPLOAD_DIR.glob("*"):
        if file_path.is_file():
            if current_time - file_path.stat().st_mtime > 3600:
                file_path.unlink()

# Register cleanup on exit
atexit.register(cleanup_old_files)

# Also cleanup on error
try:
    # ... processing ...
finally:
    if os.path.exists(file_path):
        os.unlink(file_path)
```

### 2.4 Frontend Security ⚠️ **MEDIUM PRIORITY**

**Location:** `web/src/components/KnowledgeGraphViewer.jsx`

**Issue:**
```javascript:106:106:web/src/components/KnowledgeGraphViewer.jsx
console.log('Selected node:', node.data())  // ⚠️ Console.log in production
```

**Problems:**
- Console.log left in production code
- No error boundary for React components
- No input sanitization in frontend
- Direct API calls without CSRF protection

**Recommendation:**
```javascript
// Remove console.log or use proper logging
if (process.env.NODE_ENV === 'development') {
  console.log('Selected node:', node.data())
}

// Add error boundaries
import { ErrorBoundary } from 'react-error-boundary'

<ErrorBoundary fallback={<ErrorDisplay />}>
  <KnowledgeGraphViewer graph={graph} />
</ErrorBoundary>
```

### 2.5 Polling Inefficiency ⚠️ **MEDIUM PRIORITY**

**Location:** `web/src/components/FileUpload.jsx:48-74`

**Issue:**
```javascript:48:74:web/src/components/FileUpload.jsx
const pollResults = async (taskId) => {
    const maxAttempts = 60
    let attempts = 0

    const poll = async () => {
        // ... polling logic ...
        attempts++
        if (attempts < maxAttempts) {
            setTimeout(poll, 2000) // Poll every 2 seconds
        }
    }
    poll()
}
```

**Problems:**
- Fixed 2-second polling interval
- No exponential backoff
- No WebSocket/SSE for real-time updates
- Wastes bandwidth on idle polling

**Recommendation:**
```javascript
// Use WebSockets or Server-Sent Events
// Or exponential backoff for polling
const pollResults = async (taskId) => {
    let delay = 1000  // Start with 1 second
    const maxDelay = 10000  // Max 10 seconds
    
    const poll = async () => {
        try {
            const response = await axios.get(`/api/results/${taskId}`)
            if (response.data.status === 'completed') {
                onResults(response.data)
                return
            }
            
            // Exponential backoff
            delay = Math.min(delay * 1.5, maxDelay)
            setTimeout(poll, delay)
        } catch (err) {
            onError(err)
        }
    }
    poll()
}
```

---

## 3. Code Quality Issues

### 3.1 Missing Type Hints ⚠️ **LOW PRIORITY**

**Location:** `src/reasoning_core/web/server.py:67-75`

**Issue:**
```python:67:75:src/reasoning_core/web/server.py
def get_domain(domain_name: str):
    """Get domain instance by name."""
    domain_map = {
        "medical": MedicalDomain,
        "business": BusinessDomain,
        "meeting": MeetingDomain,
    }
    domain_class = domain_map.get(domain_name.lower())
    return domain_class() if domain_class else None  # ⚠️ Returns Optional[BaseDomain]
```

**Fix:**
```python
from typing import Optional
from reasoning_core.plugins.base_domain import BaseDomain

def get_domain(domain_name: str) -> Optional[BaseDomain]:
    """Get domain instance by name."""
    # ...
```

### 3.2 Hard-coded Values ⚠️ **LOW PRIORITY**

**Location:** Multiple files

**Issues:**
- Magic numbers throughout code
- No configuration file
- Hard-coded timeouts, limits

**Recommendation:**
```python
# Create config.py
class Config:
    MAX_FILE_SIZE_MB = 50
    MAX_TEXT_LENGTH = 1_000_000
    TASK_EXPIRY_SECONDS = 3600
    POLLING_INTERVAL_SECONDS = 2
    REQUEST_TIMEOUT_SECONDS = 30
```

### 3.3 Error Message Consistency ⚠️ **LOW PRIORITY**

**Location:** Multiple files

**Issue:** Error messages vary in format and detail level

**Recommendation:** Create standard error response format

---

## 4. Performance Issues

### 4.1 Synchronous File Reading ⚠️ **MEDIUM PRIORITY**

**Location:** `src/reasoning_core/web/server.py:148-150`

**Issue:**
```python:148:150:src/reasoning_core/web/server.py
content = await file.read()  # ⚠️ Reads entire file into memory
f.write(content)
```

**Problem:** Blocks event loop for large files

**Fix:** Use async file I/O (aiofiles)

### 4.2 No Caching ⚠️ **LOW PRIORITY**

**Issue:**
- No caching of parsed documents
- No caching of analysis results
- Re-parsing same file multiple times

**Recommendation:** Add Redis/memory cache for frequent requests

### 4.3 Cytoscape Performance ⚠️ **LOW PRIORITY**

**Location:** `web/src/components/KnowledgeGraphViewer.jsx`

**Issue:** Large graphs may cause browser performance issues

**Recommendation:** Add graph size limits and pagination/virtualization

---

## 5. Testing Gaps

### 5.1 Missing Web API Tests ❌

**Issue:** No tests for web server endpoints

**Recommendation:**
```python
# tests/test_web_server.py
def test_analyze_text_endpoint():
    response = client.post("/api/analyze/text", json={
        "text": "Test text",
        "domain": "medical"
    })
    assert response.status_code == 200

def test_file_upload_size_limit():
    large_file = b"x" * (51 * 1024 * 1024)  # 51 MB
    response = client.post("/api/analyze/file", files={
        "file": ("test.pdf", large_file)
    })
    assert response.status_code == 413
```

### 5.2 Missing Parser Tests ❌

**Issue:** No tests for document parsers

### 5.3 Missing Scraper Tests ❌

**Issue:** No tests for website scraper

---

## 6. Missing Functionality

### 6.1 No Configuration Management ⚠️ **MEDIUM PRIORITY**

**Issue:** Hard-coded values throughout codebase

**Examples:**
- No `MAX_FILE_SIZE` constant
- No `MAX_TEXT_LENGTH` constant
- No `TASK_EXPIRY_SECONDS` constant
- Timeout values hard-coded

**Recommendation:** Create `src/reasoning_core/web/config.py` with all configuration

### 6.2 No Logging ⚠️ **HIGH PRIORITY**

**Issue:** Missing logging throughout web API

**Location:** `src/reasoning_core/web/server.py`

**Problem:** No request logging, error logging, or audit trail

**Recommendation:**
```python
import logging

logger = logging.getLogger("reasoning_core.web")

@app.post("/api/analyze/text")
async def analyze_text(request: AnalysisRequest):
    logger.info(f"Text analysis request: domain={request.domain}, length={len(request.text)}")
    try:
        # ... processing ...
        logger.info(f"Analysis completed: task_id={task_id}")
    except Exception as e:
        logger.exception(f"Analysis failed: {e}")
        raise
```

### 6.3 Missing Health Checks ⚠️ **LOW PRIORITY**

**Issue:** Health check is too basic

**Current:**
```python:94:97:src/reasoning_core/web/server.py
@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "reasoning-core"}
```

**Recommendation:** Add dependency checks (database, disk space, memory)

---

## 7. Installer Issues

### 6.1 macOS Installer Script Permissions ⚠️ **MEDIUM PRIORITY**

**Location:** `installers/macos/install_dependencies.sh`

**Issue:**
```bash:17:17:installers/macos/install_dependencies.sh
if [ "$EUID" -eq 0 ]; then
```

**Problem:** Checks for root but continues - should be more explicit

### 6.2 Windows Installer PowerShell Execution Policy ⚠️ **MEDIUM PRIORITY**

**Location:** `installers/windows/install_dependencies.ps1`

**Issue:** May fail if execution policy restricts scripts

**Fix:** Add execution policy bypass in installer

---

## 8. Documentation Gaps

### 7.1 Missing API Documentation ⚠️

**Issue:** No OpenAPI/Swagger docs exported

**Fix:** FastAPI auto-generates at `/docs`, but should document deployment

### 7.2 Missing Deployment Guide ⚠️

**Issue:** No production deployment documentation

**Needed:**
- Docker deployment guide
- Environment variable configuration
- Security hardening guide
- Scaling recommendations

---

## Priority Recommendations

### 🔴 **CRITICAL** (Fix Before Production)
1. **Add authentication/authorization** to web API
2. **Implement file size limits** and validation
3. **Add SSRF protection** for URL scraping
4. **Fix memory leaks** in task storage
5. **Sanitize file uploads** (path traversal prevention)

### 🟠 **HIGH** (Fix Soon)
6. Add input validation to all endpoints
7. Implement proper error logging
8. Add file cleanup mechanism
9. Remove console.log from production frontend
10. Add rate limiting

### 🟡 **MEDIUM** (Improve Over Time)
11. Implement WebSocket/SSE for real-time updates
12. Add caching layer
13. Improve error messages
14. Add comprehensive tests
15. Create deployment documentation

### 🟢 **LOW** (Nice to Have)
16. Add monitoring/metrics
17. Implement graph size limits
18. Add request/response compression
19. Create API versioning
20. Add batch processing support

---

## Code Quality Score

| Category | Score | Notes |
|----------|-------|-------|
| Architecture | 8/10 | Good plugin system, clean separation |
| Security | 3/10 | ⚠️ Critical vulnerabilities |
| Error Handling | 7/10 | Good in core, needs work in web API |
| Testing | 6/10 | Core tests good, web API missing |
| Documentation | 7/10 | Good README, needs deployment docs |
| Performance | 7/10 | Good overall, some optimization needed |
| **Overall** | **6/10** | Needs security fixes before production |

---

## Conclusion

Reasoning Core has a solid foundation with good architecture and functionality. However, **critical security vulnerabilities** must be addressed before production deployment:

1. **Authentication is mandatory** - Currently wide open
2. **File upload security** - No validation or limits
3. **Memory management** - Tasks never expire
4. **Input validation** - Missing throughout web API

With these fixes, the application would be production-ready. The codebase shows good Python practices and the plugin architecture is well-designed.

---

## Review Checklist

- [x] Security review
- [x] Functionality review
- [x] Code quality review
- [x] Performance review
- [x] Testing review
- [x] Documentation review
- [x] Installer review
- [x] Frontend review

---

**Next Steps:**
1. **Immediate:** Fix critical security issues
2. **Short-term:** Add input validation and error handling
3. **Medium-term:** Implement proper testing and documentation
4. **Long-term:** Performance optimization and feature enhancements
