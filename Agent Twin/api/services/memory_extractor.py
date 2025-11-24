"""
Memory Extraction Service
Extracts writing style, facts, and personal info from content using Gemini
"""
from django.contrib.auth.models import User
from ..models import WritingStyle, Experience, PersonalInfo, DocumentMemory
from .gemini_service import extract_writing_style, extract_facts_and_experiences, analyze_image
import json


def update_writing_style(user, style_data):
    """
    Update or create writing style for a user.
    Merges new style data with existing style.
    """
    style, created = WritingStyle.objects.get_or_create(user=user)
    
    # Update fields
    if 'tone_formality' in style_data:
        style.tone_formality = style_data['tone_formality']
    if 'average_sentence_length' in style_data:
        # Average with existing if not new
        if created:
            style.average_sentence_length = style_data['average_sentence_length']
        else:
            # Weighted average (favor new data slightly)
            style.average_sentence_length = (
                style.average_sentence_length * 0.6 + 
                style_data['average_sentence_length'] * 0.4
            )
    
    # Merge vocabulary keywords (unique list)
    if 'vocabulary_keywords' in style_data:
        existing = set(style.vocabulary_keywords or [])
        new = set(style_data['vocabulary_keywords'] or [])
        style.vocabulary_keywords = list(existing | new)
    
    # Merge signature phrases (unique list)
    if 'signature_phrases' in style_data:
        existing = set(style.signature_phrases or [])
        new = set(style_data['signature_phrases'] or [])
        style.signature_phrases = list(existing | new)
    
    # Merge sentence structure patterns
    if 'sentence_structure' in style_data:
        if not style.sentence_structure_patterns:
            style.sentence_structure_patterns = {}
        style.sentence_structure_patterns['primary'] = style_data['sentence_structure']
    
    style.save()
    return style


def save_experiences(user, experiences_data, document_memory=None, memory_type='text', source='upload'):
    """
    Save experiences extracted from content.
    Avoids duplicates by checking title + company.
    
    Args:
        user: User object
        experiences_data: List of experience dictionaries
        document_memory: Optional DocumentMemory object
        memory_type: Type of memory ('text', 'image', 'conversation')
        source: Source of the data ('upload', 'conversation', etc.)
    """
    saved_experiences = []
    
    for exp_data in experiences_data:
        # Check if experience already exists
        existing = Experience.objects.filter(
            user=user,
            title=exp_data.get('title', ''),
            company=exp_data.get('company') or ''
        ).first()
        
        if existing:
            # Update existing experience
            if exp_data.get('achievements'):
                existing_achievements = set(existing.achievements or [])
                new_achievements = set(exp_data.get('achievements', []))
                existing.achievements = list(existing_achievements | new_achievements)
            
            if exp_data.get('tech_stack'):
                existing_tech = set(existing.tech_stack or [])
                new_tech = set(exp_data.get('tech_stack', []))
                existing.tech_stack = list(existing_tech | new_tech)
            
            existing.save()
            saved_experiences.append(existing)
        else:
            # Create new experience
            experience = Experience.objects.create(
                user=user,
                title=exp_data.get('title', 'Unknown'),
                company=exp_data.get('company'),
                position=exp_data.get('position'),
                description=exp_data.get('description', ''),
                achievements=exp_data.get('achievements', []),
                tech_stack=exp_data.get('tech_stack', []),
                start_date=exp_data.get('start_date'),
                end_date=exp_data.get('end_date'),
                detected_from_sample=True,
                memory_type=memory_type,
                source_document=document_memory
            )
            saved_experiences.append(experience)
    
    return saved_experiences


