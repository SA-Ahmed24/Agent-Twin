"""
Voice Service for ElevenLabs Integration
Handles voice cloning and text-to-speech with cloned voices
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
ELEVENLABS_API_URL = 'https://api.elevenlabs.io/v1'


def get_api_key():
    """Get ElevenLabs API key, reloading env if needed"""
    key = os.getenv('ELEVENLABS_API_KEY')
    if not key:
        # Try reloading
        load_dotenv(override=True)
        key = os.getenv('ELEVENLABS_API_KEY')
    return key


def create_voice_clone(audio_file_path, voice_name):
    """
    Create a voice clone from an audio file using ElevenLabs Instant Voice Cloning.
    
    Args:
        audio_file_path: Path to the audio file (MP3, WAV, etc.)
        voice_name: Name for the cloned voice
        
    Returns:
        dict: {'voice_id': str, 'success': bool, 'error': str}
    """
    api_key = get_api_key()
    if not api_key:
        return {
            'success': False,
            'error': 'ELEVENLABS_API_KEY not set in environment variables. Please add it to .env and restart the server.'
        }
    
    try:
        # Read audio file
        with open(audio_file_path, 'rb') as audio_file:
            files = {
                'files': (os.path.basename(audio_file_path), audio_file, 'audio/mpeg')
            }
            
            data = {
                'name': voice_name
            }
            
            headers = {
                'xi-api-key': api_key
            }
            
            # Create voice clone
            response = requests.post(
                f'{ELEVENLABS_API_URL}/voices/add',
                headers=headers,
                files=files,
                data=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                voice_id = result.get('voice_id')
                return {
                    'success': True,
                    'voice_id': voice_id,
                    'name': result.get('name', voice_name)
                }
            else:
                # Parse error response
                try:
                    error_data = response.json()
                    error_msg = error_data.get('detail', {}).get('message', 'Unknown error')
                    
                    # Provide helpful guidance for permission errors
                    if 'permission' in error_msg.lower() or 'voices_write' in error_msg:
                        error_msg = (
                            f"API key missing 'voices_write' permission. "
                            f"Please check your ElevenLabs API key permissions at: "
                            f"https://elevenlabs.io/app/settings/api-keys. "
                            f"Make sure your API key has voice cloning enabled."
                        )
                except:
                    error_msg = f'HTTP {response.status_code}: {response.text[:200]}'
                
                return {
                    'success': False,
                    'error': f'ElevenLabs API error: {error_msg}',
                    'status_code': response.status_code
                }
    
    except FileNotFoundError:
        return {
            'success': False,
            'error': f'Audio file not found: {audio_file_path}'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Error creating voice clone: {str(e)}'
        }


def text_to_speech(text, voice_id, output_path=None):
    """
    Convert text to speech using a cloned voice.
    
    Args:
        text: Text to convert to speech
        voice_id: ElevenLabs voice ID
        output_path: Optional path to save audio file
        
    Returns:
        bytes: Audio data, or None if error
    """
    api_key = get_api_key()
    if not api_key:
        return None
    
    try:
        url = f'{ELEVENLABS_API_URL}/text-to-speech/{voice_id}'
        
        headers = {
            'Accept': 'audio/mpeg',
            'Content-Type': 'application/json',
            'xi-api-key': api_key
        }
        
        data = {
            'text': text,
            'model_id': 'eleven_multilingual_v2',  # or 'eleven_monolingual_v1'
            'voice_settings': {
                'stability': 0.5,
                'similarity_boost': 0.75
            }
        }
        
        response = requests.post(url, json=data, headers=headers, timeout=30)
        
        if response.status_code == 200:
            audio_data = response.content
            
            # Save to file if output_path provided
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(audio_data)
            
            return audio_data
        else:
            print(f'ElevenLabs TTS error: {response.status_code} - {response.text}')
            return None
    
    except Exception as e:
        print(f'Error in text_to_speech: {e}')
        return None


def get_voice_info(voice_id):
    """
    Get information about a voice clone.
    
    Args:
        voice_id: ElevenLabs voice ID
        
    Returns:
        dict: Voice information
    """
    api_key = get_api_key()
    if not api_key:
        return None
    
    try:
        url = f'{ELEVENLABS_API_URL}/voices/{voice_id}'
        headers = {
            'xi-api-key': ELEVENLABS_API_KEY
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
    
    except Exception as e:
        print(f'Error getting voice info: {e}')
        return None


def delete_voice_clone(voice_id):
    """
    Delete a voice clone from ElevenLabs.
    
    Args:
        voice_id: ElevenLabs voice ID
        
    Returns:
        bool: True if successful
    """
    api_key = get_api_key()
    if not api_key:
        return False
    
    try:
        url = f'{ELEVENLABS_API_URL}/voices/{voice_id}'
        headers = {
            'xi-api-key': api_key
        }
        
        response = requests.delete(url, headers=headers, timeout=10)
        return response.status_code == 200
    
    except Exception as e:
        print(f'Error deleting voice clone: {e}')
        return False

