"""
File Validation Utilities
"""
import os
from pathlib import Path


# Allowed file types
ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
ALLOWED_AUDIO_EXTENSIONS = {'.mp3', '.wav', '.m4a', '.ogg', '.flac'}
ALLOWED_DOCUMENT_EXTENSIONS = {'.pdf', '.txt', '.md', '.docx'}
ALLOWED_EXTENSIONS = ALLOWED_IMAGE_EXTENSIONS | ALLOWED_AUDIO_EXTENSIONS | ALLOWED_DOCUMENT_EXTENSIONS

# Max file sizes (in bytes)
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_AUDIO_SIZE = 50 * 1024 * 1024  # 50MB
MAX_PDF_SIZE = 20 * 1024 * 1024  # 20MB


def validate_file_extension(filename):
    """
    Validate file extension.
    
    Args:
        filename: Name of the file
        
    Returns:
        tuple: (is_valid, content_type, error_message)
    """
    ext = Path(filename).suffix.lower()
    
    if not ext:
        return False, None, "File has no extension"
    
    if ext not in ALLOWED_EXTENSIONS:
        return False, None, f"File type {ext} not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
    
    # Determine content type
    if ext in ALLOWED_IMAGE_EXTENSIONS:
        content_type = 'image'
    elif ext in ALLOWED_AUDIO_EXTENSIONS:
        content_type = 'audio'
    elif ext in ALLOWED_DOCUMENT_EXTENSIONS:
        content_type = 'pdf' if ext == '.pdf' else 'text'
    else:
        content_type = 'text'
    
    return True, content_type, None


def validate_file_size(file, content_type=None):
    """
    Validate file size.
    
    Args:
        file: File object or size in bytes
        content_type: Type of content
        
    Returns:
        tuple: (is_valid, error_message)
    """
    # Get file size
    if hasattr(file, 'size'):
        size = file.size
    elif hasattr(file, 'read'):
        # Read file to get size
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)
    else:
        size = file
    
    # Check against appropriate limit
    if content_type == 'image':
        max_size = MAX_IMAGE_SIZE
    elif content_type == 'audio':
        max_size = MAX_AUDIO_SIZE
    elif content_type == 'pdf':
        max_size = MAX_PDF_SIZE
    else:
        max_size = MAX_FILE_SIZE
    
    if size > max_size:
        max_mb = max_size / (1024 * 1024)
        return False, f"File too large. Maximum size: {max_mb}MB"
    
    return True, None


def validate_upload(file, user_id=None):
    """
    Complete validation for file upload.
    
    Args:
        file: Uploaded file object
        user_id: Optional user ID
        
    Returns:
        tuple: (is_valid, content_type, error_message)
    """
    # Validate extension
    is_valid, content_type, error = validate_file_extension(file.name)
    if not is_valid:
        return False, None, error
    
    # Validate size
    is_valid, error = validate_file_size(file, content_type)
    if not is_valid:
        return False, None, error
    
    return True, content_type, None