def save_personal_info(user, personal_info_data, source='upload'):
    """
    Save personal information as key-value pairs.
    Detects and consolidates related information to avoid duplicates.
    Updates existing keys if confidence is higher or if new information can be merged.
    """
    saved_info = []
    
    # Get all existing personal info for this user
    existing_info = {info.key: info for info in PersonalInfo.objects.filter(user=user)}
    
    for key, value in personal_info_data.items():
        if not value:  # Skip empty values
            continue
        
        # Convert value to string if it's a list/dict
        if isinstance(value, (list, dict)):
            value_str = json.dumps(value)
        else:
            value_str = str(value)
        
        value_lower = value_str.lower()
        
        # Check if exact key already exists
        if key in existing_info:
            existing = existing_info[key]
            existing_value = existing.value
            existing_lower = existing_value.lower()
            
            # If new value is more detailed or different, update
            if source == 'upload' or existing.confidence < 0.8:
                # Check if new value is a superset of existing (contains more info)
                if len(value_str) > len(existing_value) and existing_lower in value_lower:
                    # New value contains existing value + more info - update
                    existing.value = value_str
                    existing.confidence = 0.9 if source == 'upload' else 0.7
                    existing.source = source
                    existing.save()
                    saved_info.append(existing)
                elif value_lower != existing_lower:
                    # Different value - update if higher confidence
                    existing.value = value_str
                    existing.confidence = 0.9 if source == 'upload' else 0.7
                    existing.source = source
                    existing.save()
                    saved_info.append(existing)
        else:
            # Check if this information is already contained in existing entries
            already_contained = False
            
            # Check if "background" already contains this info
            if 'background' in existing_info:
                bg_value = existing_info['background'].value.lower()
                # If the new value is already in background, skip creating duplicate
                if value_lower in bg_value:
                    already_contained = True
                    # But update background if new info is more comprehensive
                    if key in ['major', 'university'] and len(value_str) > 50:
                        # This might be more detailed - update background
                        existing_info['background'].value = value_str
                        existing_info['background'].confidence = 0.9 if source == 'upload' else 0.7
                        existing_info['background'].source = source
                        existing_info['background'].save()
                        saved_info.append(existing_info['background'])
            
            # Check if specific keys (major, university) already exist and contain this info
            if not already_contained:
                if key == 'major' and 'major' in existing_info:
                    if value_lower in existing_info['major'].value.lower():
                        already_contained = True
                elif key == 'university' and 'university' in existing_info:
                    if value_lower in existing_info['university'].value.lower():
                        already_contained = True
            
            # If info is already contained, skip creating duplicate
            if not already_contained:
                # Check if we should update "background" instead of creating a new key
                if key in ['major', 'university'] and 'background' in existing_info:
                    bg_value = existing_info['background'].value.lower()
                    # If background doesn't contain this specific info, we can create the specific key
                    # (This allows both to exist - background for overview, specific keys for details)
                    pass
                
                # Create new entry
                info = PersonalInfo.objects.create(
                    user=user,
                    key=key,
                    value=value_str,
                    confidence=0.9 if source == 'upload' else 0.7,
                    source=source
                )
                saved_info.append(info)
    
    return saved_info


def extract_and_save_memory(user, text_content, content_type='text', file_path=None):
    """
    Main function: Extract memory from content and save to database.
    
    Args:
        user: User object
        text_content: Text to analyze (or extracted from image/audio)
        content_type: 'text', 'image', 'audio', 'pdf'
        file_path: Path to file if applicable
        
    Returns:
        dict: Summary of what was extracted and saved
    """
    # Extract writing style
    style_data = extract_writing_style(text_content)
    writing_style = update_writing_style(user, style_data)
    
    # Extract facts and experiences
    facts_data = extract_facts_and_experiences(text_content)
    
    # Create document memory record
    document_memory = DocumentMemory.objects.create(
        user=user,
        content_type=content_type,
        raw_text=text_content,
        file_path=file_path,
        extracted_style_signals=style_data,
        extracted_facts=facts_data
    )
    
    # Save experiences
    experiences = save_experiences(
        user,
        facts_data.get('experiences', []),
        document_memory=document_memory,
        memory_type=content_type
    )
    
    # Save personal info
    personal_info = save_personal_info(
        user,
        facts_data.get('personal_info', {}),
        source='upload'
    )
    
    return {
        'document_memory_id': document_memory.id,
        'writing_style_updated': True,
        'experiences_saved': len(experiences),
        'personal_info_saved': len(personal_info),
        'extracted_style': style_data,
        'extracted_facts': facts_data
    }


def extract_from_image(user, image_path):
    """
    Extract memory from an image using Gemini Vision.
    """
    # Analyze image
    facts_data = analyze_image(image_path)
    
    # Create document memory record
    document_memory = DocumentMemory.objects.create(
        user=user,
        content_type='image',
        file_path=image_path,
        extracted_facts=facts_data
    )
    
    # Save experiences from image
    experiences = save_experiences(
        user,
        facts_data.get('experiences', []),
        document_memory=document_memory,
        memory_type='image'
    )
    
    # Save personal info from image
    personal_info = save_personal_info(
        user,
        facts_data.get('personal_info', {}),
        source='upload'
    )
    
    return {
        'document_memory_id': document_memory.id,
        'experiences_saved': len(experiences),
        'personal_info_saved': len(personal_info),
        'extracted_facts': facts_data
    }
