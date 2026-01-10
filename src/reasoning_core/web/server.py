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
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.base import BaseHTTPMiddleware
import json
from pydantic import BaseModel

from reasoning_core import ReasoningAPI, MedicalDomain, BusinessDomain, MeetingDomain
from reasoning_core.web.config import (
    LLM_ENABLED,
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
    BatchAnalysisRequest,
    validate_file_upload,
    validate_file_size,
    sanitize_filename,
)
from reasoning_core.web.progress import (
    create_progress_tracker,
    get_progress_tracker,
    remove_progress_tracker,
)
from reasoning_core.web.exports import export_markdown, export_pdf, export_html
from reasoning_core.web.search import AdvancedSearch, Analytics
from reasoning_core.web.cache import (
    cache_text_analysis,
    get_cached_text_analysis,
    cleanup_caches,
    get_cache_stats,
)
from reasoning_core.web.domain_builder import get_domain_builder

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


def get_domain(domain_name: str, custom_domain_id: Optional[str] = None):
    """Get domain instance by name or custom domain ID.

    Args:
        domain_name: Domain name string
        custom_domain_id: Optional custom domain ID

    Returns:
        Domain instance or None if invalid
    """
    # Check for custom domain first
    if domain_name.lower() == 'custom' and custom_domain_id:
        builder = get_domain_builder()
        config = builder.load_domain(custom_domain_id)
        if config:
            return builder.create_custom_domain(config)
        return None
    
    domain_map = {
        "medical": MedicalDomain,
        "business": BusinessDomain,
        "meeting": MeetingDomain,
        "generic": None,
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
            "analyze_batch": "/api/analyze/batch",
            "get_result": "/api/results/{task_id}",
            "get_progress": "/api/progress/{task_id}",
            "export_markdown": "/api/export/{task_id}/markdown",
            "export_pdf": "/api/export/{task_id}/pdf",
            "export_html": "/api/export/{task_id}/html",
            "search": "/api/search",
            "analytics": "/api/analytics/{task_id}",
            "cache_stats": "/api/cache/stats",
            "domains": "/api/domains",
            "domain": "/api/domains/{domain_id}",
            "health": "/api/health",
        },
    }


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "reasoning-core"}


@app.get("/api/cache/stats")
async def get_cache_statistics(auth: Optional[Dict] = Depends(optional_auth)):
    """Get cache statistics.

    Returns:
        Cache statistics
    """
    stats = get_cache_stats()
    
    # Cleanup expired entries
    cleanup_stats = cleanup_caches()
    
    return {
        "cache_statistics": stats,
        "cleanup": cleanup_stats,
    }


@app.post("/api/cache/clear")
async def clear_cache_endpoint(auth: Optional[Dict] = Depends(optional_auth)):
    """Clear all caches."""
    from reasoning_core.web.cache import clear_cache
    clear_cache()
    return {"message": "Cache cleared successfully"}


# Schedule periodic cache cleanup
import asyncio

async def periodic_cache_cleanup():
    """Periodically cleanup expired cache entries."""
    while True:
        await asyncio.sleep(3600)  # Every hour
        cleanup_caches()


# Start background task for cache cleanup
@app.on_event("startup")
async def startup_event():
    """Start background tasks on startup."""
    asyncio.create_task(periodic_cache_cleanup())


@app.get("/api/domains")
async def list_domains(auth: Optional[Dict] = Depends(optional_auth)):
    """List all custom domains.

    Returns:
        List of domain metadata
    """
    builder = get_domain_builder()
    domains = builder.list_domains()
    return {"domains": domains}


