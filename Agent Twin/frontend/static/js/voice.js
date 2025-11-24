// Voice Agent JavaScript

// Use existing API_BASE if already declared (by auth.js), otherwise declare it
if (typeof window.API_BASE === 'undefined') {
    window.API_BASE = '/api';
}

let recognition = null;
let isRecording = false;
let conversationHistory = []; // Stores {role: "user"/"assistant", content: "..."}
let voiceProfile = null;
let audioContext = null;

// Voice setup recording
let mediaRecorder = null;
let audioChunks = [];
let isRecordingSetup = false;
let recordingStartTime = null;
let recordingTimer = null;

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    console.log('Voice page loaded - DOMContentLoaded');
    
    // Ensure setup is visible by default (in case JS hasn't run yet)
    const setupSection = document.getElementById('voiceSetup');
    const conversationSection = document.getElementById('voiceConversation');
    if (setupSection) {
        setupSection.style.display = 'flex';
        console.log('Set setup section to flex by default');
    }
    if (conversationSection) {
        conversationSection.style.display = 'none';
        console.log('Set conversation section to none by default');
    }
    
    checkAuth().then(() => {
        console.log('Auth check passed, loading voice profile...');
        loadVoiceProfile();
        initializeVoiceRecognition();
        setupEventListeners();
    }).catch(error => {
        console.error('Auth check failed:', error);
        window.location.href = '/login/';
    });
});

