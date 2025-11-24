// Onboarding JavaScript

// Use relative URL to avoid CORS issues
const API_BASE = '/api';

let currentStep = 1;
let selectedFiles = [];

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupFileUpload();
});

function setupFileUpload() {
    const uploadZone = document.getElementById('uploadZone');
    const fileInput = document.getElementById('fileInput');
    
    // Click to upload
    uploadZone.addEventListener('click', () => {
        fileInput.click();
    });
    
    // File input change
    fileInput.addEventListener('change', (e) => {
        handleFiles(Array.from(e.target.files));
    });
    
    // Drag and drop
    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('dragover');
    });
    
    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('dragover');
    });
    
    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('dragover');
        handleFiles(Array.from(e.dataTransfer.files));
    });
}

function handleFiles(files) {
    files.forEach(file => {
        if (!selectedFiles.find(f => f.name === file.name && f.size === file.size)) {
            selectedFiles.push(file);
        }
    });
    updateFileList();
    updateUploadButton();
}

function updateFileList() {
    const fileList = document.getElementById('fileList');
    fileList.innerHTML = '';
    
    selectedFiles.forEach((file, index) => {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        fileItem.innerHTML = `
            <div class="file-item-info">
                <span>📄</span>
                <span class="file-item-name">${file.name}</span>
                <span style="color: var(--text-light); font-size: 0.9em;">(${(file.size / 1024).toFixed(1)} KB)</span>
            </div>
            <button class="file-item-remove" onclick="removeFile(${index})">Remove</button>
        `;
        fileList.appendChild(fileItem);
    });
}

function removeFile(index) {
    selectedFiles.splice(index, 1);
    updateFileList();
    updateUploadButton();
}

function updateUploadButton() {
    const uploadBtn = document.getElementById('uploadBtn');
    uploadBtn.disabled = selectedFiles.length === 0;
}

function nextStep() {
    if (currentStep < 5) {
        // Save basic info if on step 2
        if (currentStep === 2) {
            saveBasicInfo();
        }
        
        currentStep++;
        showStep(currentStep);
        updateProgressIndicator();
    }
}

function prevStep() {
    if (currentStep > 1) {
        currentStep--;
        showStep(currentStep);
        updateProgressIndicator();
    }
}

function skipToUpload() {
    currentStep = 3;
    showStep(currentStep);
    updateProgressIndicator();
}

function showStep(step) {
    document.querySelectorAll('.onboarding-step').forEach(s => {
        s.classList.remove('active');
    });
    document.getElementById(`step${step}`).classList.add('active');
}

function updateProgressIndicator() {
    document.querySelectorAll('.progress-dot').forEach((dot, index) => {
        if (index + 1 <= currentStep) {
            dot.classList.add('active');
        } else {
            dot.classList.remove('active');
        }
    });
}

async function saveBasicInfo() {
    const name = document.getElementById('name').value;
    const university = document.getElementById('university').value;
    const major = document.getElementById('major').value;
    
    // This will be saved when files are uploaded
    // For now, just store in sessionStorage
    sessionStorage.setItem('basicInfo', JSON.stringify({ name, university, major }));
}

async function uploadFiles() {
    if (selectedFiles.length === 0) return;
    
    // Move to processing step
    currentStep = 4;
    showStep(currentStep);
    updateProgressIndicator();
    
    const formData = new FormData();
    selectedFiles.forEach(file => {
        formData.append('files', file);
    });
    
    // Update progress
    updateProcessingStatus('Uploading files...', 20);
    
    try {
        const response = await fetch(`${API_BASE}/onboarding/upload/`, {
            method: 'POST',
            credentials: 'include',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            updateProcessingStatus('Analyzing writing style...', 50);
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            updateProcessingStatus('Extracting experiences...', 75);
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            updateProcessingStatus('Complete!', 100);
            await new Promise(resolve => setTimeout(resolve, 500));
            
            // Show summary
            showSummary(data.summary);
            currentStep = 5;
            showStep(currentStep);
            updateProgressIndicator();
        } else {
            alert(`Error: ${data.error}`);
        }
    } catch (error) {
        console.error('Upload error:', error);
        alert(`Error: ${error.message}. Make sure you're logged in and the server is running.`);
    }
}

function updateProcessingStatus(text, progress) {
    document.getElementById('processingStatus').textContent = text;
    document.getElementById('progressFill').style.width = `${progress}%`;
}

function showSummary(summary) {
    const summaryDiv = document.getElementById('onboardingSummary');
    summaryDiv.innerHTML = `
        <div class="summary-item">
            <strong>📄 Files Processed:</strong> ${summary.total_files}
        </div>
        <div class="summary-item">
            <strong>💼 Experiences Found:</strong> ${summary.total_experiences}
        </div>
        <div class="summary-item">
            <strong>👤 Personal Info Learned:</strong> ${summary.total_personal_info}
        </div>
    `;
}

function completeOnboarding() {
    window.location.href = '/';
}

