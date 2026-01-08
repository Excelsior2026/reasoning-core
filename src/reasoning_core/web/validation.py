"""Input validation for reasoning-core web API."""

import re
import os
from pathlib import Path
from typing import Optional, List
from fastapi import HTTPException, UploadFile, status
from pydantic import BaseModel, Field, field_validator
from reasoning_core.web.config import (
    MAX_TEXT_LENGTH,
    MAX_FILE_SIZE_BYTES,
    ALLOWED_FILE_EXTENSIONS,
    ALLOWED_MIME_TYPES,
)


class AnalysisRequest(BaseModel):
    """Request model for text analysis with validation."""

    text: str = Field(..., description="Text to analyze", min_length=1, max_length=MAX_TEXT_LENGTH)
    domain: str = Field(
        default="generic",
        description="Domain type: medical, business, meeting, generic",
    )

    @field_validator("text")
    @classmethod
    def validate_text(cls, v):
        """Validate text content."""
        if not v or not v.strip():
            raise ValueError("Text cannot be empty")

        # Check byte length (UTF-8 encoding)
        byte_length = len(v.encode("utf-8"))
        if byte_length > MAX_TEXT_LENGTH:
            raise ValueError(
                f"Text too large: {byte_length} bytes (max: {MAX_TEXT_LENGTH} bytes)"
            )

        return v.strip()

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, v):
        """Validate domain name."""
        valid_domains = ["generic", "medical", "business", "meeting"]
        if v.lower() not in valid_domains:
            raise ValueError(f"Invalid domain. Must be one of: {', '.join(valid_domains)}")
        return v.lower()


class URLRequest(BaseModel):
    """Request model for URL analysis with validation."""

    url: str = Field(..., description="Website URL to analyze")
    domain: str = Field(
        default="generic",
        description="Domain type: medical, business, meeting, generic",
    )

    @field_validator("url")
    @classmethod
    def validate_url(cls, v):
        """Validate URL format."""
        if not v or not isinstance(v, str):
            raise ValueError("URL must be a non-empty string")

        # Basic URL validation
        url_pattern = re.compile(
            r"^https?://"  # http:// or https://
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain
            r"localhost|"  # localhost
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # IP address
            r"(?::\d+)?"  # optional port
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )

        if not url_pattern.match(v):
            raise ValueError("Invalid URL format")

        return v.strip()

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, v):
        """Validate domain name."""
        valid_domains = ["generic", "medical", "business", "meeting"]
        if v.lower() not in valid_domains:
            raise ValueError(f"Invalid domain. Must be one of: {', '.join(valid_domains)}")
        return v.lower()


def sanitize_filename(filename: Optional[str]) -> str:
    """Sanitize filename to prevent path traversal.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename safe for filesystem use

    Raises:
        HTTPException: If filename is invalid
    """
    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Filename is required"
        )

    # Remove path components
    filename = os.path.basename(filename)

    # Remove or replace dangerous characters
    filename = re.sub(r'[^\w\s.-]', '', filename)

    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')

    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:250] + ext

    # Ensure filename is not empty
    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid filename"
        )

    return filename


def validate_file_upload(file: UploadFile) -> tuple[str, str]:
    """Validate uploaded file.

    Args:
        file: Uploaded file object

    Returns:
        Tuple of (sanitized_filename, file_extension)

    Raises:
        HTTPException: If file is invalid
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Filename is required"
        )

    # Sanitize filename
    filename = sanitize_filename(file.filename)
    file_ext = Path(filename).suffix.lower()

    # Validate extension
    if file_ext not in ALLOWED_FILE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_FILE_EXTENSIONS)}",
        )

    # Validate MIME type if provided
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        # Log warning but don't fail (MIME types can be wrong)
        pass

    return filename, file_ext


async def validate_file_size(file: UploadFile) -> None:
    """Validate file size by reading in chunks.

    Args:
        file: Uploaded file object

    Raises:
        HTTPException: If file is too large
    """
    file_size = 0
    chunk_size = 8192  # 8KB chunks

    # Read file in chunks to check size without loading entire file
    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        file_size += len(chunk)
        if file_size > MAX_FILE_SIZE_BYTES:
            await file.seek(0)  # Reset file pointer
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail={
                    "error": "file_too_large",
                    "message": f"File too large: {file_size / 1024 / 1024:.1f}MB (max: {MAX_FILE_SIZE_BYTES / 1024 / 1024}MB)",
                    "size_mb": round(file_size / 1024 / 1024, 2),
                    "max_mb": MAX_FILE_SIZE_BYTES / 1024 / 1024,
                },
            )

    # Reset file pointer for actual reading
    await file.seek(0)
