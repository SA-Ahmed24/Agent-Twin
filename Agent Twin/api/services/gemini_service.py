"""
Gemini API Service
Handles all interactions with Google Gemini API
"""
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Initialize models - use gemini-2.0-flash (latest stable model)
text_model = genai.GenerativeModel('models/gemini-2.0-flash')
vision_model = genai.GenerativeModel('models/gemini-2.0-flash')


def extract_writing_style(text):
    """
    Extract writing style characteristics from text using Gemini.
    
    Args:
        text: Input text to analyze
        
    Returns:
        dict: Writing style characteristics
    """
    prompt = f"""Analyze the following text and extract writing style characteristics.

Text: {text}

Return a JSON object with:
- tone_formality: "formal" | "casual" | "professional" | "academic"
- average_sentence_length: number
- vocabulary_keywords: [list of distinctive words/phrases]
- signature_phrases: [list of unique phrases the author uses]
- sentence_structure: "complex" | "simple" | "mixed"

Return ONLY valid JSON, no additional text."""
    
    try:
        response = text_model.generate_content(prompt)
        # Try to parse JSON from response
        response_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if '```' in response_text:
            # Find JSON between code blocks
            import re
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)
            else:
                # Try to find JSON object directly
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group(0)
        
        response_text = response_text.strip()
        
        # Try to parse JSON
        parsed = json.loads(response_text)
        return parsed
    except json.JSONDecodeError as e:
        print(f"JSON decode error extracting writing style: {e}")
        print(f"Response text: {response_text[:200]}")
        # Try to extract basic info from text
        return {
            "tone_formality": "professional",
            "average_sentence_length": 15,
            "vocabulary_keywords": [],
            "signature_phrases": [],
            "sentence_structure": "mixed"
        }
    except Exception as e:
        print(f"Error extracting writing style: {e}")
        return {
            "tone_formality": "professional",
            "average_sentence_length": 15,
            "vocabulary_keywords": [],
            "signature_phrases": [],
            "sentence_structure": "mixed"
        }


def extract_facts_and_experiences(text):
    """
    Extract factual information, experiences, and achievements from text.
    
    Args:
        text: Input text to analyze
        
    Returns:
        dict: Extracted facts, experiences, and personal info
    """
    prompt = f"""You are analyzing a resume, cover letter, or professional document. Extract ALL work experiences, internships, projects, and personal information.

Text to analyze:
{text}

Extract and return a JSON object with this EXACT structure:
{{
  "experiences": [
    {{
      "title": "Job title or project name",
      "company": "Company or organization name",
      "position": "Position title if different from title",
      "achievements": ["achievement 1", "achievement 2"],
      "tech_stack": ["technology 1", "technology 2"],
      "start_date": "YYYY-MM-DD or null",
      "end_date": "YYYY-MM-DD or null"
    }}
  ],
  "personal_info": {{
    "name": "Full name",
    "university": "University or school name",
    "major": "Major or field of study",
    "interests": ["interest 1", "interest 2"],
    "background": "Brief background summary"
  }},
  "new_achievements": ["achievement 1", "achievement 2"]
}}

IMPORTANT: 
- Extract EVERY work experience, internship, or project mentioned
- Include ALL technologies, skills, and achievements
- Return ONLY valid JSON, no markdown, no explanations, no code blocks
- If a field is not found, use null or empty array/object"""
    
    try:
        response = text_model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if '```' in response_text:
            import re
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)
            else:
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group(0)
        
        response_text = response_text.strip()
        
        # Try to parse JSON
        parsed = json.loads(response_text)
        
        # Ensure required keys exist
        if 'experiences' not in parsed:
            parsed['experiences'] = []
        if 'personal_info' not in parsed:
            parsed['personal_info'] = {}
        if 'new_achievements' not in parsed:
            parsed['new_achievements'] = []
        
        return parsed
    except json.JSONDecodeError as e:
        print(f"JSON decode error extracting facts: {e}")
        print(f"Response text: {response_text[:500]}")
        return {
            "experiences": [],
            "personal_info": {},
            "new_achievements": []
        }
    except Exception as e:
        print(f"Error extracting facts: {e}")
        return {
            "experiences": [],
            "personal_info": {},
            "new_achievements": []
        }


