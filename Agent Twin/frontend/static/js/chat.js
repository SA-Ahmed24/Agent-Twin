// Chat Interface JavaScript

// Use relative URL to avoid CORS issues
const API_BASE = '/api';

let currentUser = null;
let messageHistory = []; // For UI display
let conversationHistory = []; // For API context - stores {role: "user"/"assistant", content: "..."}

// Voice functionality
let recognition = null;
let isRecording = false;
let voiceEnabled = true; // Toggle for voice responses

// Initialize - use both DOMContentLoaded and immediate execution as fallback
function initializeChat() {
    console.log('Chat page loaded, initializing...');
    checkAuth().then(() => {
        console.log('Auth check passed');
        setupEventListeners();
        console.log('Event listeners set up');
        loadInitialMessage();
        console.log('Initial message loaded');
    }).catch(error => {
        console.error('Initialization error:', error);
        // Show error to user
        const messagesContainer = document.getElementById('chatMessages');
        if (messagesContainer) {
            messagesContainer.innerHTML = `<p style="color: red; padding: 20px;">Error initializing chat: ${error.message}</p>`;
        }
    });
}

// Try multiple initialization methods
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeChat);
} else {
    // DOM already loaded
    initializeChat();
}

async function checkAuth() {
    try {
        const response = await fetch(`${API_BASE}/auth/user/`, {
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.authenticated) {
            currentUser = data.user;
            const welcomeEl = document.getElementById('welcomeMessage');
            if (welcomeEl) {
                welcomeEl.textContent = `Welcome back, ${data.user.username}!`;
            }
        } else {
            window.location.href = '/login/';
        }
    } catch (error) {
        console.error('Auth check failed:', error);
        // Immediately redirect to login if auth fails
        window.location.href = '/login/';
    }
}

function setupEventListeners() {
    // Send button
    const sendBtn = document.getElementById('sendBtn');
    if (sendBtn) {
        sendBtn.addEventListener('click', sendMessage);
    } else {
        console.error('Send button not found!');
    }
    
    // Enter key to send (Shift+Enter for new line)
    const messageInput = document.getElementById('messageInput');
    if (messageInput) {
        messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        
        // Auto-resize textarea
        messageInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 120) + 'px';
        });
    } else {
        console.error('Message input not found!');
    }
    
    // File attachment
    const attachBtn = document.getElementById('attachBtn');
    const fileInput = document.getElementById('fileInput');
    if (attachBtn && fileInput) {
        attachBtn.addEventListener('click', () => {
            fileInput.click();
        });
        fileInput.addEventListener('change', handleFileUpload);
    } else {
        console.error('File attachment elements not found!');
    }
    
    // Logout
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async () => {
            try {
                await fetch(`${API_BASE}/auth/logout/`, {
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
    
    // Voice input button
    const voiceBtn = document.getElementById('voiceBtn');
    if (voiceBtn) {
        initializeVoiceRecognition();
        setupVoiceButton(voiceBtn);
    } else {
        console.warn('Voice button not found');
    }
}

function loadInitialMessage() {
    const welcomeMsg = `👋 Hi! I'm Agent Twin, your AI writing companion. I learn your writing style and help you create content that sounds exactly like you.

Upload some writing samples to get started, or ask me to write something!`;
    addMessage('agent', welcomeMsg);
    // Don't add initial message to conversation history - it's just a greeting
}

async function sendMessage() {
    console.log('sendMessage called');
    const input = document.getElementById('messageInput');
    if (!input) {
        console.error('Message input not found!');
        return;
    }
    
    const text = input.value.trim();
    
    if (!text) {
        console.log('No text to send');
        return;
    }
    
    console.log('Sending message:', text);
    
    // Add user message to conversation history
    conversationHistory.push({ role: 'user', content: text });
    
    // Add user message to UI
    addMessage('user', text);
    input.value = '';
    input.style.height = 'auto';
    
    // Show typing indicator
    const typingId = showTypingIndicator();
    
    try {
        // Always send to generate endpoint - it now handles questions, generation, and conversation
        console.log('Sending to generate endpoint with conversation history');
        const response = await fetch(`${API_BASE}/generate/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({ 
                prompt: text,
                conversation_history: conversationHistory.slice(-10) // Last 10 messages for context
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        hideTypingIndicator(typingId);
        
        if (data.success) {
            // Add assistant response to conversation history
            conversationHistory.push({ role: 'assistant', content: data.generated_content });
            
            // Add message to UI
            addMessage('agent', data.generated_content, true);
            
            // If memory was extracted, show notification
            if (data.memory_extracted) {
                console.log('New memory extracted from conversation');
                // Show notification
                setTimeout(() => {
                    addMessage('system', '💡 I learned something new about you! <a href="/timeline/" style="color: var(--secondary); text-decoration: underline;">View Memory Timeline</a>');
                }, 500);
            }
        } else {
            const errorMsg = data.error || 'Generation failed';
            addMessage('system', `❌ Error: ${errorMsg}`);
            console.error('Generation error:', data);
        }
    } catch (error) {
        console.error('Send message error:', error);
        hideTypingIndicator(typingId);
            addMessage('system', `❌ Error: ${error.message}. Please try again or check the console for details.`);
    }
}

// Helper function to make links in messages clickable
function addMessage(type, text, showActions = false) {
    const messagesContainer = document.getElementById('chatMessages');
    if (!messagesContainer) {
        console.error('chatMessages container not found!');
        return;
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    
    const avatar = type === 'user' ? '👤' : '🤖';
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    let actionsHTML = '';
    if (showActions && type === 'agent') {
        actionsHTML = `
            <div class="message-actions">
                <button class="message-action-btn" onclick="window.copyMessage(this)">📋 Copy</button>
                <button class="message-action-btn" onclick="window.regenerateMessage()">🔄 Regenerate</button>
            </div>
        `;
    }
    
    // Convert text to HTML, preserving links
    const textHTML = text.replace(/\n/g, '<br>');
    
    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">
            <p class="message-text">${textHTML}</p>
            <div class="message-time">${time}</div>
            ${actionsHTML}
        </div>
    `;
    
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    messageHistory.push({ type, text, time });
}

function showTypingIndicator() {
    const messagesContainer = document.getElementById('chatMessages');
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message agent';
    typingDiv.id = 'typing-indicator';
    typingDiv.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="message-content">
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        </div>
    `;
    messagesContainer.appendChild(typingDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    return 'typing-indicator';
}

function hideTypingIndicator(id) {
    const indicator = document.getElementById(id);
    if (indicator) {
        indicator.remove();
    }
}

async function handleFileUpload(e) {
    const files = Array.from(e.target.files);
    
    for (const file of files) {
        await uploadFile(file);
    }
    
    // Reset input
    e.target.value = '';
}

async function uploadFile(file) {
    // Show upload message
    const uploadMessageId = `upload-${Date.now()}`;
    addFileUploadMessage(uploadMessageId, file.name);
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch(`${API_BASE}/upload-sample/`, {
            method: 'POST',
            credentials: 'include',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            updateFileUploadMessage(uploadMessageId, 'complete', data);
            addMessage('system', `✅ I've learned about your writing style! Found ${data.result.experiences_saved} experiences and ${data.result.personal_info_saved} personal details. <a href="/timeline/" style="color: var(--secondary); text-decoration: underline;">View Timeline</a>`);
        } else {
            updateFileUploadMessage(uploadMessageId, 'error', data);
            addMessage('system', `❌ Error: ${data.error || 'Upload failed'}`);
        }
    } catch (error) {
        console.error('File upload error:', error);
        updateFileUploadMessage(uploadMessageId, 'error', { error: error.message });
        addMessage('system', `❌ Upload error: ${error.message}`);
    }
}

function addFileUploadMessage(id, fileName) {
    const messagesContainer = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message user';
    messageDiv.id = id;
    messageDiv.innerHTML = `
        <div class="message-avatar">👤</div>
        <div class="message-content">
            <div class="file-message">
                <div class="file-icon">📄</div>
                <div class="file-info">
                    <div class="file-name">${fileName}</div>
                    <div class="file-progress">
                        <div class="file-progress-fill" style="width: 0%"></div>
                    </div>
                </div>
            </div>
        </div>
    `;
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function updateFileUploadMessage(id, status, data) {
    const messageDiv = document.getElementById(id);
    if (!messageDiv) return;
    
    if (status === 'complete') {
        messageDiv.querySelector('.file-progress-fill').style.width = '100%';
        messageDiv.querySelector('.file-progress-fill').style.background = 'var(--highlight)';
    } else if (status === 'error') {
        messageDiv.querySelector('.file-progress-fill').style.background = 'var(--accent)';
        messageDiv.querySelector('.file-name').textContent += ' - Error: ' + (data.error || 'Upload failed');
    }
}

// Timeline functions removed - now on separate page

// Make functions globally accessible
window.copyMessage = function(btn) {
    console.log('copyMessage called');
    try {
        const messageText = btn.closest('.message-content').querySelector('.message-text').textContent;
        navigator.clipboard.writeText(messageText).then(() => {
            btn.textContent = '✓ Copied!';
            setTimeout(() => {
                btn.textContent = '📋 Copy';
            }, 2000);
        }).catch(err => {
            console.error('Failed to copy:', err);
            alert('Failed to copy to clipboard');
        });
    } catch (error) {
        console.error('Copy error:', error);
    }
}

window.regenerateMessage = function() {
    console.log('regenerateMessage called');
    // Get last user message from conversation history
    const lastUserMsg = conversationHistory.filter(m => m.role === 'user').pop();
    if (lastUserMsg) {
        // Remove the last assistant response from conversation history
        if (conversationHistory.length > 0 && conversationHistory[conversationHistory.length - 1].role === 'assistant') {
            conversationHistory.pop();
        }
        // Remove the last assistant message from UI
        const messagesContainer = document.getElementById('chatMessages');
        if (messagesContainer) {
            const messages = messagesContainer.querySelectorAll('.message.agent');
            if (messages.length > 0) {
                messages[messages.length - 1].remove();
            }
        }
        // Resend the last user message
        const input = document.getElementById('messageInput');
        if (input) {
            input.value = lastUserMsg.content;
            sendMessage();
        }
    } else {
        addMessage('system', 'No previous message to regenerate');
    }
}

// Make sendMessage globally accessible for debugging
window.sendMessage = sendMessage;

// ==================== VOICE FUNCTIONALITY ====================

function initializeVoiceRecognition() {
    // Check if browser supports Web Speech API
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        console.warn('Speech recognition not supported in this browser');
        const voiceBtn = document.getElementById('voiceBtn');
        if (voiceBtn) {
            voiceBtn.disabled = true;
            voiceBtn.title = 'Voice input not supported in this browser';
        }
        return;
    }
    
    // Initialize speech recognition
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';
    
    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        console.log('Voice transcript:', transcript);
        
        // Put transcript in input field
        const input = document.getElementById('messageInput');
        if (input) {
            input.value = transcript;
            input.style.height = 'auto';
            input.style.height = Math.min(input.scrollHeight, 120) + 'px';
        }
        
        // Automatically send the message
        setTimeout(() => {
            sendVoiceMessage(transcript);
        }, 100);
    };
    
    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        stopVoiceRecording();
        addMessage('system', `Voice recognition error: ${event.error}`);
    };
    
    recognition.onend = () => {
        stopVoiceRecording();
    };
}

function setupVoiceButton(button) {
    let isPressed = false;
    
    button.addEventListener('mousedown', (e) => {
        e.preventDefault();
        if (!isRecording) {
            startVoiceRecording();
            isPressed = true;
        }
    });
    
    button.addEventListener('mouseup', () => {
        if (isPressed && isRecording) {
            stopVoiceRecording();
            isPressed = false;
        }
    });
    
    button.addEventListener('mouseleave', () => {
        if (isPressed && isRecording) {
            stopVoiceRecording();
            isPressed = false;
        }
    });
    
    // Touch events for mobile
    button.addEventListener('touchstart', (e) => {
        e.preventDefault();
        if (!isRecording) {
            startVoiceRecording();
            isPressed = true;
        }
    });
    
    button.addEventListener('touchend', (e) => {
        e.preventDefault();
        if (isPressed && isRecording) {
            stopVoiceRecording();
            isPressed = false;
        }
    });
}

function startVoiceRecording() {
    if (!recognition) {
        console.error('Speech recognition not initialized');
        return;
    }
    
    if (isRecording) {
        return;
    }
    
    isRecording = true;
    const voiceBtn = document.getElementById('voiceBtn');
    const voiceIndicator = document.getElementById('voiceIndicator');
    
    if (voiceBtn) {
        voiceBtn.style.background = 'var(--accent)';
        voiceBtn.style.transform = 'scale(1.1)';
    }
    
    if (voiceIndicator) {
        voiceIndicator.style.display = 'flex';
    }
    
    try {
        recognition.start();
        console.log('Voice recording started');
    } catch (error) {
        console.error('Error starting recognition:', error);
        stopVoiceRecording();
    }
}

function stopVoiceRecording() {
    if (!isRecording) {
        return;
    }
    
    isRecording = false;
    const voiceBtn = document.getElementById('voiceBtn');
    const voiceIndicator = document.getElementById('voiceIndicator');
    
    if (voiceBtn) {
        voiceBtn.style.background = '';
        voiceBtn.style.transform = '';
    }
    
    if (voiceIndicator) {
        voiceIndicator.style.display = 'none';
    }
    
    if (recognition) {
        try {
            recognition.stop();
        } catch (error) {
            // Ignore errors when stopping
        }
    }
    
    console.log('Voice recording stopped');
}

async function sendVoiceMessage(text) {
    if (!text || !text.trim()) {
        return;
    }
    
    // Add user message to conversation history
    conversationHistory.push({ role: 'user', content: text });
    
    // Add user message to UI
    addMessage('user', text);
    
    // Show typing indicator
    const typingId = showTypingIndicator();
    
    try {
        // Use voice_ask endpoint which is optimized for voice
        const response = await fetch(`${window.API_BASE}/voice/ask/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({
                text: text,
                conversation_history: conversationHistory.slice(-10)
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        hideTypingIndicator(typingId);
        
        if (data.success) {
            // Add assistant response to conversation history
            conversationHistory.push({ role: 'assistant', content: data.response_text });
            
            // Add assistant message to UI
            addMessage('agent', data.response_text);
            
            // Speak the response if voice is enabled
            if (voiceEnabled && 'speechSynthesis' in window) {
                speakResponse(data.response_text);
            }
            
            // Show memory extraction notification if applicable
            if (data.memory_extracted) {
                setTimeout(() => {
                    addMessage('system', '💡 I learned something new from our conversation! Check your <a href="/timeline/" style="color: var(--secondary); text-decoration: underline;">Memory Timeline</a> to see what I remembered.');
                }, 500);
            }
        } else {
            throw new Error(data.error || 'Failed to get response');
        }
    } catch (error) {
        console.error('Error sending voice message:', error);
        hideTypingIndicator(typingId);
        addMessage('system', `Error: ${error.message}`);
    }
}

function speakResponse(text) {
    if (!('speechSynthesis' in window)) {
        console.warn('Text-to-speech not supported');
        return;
    }
    
    // Cancel any ongoing speech
    window.speechSynthesis.cancel();
    
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;
    utterance.lang = 'en-US';
    
    utterance.onerror = (event) => {
        console.error('Speech synthesis error:', event.error);
    };
    
    window.speechSynthesis.speak(utterance);
}