@app.post("/api/domains")
async def create_domain(
    config: Dict[str, Any],
    auth: Optional[Dict] = Depends(optional_auth),
):
    """Create or update a custom domain.

    Args:
        config: Domain configuration

    Returns:
        Created domain metadata
    """
    import time
    
    builder = get_domain_builder()
    
    # Add timestamps
    if 'id' in config and builder.load_domain(config['id']):
        # Update existing
        config['updated_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
    else:
        # Create new
        config['created_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
        config['updated_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
    
    domain_id = builder.save_domain(config)
    
    return {
        "id": domain_id,
        "message": "Domain saved successfully",
        "config": config,
    }


@app.get("/api/domains/{domain_id}")
async def get_domain(domain_id: str, auth: Optional[Dict] = Depends(optional_auth)):
    """Get custom domain configuration.

    Args:
        domain_id: Domain identifier

    Returns:
        Domain configuration
    """
    builder = get_domain_builder()
    config = builder.load_domain(domain_id)
    
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Domain not found")
    
    return {"domain": config}


@app.delete("/api/domains/{domain_id}")
async def delete_domain(domain_id: str, auth: Optional[Dict] = Depends(optional_auth)):
    """Delete custom domain.

    Args:
        domain_id: Domain identifier

    Returns:
        Deletion status
    """
    builder = get_domain_builder()
    deleted = builder.delete_domain(domain_id)
    
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Domain not found")
    
    return {"message": "Domain deleted successfully"}


@app.post("/api/domains/{domain_id}/test")
async def test_domain(
    domain_id: str,
    test_text: str,
    auth: Optional[Dict] = Depends(optional_auth),
):
    """Test custom domain on sample text.

    Args:
        domain_id: Domain identifier
        test_text: Sample text to test

    Returns:
        Test results
    """
    builder = get_domain_builder()
    config = builder.load_domain(domain_id)
    
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Domain not found")
    
    # Create domain instance and test
    try:
        custom_domain = builder.create_custom_domain(config)
        api = ReasoningAPI(domain=custom_domain, use_llm=False)
        
        result = api.process_text(test_text, include_graph=True, use_llm=False)
    except Exception as e:
        logger.exception(f"Error testing domain: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test domain: {str(e)}",
        )
    
    return {
        "domain_id": domain_id,
        "test_text": test_text,
        "result": result,
    }


@app.get("/api/progress/{task_id}")
async def stream_progress(task_id: str):
    """Stream progress updates via Server-Sent Events.

    Args:
        task_id: Task identifier

    Returns:
        SSE stream of progress updates
    """
    async def event_generator():
        """Generate SSE events."""
        tracker = get_progress_tracker(task_id)
        last_progress = -1
        
        # Send initial progress if available
        if tracker:
            update = tracker.to_dict()
            yield f"data: {json.dumps(update)}\n\n"
            last_progress = tracker.progress
        
        # Poll for updates
        import asyncio
        max_attempts = 600  # 10 minutes at 1 second intervals
        attempts = 0
        
        while attempts < max_attempts:
            await asyncio.sleep(1)  # Check every second
            attempts += 1
            
            tracker = get_progress_tracker(task_id)
            if tracker:
                if tracker.progress != last_progress:
                    update = tracker.to_dict()
                    yield f"data: {json.dumps(update)}\n\n"
                    last_progress = tracker.progress
                    
                    # Stop streaming when complete
                    if tracker.progress >= 100 or tracker.stage in ("completed", "error"):
                        yield f"data: {json.dumps({**tracker.to_dict(), 'done': True})}\n\n"
                        break
            else:
                # Check if task is completed in tasks dict
                if task_id in tasks:
                    task = tasks[task_id]
                    if task.get("status") in ("completed", "error"):
                        yield f"data: {json.dumps({'task_id': task_id, 'status': task.get('status'), 'done': True})}\n\n"
                        break
                else:
                    # Task not found
                    yield f"data: {json.dumps({'task_id': task_id, 'error': 'Task not found', 'done': True})}\n\n"
                    break
        
        # Cleanup
        remove_progress_tracker(task_id)
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/api/analyze/text", response_model=AnalysisResponse)
async def analyze_text(request: AnalysisRequest, auth: Optional[Dict] = Depends(optional_auth)):
    """Analyze text directly."""
    logger.info(f"Text analysis request: domain={request.domain}, length={len(request.text)}")

    try:
        # Get LLM preference from request or use default
        use_llm = request.use_llm if request.use_llm is not None else LLM_ENABLED
        
        # Check cache first
        cached_result = get_cached_text_analysis(request.text, request.domain, use_llm)
        if cached_result:
            logger.info("Returning cached analysis result")
            task_id = str(uuid.uuid4())
            tasks[task_id] = {
                "status": "completed",
                "result": cached_result.get("result", cached_result),
                "domain": request.domain,
                "created_at": time.time(),
            }
            return AnalysisResponse(
                task_id=task_id,
                status="completed",
                message="Analysis completed (cached)",
            )
        
        # Create task ID for progress tracking
        task_id = str(uuid.uuid4())
        tracker = create_progress_tracker(task_id)
        
        # Get domain
        domain = get_domain(request.domain)
        api = ReasoningAPI(domain=domain, use_llm=use_llm)

        # Process text with progress updates
        def update_progress(stage: str, progress: int, message: str = ""):
            tracker.update(stage, progress, message)
        
        # Process with progress callbacks
        update_progress("extracting_concepts", 10, "Extracting concepts...")
        concepts = api.concept_extractor.extract(request.text)
        
        update_progress("mapping_relationships", 40, "Mapping relationships...")
        relationships = api.relationship_mapper.map_relationships(concepts, request.text)
        
        update_progress("building_chains", 60, "Building reasoning chains...")
        chains = api.chain_builder.build_chains(concepts, relationships)
        
        update_progress("building_graph", 80, "Building knowledge graph...")
        from dataclasses import asdict
        result = {
            "concepts": [asdict(c) for c in concepts],
            "relationships": [asdict(r) for r in relationships],
            "reasoning_chains": [asdict(c) for c in chains],
            "llm_enhanced": use_llm,
        }
        
        try:
            graph = api._build_knowledge_graph(concepts, relationships)
            result["knowledge_graph"] = graph.to_dict()
        except Exception as e:
            result["knowledge_graph"] = None
            result["graph_error"] = str(e)
        
        # Generate questions
        if api.domain:
            try:
                content_dict = api._prepare_content_for_questions(concepts)
                questions = api.domain.generate_questions(content_dict)
                result["questions"] = questions
            except Exception:
                result["questions"] = []
        
        update_progress("completed", 100, "Analysis complete")

        # Store result with expiration
        tasks[task_id] = {
            "status": "completed",
            "result": result,
            "domain": request.domain,
            "created_at": time.time(),
        }

        logger.info(f"Analysis completed: task_id={task_id}")

        # Cache the result
        cache_text_analysis(request.text, request.domain, result, use_llm)

        # Clean up tracker after a delay
        remove_progress_tracker(task_id)

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

        # Create progress tracker
        tracker = create_progress_tracker(task_id)
        tracker.update("uploaded", 5, "File uploaded, starting analysis...")
        
        # Process in background
        use_llm_final = use_llm if use_llm is not None else LLM_ENABLED
        background_tasks.add_task(process_file_task, task_id, str(file_path), domain, use_llm_final)

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


def process_file_task(task_id: str, file_path: str, domain: str, use_llm: bool = False):
    """Process file in background."""
    logger.info(f"Processing file task: task_id={task_id}, file={file_path}, use_llm={use_llm}")
    
    tracker = get_progress_tracker(task_id)
    if tracker:
        tracker.update("parsing", 10, "Parsing document...")

    try:
        # Parse document
        doc_data = parse_document(file_path)
        text = doc_data["text"]

        if not text or not text.strip():
            raise ValueError("No text content extracted from document")

        if tracker:
            tracker.update("extracting", 20, "Extracting concepts...")

        # Get domain
        domain_instance = get_domain(domain)
        api = ReasoningAPI(domain=domain_instance, use_llm=use_llm)

        # Process text with progress
        from dataclasses import asdict
        
        if tracker:
            tracker.update("extracting_concepts", 25, "Extracting concepts...")
        concepts = api.concept_extractor.extract(text)
        
        if tracker:
            tracker.update("mapping_relationships", 50, "Mapping relationships...")
        relationships = api.relationship_mapper.map_relationships(concepts, text)
        
        if tracker:
            tracker.update("building_chains", 65, "Building reasoning chains...")
        chains = api.chain_builder.build_chains(concepts, relationships)
        
        if tracker:
            tracker.update("building_graph", 80, "Building knowledge graph...")
        
        result = {
            "concepts": [asdict(c) for c in concepts],
            "relationships": [asdict(r) for r in relationships],
            "reasoning_chains": [asdict(c) for c in chains],
            "llm_enhanced": use_llm,
        }
        
        try:
            graph = api._build_knowledge_graph(concepts, relationships)
            result["knowledge_graph"] = graph.to_dict()
        except Exception as e:
            result["knowledge_graph"] = None
            result["graph_error"] = str(e)
        
        if api.domain:
            try:
                content_dict = api._prepare_content_for_questions(concepts)
                questions = api.domain.generate_questions(content_dict)
                result["questions"] = questions
            except Exception:
                result["questions"] = []
        
        if tracker:
            tracker.update("completed", 100, "Analysis complete")
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
        
        # Cleanup tracker
        if tracker:
            remove_progress_tracker(task_id)

        # Cleanup file
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
        except Exception as e:
            logger.warning(f"Failed to cleanup file {file_path}: {e}")

    except DocumentParserError as e:
        logger.error(f"Document parsing failed for task {task_id}: {e}")
        tracker = get_progress_tracker(task_id)
        if tracker:
            tracker.update("error", 0, "Failed to parse document")
            remove_progress_tracker(task_id)
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
        tracker = get_progress_tracker(task_id)
        if tracker:
            tracker.update("error", 0, "An unexpected error occurred")
            remove_progress_tracker(task_id)
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
    use_llm = request.use_llm if request.use_llm is not None else LLM_ENABLED
    logger.info(f"URL analysis request: url={request.url}, domain={request.domain}, use_llm={use_llm}")

    task_id = str(uuid.uuid4())

    # Store task as processing
    tasks[task_id] = {
        "status": "processing",
        "result": None,
        "domain": request.domain,
        "created_at": time.time(),
    }

    # Create progress tracker
    tracker = create_progress_tracker(task_id)
    tracker.update("initializing", 5, "Starting URL analysis...")
    
    # Process in background
    background_tasks.add_task(process_url_task, task_id, request.url, request.domain, use_llm)

    return AnalysisResponse(
        task_id=task_id,
        status="processing",
        message="URL processing started",
    )


def process_url_task(task_id: str, url: str, domain: str, use_llm: bool = False):
    """Process URL in background."""
    logger.info(f"Processing URL task: task_id={task_id}, url={url}, use_llm={use_llm}")
    
    tracker = get_progress_tracker(task_id)
    if tracker:
        tracker.update("scraping", 15, "Scraping website content...")

    try:
        # Scrape website (includes SSRF protection)
        scraped_data = scrape_website(url)
        text = scraped_data["text"]

        if not text or not text.strip():
            raise ValueError("No text content extracted from URL")

        if tracker:
            tracker.update("extracting", 30, "Extracting concepts...")

        # Get domain
        domain_instance = get_domain(domain)
        api = ReasoningAPI(domain=domain_instance, use_llm=use_llm)

        # Process text with progress
        from dataclasses import asdict
        
        if tracker:
            tracker.update("extracting_concepts", 35, "Extracting concepts...")
        concepts = api.concept_extractor.extract(text)
        
        if tracker:
            tracker.update("mapping_relationships", 55, "Mapping relationships...")
        relationships = api.relationship_mapper.map_relationships(concepts, text)
        
        if tracker:
            tracker.update("building_chains", 70, "Building reasoning chains...")
        chains = api.chain_builder.build_chains(concepts, relationships)
        
        if tracker:
            tracker.update("building_graph", 85, "Building knowledge graph...")
        
        result = {
            "concepts": [asdict(c) for c in concepts],
            "relationships": [asdict(r) for r in relationships],
            "reasoning_chains": [asdict(c) for c in chains],
            "llm_enhanced": use_llm,
        }
        
        try:
            graph = api._build_knowledge_graph(concepts, relationships)
            result["knowledge_graph"] = graph.to_dict()
        except Exception as e:
            result["knowledge_graph"] = None
            result["graph_error"] = str(e)
        
        if api.domain:
            try:
                content_dict = api._prepare_content_for_questions(concepts)
                questions = api.domain.generate_questions(content_dict)
                result["questions"] = questions
            except Exception:
                result["questions"] = []
        
        if tracker:
            tracker.update("completed", 100, "Analysis complete")
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
        
        # Cleanup tracker
        if tracker:
            remove_progress_tracker(task_id)

    except ScrapingError as e:
        logger.error(f"Scraping failed for task {task_id}: {e}")
        tracker = get_progress_tracker(task_id)
        if tracker:
            tracker.update("error", 0, f"Error: {str(e)}")
            remove_progress_tracker(task_id)
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


@app.post("/api/search")
async def search_results(
    task_id: str,
    query: Optional[str] = None,
    filters: Optional[Dict] = None,
    auth: Optional[Dict] = Depends(optional_auth),
):
    """Advanced search across analysis results.

    Args:
        task_id: Task ID to search
        query: Search query string
        filters: Filter options (type, confidence, etc.)

    Returns:
        Search results with relevance scores
    """
    if task_id not in tasks:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    task = tasks[task_id]
    if task.get("status") != "completed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Task not completed")

    result = task.get("result", {})

    search_engine = AdvancedSearch()
    search_results = search_engine.search(query or "", result, filters)

    # Convert SearchResult objects to dictionaries
    formatted_results = {}
    for category, results_list in search_results.items():
        formatted_results[category] = [
            {
                "item": r.item,
                "score": r.score,
                "matched_fields": r.matched_fields,
                "highlights": r.highlights,
            }
            for r in results_list
        ]

    return {
        "query": query,
        "filters": filters,
        "results": formatted_results,
        "total": sum(len(r) for r in formatted_results.values()),
    }


@app.get("/api/analytics/{task_id}")
async def get_analytics(task_id: str, auth: Optional[Dict] = Depends(optional_auth)):
    """Get analytics and statistics for analysis results.

    Args:
        task_id: Task ID

    Returns:
        Analytics data
    """
    if task_id not in tasks:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    task = tasks[task_id]
    if task.get("status") != "completed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Task not completed")

    result = task.get("result", {})
    statistics = Analytics.calculate_statistics(result)

    return {
        "task_id": task_id,
        "statistics": statistics,
    }


@app.get("/api/export/{task_id}/markdown")
async def export_results_markdown(task_id: str, auth: Optional[Dict] = Depends(optional_auth)):
    """Export analysis results as Markdown."""
    if task_id not in tasks:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    task = tasks[task_id]
    if task.get("status") != "completed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Task not completed")

    result = task.get("result", {})
    markdown = export_markdown(result)

    from fastapi.responses import Response
    return Response(
        content=markdown,
        media_type="text/markdown",
        headers={
            "Content-Disposition": f'attachment; filename="reasoning-core-{task_id}.md"',
        },
    )


