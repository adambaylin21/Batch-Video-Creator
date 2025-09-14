const API_BASE = 'http://localhost:5001';
let currentBatchId = null;
let statusInterval = null;

// DOM Elements
const inputFolderPathInput = document.getElementById('input-folder-path');
const outputFolderPathInput = document.getElementById('output-folder-path');
const scanBtn = document.getElementById('scan-btn');
const videoListSection = document.getElementById('video-list-section');
const videoCount = document.getElementById('video-count');
const videoList = document.getElementById('video-list');
const configSection = document.getElementById('config-section');
const videoCountInput = document.getElementById('video-count');
const videoDurationInput = document.getElementById('video-duration');
const outputCountInput = document.getElementById('output-count');
const processBtn = document.getElementById('process-btn');
const progressSection = document.getElementById('progress-section');
const progressFill = document.querySelector('.progress-fill');
const progressText = document.querySelector('.progress-text');
const statusMessage = document.getElementById('status-message');
const resultsSection = document.getElementById('results-section');
const downloadLinks = document.getElementById('download-links');

// Event Listeners
scanBtn.addEventListener('click', scanFolder);
processBtn.addEventListener('click', startProcessing);

// Functions
async function browseInputFolder() {
    // Try to use the File System Access API first (Chrome/Edge supported)
    if ('showDirectoryPicker' in window) {
        try {
            const dirHandle = await window.showDirectoryPicker({
                mode: 'read'
            });
            
            // Try to get the path from the handle
            // Note: Due to security restrictions, we can't get the actual path in all browsers
            // But we can try some approaches
            let path = '';
            
            // Check if the handle has a name property (most browsers)
            if (dirHandle.name) {
                // Try to construct a reasonable path
                path = `/path/to/${dirHandle.name}`;
                
                // Try to get a more accurate path if possible
                try {
                    // This might work in some environments
                    if (dirHandle.resolve && typeof dirHandle.resolve === 'function') {
                        const resolved = await dirHandle.resolve();
                        if (resolved && resolved.path) {
                            path = resolved.path;
                        }
                    }
                } catch (e) {
                    // Ignore errors, use the constructed path
                }
            }
            
            // Show a modal to confirm the path
            showPathConfirmationModal('input', path);
            return;
        } catch (err) {
            if (err.name !== 'AbortError') {
                console.error('Error selecting directory:', err);
            }
            // User cancelled or API not available, fall back to webkitdirectory
        }
    }
    
    // Fallback: Try to use webkitdirectory attribute
    tryFolderSelection('input');
}

async function browseOutputFolder() {
    // Try to use the File System Access API first (Chrome/Edge supported)
    if ('showDirectoryPicker' in window) {
        try {
            const dirHandle = await window.showDirectoryPicker({
                mode: 'readwrite'
            });
            
            // Try to get the path from the handle
            let path = '';
            
            // Check if the handle has a name property (most browsers)
            if (dirHandle.name) {
                // Try to construct a reasonable path
                path = `/path/to/${dirHandle.name}`;
                
                // Try to get a more accurate path if possible
                try {
                    // This might work in some environments
                    if (dirHandle.resolve && typeof dirHandle.resolve === 'function') {
                        const resolved = await dirHandle.resolve();
                        if (resolved && resolved.path) {
                            path = resolved.path;
                        }
                    }
                } catch (e) {
                    // Ignore errors, use the constructed path
                }
            }
            
            // Show a modal to confirm the path
            showPathConfirmationModal('output', path);
            return;
        } catch (err) {
            if (err.name !== 'AbortError') {
                console.error('Error selecting directory:', err);
            }
            // User cancelled or API not available, fall back to webkitdirectory
        }
    }
    
    // Fallback: Try to use webkitdirectory attribute
    tryFolderSelection('output');
}

