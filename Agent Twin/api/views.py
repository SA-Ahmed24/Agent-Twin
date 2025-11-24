"""
API Views for Agent Twin
"""
import json
import os
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.conf import settings

from .services.memory_extractor import extract_and_save_memory, extract_from_image
from .services.memory_retriever import get_user_memory_context, get_memory_timeline
from .services.gemini_service import generate_content as gemini_generate_content
from .utils.file_parser import extract_text_from_file, save_uploaded_file
from .utils.validators import validate_upload
from .models import WritingStyle, Experience, PersonalInfo, DocumentMemory, UserProfile, VoiceProfile, VoiceShareToken


def index(request):
    """Serve the frontend HTML - redirect to login if not authenticated"""
    # Check if user is authenticated
    if not request.user.is_authenticated:
        from django.shortcuts import redirect
        return redirect('/login/')
    
    frontend_path = os.path.join(settings.BASE_DIR, 'frontend', 'index.html')
    try:
        with open(frontend_path, 'r') as f:
            return HttpResponse(f.read(), content_type='text/html')
    except FileNotFoundError:
        return HttpResponse("Frontend not found", status=404)


def login_page(request):
    """Serve login page"""
    frontend_path = os.path.join(settings.BASE_DIR, 'frontend', 'login.html')
    try:
        with open(frontend_path, 'r') as f:
            return HttpResponse(f.read(), content_type='text/html')
    except FileNotFoundError:
        return HttpResponse("Login page not found", status=404)


def signup_page(request):
    """Serve signup page"""
    frontend_path = os.path.join(settings.BASE_DIR, 'frontend', 'signup.html')
    try:
        with open(frontend_path, 'r') as f:
            return HttpResponse(f.read(), content_type='text/html')
    except FileNotFoundError:
        return HttpResponse("Signup page not found", status=404)


def onboarding_page(request):
    """Serve onboarding page - redirect to login if not authenticated"""
    # Check if user is authenticated
    if not request.user.is_authenticated:
        from django.shortcuts import redirect
        return redirect('/login/')
    
    frontend_path = os.path.join(settings.BASE_DIR, 'frontend', 'onboarding.html')
    try:
        with open(frontend_path, 'r') as f:
            return HttpResponse(f.read(), content_type='text/html')
    except FileNotFoundError:
        return HttpResponse("Onboarding page not found", status=404)


def timeline_page(request):
    """Serve timeline page - redirect to login if not authenticated"""
    # Check if user is authenticated
    if not request.user.is_authenticated:
        from django.shortcuts import redirect
        return redirect('/login/')
    
    frontend_path = os.path.join(settings.BASE_DIR, 'frontend', 'timeline.html')
    try:
        with open(frontend_path, 'r') as f:
            return HttpResponse(f.read(), content_type='text/html')
    except FileNotFoundError:
        return HttpResponse("Timeline page not found", status=404)


