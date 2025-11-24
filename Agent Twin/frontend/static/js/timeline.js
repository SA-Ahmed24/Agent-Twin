// Timeline Page JavaScript

// Use existing API_BASE if already declared (by auth.js), otherwise declare it
// Store in window to avoid redeclaration errors when multiple scripts load
if (typeof window.API_BASE === 'undefined') {
    window.API_BASE = '/api';
}
// Reference window.API_BASE directly to avoid const redeclaration errors
// Don't create a local const - just use window.API_BASE throughout

console.log('Timeline.js script loaded, API_BASE:', window.API_BASE);

// Declare loadMemory function (will be defined below)
let loadMemory;

// Try multiple initialization methods
function initializeTimeline() {
    console.log('Initializing timeline page...');
    
    // Check if elements exist
    const container = document.getElementById('timelineContainer');
    const summaryContainer = document.getElementById('memorySummary');
    console.log('Container found:', !!container);
    console.log('Summary container found:', !!summaryContainer);
    
    if (!container) {
        console.error('timelineContainer element not found!');
        return;
    }
    
    checkAuth().then(() => {
        console.log('Auth check passed, loading memory...');
        loadMemory();
        setupEventListeners();
    }).catch(error => {
        console.error('Auth check failed:', error);
        // Don't redirect immediately - show error
        if (container) {
            container.innerHTML = `
                <div class="loading-state">
                    <p style="color: var(--accent);">Authentication error: ${error.message}</p>
                    <p style="margin-top: 10px; color: var(--text-medium);">Redirecting to login...</p>
                </div>
            `;
        }
        setTimeout(() => {
            window.location.href = '/login/';
        }, 2000);
    });
}

// Try DOMContentLoaded first
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeTimeline);
} else {
    // DOM already loaded
    initializeTimeline();
}

// Fallback: try after a short delay
setTimeout(() => {
    if (document.getElementById('timelineContainer') && document.getElementById('timelineContainer').innerHTML.includes('Loading your memories...')) {
        console.log('Still loading after 2 seconds, checking if script executed...');
    }
}, 2000);

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
                const username = data.user.username;
                welcomeEl.textContent = `${username}'s Memory Timeline`;
            }
        } else {
            window.location.href = '/login/';
        }
    } catch (error) {
        console.error('Auth check error:', error);
        window.location.href = '/login/';
    }
}

function setupEventListeners() {
    // Refresh button
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            loadMemory();
            // Add visual feedback
            refreshBtn.style.transform = 'rotate(360deg)';
            setTimeout(() => {
                refreshBtn.style.transform = 'rotate(0deg)';
            }, 500);
        });
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

// Define loadMemory function
loadMemory = async function() {
    console.log('Loading memory...');
    const container = document.getElementById('timelineContainer');
    const summaryContainer = document.getElementById('memorySummary');
    
    // Show loading state
    if (container) {
        container.innerHTML = `
            <div class="loading-state">
                <div class="spinner"></div>
                <p>Loading your memories...</p>
            </div>
        `;
    }
    
    // Also show loading for summary
    if (summaryContainer) {
        summaryContainer.innerHTML = `
            <div class="summary-card"><div class="number">...</div><div class="label">Loading</div></div>
            <div class="summary-card"><div class="number">...</div><div class="label">Loading</div></div>
            <div class="summary-card"><div class="number">...</div><div class="label">Loading</div></div>
        `;
    }
    
    try {
        console.log('Fetching memory from:', `${window.API_BASE}/memory/view/`);
        const response = await fetch(`${window.API_BASE}/memory/view/`, {
            method: 'GET',
            credentials: 'include',
            headers: {
                'Accept': 'application/json'
            }
        });
        
        console.log('Response status:', response.status, response.statusText);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Response error text:', errorText);
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('Memory data received:', data);
        console.log('Timeline length:', data.timeline ? data.timeline.length : 0);
        console.log('Summary:', data.summary);
        
        if (data.success) {
            console.log('Rendering memory summary and timeline...');
            renderMemorySummary(data.summary, summaryContainer);
            renderTimeline(data.timeline, container);
            console.log('Rendering complete!');
        } else {
            throw new Error(data.error || 'Failed to load memory');
        }
    } catch (error) {
        console.error('Failed to load memory:', error);
        console.error('Error stack:', error.stack);
        if (container) {
            container.innerHTML = `
                <div class="loading-state">
                    <p style="color: var(--accent); font-size: 1.1em; margin-bottom: 15px;">❌ Error loading memories: ${error.message}</p>
                    <button onclick="window.loadMemory()" class="btn btn-primary" style="margin-top: 20px; padding: 12px 24px; border-radius: 25px; cursor: pointer; background: var(--secondary); color: white; border: none;">🔄 Retry</button>
                    <p style="margin-top: 15px; color: var(--text-medium); font-size: 0.9em;">Check browser console (F12) for more details</p>
                    <p style="margin-top: 10px; color: var(--text-medium); font-size: 0.85em;">API Endpoint: ${window.API_BASE}/memory/view/</p>
                </div>
            `;
        }
        // Also clear summary on error
        if (summaryContainer) {
            summaryContainer.innerHTML = '';
        }
    }
};

