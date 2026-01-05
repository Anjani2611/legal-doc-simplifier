let currentSessionId = null;
let currentFilename = null;

// ============================================================================
// INITIALIZATION
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    setupTabSystem();
    setupTextInput();
    setupFileUpload();
    setupExports();
});

// ============================================================================
// TAB SYSTEM
// ============================================================================

function setupTabSystem() {
    const tabButtons = document.querySelectorAll('.tab-button');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const tabName = this.getAttribute('data-tab');
            const section = this.closest('.section');
            
            // Remove active class from all buttons in this section
            section.querySelectorAll('.tab-button').forEach(btn => {
                btn.classList.remove('active');
            });
            
            // Remove active class from all contents in this section
            section.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            
            // Add active class to clicked button
            this.classList.add('active');
            
            // Add active class to corresponding content
            const tabContent = section.querySelector(`#${tabName}`);
            if (tabContent) {
                tabContent.classList.add('active');
            }
        });
    });
}

// ============================================================================
// TEXT INPUT
// ============================================================================

function setupTextInput() {
    const simplifyBtn = document.getElementById('simplifyBtn');
    if (simplifyBtn) {
        simplifyBtn.addEventListener('click', handleSimplifyText);
    }
}

async function handleSimplifyText() {
    const textInput = document.getElementById('textInput').value.trim();
    
    if (!textInput) {
        showMessage('Please enter text to simplify', 'error');
        return;
    }
    
    try {
        const response = await fetch(`/simplify/text?text=${encodeURIComponent(textInput)}`);
        
        if (!response.ok) {
            throw new Error('Simplification failed');
        }
        
        const data = await response.json();
        displayResults(data);
        showMessage('Text simplified successfully', 'success');
        
        // Switch to results tab
        switchTab('results');
    } catch (error) {
        showMessage(`Error: ${error.message}`, 'error');
    }
}

// ============================================================================
// FILE UPLOAD
// ============================================================================

function setupFileUpload() {
    const uploadZone = document.getElementById('uploadZone');
    const fileInput = document.getElementById('fileInput');
    
    if (!uploadZone || !fileInput) return;
    
    // Click to upload
    uploadZone.addEventListener('click', () => fileInput.click());
    
    // File selection
    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            handleFileUpload(file);
        }
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
        
        const file = e.dataTransfer.files[0];
        if (file) {
            handleFileUpload(file);
        }
    });
}

async function handleFileUpload(file) {
    // Validate
    if (!['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'].includes(file.type)) {
        showMessage('Only PDF and DOCX files are supported', 'error');
        return;
    }
    
    if (file.size > 25 * 1024 * 1024) {
        showMessage('File too large (max 25MB)', 'error');
        return;
    }
    
    // Show progress
    const uploadZone = document.getElementById('uploadZone');
    const uploadProgress = document.getElementById('uploadProgress');
    uploadZone.style.display = 'none';
    uploadProgress.style.display = 'block';
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Upload failed');
        }
        
        const data = await response.json();
        currentSessionId = data.session_id;
        currentFilename = data.filename;
        
        displayResults(data.simplify_output);
        showMessage(`File "${file.name}" uploaded and processed successfully`, 'success');
        switchTab('results');
    } catch (error) {
        showMessage(`Upload error: ${error.message}`, 'error');
    } finally {
        uploadZone.style.display = 'block';
        uploadProgress.style.display = 'none';
        document.getElementById('fileInput').value = '';
    }
}

// ============================================================================
// EXPORTS
// ============================================================================

function setupExports() {
    const downloadPdfBtn = document.getElementById('downloadPdfBtn');
    const downloadSimplePdfBtn = document.getElementById('downloadSimplePdfBtn');
    const downloadJsonBtn = document.getElementById('downloadJsonBtn');
    
    if (downloadPdfBtn) {
        downloadPdfBtn.addEventListener('click', handleExportPdf);
    }
    if (downloadSimplePdfBtn) {
        downloadSimplePdfBtn.addEventListener('click', handleExportSimplePdf);
    }
    if (downloadJsonBtn) {
        downloadJsonBtn.addEventListener('click', handleExportJson);
    }
}

