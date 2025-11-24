"""
Memory Retrieval Service
Retrieves and formats user memories for content generation
"""
from django.contrib.auth.models import User
from ..models import WritingStyle, Experience, PersonalInfo, DocumentMemory
from datetime import datetime


def get_user_memory_context(user):
    """
    Retrieve all user memories and format for content generation.
    
    Returns:
        dict: Formatted memory context with style, experiences, and personal info
    """
    # Get writing style
    try:
        writing_style = WritingStyle.objects.get(user=user)
        style_context = {
            'tone_formality': writing_style.tone_formality,
            'average_sentence_length': writing_style.average_sentence_length,
            'vocabulary_keywords': writing_style.vocabulary_keywords or [],
            'signature_phrases': writing_style.signature_phrases or [],
            'sentence_structure': writing_style.sentence_structure_patterns.get('primary', 'mixed') if writing_style.sentence_structure_patterns else 'mixed'
        }
    except WritingStyle.DoesNotExist:
        style_context = {
            'tone_formality': 'professional',
            'average_sentence_length': 15,
            'vocabulary_keywords': [],
            'signature_phrases': [],
            'sentence_structure': 'mixed'
        }
    
    # Get all experiences
    experiences = Experience.objects.filter(user=user).order_by('-created_at')
    experiences_list = []
    for exp in experiences:
        experiences_list.append({
            'title': exp.title,
            'company': exp.company,
            'position': exp.position,
            'description': exp.description,
            'achievements': exp.achievements or [],
            'tech_stack': exp.tech_stack or [],
            'start_date': exp.start_date.isoformat() if exp.start_date else None,
            'end_date': exp.end_date.isoformat() if exp.end_date else None,
        })
    
    # Get all personal info
    personal_info_list = PersonalInfo.objects.filter(user=user)
    personal_info_dict = {}
    for info in personal_info_list:
        # Try to parse JSON, otherwise use as string
        try:
            import json
            value = json.loads(info.value)
        except (json.JSONDecodeError, TypeError):
            value = info.value
        personal_info_dict[info.key] = value
    
    return {
        'style': style_context,
        'experiences': experiences_list,
        'personal_info': personal_info_dict
    }


def get_memory_timeline(user):
    """
    Get chronological timeline of all memories for display.
    
    Returns:
        list: Timeline entries with type, description, and date
    """
    timeline = []
    
    # Writing style updates
    try:
        style = WritingStyle.objects.get(user=user)
        timeline.append({
            'date': style.last_updated.isoformat(),
            'type': 'style_learned',
            'description': f"Learned {style.tone_formality} writing style",
            'source': 'writing_style',
            'details': {
                'tone': style.tone_formality,
                'avg_sentence_length': style.average_sentence_length
            }
        })
    except WritingStyle.DoesNotExist:
        pass
    
    # Experiences
    experiences = Experience.objects.filter(user=user).order_by('-created_at')
    for exp in experiences:
        timeline.append({
            'date': exp.created_at.isoformat(),
            'type': 'experience_discovered',
            'description': f"Discovered: {exp.title}" + (f" at {exp.company}" if exp.company else ""),
            'source': 'experience',
            'memory_type': exp.memory_type,
            'details': {
                'title': exp.title,
                'company': exp.company,
                'position': exp.position,
                'achievements': exp.achievements or []
            }
        })
    
    # Personal info - group related entries
    personal_info = PersonalInfo.objects.filter(user=user).order_by('-created_at')
    
    # Group related personal info entries
    grouped_info = {}
    for info in personal_info:
        # Check if this info is related to existing grouped entries
        key = info.key
        value = str(info.value).lower()
        
        # Group related keys together
        group_key = None
        if key in ['background', 'major', 'university', 'education']:
            # Education-related info
            group_key = 'education'
        elif key in ['name', 'full_name']:
            group_key = 'identity'
        elif key in ['interests', 'hobbies']:
            group_key = 'interests'
        else:
            group_key = key  # Use key as group key for others
        
        if group_key not in grouped_info:
            grouped_info[group_key] = []
        grouped_info[group_key].append(info)
    
    # Create timeline entries for grouped info
    for group_key, info_list in grouped_info.items():
        # Sort by creation date (newest first)
        info_list.sort(key=lambda x: x.created_at, reverse=True)
        
        # Use the most recent entry as the primary one
        primary_info = info_list[0]
        
        # Build consolidated description
        if group_key == 'education':
            # Consolidate education-related info
            descriptions = []
            for info in info_list:
                if info.key == 'background':
                    descriptions.append(f"Background: {str(info.value)[:60]}")
                elif info.key == 'major':
                    descriptions.append(f"Major: {str(info.value)}")
                elif info.key == 'university':
                    descriptions.append(f"University: {str(info.value)}")
                else:
                    descriptions.append(f"{info.key}: {str(info.value)[:40]}")
            
            if len(descriptions) > 1:
                # Multiple related entries - consolidate
                timeline.append({
                    'date': primary_info.created_at.isoformat(),
                    'type': 'personal_info_learned',
                    'description': f"Learned education: {', '.join(descriptions[:2])}",
                    'source': 'personal_info',
                    'grouped': True,
                    'details': {
                        'group': 'education',
                        'entries': [{'key': info.key, 'value': info.value} for info in info_list]
                    }
                })
            else:
                # Single entry
                timeline.append({
                    'date': primary_info.created_at.isoformat(),
                    'type': 'personal_info_learned',
                    'description': f"Learned {primary_info.key}: {str(primary_info.value)[:50]}",
                    'source': 'personal_info',
                    'details': {
                        'key': primary_info.key,
                        'value': primary_info.value,
                        'confidence': primary_info.confidence
                    }
                })
        else:
            # Non-grouped entries - show individually
            for info in info_list:
                timeline.append({
                    'date': info.created_at.isoformat(),
                    'type': 'personal_info_learned',
                    'description': f"Learned {info.key}: {str(info.value)[:50]}",
                    'source': 'personal_info',
                    'details': {
                        'key': info.key,
                        'value': info.value,
                        'confidence': info.confidence
                    }
                })
    
    # Document memories
    documents = DocumentMemory.objects.filter(user=user).order_by('-created_at')
    for doc in documents:
        timeline.append({
            'date': doc.created_at.isoformat(),
            'type': 'document_uploaded',
            'description': f"Uploaded {doc.content_type} document",
            'source': 'document',
            'details': {
                'content_type': doc.content_type,
                'has_style_extraction': bool(doc.extracted_style_signals),
                'has_facts_extraction': bool(doc.extracted_facts)
            }
        })
    
    # Sort by date (newest first)
    timeline.sort(key=lambda x: x['date'], reverse=True)
    
    return timeline