// Make loadMemory globally accessible immediately
window.loadMemory = loadMemory;
console.log('✅ loadMemory function assigned to window');

function renderMemorySummary(summary, container) {
    console.log('Rendering memory summary:', summary, 'in container:', container);
    if (!container) {
        console.error('Summary container not found!');
        return;
    }
    
    if (!summary) {
        console.warn('Summary data is null or undefined');
        container.innerHTML = `
            <div class="summary-card"><div class="number">0</div><div class="label">Experiences</div></div>
            <div class="summary-card"><div class="number">0</div><div class="label">Personal Info</div></div>
            <div class="summary-card"><div class="number">0</div><div class="label">Documents</div></div>
        `;
        return;
    }
    
    const html = `
        <div class="summary-card">
            <span class="number">${summary.total_experiences || 0}</span>
            <div class="label">Experiences</div>
        </div>
        <div class="summary-card">
            <span class="number">${summary.total_personal_info || 0}</span>
            <div class="label">Personal Info</div>
        </div>
        <div class="summary-card">
            <span class="number">${summary.total_documents || 0}</span>
            <div class="label">Documents</div>
        </div>
    `;
    
    container.innerHTML = html;
    console.log('Summary rendered successfully');
}

function renderTimeline(timeline, container) {
    console.log('Rendering timeline:', timeline, 'in container:', container);
    if (!container) {
        console.error('Timeline container not found!');
        return;
    }
    
    if (!timeline || timeline.length === 0) {
        console.log('No timeline data, showing empty state');
        container.innerHTML = `
            <div class="loading-state">
                <p style="font-size: 1.1em; color: var(--text-medium);">🧠 No memories yet. Start chatting or upload some documents!</p>
                <a href="/" class="btn btn-primary" style="margin-top: 20px; display: inline-block; padding: 12px 24px; border-radius: 25px; text-decoration: none; background: var(--secondary); color: white;">💬 Go to Chat</a>
            </div>
        `;
        return;
    }
    
    console.log(`Rendering ${timeline.length} timeline items`);
    
    let html = '';
    timeline.forEach((item, index) => {
        try {
            const date = new Date(item.date).toLocaleString();
            const icon = getIconForType(item.type);
            const typeClass = getClassForType(item.type);
            
            // Handle grouped entries
            let description = item.description || 'Memory item';
            let detailsContent = '';
            
            if (item.grouped && item.details && item.details.entries) {
                const entries = item.details.entries;
                if (entries.length > 1) {
                    const parts = [];
                    entries.forEach(entry => {
                        if (entry.key === 'background') {
                            parts.push(entry.value.substring(0, 60));
                        } else {
                            parts.push(`${entry.key}: ${entry.value}`);
                        }
                    });
                    description = `Learned ${item.details.group || 'information'}: ${parts.join(' • ')}`;
                }
                detailsContent = `
                    <details class="timeline-details">
                        <summary>► View Details</summary>
                        <div class="timeline-grouped-entries">
                            ${entries.map(entry => `
                                <div class="timeline-entry-item">
                                    <strong>${entry.key}:</strong> ${entry.value}
                                </div>
                            `).join('')}
                        </div>
                    </details>
                `;
            } else if (item.details) {
                detailsContent = `
                    <details class="timeline-details">
                        <summary>► View Details</summary>
                        <pre style="background: var(--white); padding: 15px; border-radius: 8px; overflow-x: auto;">${JSON.stringify(item.details, null, 2)}</pre>
                    </details>
                `;
            }
            
            html += `
                <div class="timeline-item ${typeClass}" style="animation-delay: ${index * 0.1}s">
                    <div class="timeline-icon">${icon}</div>
                    <div class="timeline-content">
                        <div class="timeline-date">${date}</div>
                        <div class="timeline-title">${description}</div>
                        ${detailsContent}
                    </div>
                </div>
            `;
        } catch (error) {
            console.error('Error rendering timeline item:', error, item);
        }
    });
    
    container.innerHTML = html;
    console.log('Timeline rendered successfully with', timeline.length, 'items');
}

function getIconForType(type) {
    const icons = {
        'style_learned': '📝',
        'experience_discovered': '💼',
        'personal_info_learned': '👤',
        'document_uploaded': '📄'
    };
    return icons[type] || '📌';
}

function getClassForType(type) {
    if (type === 'style_learned') return 'style';
    if (type === 'experience_discovered') return 'experience';
    if (type === 'personal_info_learned') return 'personal';
    if (type === 'document_uploaded') return 'document';
    return '';
}

// Already assigned above

