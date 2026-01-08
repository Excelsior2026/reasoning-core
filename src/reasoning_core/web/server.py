"""FastAPI web server for reasoning-core."""

import os
import time
import uuid
import logging
import atexit
import asyncio
from typing import Optional, Dict, Any
from pathlib import Path
from collections import OrderedDict

import aiofiles

from fastapi import FastAPI, UploadFile, File, HTTPException, Form, BackgroundTasks, Depends, Request
from fastapi import status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel

from reasoning_core import ReasoningAPI, MedicalDomain, BusinessDomain, MeetingDomain
from reasoning_core.web.parsers import parse_document, DocumentParserError
from reasoning_core.web.scraper import scrape_website, ScrapingError
from reasoning_core.web.config import (
    UPLOAD_DIR,
    CORS_ALLOW_ORIGINS,
    CORS_ALLOW_CREDENTIALS,
    CORS_ALLOW_METHODS,
    CORS_ALLOW_HEADERS,
    TASK_EXPIRY_SECONDS,
    FILE_CLEANUP_INTERVAL_SECONDS,
    FILE_MAX_AGE_SECONDS,
    LOG_LEVEL,
    LOG_FILE,
)
from reasoning_core.web.auth import authenticate, optional_auth, AuthenticationError
from reasoning_core.web.rate_limit import rate_limit_middleware, cleanup_rate_limits
from reasoning_core.web.validation import (
    AnalysisRequest,
    URLRequest,
    validate_file_upload,
    validate_file_size,
    sanitize_filename,
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE) if LOG_FILE else logging.StreamHandler()
    ],
)
logger = logging.getLogger("reasoning_core.web")

# Pydantic models
class AnalysisResponse(BaseModel):
    """Response model for analysis results."""

    task_id: str
    status: str
    message: str


# Create FastAPI app
app = FastAPI(
    title="Reasoning Core API",
    description="Universal reasoning extraction engine with web interface",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=CORS_ALLOW_CREDENTIALS,
    allow_methods=CORS_ALLOW_METHODS,
    allow_headers=CORS_ALLOW_HEADERS,
)

# Rate limiting middleware
app.add_middleware(BaseHTTPMiddleware, dispatch=rate_limit_middleware)

# Task storage with expiration
tasks: OrderedDict = OrderedDict()


class Task:
    """Task data structure."""

    def __init__(self, task_id: str, domain: str):
        self.task_id = task_id
        self.domain = domain
        self.status = "processing"
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.created_at = time.time()


def cleanup_expired_tasks():
    """Remove expired tasks from storage."""
    current_time = time.time()
    expired = []

    for task_id, task in tasks.items():
        if isinstance(task, dict):
            created_at = task.get("created_at", 0)
            if current_time - created_at > TASK_EXPIRY_SECONDS:
                expired.append(task_id)
        elif hasattr(task, "created_at"):
            if current_time - task.created_at > TASK_EXPIRY_SECONDS:
                expired.append(task_id)

    for task_id in expired:
        tasks.pop(task_id, None)
        logger.debug(f"Cleaned up expired task: {task_id}")


def cleanup_old_files():
    """Remove old files from upload directory."""
    current_time = time.time()
    removed_count = 0

    try:
        for file_path in UPLOAD_DIR.glob("*"):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > FILE_MAX_AGE_SECONDS:
                    try:
                        file_path.unlink()
                        removed_count += 1
                        logger.debug(f"Cleaned up old file: {file_path.name}")
                    except Exception as e:
                        logger.warning(f"Failed to cleanup file {file_path}: {e}")
    except Exception as e:
        logger.error(f"Error during file cleanup: {e}")

    if removed_count > 0:
        logger.info(f"Cleaned up {removed_count} old files")


# Periodic cleanup tasks
async def periodic_cleanup():
    """Run periodic cleanup tasks."""
    while True:
        await asyncio.sleep(FILE_CLEANUP_INTERVAL_SECONDS)
        cleanup_expired_tasks()
        cleanup_old_files()
        cleanup_rate_limits()


# Start cleanup task on startup
@app.on_event("startup")
async def startup_event():
    """Startup tasks."""
    logger.info("Starting Reasoning Core Web Server")
    logger.info(f"Upload directory: {UPLOAD_DIR}")
    logger.info(f"CORS allowed origins: {CORS_ALLOW_ORIGINS}")
    asyncio.create_task(periodic_cleanup())


# Register cleanup on shutdown
@atexit.register
def cleanup_on_exit():
    """Cleanup on application exit."""
    cleanup_expired_tasks()
    cleanup_old_files()
    logger.info("Shutting down Reasoning Core Web Server")