function showFolderSelectionInstructions(type) {
    // Create a modal with instructions instead of using alert
    const modal = document.createElement('div');
    modal.className = 'modal';
    
    const title = type === 'input' ? 'Select Input Folder' : 'Select Output Folder';
    const description = type === 'input' ?
        'For the best experience, please select a folder containing your video files.' :
        'Please enter the path where you want to save the merged video files.';
    
    const examplePath = type === 'input' ?
        '/Users/username/Videos' :
        '/Users/username/Desktop/outputs';
    
    // Try to detect the user's OS for more specific instructions
    const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
    const osName = isMac ? 'Mac' : 'Windows';
    const fileExplorer = isMac ? 'Finder' : 'File Explorer';
    const copyShortcut = isMac ? 'Cmd+C' : 'Ctrl+C';
    const pasteShortcut = isMac ? 'Cmd+V' : 'Ctrl+V';
    
    modal.innerHTML = `
        <div class="modal-content">
            <h3>${title}</h3>
            <p>${description}</p>
            <p><strong>Instructions for ${osName}:</strong></p>
            <ol>
                <li>Open ${fileExplorer}</li>
                <li>Navigate to the ${type === 'input' ? 'folder containing your videos' : 'folder where you want to save outputs'}</li>
                <li>Click on the address bar to highlight the full path</li>
                <li>Copy the path (${copyShortcut})</li>
                <li>Paste it into the input field (${pasteShortcut})</li>
            </ol>
            <div class="example-path">
                <strong>Example:</strong> <code>${examplePath}</code>
            </div>
            <div class="modal-actions">
                <button id="copy-example-btn" class="btn-secondary">Copy Example</button>
                <button id="try-folder-btn" class="btn-secondary">Try Folder Selection</button>
                <button id="close-modal-btn" class="btn-primary">OK</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Add event listeners
    document.getElementById('close-modal-btn').addEventListener('click', () => {
        document.body.removeChild(modal);
        if (type === 'input') {
            inputFolderPathInput.focus();
        } else {
            outputFolderPathInput.focus();
        }
    });
    
    document.getElementById('copy-example-btn').addEventListener('click', () => {
        navigator.clipboard.writeText(examplePath).then(() => {
            const btn = document.getElementById('copy-example-btn');
            const originalText = btn.textContent;
            btn.textContent = 'Copied!';
            setTimeout(() => {
                btn.textContent = originalText;
            }, 2000);
        });
    });
    
    document.getElementById('try-folder-btn').addEventListener('click', () => {
        document.body.removeChild(modal);
        tryFolderSelection(type);
    });
    
    // Focus the appropriate input field when modal is closed
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            document.body.removeChild(modal);
            if (type === 'input') {
                inputFolderPathInput.focus();
            } else {
                outputFolderPathInput.focus();
            }
        }
    });
}

function tryFolderSelection(type) {
    // Try to use the webkitdirectory attribute for folder selection
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.webkitdirectory = true;
    fileInput.directory = true;
    
    fileInput.onchange = function(e) {
        const files = e.target.files;
        if (files && files.length > 0) {
            // Get the directory path from the first file
            const firstFile = files[0];
            const relativePath = firstFile.webkitRelativePath;
            if (relativePath) {
                // Extract directory name from the relative path
                const dirName = relativePath.split('/')[0];
                
                // Show a modal to help the user construct the full path
                showPathConstructionModal(type, dirName);
            } else if (firstFile.path) {
                // For Electron context, extract directory from full path
                const directory = firstFile.path.substring(0, firstFile.path.lastIndexOf('\\') !== -1 ?
                    firstFile.path.lastIndexOf('\\') : firstFile.path.lastIndexOf('/'));
                if (type === 'input') {
                    inputFolderPathInput.value = directory;
                } else {
                    outputFolderPathInput.value = directory;
                }
            } else {
                // Fallback for browsers that don't expose path information
                showFolderSelectionInstructions(type);
            }
        }
    };
    
    fileInput.click();
}

function showPathConstructionModal(type, dirName) {
    const modal = document.createElement('div');
    modal.className = 'modal';
    
    const title = type === 'input' ? 'Complete Input Folder Path' : 'Complete Output Folder Path';
    
    // Try to detect common paths based on the directory name
    const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
    let suggestedPaths = [];
    
    if (isMac) {
        suggestedPaths = [
            `/Users/${dirName}`,
            `/Users/username/${dirName}`,
            `/Users/admin/${dirName}`,
            `/Users/${dirName}`,
            `/Volumes/${dirName}`
        ];
    } else {
        suggestedPaths = [
            `C:\\Users\\${dirName}`,
            `C:\\Users\\username\\${dirName}`,
            `C:\\Users\\admin\\${dirName}`,
            `D:\\${dirName}`,
            `E:\\${dirName}`
        ];
    }
    
    let pathOptions = suggestedPaths.map((path, index) =>
        `<div class="path-option">
            <input type="radio" name="path-option" id="path-option-${index}" value="${path}" ${index === 0 ? 'checked' : ''}>
            <label for="path-option-${index}">${path}</label>
        </div>`
    ).join('');
    
    modal.innerHTML = `
        <div class="modal-content">
            <h3>${title}</h3>
            <p>You selected a folder named: <strong>${dirName}</strong></p>
            <p>Please select the most likely path or edit it:</p>
            <div class="path-options-container">
                ${pathOptions}
            </div>
            <div class="path-input-container">
                <input type="text" id="custom-path-input" class="full-path-input" value="${suggestedPaths[0]}" placeholder="Enter the full path">
            </div>
            <div class="modal-actions">
                <button id="use-path-btn" class="btn-primary">Use This Path</button>
                <button id="cancel-btn" class="btn-secondary">Cancel</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Focus the input field
    const customPathInput = document.getElementById('custom-path-input');
    customPathInput.focus();
    
    // Add event listeners for radio buttons
    const radioButtons = modal.querySelectorAll('input[name="path-option"]');
    radioButtons.forEach(radio => {
        radio.addEventListener('change', () => {
            customPathInput.value = radio.value;
        });
    });
    
    // Add event listeners
    document.getElementById('use-path-btn').addEventListener('click', () => {
        const fullPath = customPathInput.value.trim();
        if (fullPath) {
            if (type === 'input') {
                inputFolderPathInput.value = fullPath;
            } else {
                outputFolderPathInput.value = fullPath;
            }
        }
        document.body.removeChild(modal);
    });
    
    document.getElementById('cancel-btn').addEventListener('click', () => {
        document.body.removeChild(modal);
        showFolderSelectionInstructions(type);
    });
    
    // Handle Enter key
    customPathInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            document.getElementById('use-path-btn').click();
        }
    });
}