async function checkAuth() {
    try {
        const response = await fetch(`${window.API_BASE}/auth/user/`, {
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.authenticated) {
            const welcomeEl = document.getElementById('welcomeMessage');
            if (welcomeEl) {
                welcomeEl.textContent = `Voice Agent - ${data.user.username}`;
            }
        } else {
            window.location.href = '/login/';
        }
    } catch (error) {
        console.error('Auth check error:', error);
        window.location.href = '/login/';
    }
}

async function loadVoiceProfile() {
    const setupSection = document.getElementById('voiceSetup');
    const conversationSection = document.getElementById('voiceConversation');
    
    // Default to showing setup if profile check fails
    let showSetup = true;
    
    try {
        const response = await fetch(`${window.API_BASE}/voice/profile/`, {
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        voiceProfile = data;
        console.log('Voice profile data:', data);
        
        // Only show conversation if voice is active
        if (data.is_active === true) {
            console.log('Voice is active, showing conversation interface');
            showSetup = false;
        } else {
            console.log('Voice is NOT active, showing setup interface');
            showSetup = true;
        }
    } catch (error) {
        console.error('Error loading voice profile:', error);
        // On error, show setup section
        showSetup = true;
    }
    
    // Show/hide sections based on result
    console.log('Final decision - showSetup:', showSetup);
    if (showSetup) {
        console.log('Showing setup section, hiding conversation');
        if (setupSection) {
            setupSection.style.display = 'flex';
            console.log('Setup section display set to flex');
        } else {
            console.error('Setup section element not found!');
        }
        if (conversationSection) {
            conversationSection.style.display = 'none';
            console.log('Conversation section display set to none');
        } else {
            console.error('Conversation section element not found!');
        }
    } else {
        console.log('Showing conversation section, hiding setup');
        if (setupSection) {
            setupSection.style.display = 'none';
        }
        if (conversationSection) {
            conversationSection.style.display = 'flex';
        }
    }
}

function initializeVoiceRecognition() {
    // Check if browser supports Web Speech API
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        console.warn('Speech recognition not supported');
        const recordBtn = document.getElementById('voiceRecordBtn');
        if (recordBtn) {
            recordBtn.disabled = true;
            recordBtn.title = 'Voice input not supported in this browser';
        }
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
    // Voice record button (for conversation interface)
    const voiceRecordBtn = document.getElementById('voiceRecordBtn');
    if (voiceRecordBtn) {
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
        
        // Touch events
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
    
    // Voice setup recording button (for setup interface)
    const setupRecordBtn = document.getElementById('recordBtn');
    if (setupRecordBtn) {
        console.log('Setting up setup record button listeners');
        let isPressed = false;
        
        setupRecordBtn.addEventListener('mousedown', (e) => {
            e.preventDefault();
            console.log('Setup record button mousedown');
            if (!isRecordingSetup) {
                console.log('Starting setup recording...');
                startSetupRecording();
                isPressed = true;
            } else {
                console.log('Already recording, ignoring');
            }
        });
        
        setupRecordBtn.addEventListener('mouseup', () => {
            console.log('Setup record button mouseup, isPressed:', isPressed, 'isRecordingSetup:', isRecordingSetup);
            if (isPressed && isRecordingSetup) {
                console.log('Stopping setup recording...');
                stopSetupRecording();
                isPressed = false;
            }
        });
        
        setupRecordBtn.addEventListener('mouseleave', () => {
            console.log('Setup record button mouseleave');
            if (isPressed && isRecordingSetup) {
                console.log('Stopping setup recording (mouse left)...');
                stopSetupRecording();
                isPressed = false;
            }
        });
        
        // Touch events
        setupRecordBtn.addEventListener('touchstart', (e) => {
            e.preventDefault();
            console.log('Setup record button touchstart');
            if (!isRecordingSetup) {
                console.log('Starting setup recording (touch)...');
                startSetupRecording();
                isPressed = true;
            }
        });
        
        setupRecordBtn.addEventListener('touchend', (e) => {
            e.preventDefault();
            console.log('Setup record button touchend');
            if (isPressed && isRecordingSetup) {
                console.log('Stopping setup recording (touch end)...');
                stopSetupRecording();
                isPressed = false;
            }
        });
        
        console.log('Setup record button listeners set up');
    } else {
        console.error('Setup record button (recordBtn) not found!');
    }
    
    // Logout button
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async () => {
            try {
                await fetch(`${window.API_BASE}/auth/logout/`, {
                    method: 'POST',
                    credentials: 'include'
                });
                window.location.href = '/login/';
            } catch (error) {
                console.error('Logout error:', error);
                window.location.href = '/login/';
            }
        });
    }
}

function startRecording() {
    if (!recognition || isRecording) return;
    
    isRecording = true;
    const recordBtn = document.getElementById('voiceRecordBtn');
    
    if (recordBtn) {
        recordBtn.classList.add('recording');
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
    const recordBtn = document.getElementById('voiceRecordBtn');
    
    if (recordBtn) {
        recordBtn.classList.remove('recording');
    }
    
    if (recognition) {
        try {
            recognition.stop();
        } catch (error) {
            // Ignore
        }
    }
    
    setWaveformState('processing');
    updateStatus('Processing...', 'processing');
}

async function handleVoiceInput(text) {
    if (!text || !text.trim()) {
        setWaveformState('');
        updateStatus('Ready to listen', 'ready');
        return;
    }
    
    // Add user message to conversation history (for context, not displayed)
    conversationHistory.push({ role: 'user', content: text });
    
    setWaveformState('processing');
    updateStatus('Getting response...', 'processing');
    
    try {
        const response = await fetch(`${window.API_BASE}/voice/ask/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
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
            // Add assistant response to conversation history (for context, not displayed)
            conversationHistory.push({ role: 'assistant', content: data.response_text });
            
            // Play audio if available
            if (data.audio_url) {
                setWaveformState('active');
                updateStatus('Speaking...', 'speaking');
                await playAudio(data.audio_url);
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
    return new Promise((resolve, reject) => {
        const audioPlayer = document.getElementById('audioPlayer');
        if (!audioPlayer) {
            reject('Audio player not found');
            return;
        }
        
        audioPlayer.src = audioUrl;
        
        audioPlayer.onended = () => {
            console.log('Audio playback ended');
            setWaveformState('');
            updateStatus('Ready to listen', 'ready');
            resolve();
        };
        
        audioPlayer.onerror = (e) => {
            console.error('Error playing audio:', e);
            setWaveformState('');
            updateStatus('Error playing audio', 'error');
            reject(e);
        };
        
        audioPlayer.play().catch(error => {
            console.error('Error starting audio playback:', error);
            setWaveformState('');
            updateStatus('Error starting audio playback', 'error');
            reject(error);
        });
    });
}

function setWaveformState(state) {
    const waveform = document.getElementById('waveform');
    if (waveform) {
        waveform.className = 'waveform';
        if (state) {
            waveform.classList.add(state);
        }
    }
}

function updateStatus(text, type = 'ready') {
    const statusText = document.getElementById('statusText');
    const statusIcon = document.getElementById('statusIcon');
    const statusMessage = document.getElementById('statusMessage');
    
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

async function startSetupRecording() {
    console.log('startSetupRecording called');
    
    if (isRecordingSetup) {
        console.log('Already recording, ignoring');
        return;
    }
    
    try {
        console.log('Requesting microphone access...');
        // Request microphone access
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        console.log('Microphone access granted');
        
        // Check available MIME types
        let mimeType = 'audio/webm';
        if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
            mimeType = 'audio/webm;codecs=opus';
        } else if (MediaRecorder.isTypeSupported('audio/webm')) {
            mimeType = 'audio/webm';
        } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
            mimeType = 'audio/mp4';
        }
        console.log('Using MIME type:', mimeType);
        
        // Initialize MediaRecorder
        mediaRecorder = new MediaRecorder(stream, {
            mimeType: mimeType
        });
        
        audioChunks = [];
        
        mediaRecorder.ondataavailable = (event) => {
            console.log('Data available:', event.data.size, 'bytes');
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };
        
        mediaRecorder.onerror = (event) => {
            console.error('MediaRecorder error:', event.error);
            showRecordingResult('Recording error: ' + event.error.message, 'error');
            stopSetupRecording();
        };
        
        mediaRecorder.onstop = async () => {
            console.log('Recording stopped, processing...');
            // Stop all tracks
            stream.getTracks().forEach(track => track.stop());
            
            // Calculate actual recording duration from start time
            const actualDuration = (Date.now() - recordingStartTime) / 1000;
            console.log('Actual recording duration:', actualDuration, 'seconds');
            
            // Create audio blob
            const audioBlob = new Blob(audioChunks, { type: mimeType });
            console.log('Audio blob created:', audioBlob.size, 'bytes');
            
            // Check minimum duration (30 seconds) - use actual duration, not blob metadata
            if (actualDuration < 30) {
                showRecordingResult(`Recording too short (${Math.round(actualDuration)}s). Please record at least 30 seconds.`, 'error');
                resetRecordingUI();
                return;
            }
            
            // Upload the recording
            await uploadRecording(audioBlob);
        };
        
        // Start recording
        mediaRecorder.start(1000); // Collect data every second
        isRecordingSetup = true;
        recordingStartTime = Date.now();
        console.log('MediaRecorder started, state:', mediaRecorder.state);
        
        // Update UI
        const recordBtn = document.getElementById('recordBtn');
        const statusDot = document.getElementById('statusDot');
        const statusText = document.getElementById('recordingStatusText');
        const timerDiv = document.getElementById('recordingTimer');
        const timerText = document.getElementById('timerText');
        
        if (recordBtn) {
            recordBtn.classList.add('recording');
            console.log('Record button class updated');
        }
        if (statusDot) {
            statusDot.classList.add('recording');
            console.log('Status dot updated');
        }
        if (statusText) {
            statusText.textContent = 'Recording...';
            console.log('Status text updated');
        }
        if (timerDiv) {
            timerDiv.style.display = 'block';
            console.log('Timer displayed');
        }
        
        // Start timer
        recordingTimer = setInterval(() => {
            const elapsed = Math.floor((Date.now() - recordingStartTime) / 1000);
            const minutes = Math.floor(elapsed / 60);
            const seconds = elapsed % 60;
            if (timerText) {
                timerText.textContent = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
            }
        }, 1000);
        
        console.log('Setup recording started successfully');
    } catch (error) {
        console.error('Error starting recording:', error);
        console.error('Error details:', error.name, error.message);
        let errorMsg = 'Error accessing microphone. ';
        if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
            errorMsg += 'Please allow microphone permissions in your browser settings.';
        } else if (error.name === 'NotFoundError') {
            errorMsg += 'No microphone found.';
        } else {
            errorMsg += error.message;
        }
        showRecordingResult(errorMsg, 'error');
        resetRecordingUI();
    }
}

function resetRecordingUI() {
    const recordBtn = document.getElementById('recordBtn');
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('recordingStatusText');
    const timerDiv = document.getElementById('recordingTimer');
    
    if (recordBtn) recordBtn.classList.remove('recording');
    if (statusDot) statusDot.classList.remove('recording');
    if (statusText) statusText.textContent = 'Ready to record';
    if (timerDiv) timerDiv.style.display = 'none';
    
    isRecordingSetup = false;
}

function stopSetupRecording() {
    console.log('stopSetupRecording called, isRecordingSetup:', isRecordingSetup, 'mediaRecorder:', !!mediaRecorder);
    
    if (!isRecordingSetup) {
        console.log('Not recording, ignoring stop');
        return;
    }
    
    // Stop recording
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        console.log('Stopping MediaRecorder, current state:', mediaRecorder.state);
        try {
            mediaRecorder.stop();
            console.log('MediaRecorder stopped, new state:', mediaRecorder.state);
        } catch (error) {
            console.error('Error stopping MediaRecorder:', error);
        }
    }
    
    isRecordingSetup = false;
    
    // Clear timer
    if (recordingTimer) {
        clearInterval(recordingTimer);
        recordingTimer = null;
        console.log('Timer cleared');
    }
    
    // Update UI
    const recordBtn = document.getElementById('recordBtn');
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('recordingStatusText');
    const timerDiv = document.getElementById('recordingTimer');
    
    if (recordBtn) {
        recordBtn.classList.remove('recording');
        console.log('Record button class removed');
    }
    if (statusDot) {
        statusDot.classList.remove('recording');
    }
    if (statusText) {
        statusText.textContent = 'Processing...';
    }
    // Keep timer visible during processing
    // if (timerDiv) timerDiv.style.display = 'none';
    
    console.log('Setup recording stopped');
}

async function getAudioDuration(audioBlob) {
    return new Promise((resolve) => {
        const audio = new Audio();
        const url = URL.createObjectURL(audioBlob);
        audio.src = url;
        
        // Set a timeout to prevent hanging
        const timeout = setTimeout(() => {
            URL.revokeObjectURL(url);
            console.warn('Audio duration calculation timed out, using blob size estimate');
            // Estimate duration based on file size (rough estimate: ~16KB per second for webm)
            const estimatedDuration = audioBlob.size / 16000;
            resolve(estimatedDuration);
        }, 5000);
        
        audio.addEventListener('loadedmetadata', () => {
            clearTimeout(timeout);
            const duration = audio.duration;
            URL.revokeObjectURL(url);
            console.log('Audio duration calculated:', duration, 'seconds');
            if (isFinite(duration) && duration > 0) {
                resolve(duration);
            } else {
                // Fallback: estimate from file size
                const estimatedDuration = audioBlob.size / 16000;
                console.log('Duration was not finite, using estimate:', estimatedDuration);
                resolve(estimatedDuration);
            }
        });
        
        audio.addEventListener('error', (e) => {
            clearTimeout(timeout);
            console.error('Error loading audio for duration:', e);
            URL.revokeObjectURL(url);
            // Fallback: estimate from file size
            const estimatedDuration = audioBlob.size / 16000;
            console.log('Using estimated duration:', estimatedDuration);
            resolve(estimatedDuration);
        });
        
        // Try to load the audio
        audio.load();
    });
}

async function uploadRecording(audioBlob) {
    const resultDiv = document.getElementById('recordingResult');
    const statusText = document.getElementById('recordingStatusText');
    
    if (statusText) statusText.textContent = 'Uploading and creating voice clone...';
    
    try {
        // Convert to File
        const audioFile = new File([audioBlob], 'voice-sample.webm', { type: 'audio/webm' });
        
        const formData = new FormData();
        formData.append('audio_file', audioFile);
        
        const response = await fetch(`${window.API_BASE}/voice/upload-sample/`, {
            method: 'POST',
            credentials: 'include',
            body: formData
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Upload failed');
        }
        
        const data = await response.json();
        
        if (data.success) {
            showRecordingResult('Voice clone created successfully! Reloading...', 'success');
            if (statusText) statusText.textContent = 'Success!';
            setTimeout(() => {
                window.location.reload();
            }, 2000);
        } else {
            throw new Error(data.error || 'Failed to create voice clone');
        }
    } catch (error) {
        console.error('Upload error:', error);
        showRecordingResult(error.message, 'error');
        if (statusText) statusText.textContent = 'Ready to record';
    }
}

function showRecordingResult(message, type) {
    const resultDiv = document.getElementById('recordingResult');
    if (resultDiv) {
        resultDiv.textContent = message;
        resultDiv.className = `recording-result ${type}`;
        resultDiv.style.display = 'block';
    }
}