async function handleExportPdf() {
    if (!currentSessionId) {
        showMessage('No session data. Please upload a file first.', 'error');
        return;
    }
    
    const btn = document.getElementById('downloadPdfBtn');
    btn.disabled = true;
    btn.textContent = 'Generating PDF...';
    
    try {
        const response = await fetch(`/export/pdf?session_id=${currentSessionId}`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error('PDF generation failed');
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${currentFilename || 'document'}_report.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        showMessage('Analysis PDF downloaded successfully', 'success');
    } catch (error) {
        showMessage(`PDF export error: ${error.message}`, 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Download Analysis Report';
    }
}

async function handleExportSimplePdf() {
    if (!currentSessionId) {
        showMessage('No session data. Please upload a file first.', 'error');
        return;
    }
    
    const btn = document.getElementById('downloadSimplePdfBtn');
    btn.disabled = true;
    btn.textContent = 'Generating PDF...';
    
    try {
        const response = await fetch(`/export/pdf/simple?session_id=${currentSessionId}`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error('PDF generation failed');
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${currentFilename || 'document'}_simplified.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        showMessage('Simplified PDF downloaded successfully', 'success');
    } catch (error) {
        showMessage(`PDF export error: ${error.message}`, 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Download Simplified PDF';
    }
}

async function handleExportJson() {
    if (!currentSessionId) {
        showMessage('No session data. Please upload a file first.', 'error');
        return;
    }
    
    const btn = document.getElementById('downloadJsonBtn');
    btn.disabled = true;
    btn.textContent = 'Generating JSON...';
    
    try {
        const response = await fetch(`/export/json?session_id=${currentSessionId}`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error('JSON export failed');
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${currentFilename || 'document'}_data.json`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        showMessage('JSON data downloaded successfully', 'success');
    } catch (error) {
        showMessage(`JSON export error: ${error.message}`, 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Download JSON Data';
    }
}

// ============================================================================
// DISPLAY RESULTS
// ============================================================================

function displayResults(data) {
    const container = document.getElementById('resultsContainer');
    
    if (!data || !data.clauses || data.clauses.length === 0) {
        container.innerHTML = '<p class="placeholder">No results to display</p>';
        return;
    }
    
    let html = '';
    data.clauses.forEach((clause, index) => {
        const expl = clause.explanation || {};
        html += `
            <div class="clause">
                <div class="clause-title">Section ${index + 1}: ${clause.type || 'Clause'}</div>
                <div class="clause-text">
                    <strong>Original clause:</strong><br>
                    <span style="color:#475569;">${clause.original_text || 'N/A'}</span>
                </div>
                <div class="clause-text" style="margin-top:0.75rem;">
                    <strong>Summary (plain English):</strong><br>
                    ${expl.summary || 'No summary available.'}
                </div>
                <div class="clause-text" style="margin-top:0.75rem;">
                    <strong>Who is protected?</strong><br>
                    ${expl.who_is_protected || 'Not extracted.'}
                </div>
                <div class="clause-text" style="margin-top:0.75rem;">
                    <strong>What is covered?</strong><br>
                    ${expl.what_is_covered || 'Not extracted.'}
                </div>
                <div class="clause-text" style="margin-top:0.75rem;">
                    <strong>Exceptions / limitations:</strong><br>
                    ${expl.exceptions || 'Not extracted.'}
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}


// ============================================================================
// UTILITIES
// ============================================================================

function showMessage(message, type = 'info') {
    const container = document.getElementById('messageContainer');
    const msg = document.createElement('div');
    msg.className = `message ${type}`;
    msg.textContent = message;
    
    container.appendChild(msg);
    
    setTimeout(() => {
        msg.remove();
    }, 5000);
}

function switchTab(tabName) {
    const button = document.querySelector(`[data-tab="${tabName}"]`);
    if (button) {
        button.click();
    }
}