def get_domain(domain_name: str):
    """Get domain instance by name.

    Args:
        domain_name: Domain name string

    Returns:
        Domain instance or None if invalid
    """
    domain_map = {
        "medical": MedicalDomain,
        "business": BusinessDomain,
        "meeting": MeetingDomain,
    }
    domain_class = domain_map.get(domain_name.lower())
    return domain_class() if domain_class else None


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Reasoning Core API",
        "version": "0.1.0",
        "endpoints": {
            "analyze_text": "/api/analyze/text",
            "analyze_file": "/api/analyze/file",
            "analyze_url": "/api/analyze/url",
            "get_result": "/api/results/{task_id}",
            "health": "/api/health",
        },
    }


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "reasoning-core"}


@app.post("/api/analyze/text", response_model=AnalysisResponse)
async def analyze_text(request: AnalysisRequest, auth: Optional[Dict] = Depends(optional_auth)):
    """Analyze text directly."""
    logger.info(f"Text analysis request: domain={request.domain}, length={len(request.text)}")

    try:
        # Get domain
        domain = get_domain(request.domain)
        api = ReasoningAPI(domain=domain)

        # Process text
        result = api.process_text(request.text, include_graph=True)

        # Store result with expiration
        task_id = str(uuid.uuid4())
        tasks[task_id] = {
            "status": "completed",
            "result": result,
            "domain": request.domain,
            "created_at": time.time(),
        }

        logger.info(f"Analysis completed: task_id={task_id}")

        return AnalysisResponse(
            task_id=task_id,
            status="completed",
            message="Analysis completed successfully",
        )

    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception(f"Error processing text analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred processing your request. Please try again.",
        )


@app.post("/api/analyze/file")
async def analyze_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    domain: str = Form(default="generic"),
    auth: Optional[Dict] = Depends(optional_auth),
):
    """Analyze uploaded document file."""
    logger.info(f"File upload request: filename={file.filename}, domain={domain}")

    # Validate domain
    if domain not in ["generic", "medical", "business", "meeting"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid domain: {domain}. Must be one of: generic, medical, business, meeting",
        )

    # Validate file
    try:
        filename, file_ext = validate_file_upload(file)
        await validate_file_size(file)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File validation failed: {str(e)}",
        )

    task_id = str(uuid.uuid4())

    # Store task as processing
    tasks[task_id] = {
        "status": "processing",
        "result": None,
        "domain": domain,
        "created_at": time.time(),
    }

    # Sanitize filename and create safe file path
    safe_filename = sanitize_filename(filename)
    file_path = UPLOAD_DIR / f"{task_id}_{safe_filename}"

    try:
        # Stream file to disk in chunks (prevents memory issues)
        file_size = 0
        async with aiofiles.open(file_path, "wb") as f:
            while True:
                chunk = await file.read(8192)  # 8KB chunks
                if not chunk:
                    break
                file_size += len(chunk)
                await f.write(chunk)

        logger.info(f"File uploaded: {file_path.name}, size: {file_size / 1024:.2f}KB")

        # Process in background
        background_tasks.add_task(process_file_task, task_id, str(file_path), domain)

        return AnalysisResponse(
            task_id=task_id,
            status="processing",
            message="File uploaded and processing started",
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception:
                pass
        raise
    except Exception as e:
        logger.exception(f"Error uploading file: {e}")
        # Cleanup on error
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception:
                pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred uploading your file. Please try again.",
        )


def process_file_task(task_id: str, file_path: str, domain: str):
    """Process file in background."""
    logger.info(f"Processing file task: task_id={task_id}, file={file_path}")

    try:
        # Parse document
        doc_data = parse_document(file_path)
        text = doc_data["text"]

        if not text or not text.strip():
            raise ValueError("No text content extracted from document")

        # Get domain
        domain_instance = get_domain(domain)
        api = ReasoningAPI(domain=domain_instance)

        # Process text
        result = api.process_text(text, include_graph=True)
        result["source"] = {
            "type": "file",
            "filename": Path(file_path).name,
            "metadata": doc_data.get("metadata", {}),
        }

        # Update task
        if task_id in tasks:
            tasks[task_id] = {
                "status": "completed",
                "result": result,
                "domain": domain,
                "created_at": tasks[task_id].get("created_at", time.time()),
            }

        logger.info(f"File processing completed: task_id={task_id}")

        # Cleanup file
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
        except Exception as e:
            logger.warning(f"Failed to cleanup file {file_path}: {e}")

    except DocumentParserError as e:
        logger.error(f"Document parsing failed for task {task_id}: {e}")
        if task_id in tasks:
            tasks[task_id] = {
                "status": "error",
                "error": "Failed to parse document. Please check file format.",
                "domain": domain,
                "created_at": tasks[task_id].get("created_at", time.time()),
            }
        # Cleanup file on error
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
        except Exception:
            pass
    except ValueError as e:
        logger.error(f"Validation error for task {task_id}: {e}")
        if task_id in tasks:
            tasks[task_id] = {
                "status": "error",
                "error": str(e),
                "domain": domain,
                "created_at": tasks[task_id].get("created_at", time.time()),
            }
        # Cleanup file
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
        except Exception:
            pass
    except Exception as e:
        logger.exception(f"Unexpected error processing task {task_id}: {e}")
        if task_id in tasks:
            tasks[task_id] = {
                "status": "error",
                "error": "An unexpected error occurred during processing.",
                "domain": domain,
                "created_at": tasks[task_id].get("created_at", time.time()),
            }
        # Cleanup file
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
        except Exception:
            pass