def analyze_image(image_path):
    """
    Analyze an image using Gemini Vision API.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        dict: Extracted information from image
    """
    try:
        from PIL import Image
        
        # Load image
        img = Image.open(image_path)
        
        prompt = """Analyze this image and extract:
- Any text visible (OCR)
- Objects, achievements, projects shown
- Personal information visible
- Context and meaning

Return a JSON object with the same structure as extract_facts_and_experiences:
- experiences: [{"title": str, "company": str, "position": str, "achievements": [str], "tech_stack": [str]}]
- personal_info: {"name": str, "university": str, "major": str, "interests": [str], "background": str}
- new_achievements: [list of accomplishments]

Return ONLY valid JSON, no additional text."""
        
        response = vision_model.generate_content([prompt, img])
        response_text = response.text.strip()
        # Remove markdown code blocks if present
        if response_text.startswith('```'):
            response_text = response_text.split('```')[1]
            if response_text.startswith('json'):
                response_text = response_text[4:]
        response_text = response_text.strip()
        
        return json.loads(response_text)
    except Exception as e:
        print(f"Error analyzing image: {e}")
        return {
            "experiences": [],
            "personal_info": {},
            "new_achievements": []
        }


def generate_content(user_prompt, style_context, experiences, personal_info, conversation_history=None):
    """
    Generate content using user's writing style and personal information.
    Supports conversational flow with context from previous messages.
    
    Args:
        user_prompt: What the user wants to generate or ask
        style_context: Writing style information
        experiences: List of user experiences
        personal_info: Personal information dict
        conversation_history: List of previous messages in format [{"role": "user"/"assistant", "content": "..."}]
        
    Returns:
        str: Generated content or answer
    """
    # Format experiences
    experiences_text = ""
    for exp in experiences:
        exp_str = f"- {exp.get('title', 'N/A')}"
        if exp.get('company'):
            exp_str += f" at {exp['company']}"
        if exp.get('position'):
            exp_str += f" ({exp['position']})"
        if exp.get('achievements'):
            exp_str += f"\n  Achievements: {', '.join(exp['achievements'])}"
        experiences_text += exp_str + "\n"
    
    # Format personal info
    personal_text = ""
    for key, value in personal_info.items():
        if value:
            personal_text += f"- {key}: {value}\n"
    
    # Format conversation history if provided
    conversation_context = ""
    if conversation_history and len(conversation_history) > 0:
        conversation_context = "\n\nRECENT CONVERSATION:\n"
        for msg in conversation_history[-6:]:  # Last 6 messages for context
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            speaker = "User" if role == "user" else "You (Agent Twin)"
            conversation_context += f"{speaker}: {content}\n"
    
    # Detect intent: question, modification request, or generation request
    user_lower = user_prompt.lower()
    is_question = any(word in user_lower for word in ['what', 'who', 'where', 'when', 'why', 'how', '?', 'does', 'did', 'do', 'is', 'are', 'can', 'could'])
    is_modification = any(word in user_lower for word in ['change', 'modify', 'edit', 'update', 'make it', 'shorter', 'longer', 'add', 'remove', 'different'])
    
    system_prompt = f"""You are Agent Twin, an AI writing companion that helps users create content in their authentic voice.

USER'S WRITING STYLE:
- Tone: {style_context.get('tone_formality', 'professional')}
- Average sentence length: {style_context.get('average_sentence_length', 15)} words
- Signature phrases: {', '.join(style_context.get('signature_phrases', []))}
- Vocabulary patterns: {', '.join(style_context.get('vocabulary_keywords', []))}
- Sentence structure: {style_context.get('sentence_structure', 'mixed')}

USER'S EXPERIENCES:
{experiences_text if experiences_text else "None recorded yet."}

USER'S PERSONAL INFO:
{personal_text if personal_text else "None recorded yet."}
{conversation_context}

CAPABILITIES:
1. **Answer Questions**: If the user asks about their background, experiences, or work, answer using the stored information above.
2. **Generate Content**: If the user asks to write/generate/create something, write it in their exact style using their information.
3. **Modify Content**: If the user asks to change/modify previous content, understand the context from the conversation and make the requested changes.

GUIDELINES:
- Be conversational and helpful
- Use ONLY true information about the user from the stored data
- Match the user's writing style (tone, sentence length, vocabulary, phrasing)
- If asked about something not in memory, say you don't have that information yet
- If modifying content, reference the conversation history to understand what to change
- Be natural and engaging, not robotic

Current user message: {user_prompt}

Respond naturally:"""
    
    try:
        response = text_model.generate_content(system_prompt)
        if hasattr(response, 'text'):
            return response.text
        else:
            # Handle different response formats
            return str(response)
    except Exception as e:
        print(f"Error generating content: {e}")
        import traceback
        traceback.print_exc()
        return f"Error generating content: {str(e)}"