@app.get("/api/export/{task_id}/pdf")
async def export_results_pdf(task_id: str, auth: Optional[Dict] = Depends(optional_auth)):
    """Export analysis results as PDF."""
    if task_id not in tasks:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    task = tasks[task_id]
    if task.get("status") != "completed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Task not completed")

    result = task.get("result", {})
    try:
        pdf_bytes = export_pdf(result)
    except ImportError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PDF export requires reportlab. Install with: pip install reportlab",
        )

    from fastapi.responses import Response
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="reasoning-core-{task_id}.pdf"',
        },
    )


@app.get("/api/export/{task_id}/html")
async def export_results_html(task_id: str, auth: Optional[Dict] = Depends(optional_auth)):
    """Export analysis results as HTML."""
    if task_id not in tasks:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    task = tasks[task_id]
    if task.get("status") != "completed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Task not completed")

    result = task.get("result", {})
    html = export_html(result)

    from fastapi.responses import Response
    return Response(
        content=html,
        media_type="text/html",
        headers={
            "Content-Disposition": f'attachment; filename="reasoning-core-{task_id}.html"',
        },
    )


@app.post("/api/analyze/batch")
async def analyze_batch(
    background_tasks: BackgroundTasks,
    request: BatchAnalysisRequest,
    auth: Optional[Dict] = Depends(optional_auth),
):
    """Analyze multiple items in batch."""
    logger.info(f"Batch analysis request: {len(request.items)} items, domain={request.domain}")

    batch_id = str(uuid.uuid4())
    use_llm = request.use_llm if request.use_llm is not None else LLM_ENABLED

    # Store batch task
    tasks[batch_id] = {
        "status": "processing",
        "result": None,
        "type": "batch",
        "domain": request.domain,
        "item_count": len(request.items),
        "completed_items": 0,
        "results": [],
        "created_at": time.time(),
    }

    # Create progress tracker
    tracker = create_progress_tracker(batch_id)
    tracker.update("initializing", 5, f"Starting batch analysis of {len(request.items)} items...")

    # Process in background
    background_tasks.add_task(process_batch_task, batch_id, request.items, request.domain, use_llm)

    return AnalysisResponse(
        task_id=batch_id,
        status="processing",
        message=f"Batch analysis started for {len(request.items)} items",
    )


