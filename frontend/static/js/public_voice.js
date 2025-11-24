// Public Voice Agent JavaScript

// Get token from script tag or global variable
const SHARE_TOKEN = typeof SHARE_TOKEN !== 'undefined' ? SHARE_TOKEN : (window.SHARE_TOKEN || '');
const USERNAME = typeof USERNAME !== 'undefined' ? USERNAME : (window.USERNAME || '');

if (!SHARE_TOKEN) {
    console.error('Share token not found');
    document.body.innerHTML = '<div style="text-align: center; padding: 50px;"><h1>Invalid Link</h1><p>This voice agent link is invalid.</p></div>';
}

// Use existing API_BASE if already declared, otherwise declare it
if (typeof window.API_BASE === 'undefined') {
    window.API_BASE = '/api';
}

let recognition = null;
let isRecording = false;
let conversationHistory = [];

// DOM elements
const voiceRecordBtn = document.getElementById('voiceRecordBtn');
const statusMessage = document.getElementById('statusMessage');
const statusText = document.getElementById('statusText');
const statusIcon = document.getElementById('statusIcon');
const waveform = document.getElementById('waveform');
const waveformContainer = document.getElementById('waveformContainer');
const audioPlayer = document.getElementById('audioPlayer');

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    console.log('Public voice page loaded');
    initializeVoiceRecognition();
    setupEventListeners();
});

function initializeVoiceRecognition() {
    // Check if browser supports Web Speech API
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        console.warn('Speech recognition not supported');
        if (voiceRecordBtn) {
            voiceRecordBtn.disabled = true;
            voiceRecordBtn.title = 'Voice input not supported in this browser';
        }
        updateStatus('Voice input not supported', 'error');
        return;
    }
    
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';
    
    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        console.log('Voice transcript:', transcript);
        handleVoiceInput(transcript);
    };
    
    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        stopRecording();
        updateStatus('Error: ' + event.error, 'error');
    };
    
    recognition.onend = () => {
        stopRecording();
    };
}

function setupEventListeners() {
    if (!voiceRecordBtn) return;
    
    let isPressed = false;
    
    voiceRecordBtn.addEventListener('mousedown', (e) => {
        e.preventDefault();
        if (!isRecording) {
            startRecording();
            isPressed = true;
        }
    });
    
    voiceRecordBtn.addEventListener('mouseup', () => {
        if (isPressed && isRecording) {
            stopRecording();
            isPressed = false;
        }
    });
    
    voiceRecordBtn.addEventListener('mouseleave', () => {
        if (isPressed && isRecording) {
            stopRecording();
            isPressed = false;
        }
    });
    
    // Touch events for mobile
    voiceRecordBtn.addEventListener('touchstart', (e) => {
        e.preventDefault();
        if (!isRecording) {
            startRecording();
            isPressed = true;
        }
    });
    
    voiceRecordBtn.addEventListener('touchend', (e) => {
        e.preventDefault();
        if (isPressed && isRecording) {
            stopRecording();
            isPressed = false;
        }
    });
}

function startRecording() {
    if (!recognition || isRecording) return;
    
    isRecording = true;
    
    if (voiceRecordBtn) {
        voiceRecordBtn.classList.add('recording');
    }
    
    setWaveformState('listening');
    updateStatus('Listening...', 'listening');
    
    try {
        recognition.start();
        console.log('Recording started');
    } catch (error) {
        console.error('Error starting recognition:', error);
        stopRecording();
    }
}

function stopRecording() {
    if (!isRecording) return;
    
    isRecording = false;
    
    if (voiceRecordBtn) {
        voiceRecordBtn.classList.remove('recording');
    }
    
    setWaveformState('processing');
    updateStatus('Processing...', 'processing');
    
    if (recognition) {
        try {
            recognition.stop();
        } catch (error) {
            // Ignore
        }
    }
}

function updateStatus(text, type = 'ready') {
    if (statusText) {
        statusText.textContent = text;
    }
    
    if (statusMessage) {
        statusMessage.className = 'status-message';
        if (type !== 'ready') {
            statusMessage.classList.add(type);
        }
    }
    
    if (statusIcon) {
        switch(type) {
            case 'listening':
                statusIcon.textContent = '🎤';
                break;
            case 'processing':
                statusIcon.textContent = '⚙️';
                break;
            case 'speaking':
                statusIcon.textContent = '🔊';
                break;
            case 'error':
                statusIcon.textContent = '❌';
                break;
            default:
                statusIcon.textContent = '🎤';
        }
    }
}

function setWaveformState(state) {
    if (waveform) {
        waveform.className = 'waveform';
        if (state) {
            waveform.classList.add(state);
        }
    }
}

async function handleVoiceInput(text) {
    if (!text || !text.trim()) {
        setWaveformState('');
        updateStatus('Ready to listen', 'ready');
        return;
    }
    
    conversationHistory.push({ role: 'user', content: text });
    
    setWaveformState('processing');
    updateStatus('Getting response...', 'processing');
    
    try {
        const response = await fetch(`${window.API_BASE}/voice/public/${SHARE_TOKEN}/ask/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: text,
                conversation_history: conversationHistory.slice(-10) // Last 10 messages
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            conversationHistory.push({ role: 'assistant', content: data.response_text });
            
            // Play audio if available
            if (data.audio_url) {
                setWaveformState('active');
                updateStatus('Speaking...', 'speaking');
                playAudio(data.audio_url);
            } else {
                setWaveformState('');
                updateStatus('Ready to listen', 'ready');
            }
        } else {
            throw new Error(data.error || 'Failed to get response');
        }
    } catch (error) {
        console.error('Error handling voice input:', error);
        setWaveformState('');
        updateStatus('Error: ' + error.message, 'error');
    }
}

function playAudio(audioUrl) {
    if (!audioPlayer) return;
    
    audioPlayer.src = audioUrl;
    
    audioPlayer.onended = () => {
        setWaveformState('');
        updateStatus('Ready to listen', 'ready');
    };
    
    audioPlayer.onerror = () => {
        setWaveformState('');
        updateStatus('Error playing audio', 'error');
    };
    
    audioPlayer.play().catch(error => {
        console.error('Error playing audio:', error);
        setWaveformState('');
        updateStatus('Error playing audio', 'error');
    });
}