@app.post("/api/analyze/url")
async def analyze_url(
    background_tasks: BackgroundTasks,
    request: URLRequest,
    auth: Optional[Dict] = Depends(optional_auth),
):
    """Analyze website URL."""
    logger.info(f"URL analysis request: url={request.url}, domain={request.domain}")

    task_id = str(uuid.uuid4())

    # Store task as processing
    tasks[task_id] = {
        "status": "processing",
        "result": None,
        "domain": request.domain,
        "created_at": time.time(),
    }

    # Process in background
    background_tasks.add_task(process_url_task, task_id, request.url, request.domain)

    return AnalysisResponse(
        task_id=task_id,
        status="processing",
        message="URL processing started",
    )


def process_url_task(task_id: str, url: str, domain: str):
    """Process URL in background."""
    logger.info(f"Processing URL task: task_id={task_id}, url={url}")

    try:
        # Scrape website (includes SSRF protection)
        scraped_data = scrape_website(url)
        text = scraped_data["text"]

        if not text or not text.strip():
            raise ValueError("No text content extracted from URL")

        # Get domain
        domain_instance = get_domain(domain)
        api = ReasoningAPI(domain=domain_instance)

        # Process text
        result = api.process_text(text, include_graph=True)
        result["source"] = {
            "type": "url",
            "url": url,
            "metadata": scraped_data.get("metadata", {}),
        }

        # Update task
        if task_id in tasks:
            tasks[task_id] = {
                "status": "completed",
                "result": result,
                "domain": domain,
                "created_at": tasks[task_id].get("created_at", time.time()),
            }

        logger.info(f"URL processing completed: task_id={task_id}")

    except ScrapingError as e:
        logger.error(f"Scraping failed for task {task_id}: {e}")
        if task_id in tasks:
            tasks[task_id] = {
                "status": "error",
                "error": str(e),
                "domain": domain,
                "created_at": tasks[task_id].get("created_at", time.time()),
            }
    except ValueError as e:
        logger.error(f"Validation error for task {task_id}: {e}")
        if task_id in tasks:
            tasks[task_id] = {
                "status": "error",
                "error": str(e),
                "domain": domain,
                "created_at": tasks[task_id].get("created_at", time.time()),
            }
    except Exception as e:
        logger.exception(f"Unexpected error processing URL task {task_id}: {e}")
        if task_id in tasks:
            tasks[task_id] = {
                "status": "error",
                "error": "An unexpected error occurred during processing.",
                "domain": domain,
                "created_at": tasks[task_id].get("created_at", time.time()),
            }


@app.get("/api/results/{task_id}")
async def get_results(task_id: str, auth: Optional[Dict] = Depends(optional_auth)):
    """Get analysis results by task ID."""
    # Cleanup expired tasks before checking
    cleanup_expired_tasks()

    if task_id not in tasks:
        logger.warning(f"Task not found: {task_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found or expired"
        )

    task = tasks[task_id]

    if task.get("status") == "error":
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "error": task.get("error", "Unknown error"),
            },
        )

    if task.get("status") == "processing":
        return {
            "status": "processing",
            "message": "Analysis in progress",
        }

    return {
        "status": "completed",
        "result": task.get("result"),
        "domain": task.get("domain"),
    }


# Exception handlers
@app.exception_handler(AuthenticationError)
async def auth_exception_handler(request: Request, exc: AuthenticationError):
    """Handle authentication errors."""
    logger.warning(f"Authentication error: {request.url.path} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "authentication_error", "message": exc.detail},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    logger.warning(f"HTTP error {exc.status_code}: {request.url.path} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail if isinstance(exc.detail, dict) else {"message": str(exc.detail)}},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.exception(f"Unhandled exception: {request.url.path} - {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "internal_error",
            "message": "An unexpected error occurred. Please try again later.",
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level=LOG_LEVEL.lower())