def process_batch_task(batch_id: str, items: List[Dict], domain: str, use_llm: bool = False):
    """Process batch analysis."""
    logger.info(f"Processing batch task: batch_id={batch_id}, items={len(items)}")
    
    tracker = get_progress_tracker(batch_id)
    domain_instance = get_domain(domain)
    api = ReasoningAPI(domain=domain_instance, use_llm=use_llm)
    
    results = []
    
    for i, item in enumerate(items):
        try:
            # Get text from item
            text = None
            source_info = {}
            
            if item.get("text"):
                text = item["text"]
                source_info = {"type": "text", "index": i}
            elif item.get("url"):
                if tracker:
                    tracker.update("processing", int(10 + (i / len(items)) * 80), 
                                 f"Processing item {i+1}/{len(items)}: {item['url']}")
                scraped_data = scrape_website(item["url"])
                text = scraped_data["text"]
                source_info = {"type": "url", "url": item["url"], "index": i}
            elif item.get("file"):
                # File processing would need file path
                # For now, skip if file not available
                logger.warning(f"File item {i} skipped - file processing requires file path")
                continue
            
            if not text or not text.strip():
                continue
            
            # Process item
            if tracker:
                tracker.update("processing", int(10 + (i / len(items)) * 80),
                             f"Analyzing item {i+1}/{len(items)}...")
            
            from dataclasses import asdict
            
            concepts = api.concept_extractor.extract(text)
            relationships = api.relationship_mapper.map_relationships(concepts, text)
            chains = api.chain_builder.build_chains(concepts, relationships)
            
            result = {
                "index": i,
                "source": source_info,
                "concepts": [asdict(c) for c in concepts],
                "relationships": [asdict(r) for r in relationships],
                "reasoning_chains": [asdict(c) for c in chains],
                "llm_enhanced": use_llm,
            }
            
            try:
                graph = api._build_knowledge_graph(concepts, relationships)
                result["knowledge_graph"] = graph.to_dict()
            except Exception:
                result["knowledge_graph"] = None
            
            if api.domain:
                try:
                    content_dict = api._prepare_content_for_questions(concepts)
                    questions = api.domain.generate_questions(content_dict)
                    result["questions"] = questions
                except Exception:
                    result["questions"] = []
            
            results.append(result)
            
            # Update batch progress
            if batch_id in tasks:
                tasks[batch_id]["completed_items"] = len(results)
                tasks[batch_id]["results"] = results
            
        except Exception as e:
            logger.error(f"Error processing batch item {i}: {e}")
            results.append({
                "index": i,
                "error": str(e),
                "source": item,
            })
    
    # Update batch task
    if batch_id in tasks:
        tasks[batch_id] = {
            "status": "completed",
            "result": {
                "items": results,
                "total": len(items),
                "completed": len([r for r in results if "error" not in r]),
                "failed": len([r for r in results if "error" in r]),
            },
            "type": "batch",
            "domain": domain,
            "item_count": len(items),
            "completed_items": len(results),
            "created_at": tasks[batch_id].get("created_at", time.time()),
        }
    
    if tracker:
        tracker.update("completed", 100, f"Batch analysis complete: {len(results)} items processed")
        remove_progress_tracker(batch_id)
    
    logger.info(f"Batch processing completed: batch_id={batch_id}, processed={len(results)}/{len(items)}")


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
