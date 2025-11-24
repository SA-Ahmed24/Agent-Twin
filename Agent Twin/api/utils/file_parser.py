"""
File Parser Utility
Handles parsing of different file types (PDF, text, images, audio)
"""
import os
from pathlib import Path


def extract_text_from_pdf(pdf_path):
    """
    Extract text from PDF file.
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        str: Extracted text
    """
    try:
        import PyPDF2
        
        text = ""
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        
        return text.strip()
    except Exception as e:
        raise Exception(f"Error extracting text from PDF: {str(e)}")


def extract_text_from_file(file_path, content_type=None):
    """
    Extract text from various file types.
    
    Args:
        file_path: Path to file
        content_type: Optional content type hint
        
    Returns:
        tuple: (text_content, detected_type)
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Detect file type from extension if not provided
    if not content_type:
        ext = Path(file_path).suffix.lower()
        if ext == '.pdf':
            content_type = 'pdf'
        elif ext in ['.txt', '.md']:
            content_type = 'text'
        elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
            content_type = 'image'
        elif ext in ['.mp3', '.wav', '.m4a', '.ogg']:
            content_type = 'audio'
        else:
            content_type = 'text'  # Default
    
    # Extract text based on type
    if content_type == 'pdf':
        text = extract_text_from_pdf(file_path)
        return text, 'pdf'
    
    elif content_type == 'text':
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
        return text, 'text'
    
    elif content_type == 'image':
        # For images, we'll return empty text - analysis happens via Gemini Vision
        return "", 'image'
    
    elif content_type == 'audio':
        # For audio, we'll need transcription (to be implemented)
        # For now, return empty
        return "", 'audio'
    
    else:
        # Try to read as text
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
            return text, 'text'
        except:
            return "", 'unknown'


def save_uploaded_file(uploaded_file, user, upload_dir='media/uploads', use_media_root=True):
    """
    Save uploaded file to disk.
    
    Args:
        uploaded_file: Django UploadedFile object
        user: User object or username string
        upload_dir: Base upload directory (relative to MEDIA_ROOT if use_media_root=True)
        use_media_root: If True, prepend MEDIA_ROOT to upload_dir
        
    Returns:
        str: Relative path to saved file (from MEDIA_ROOT)
    """
    from django.conf import settings
    
    # Get username
    username = user.username if hasattr(user, 'username') else str(user)
    
    # Build full path
    if use_media_root:
        base_dir = settings.MEDIA_ROOT
        full_upload_dir = os.path.join(base_dir, upload_dir)
    else:
        full_upload_dir = upload_dir
    
    # Create user-specific directory
    user_dir = os.path.join(full_upload_dir, username)
    os.makedirs(user_dir, exist_ok=True)
    
    # Generate unique filename
    filename = uploaded_file.name
    file_path = os.path.join(user_dir, filename)
    
    # Handle filename conflicts
    counter = 1
    base_name, ext = os.path.splitext(filename)
    while os.path.exists(file_path):
        filename = f"{base_name}_{counter}{ext}"
        file_path = os.path.join(user_dir, filename)
        counter += 1
    
    # Save file
    with open(file_path, 'wb+') as destination:
        for chunk in uploaded_file.chunks():
            destination.write(chunk)
    
    # Return relative path from MEDIA_ROOT
    if use_media_root:
        relative_path = os.path.relpath(file_path, settings.MEDIA_ROOT)
        return relative_path
    else:
        return file_path