def extract_memory_from_conversation(conversation_text):
    """
    Extract important information from conversation text that should be added to memory.
    Only extracts relevant facts, experiences, or personal info - filters out trivial details.
    
    Args:
        conversation_text: Recent conversation text to analyze
        
    Returns:
        dict: Extracted facts, experiences, and personal info (same format as extract_facts_and_experiences)
    """
    prompt = f"""Analyze the following conversation and extract ONLY important, factual information that should be remembered about the user.

Conversation:
{conversation_text}

Extract ONLY:
- New work experiences, internships, or projects mentioned
- Important achievements or accomplishments
- Personal information (education, background, interests) that wasn't known before
- Skills, technologies, or expertise mentioned

DO NOT extract:
- Casual conversation or greetings
- Questions asked by the user
- Trivial details or small talk
- Information that's already obvious or generic

Return a JSON object with this structure:
{{
  "experiences": [
    {{
      "title": "Job title or project name",
      "company": "Company or organization name",
      "position": "Position title",
      "achievements": ["achievement 1"],
      "tech_stack": ["technology 1"],
      "start_date": "YYYY-MM-DD or null",
      "end_date": "YYYY-MM-DD or null"
    }}
  ],
  "personal_info": {{
    "name": "Full name or null",
    "university": "University or null",
    "major": "Major or null",
    "interests": ["interest 1"],
    "background": "Background info or null"
  }},
  "new_achievements": ["achievement 1"]
}}

If NO important information is found, return:
{{
  "experiences": [],
  "personal_info": {{}},
  "new_achievements": []
}}

Return ONLY valid JSON, no markdown, no explanations."""
    
    try:
        response = text_model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if '```' in response_text:
            import re
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)
            else:
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group(0)
        
        response_text = response_text.strip()
        
        # Try to parse JSON
        parsed = json.loads(response_text)
        
        # Ensure required keys exist
        if 'experiences' not in parsed:
            parsed['experiences'] = []
        if 'personal_info' not in parsed:
            parsed['personal_info'] = {}
        if 'new_achievements' not in parsed:
            parsed['new_achievements'] = []
        
        return parsed
    except json.JSONDecodeError as e:
        print(f"JSON decode error extracting memory from conversation: {e}")
        print(f"Response text: {response_text[:500]}")
        return {
            "experiences": [],
            "personal_info": {},
            "new_achievements": []
        }
    except Exception as e:
        print(f"Error extracting memory from conversation: {e}")
        return {
            "experiences": [],
            "personal_info": {},
            "new_achievements": []
        }