function showPathConfirmationModal(type, path) {
    const modal = document.createElement('div');
    modal.className = 'modal';
    
    const title = type === 'input' ? 'Confirm Input Folder Path' : 'Confirm Output Folder Path';
    
    modal.innerHTML = `
        <div class="modal-content">
            <h3>${title}</h3>
            <p>You selected a folder. Please confirm or edit the path:</p>
            <div class="path-input-container">
                <input type="text" id="confirmed-path-input" class="full-path-input" value="${path}" placeholder="Enter the full path to the folder">
            </div>
            <div class="modal-actions">
                <button id="confirm-path-btn" class="btn-primary">Confirm</button>
                <button id="edit-path-btn" class="btn-secondary">Edit Manually</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Focus the input field
    const pathInput = document.getElementById('confirmed-path-input');
    pathInput.focus();
    pathInput.select();
    
    // Add event listeners
    document.getElementById('confirm-path-btn').addEventListener('click', () => {
        const confirmedPath = pathInput.value.trim();
        if (confirmedPath) {
            if (type === 'input') {
                inputFolderPathInput.value = confirmedPath;
            } else {
                outputFolderPathInput.value = confirmedPath;
            }
        }
        document.body.removeChild(modal);
    });
    
    document.getElementById('edit-path-btn').addEventListener('click', () => {
        document.body.removeChild(modal);
        showFolderSelectionInstructions(type);
    });
    
    // Handle Enter key
    pathInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            document.getElementById('confirm-path-btn').click();
        }
    });
}

async function scanFolder() {
    const inputFolderPath = inputFolderPathInput.value.trim();
    if (!inputFolderPath) {
        alert('Please enter an input folder path');
        return;
    }
    
    scanBtn.disabled = true;
    scanBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Scanning...';
    
    try {
        const response = await fetch(`${API_BASE}/api/scan-folder`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ folder_path: inputFolderPath }),
        });
        
        const data = await response.json();
        
        if (response.ok) {
            displayVideos(data.videos);
            showConfigSection();
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        alert('Network error: ' + error.message);
    } finally {
        scanBtn.disabled = false;
        scanBtn.innerHTML = '<i class="fas fa-search"></i> Scan Folder';
    }
}

function displayVideos(videos) {
    videoCount.textContent = `Found ${videos.length} videos`;
    videoList.innerHTML = videos.map(video => `
        <div class="video-item">
            <i class="fas fa-file-video"></i>
            <div class="video-info">
                <h4>${video.name}</h4>
                <p>Duration: ${formatDuration(video.duration)}</p>
            </div>
        </div>
    `).join('');
    
    videoListSection.classList.remove('hidden');
}

function formatDuration(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function showConfigSection() {
    configSection.classList.remove('hidden');
}

async function startProcessing() {
    const inputFolderPath = inputFolderPathInput.value.trim();
    const outputFolderPath = outputFolderPathInput.value.trim();
    const videoCount = parseInt(videoCountInput.value);
    const videoDuration = parseFloat(videoDurationInput.value);
    const outputCount = parseInt(outputCountInput.value);
    
    if (!inputFolderPath) {
        alert('Please select an input folder first');
        return;
    }
    
    if (!outputFolderPath) {
        alert('Please select an output folder first');
        return;
    }
    
    processBtn.disabled = true;
    processBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
    
    showProgressSection();
    updateProgress(0, 'Starting processing...');
    
    try {
        const response = await fetch(`${API_BASE}/api/process-batch`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                input_folder_path: inputFolderPath,
                output_folder_path: outputFolderPath,
                video_count: videoCount,
                video_duration: videoDuration,
                output_count: outputCount,
            }),
        });
        
        const data = await response.json();
        
        if (response.ok) {
            currentBatchId = data.batch_id;
            pollStatus();
        } else {
            alert('Error: ' + data.error);
            hideProgressSection();
        }
    } catch (error) {
        alert('Network error: ' + error.message);
        hideProgressSection();
    } finally {
        processBtn.disabled = false;
        processBtn.innerHTML = '<i class="fas fa-play"></i> Start Processing';
    }
}

function showProgressSection() {
    progressSection.classList.remove('hidden');
    resultsSection.classList.add('hidden');
}

function hideProgressSection() {
    progressSection.classList.add('hidden');
}

function updateProgress(percent, message) {
    progressFill.style.width = `${percent}%`;
    progressText.textContent = `${percent}%`;
    statusMessage.textContent = message;
}

async function pollStatus() {
    if (statusInterval) {
        clearInterval(statusInterval);
    }
    
    statusInterval = setInterval(async () => {
        try {
            const response = await fetch(`${API_BASE}/api/status/${currentBatchId}`);
            const data = await response.json();
            
            if (response.ok) {
                updateProgress(data.progress || 0, data.message || data.status);
                
                if (data.status === 'completed') {
                    clearInterval(statusInterval);
                    showResults(data.outputs);
                } else if (data.status === 'error') {
                    clearInterval(statusInterval);
                    alert('Processing error: ' + data.error);
                    hideProgressSection();
                }
            } else {
                clearInterval(statusInterval);
                alert('Status error: ' + data.error);
                hideProgressSection();
            }
        } catch (error) {
            clearInterval(statusInterval);
            alert('Network error: ' + error.message);
            hideProgressSection();
        }
    }, 2000);
}

function showResults(outputs) {
    downloadLinks.innerHTML = outputs.map(filename => `
        <div class="download-item">
            <a href="${API_BASE}/api/download/${currentBatchId}/${filename}" download>
                <i class="fas fa-download"></i>
                ${filename}
            </a>
        </div>
    `).join('');
    
    resultsSection.classList.remove('hidden');
}