def voice_page(request):
    """Serve voice agent page - redirect to login if not authenticated"""
    # Check if user is authenticated
    if not request.user.is_authenticated:
        from django.shortcuts import redirect
        return redirect('/login/')
    
    frontend_path = os.path.join(settings.BASE_DIR, 'frontend', 'voice.html')
    try:
        with open(frontend_path, 'r') as f:
            return HttpResponse(f.read(), content_type='text/html')
    except FileNotFoundError:
        return HttpResponse("Voice page not found", status=404)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def onboarding_upload(request):
    """
    Bulk upload for onboarding.
    Accepts multiple files.
    """
    try:
        user = request.user
        files = request.FILES.getlist('files')
        
        if not files:
            return JsonResponse({
                'error': 'No files provided'
            }, status=400)
        
        results = []
        total_experiences = 0
        total_personal_info = 0
        
        for file in files:
            # Validate file
            is_valid, content_type, error = validate_upload(file, user.username)
            if not is_valid:
                results.append({
                    'filename': file.name,
                    'error': error
                })
                continue
            
            # Save file (returns relative path from MEDIA_ROOT)
            file_path = save_uploaded_file(file, user)
            full_file_path = os.path.join(settings.MEDIA_ROOT, file_path)
            
            # Process file
            try:
                if content_type in ['text', 'pdf']:
                    text_content, _ = extract_text_from_file(full_file_path, content_type)
                    if text_content:
                        result = extract_and_save_memory(
                            user=user,
                            text_content=text_content,
                            content_type=content_type,
                            file_path=file_path
                        )
                        total_experiences += result.get('experiences_saved', 0)
                        total_personal_info += result.get('personal_info_saved', 0)
                        results.append({
                            'filename': file.name,
                            'success': True,
                            'experiences': result.get('experiences_saved', 0),
                            'personal_info': result.get('personal_info_saved', 0)
                        })
                    else:
                        results.append({
                            'filename': file.name,
                            'error': 'Could not extract text'
                        })
                
                elif content_type == 'image':
                    result = extract_from_image(user, full_file_path)
                    total_experiences += result.get('experiences_saved', 0)
                    total_personal_info += result.get('personal_info_saved', 0)
                    results.append({
                        'filename': file.name,
                        'success': True,
                        'experiences': result.get('experiences_saved', 0),
                        'personal_info': result.get('personal_info_saved', 0)
                    })
                
                else:
                    results.append({
                        'filename': file.name,
                        'error': f'Unsupported type: {content_type}'
                    })
            
            except Exception as e:
                results.append({
                    'filename': file.name,
                    'error': str(e)
                })
        
        # Mark onboarding as complete
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.onboarding_completed = True
        profile.save()
        
        return JsonResponse({
            'success': True,
            'results': results,
            'summary': {
                'total_files': len(files),
                'total_experiences': total_experiences,
                'total_personal_info': total_personal_info
            }
        })
    
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
@login_required
def onboarding_status(request):
    """Get onboarding status"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    return JsonResponse({
        'onboarding_completed': profile.onboarding_completed
    })


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def upload_sample(request):
    """
    Upload a writing sample (text, file, image, audio) for analysis.
    """
    try:
        user = request.user
        
        # Check if text is provided directly
        text_content = request.POST.get('text', '').strip()
        file = request.FILES.get('file')
        
        if not text_content and not file:
            return JsonResponse({
                'error': 'Either "text" or "file" must be provided'
            }, status=400)
        
        # Handle file upload
        if file:
            # Validate file
            is_valid, content_type, error = validate_upload(file, user.username)
            if not is_valid:
                return JsonResponse({
                    'error': error
                }, status=400)
            
            # Save file (returns relative path from MEDIA_ROOT)
            file_path = save_uploaded_file(file, user)
            full_file_path = os.path.join(settings.MEDIA_ROOT, file_path)
            
            # Extract text from file (if applicable)
            if content_type in ['text', 'pdf']:
                text_content, _ = extract_text_from_file(full_file_path, content_type)
                if not text_content:
                    return JsonResponse({
                        'error': 'Could not extract text from file'
                    }, status=400)
                
                # Extract and save memory
                result = extract_and_save_memory(
                    user=user,
                    text_content=text_content,
                    content_type=content_type,
                    file_path=file_path
                )
            
            elif content_type == 'image':
                # Use Gemini Vision API
                result = extract_from_image(user, file_path)
            
            elif content_type == 'audio':
                return JsonResponse({
                    'error': 'Audio transcription not yet implemented. Please extract text manually and upload as text.'
                }, status=501)
            
            else:
                return JsonResponse({
                    'error': f'Unsupported content type: {content_type}'
                }, status=400)
        
        # Handle direct text upload
        elif text_content:
            result = extract_and_save_memory(
                user=user,
                text_content=text_content,
                content_type='text'
            )
        
        return JsonResponse({
            'success': True,
            'message': 'Memory extracted and saved successfully',
            'result': {
                'document_memory_id': result.get('document_memory_id'),
                'writing_style_updated': result.get('writing_style_updated', False),
                'experiences_saved': result.get('experiences_saved', 0),
                'personal_info_saved': result.get('personal_info_saved', 0),
            },
            'extracted_style': result.get('extracted_style', {}),
            'extracted_facts': result.get('extracted_facts', {})
        })
    
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def generate_content(request):
    """
    Generate content using user's writing style and memories.
    """
    try:
        user = request.user
        
        # Parse request body
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = {
                'prompt': request.POST.get('prompt', ''),
                'content_type': request.POST.get('content_type', 'general')
            }
        
        prompt = data.get('prompt', '').strip()
        conversation_history = data.get('conversation_history', [])  # List of {role, content}
        
        if not prompt:
            return JsonResponse({
                'error': 'prompt is required'
            }, status=400)
        
        # Get user memory context
        memory_context = get_user_memory_context(user)
        
        # Generate content using Gemini with conversation history
        generated_text = gemini_generate_content(
            user_prompt=prompt,
            style_context=memory_context['style'],
            experiences=memory_context['experiences'],
            personal_info=memory_context['personal_info'],
            conversation_history=conversation_history
        )
        
        # Extract memory from recent conversation if there's substantial content
        memory_extracted = False
        if conversation_history and len(conversation_history) >= 2:
            # Get last few messages for context
            recent_messages = conversation_history[-4:] + [{'role': 'user', 'content': prompt}]
            conversation_text = "\n".join([f"{msg.get('role', 'user')}: {msg.get('content', '')}" for msg in recent_messages])
            
            # Extract memory from conversation
            from .services.gemini_service import extract_memory_from_conversation
            extracted_memory = extract_memory_from_conversation(conversation_text)
            
            # Only save if there's actually new information
            if (extracted_memory.get('experiences') or 
                extracted_memory.get('personal_info') or 
                extracted_memory.get('new_achievements')):
                # Save extracted memory
                from .services.memory_extractor import save_experiences, save_personal_info
                experiences_saved = save_experiences(
                    user,
                    extracted_memory.get('experiences', []),
                    document_memory=None,
                    memory_type='conversation',
                    source='conversation'
                )
                personal_info_saved = save_personal_info(
                    user,
                    extracted_memory.get('personal_info', {}),
                    source='conversation'
                )
                memory_extracted = len(experiences_saved) > 0 or len(personal_info_saved) > 0
        
        return JsonResponse({
            'success': True,
            'generated_content': generated_text,
            'memory_extracted': memory_extracted,
            'used_memories': {
                'style_signals': list(memory_context['style'].keys()),
                'experiences_count': len(memory_context['experiences']),
                'personal_info_keys': list(memory_context['personal_info'].keys())
            }
        })
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in generate_content view: {e}")
        print(error_trace)
        return JsonResponse({
            'error': str(e),
            'details': error_trace if settings.DEBUG else None
        }, status=500)


@require_http_methods(["GET"])
@login_required
def view_memory(request):
    """
    View all stored memories for a user.
    """
    try:
        user = request.user
        print(f"View memory called for user: {user.username}")
        
        # Get memory context
        memory_context = get_user_memory_context(user)
        print(f"Memory context retrieved: {len(memory_context.get('experiences', []))} experiences")
        
        # Get timeline
        timeline = get_memory_timeline(user)
        print(f"Timeline retrieved: {len(timeline)} entries")
        
        # Get document memories
        documents = DocumentMemory.objects.filter(user=user).order_by('-created_at')
        document_list = []
        for doc in documents:
            document_list.append({
                'id': doc.id,
                'content_type': doc.content_type,
                'created_at': doc.created_at.isoformat(),
                'has_style_extraction': bool(doc.extracted_style_signals),
                'has_facts_extraction': bool(doc.extracted_facts)
            })
        
        response_data = {
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username
            },
            'writing_style': memory_context['style'],
            'experiences': memory_context['experiences'],
            'personal_info': memory_context['personal_info'],
            'document_memories': document_list,
            'timeline': timeline,
            'summary': {
                'total_experiences': len(memory_context['experiences']),
                'total_personal_info': len(memory_context['personal_info']),
                'total_documents': len(document_list),
                'timeline_entries': len(timeline)
            }
        }
        
        print(f"Returning response with {len(timeline)} timeline entries")
        return JsonResponse(response_data)
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in view_memory: {e}")
        print(error_trace)
        return JsonResponse({
            'success': False,
            'error': str(e),
            'details': error_trace if settings.DEBUG else None
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def reset_memory(request):
    """
    Reset all memories for a user.
    """
    try:
        user = request.user
        
        # Parse request body
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = {
                'confirm': request.POST.get('confirm', 'false').lower() == 'true'
            }
        
        confirm = data.get('confirm', False)
        
        if not confirm:
            return JsonResponse({
                'error': 'Must set "confirm": true to reset memory'
            }, status=400)
        
        # Delete all memories
        deleted_counts = {
            'writing_styles': WritingStyle.objects.filter(user=user).delete()[0],
            'experiences': Experience.objects.filter(user=user).delete()[0],
            'personal_info': PersonalInfo.objects.filter(user=user).delete()[0],
            'documents': DocumentMemory.objects.filter(user=user).delete()[0]
        }
        
        total_deleted = sum(deleted_counts.values())
        
        return JsonResponse({
            'success': True,
            'message': f'All memories cleared for user {user.username}',
            'deleted_counts': deleted_counts,
            'total_deleted': total_deleted
        })
    
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def upload_voice_sample(request):
    """
    Upload a voice sample for voice cloning.
    Accepts audio file (WAV, MP3, etc.) - at least 30 seconds recommended.
    """
    try:
        user = request.user
        
        if 'audio_file' not in request.FILES:
            return JsonResponse({
                'error': 'audio_file is required'
            }, status=400)
        
        audio_file = request.FILES['audio_file']
        
        # Validate file type (allow webm from MediaRecorder)
        allowed_types = ['audio/wav', 'audio/mpeg', 'audio/mp3', 'audio/webm', 'audio/ogg', 'audio/webm;codecs=opus']
        # Also check if content_type is None (some browsers don't set it for webm)
        if audio_file.content_type and audio_file.content_type not in allowed_types:
            # Check file extension as fallback
            file_name = audio_file.name.lower()
            if not any(file_name.endswith(ext) for ext in ['.wav', '.mp3', '.webm', '.ogg', '.m4a']):
                return JsonResponse({
                    'error': f'Invalid file type. Allowed: {", ".join(allowed_types)}'
                }, status=400)
        
        # Validate file size (max 10MB)
        if audio_file.size > 10 * 1024 * 1024:
            return JsonResponse({
                'error': 'File size too large. Maximum 10MB allowed.'
            }, status=400)
        
        # Save file (returns relative path from MEDIA_ROOT)
        file_path = save_uploaded_file(audio_file, user.username, 'voice_samples', use_media_root=True)
        full_file_path = os.path.join(settings.MEDIA_ROOT, file_path)
        
        # Verify file exists
        if not os.path.exists(full_file_path):
            return JsonResponse({
                'error': f'Audio file not found after save: {full_file_path}'
            }, status=500)
        
        # Get or create voice profile
        voice_profile, created = VoiceProfile.objects.get_or_create(user=user)
        voice_profile.voice_sample_file = file_path
        voice_profile.tts_service = 'elevenlabs'
        
        # Create voice clone with ElevenLabs
        from .services.voice_service import create_voice_clone
        voice_name = f"{user.username}_voice"
        clone_result = create_voice_clone(full_file_path, voice_name)
        
        if clone_result.get('success'):
            voice_profile.voice_clone_id = clone_result['voice_id']
            voice_profile.is_active = True
            voice_profile.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Voice clone created successfully!',
                'voice_id': clone_result['voice_id'],
                'voice_profile_id': voice_profile.id
            })
        else:
            voice_profile.is_active = False
            voice_profile.save()
            
            return JsonResponse({
                'success': False,
                'error': clone_result.get('error', 'Failed to create voice clone'),
                'voice_profile_id': voice_profile.id
            }, status=400)
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in upload_voice_sample: {e}")
        print(error_trace)
        return JsonResponse({
            'error': str(e),
            'details': error_trace if settings.DEBUG else None
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def voice_ask(request):
    """
    Voice agent endpoint: Takes text input (from speech-to-text), generates response
    using user's memory, and returns text response (for text-to-speech).
    
    This endpoint works with the existing generate_content logic but is optimized for voice.
    """
    try:
        user = request.user
        
        # Parse request body
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = {
                'text': request.POST.get('text', ''),
                'conversation_history': []
            }
        
        text = data.get('text', '').strip()
        conversation_history = data.get('conversation_history', [])
        
        if not text:
            return JsonResponse({
                'error': 'text is required'
            }, status=400)
        
        # Get user memory context
        memory_context = get_user_memory_context(user)
        
        # Generate response using Gemini with conversation history
        generated_text = gemini_generate_content(
            user_prompt=text,
            style_context=memory_context['style'],
            experiences=memory_context['experiences'],
            personal_info=memory_context['personal_info'],
            conversation_history=conversation_history
        )
        
        # Extract memory from conversation if applicable
        memory_extracted = False
        if conversation_history and len(conversation_history) >= 2:
            recent_messages = conversation_history[-4:] + [{'role': 'user', 'content': text}]
            conversation_text = "\n".join([f"{msg.get('role', 'user')}: {msg.get('content', '')}" for msg in recent_messages])
            
            from .services.gemini_service import extract_memory_from_conversation
            extracted_memory = extract_memory_from_conversation(conversation_text)
            
            if (extracted_memory.get('experiences') or 
                extracted_memory.get('personal_info') or 
                extracted_memory.get('new_achievements')):
                from .services.memory_extractor import save_experiences, save_personal_info
                experiences_saved = save_experiences(
                    user,
                    extracted_memory.get('experiences', []),
                    document_memory=None,
                    memory_type='conversation',
                    source='conversation'
                )
                personal_info_saved = save_personal_info(
                    user,
                    extracted_memory.get('personal_info', {}),
                    source='conversation'
                )
                memory_extracted = len(experiences_saved) > 0 or len(personal_info_saved) > 0
        
        # Get voice profile and generate audio if available
        audio_url = None
        voice_available = False
        try:
            voice_profile = VoiceProfile.objects.get(user=user)
            voice_available = voice_profile.is_active
            
            # Generate audio with cloned voice if available
            if voice_profile.is_active and voice_profile.voice_clone_id and voice_profile.tts_service == 'elevenlabs':
                from .services.voice_service import text_to_speech
                import tempfile
                import base64
                
                # Generate audio
                temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
                audio_data = text_to_speech(generated_text, voice_profile.voice_clone_id, temp_audio.name)
                
                if audio_data:
                    # Convert to base64 for frontend
                    with open(temp_audio.name, 'rb') as f:
                        audio_base64 = base64.b64encode(f.read()).decode('utf-8')
                    audio_url = f"data:audio/mpeg;base64,{audio_base64}"
                    os.unlink(temp_audio.name)
        except VoiceProfile.DoesNotExist:
            pass
        
        return JsonResponse({
            'success': True,
            'response_text': generated_text,
            'audio_url': audio_url,  # Base64 encoded audio
            'memory_extracted': memory_extracted,
            'voice_available': voice_available,
            'used_memories': {
                'style_signals': list(memory_context['style'].keys()),
                'experiences_count': len(memory_context['experiences']),
                'personal_info_keys': list(memory_context['personal_info'].keys())
            }
        })
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in voice_ask: {e}")
        print(error_trace)
        return JsonResponse({
            'error': str(e),
            'details': error_trace if settings.DEBUG else None
        }, status=500)


@require_http_methods(["GET"])
@login_required
def voice_profile(request):
    """
    Get user's voice profile status.
    """
    try:
        user = request.user
        
        try:
            voice_profile = VoiceProfile.objects.get(user=user)
            return JsonResponse({
                'success': True,
                'has_voice_sample': bool(voice_profile.voice_sample_file),
                'is_active': voice_profile.is_active,
                'tts_service': voice_profile.tts_service,
                'created_at': voice_profile.created_at.isoformat() if voice_profile.created_at else None
            })
        except VoiceProfile.DoesNotExist:
            return JsonResponse({
                'success': True,
                'has_voice_sample': False,
                'is_active': False,
                'tts_service': 'web_speech',
                'created_at': None
            })
    
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)


def public_voice_page(request, token=None):
    """
    Public voice agent page - accessible without login via shareable token.
    If token is provided, use that user's voice. Otherwise, show error.
    """
    # If no token, redirect to login or show error
    if not token:
        return HttpResponse("""
        <html>
        <head><title>Voice Agent - Invalid Link</title></head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1>Invalid Voice Agent Link</h1>
            <p>This voice agent link is invalid or has expired.</p>
            <p>Please contact the owner for a valid link.</p>
        </body>
        </html>
        """, status=404)
    
    # Verify token exists and is active
    try:
        share_token = VoiceShareToken.objects.get(token=token, is_active=True)
        user = share_token.user
        
        # Check if user has active voice profile
        try:
            voice_profile = VoiceProfile.objects.get(user=user, is_active=True)
        except VoiceProfile.DoesNotExist:
            return HttpResponse("""
            <html>
            <head><title>Voice Agent - Not Available</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1>Voice Agent Not Available</h1>
                <p>The voice agent for this user is not set up yet.</p>
            </body>
            </html>
            """, status=404)
        
        # Serve the public voice page
        frontend_path = os.path.join(settings.BASE_DIR, 'frontend', 'public_voice.html')
        try:
            with open(frontend_path, 'r') as f:
                html_content = f.read()
                # Inject token and username into page
                html_content = html_content.replace('{{TOKEN}}', token)
                html_content = html_content.replace('{{USERNAME}}', user.username)
                return HttpResponse(html_content, content_type='text/html')
        except FileNotFoundError:
            return HttpResponse("Voice page not found", status=404)
    
    except VoiceShareToken.DoesNotExist:
        return HttpResponse("""
        <html>
        <head><title>Voice Agent - Invalid Link</title></head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1>Invalid Voice Agent Link</h1>
            <p>This voice agent link is invalid or has expired.</p>
        </body>
        </html>
        """, status=404)


@csrf_exempt
@require_http_methods(["POST"])
def public_voice_ask(request, token):
    """
    Public voice agent endpoint - accepts token instead of session auth.
    """
    try:
        # Verify token
        try:
            share_token = VoiceShareToken.objects.get(token=token, is_active=True)
        except VoiceShareToken.DoesNotExist:
            return JsonResponse({
                'error': 'Invalid or inactive token'
            }, status=401)
        
        user = share_token.user
        
        # Parse request body
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = {
                'text': request.POST.get('text', ''),
                'conversation_history': []
            }
        
        text = data.get('text', '').strip()
        conversation_history = data.get('conversation_history', [])
        
        if not text:
            return JsonResponse({
                'error': 'text is required'
            }, status=400)
        
        # Get user memory context
        memory_context = get_user_memory_context(user)
        
        # Generate response using Gemini with conversation history
        generated_text = gemini_generate_content(
            user_prompt=text,
            style_context=memory_context['style'],
            experiences=memory_context['experiences'],
            personal_info=memory_context['personal_info'],
            conversation_history=conversation_history
        )
        
        # Get voice profile and generate audio
        audio_url = None
        voice_available = False
        try:
            voice_profile = VoiceProfile.objects.get(user=user, is_active=True)
            voice_available = voice_profile.is_active
            
            # Generate audio with cloned voice if available
            if voice_profile.is_active and voice_profile.voice_clone_id and voice_profile.tts_service == 'elevenlabs':
                from .services.voice_service import text_to_speech
                import tempfile
                import base64
                
                # Generate audio
                temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
                audio_data = text_to_speech(generated_text, voice_profile.voice_clone_id, temp_audio.name)
                
                if audio_data:
                    # Convert to base64 for frontend
                    with open(temp_audio.name, 'rb') as f:
                        audio_base64 = base64.b64encode(f.read()).decode('utf-8')
                    audio_url = f"data:audio/mpeg;base64,{audio_base64}"
                    os.unlink(temp_audio.name)
        except VoiceProfile.DoesNotExist:
            pass
        
        return JsonResponse({
            'success': True,
            'response_text': generated_text,
            'audio_url': audio_url,
            'voice_available': voice_available
        })
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in public_voice_ask: {e}")
        print(error_trace)
        return JsonResponse({
            'error': str(e),
            'details': error_trace if settings.DEBUG else None
        }, status=500)


@require_http_methods(["GET"])
def public_voice_status(request, token):
    """
    Get status info for a public voice token.
    """
    try:
        share_token = VoiceShareToken.objects.get(token=token, is_active=True)
        
        return JsonResponse({
            'success': True,
            'is_active': share_token.is_active
        })
    except VoiceShareToken.DoesNotExist:
        return JsonResponse({
            'error': 'Invalid or inactive token'
        }, status=404)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def create_share_token(request):
    """
    Create a new shareable token for the logged-in user.
    """
    try:
        user = request.user
        
        # Check if user has active voice profile
        try:
            voice_profile = VoiceProfile.objects.get(user=user, is_active=True)
        except VoiceProfile.DoesNotExist:
            return JsonResponse({
                'error': 'Voice profile not set up. Please record your voice first.'
            }, status=400)
        
        # Parse request body
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = {}
        
        name = data.get('name', '')
        
        # Generate unique token
        import secrets
        token = secrets.token_urlsafe(32)  # 32 bytes = 43 characters base64
        
        # Create share token
        share_token = VoiceShareToken.objects.create(
            user=user,
            token=token,
            name=name
        )
        
        # Generate shareable URL
        share_url = request.build_absolute_uri(f'/voice/public/{token}/')
        
        return JsonResponse({
            'success': True,
            'token': token,
            'share_url': share_url,
            'created_at': share_token.created_at.isoformat()
        })
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in create_share_token: {e}")
        print(error_trace)
        return JsonResponse({
            'error': str(e),
            'details': error_trace if settings.DEBUG else None
        }, status=500)


@require_http_methods(["GET"])
@login_required
def list_share_tokens(request):
    """
    List all shareable tokens for the logged-in user.
    """
    try:
        user = request.user
        tokens = VoiceShareToken.objects.filter(user=user).order_by('-created_at')
        
        token_list = []
        for token in tokens:
            share_url = request.build_absolute_uri(f'/voice/public/{token.token}/')
            
            token_list.append({
                'id': token.id,
                'token': token.token,
                'name': token.name,
                'share_url': share_url,
                'is_active': token.is_active,
                'created_at': token.created_at.isoformat()
            })
        
        return JsonResponse({
            'success': True,
            'tokens': token_list
        })
    
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)
