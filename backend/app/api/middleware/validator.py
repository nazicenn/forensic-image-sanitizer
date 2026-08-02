"""
File Validator - Validate uploaded files.
"""

from fastapi import UploadFile, HTTPException
import hashlib
import os
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

# Allowed file types
ALLOWED_IMAGE_TYPES = {
    'image/jpeg': ['.jpg', '.jpeg'],
    'image/png': ['.png'],
    'image/webp': ['.webp'],
    'image/tiff': ['.tiff', '.tif'],
    'image/bmp': ['.bmp'],
}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


async def validate_file(file: UploadFile) -> Tuple[bool, str]:
    """
    Validate uploaded file.

    Args:
        file: Uploaded file

    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    # 1. Check file size
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)

    if size > MAX_FILE_SIZE:
        return False, f"File size exceeds {MAX_FILE_SIZE // (1024 * 1024)}MB limit"

    # 2. Check content type
    content_type = file.content_type
    if content_type not in ALLOWED_IMAGE_TYPES:
        return False, f"Unsupported file type: {content_type}. Allowed: {', '.join(ALLOWED_IMAGE_TYPES.keys())}"

    # 3. Check file extension
    filename = file.filename or "unknown"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_IMAGE_TYPES.get(content_type, []):
        return False, f"File extension {ext} does not match content type {content_type}"

    return True, ""


async def validate_file_upload(file: UploadFile) -> UploadFile:
    """
    Validate and return file.

    Args:
        file: Uploaded file

    Returns:
        UploadFile: Validated file

    Raises:
        HTTPException: If validation fails
    """
    is_valid, error_message = await validate_file(file)

    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail=error_message
        )

    return file


def calculate_file_hash(file: UploadFile) -> str:
    """
    Calculate SHA-256 hash of file.

    Args:
        file: Uploaded file

    Returns:
        str: SHA-256 hash
    """
    hasher = hashlib.sha256()
    content = file.file.read()
    hasher.update(content)
    file.file.seek(0)
    return hasher.hexdigest()