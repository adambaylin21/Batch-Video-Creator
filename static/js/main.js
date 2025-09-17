const API_BASE = 'http://localhost:5001';
let currentBatchId = null;
let currentVABatchId = null;
let currentVoiceBatchId = null;
let statusInterval = null;
let vaStatusInterval = null;
let voiceStatusInterval = null;

// DOM Elements
// Tab elements
const tabBtns = document.querySelectorAll('.tab-btn');
const tabPanes = document.querySelectorAll('.tab-pane');

// Batch Creator elements
const inputFolderPathInput = document.getElementById('input-folder-path');
const outputFolderPathInput = document.getElementById('output-folder-path');
const scanBtn = document.getElementById('scan-btn');
const videoListSection = document.getElementById('video-list-section');
const videoCount = document.getElementById('video-count');
const videoList = document.getElementById('video-list');
const configSection = document.getElementById('config-section');
const videoCountInput = document.getElementById('videos-per-output');
const videoDurationInput = document.getElementById('video-duration');
const outputCountInput = document.getElementById('output-count');
const processBtn = document.getElementById('process-btn');
const progressSection = document.getElementById('progress-section');
const progressFill = document.querySelector('.progress-fill');
const progressText = document.querySelector('.progress-text');
const statusMessage = document.getElementById('status-message');
const resultsSection = document.getElementById('results-section');
const downloadLinks = document.getElementById('download-links');
const videoTrimModeSelect = document.getElementById('video-trim-mode');
const videoDurationDescription = document.getElementById('video-duration-description');

// Video-Audio Merger elements
const videoFolderPathInput = document.getElementById('video-folder-path');
const audioFolderPathInput = document.getElementById('audio-folder-path');
const outputFolderPathInputVA = document.getElementById('output-folder-path-va');
const scanVABtn = document.getElementById('scan-va-btn');
const vaFileListSection = document.getElementById('va-file-list-section');
const videoCountVA = document.getElementById('video-count-va');
const audioCountVA = document.getElementById('audio-count-va');
const videoListVA = document.getElementById('video-list-va');
const audioListVA = document.getElementById('audio-list-va');
const processVABtn = document.getElementById('process-va-btn');
const vaProgressSection = document.getElementById('va-progress-section');
const vaProgressFill = document.querySelector('.progress-fill-va');
const vaProgressText = document.querySelector('.progress-text-va');
const vaStatusMessage = document.getElementById('va-status-message');
const vaResultsSection = document.getElementById('va-results-section');
const vaDownloadLinks = document.getElementById('va-download-links');
const audioTrimModeSelect = document.getElementById('audio-trim-mode');
const audioSelectionModeSelect = document.getElementById('audio-selection-mode');

// Voice Adder elements
const voiceVideoFileInput = document.getElementById('voice-video-file');
const voiceAudioFileInput = document.getElementById('voice-audio-file');
const originalAudioVolumeInput = document.getElementById('original-audio-volume');
const volumeValueSpan = document.getElementById('volume-value');
const outputFolderPathVoiceInput = document.getElementById('output-folder-path-voice');
const processVoiceBtn = document.getElementById('process-voice-btn');
const voiceFileInfoSection = document.getElementById('voice-file-info-section');
const videoFileInfo = document.getElementById('video-file-info');
const audioFileInfo = document.getElementById('audio-file-info');
const voiceProgressSection = document.getElementById('voice-progress-section');
const voiceProgressFill = document.querySelector('.progress-fill-voice');
const voiceProgressText = document.querySelector('.progress-text-voice');
const voiceStatusMessage = document.getElementById('voice-status-message');
const voiceResultsSection = document.getElementById('voice-results-section');
const voiceDownloadLink = document.getElementById('voice-download-link');

// Event Listeners
// Tab switching
tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        const tabId = btn.getAttribute('data-tab');
        
        // Update active tab button
        tabBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        // Update active tab pane
        tabPanes.forEach(pane => {
            pane.classList.remove('active');
            if (pane.id === tabId) {
                pane.classList.add('active');
            }
        });
    });
});

// Batch Creator event listeners
scanBtn.addEventListener('click', scanFolder);
processBtn.addEventListener('click', startProcessing);
videoTrimModeSelect.addEventListener('change', updateVideoDurationDescription);

// Video-Audio Merger event listeners
scanVABtn.addEventListener('click', scanVAFolders);
processVABtn.addEventListener('click', startVAProcessing);

// Voice Adder event listeners
voiceVideoFileInput.addEventListener('change', handleVideoFileSelect);
voiceAudioFileInput.addEventListener('change', handleAudioFileSelect);
originalAudioVolumeInput.addEventListener('input', updateVolumeValue);
processVoiceBtn.addEventListener('click', startVoiceProcessing);

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

function updateVideoDurationDescription() {
    const mode = videoTrimModeSelect.value;
    if (mode === 'fixed') {
        videoDurationDescription.textContent = 'Each video will be cut to this duration (start from 0s)';
    } else {
        videoDurationDescription.textContent = 'Each video will be cut to this duration (random start position)';
    }
}

async function startProcessing() {
    const inputFolderPath = inputFolderPathInput.value.trim();
    const outputFolderPath = outputFolderPathInput.value.trim();
    const videoCount = parseInt(videoCountInput.value);
    const videoDuration = parseFloat(videoDurationInput.value);
    const videoTrimMode = videoTrimModeSelect.value;
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
                video_trim_mode: videoTrimMode,
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

// Video-Audio Merger Functions
async function scanVAFolders() {
    const videoFolderPath = videoFolderPathInput.value.trim();
    const audioFolderPath = audioFolderPathInput.value.trim();
    
    if (!videoFolderPath) {
        alert('Please enter a video folder path');
        return;
    }
    
    if (!audioFolderPath) {
        alert('Please enter an audio folder path');
        return;
    }
    
    scanVABtn.disabled = true;
    scanVABtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Scanning...';
    
    try {
        // Scan video folder
        const videoResponse = await fetch(`${API_BASE}/api/scan-folder`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ folder_path: videoFolderPath }),
        });
        
        // Scan audio folder
        const audioResponse = await fetch(`${API_BASE}/api/scan-audio-folder`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ folder_path: audioFolderPath }),
        });
        
        const videoData = await videoResponse.json();
        const audioData = await audioResponse.json();
        
        if (videoResponse.ok && audioResponse.ok) {
            displayVAFiles(videoData.videos, audioData.audios);
            showVAProcessSection();
        } else {
            alert('Error: ' + (videoData.error || audioData.error));
        }
    } catch (error) {
        alert('Network error: ' + error.message);
    } finally {
        scanVABtn.disabled = false;
        scanVABtn.innerHTML = '<i class="fas fa-search"></i> Scan Folders';
    }
}

function displayVAFiles(videos, audios) {
    videoCountVA.textContent = `Found ${videos.length} videos`;
    audioCountVA.textContent = `Found ${audios.length} audio files`;
    
    videoListVA.innerHTML = videos.map(video => `
        <div class="file-item">
            <i class="fas fa-file-video"></i>
            <div class="file-info">
                <h4>${video.name}</h4>
                <p>Duration: ${formatDuration(video.duration)}</p>
            </div>
        </div>
    `).join('');
    
    audioListVA.innerHTML = audios.map(audio => `
        <div class="file-item">
            <i class="fas fa-file-audio"></i>
            <div class="file-info">
                <h4>${audio.name}</h4>
                <p>Duration: ${formatDuration(audio.duration)}</p>
            </div>
        </div>
    `).join('');
    
    vaFileListSection.classList.remove('hidden');
}

function showVAProcessSection() {
    // Show the process button
    processVABtn.style.display = 'block';
}

async function startVAProcessing() {
    const videoFolderPath = videoFolderPathInput.value.trim();
    const audioFolderPath = audioFolderPathInput.value.trim();
    const outputFolderPath = outputFolderPathInputVA.value.trim();
    const audioTrimMode = audioTrimModeSelect.value;
    const audioSelectionMode = audioSelectionModeSelect.value;
    
    if (!videoFolderPath) {
        alert('Please select a video folder first');
        return;
    }
    
    if (!audioFolderPath) {
        alert('Please select an audio folder first');
        return;
    }
    
    if (!outputFolderPath) {
        alert('Please select an output folder first');
        return;
    }
    
    processVABtn.disabled = true;
    processVABtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
    
    showVAProgressSection();
    updateVAProgress(0, 'Starting processing...');
    
    try {
        const response = await fetch(`${API_BASE}/api/process-video-audio-batch`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                video_folder_path: videoFolderPath,
                audio_folder_path: audioFolderPath,
                output_folder_path: outputFolderPath,
                audio_trim_mode: audioTrimMode,
                audio_selection_mode: audioSelectionMode,
            }),
        });
        
        const data = await response.json();
        
        if (response.ok) {
            currentVABatchId = data.batch_id;
            pollVAStatus();
        } else {
            alert('Error: ' + data.error);
            hideVAProgressSection();
        }
    } catch (error) {
        alert('Network error: ' + error.message);
        hideVAProgressSection();
    } finally {
        processVABtn.disabled = false;
        processVABtn.innerHTML = '<i class="fas fa-play"></i> Start Processing';
    }
}

function showVAProgressSection() {
    vaProgressSection.classList.remove('hidden');
    vaResultsSection.classList.add('hidden');
}

function hideVAProgressSection() {
    vaProgressSection.classList.add('hidden');
}

function updateVAProgress(percent, message) {
    vaProgressFill.style.width = `${percent}%`;
    vaProgressText.textContent = `${percent}%`;
    vaStatusMessage.textContent = message;
}

async function pollVAStatus() {
    if (vaStatusInterval) {
        clearInterval(vaStatusInterval);
    }
    
    vaStatusInterval = setInterval(async () => {
        try {
            const response = await fetch(`${API_BASE}/api/status/${currentVABatchId}`);
            const data = await response.json();
            
            if (response.ok) {
                updateVAProgress(data.progress || 0, data.message || data.status);
                
                if (data.status === 'completed') {
                    clearInterval(vaStatusInterval);
                    showVAResults(data.outputs);
                } else if (data.status === 'error') {
                    clearInterval(vaStatusInterval);
                    alert('Processing error: ' + data.error);
                    hideVAProgressSection();
                }
            } else {
                clearInterval(vaStatusInterval);
                alert('Status error: ' + data.error);
                hideVAProgressSection();
            }
        } catch (error) {
            clearInterval(vaStatusInterval);
            alert('Network error: ' + error.message);
            hideVAProgressSection();
        }
    }, 2000);
}

function showVAResults(outputs) {
    vaDownloadLinks.innerHTML = outputs.map(filename => `
        <div class="download-item">
            <a href="${API_BASE}/api/download/${currentVABatchId}/${filename}" download>
                <i class="fas fa-download"></i>
                ${filename}
            </a>
        </div>
    `).join('');
    
    vaResultsSection.classList.remove('hidden');
}

// Voice Adder Functions
function handleVideoFileSelect() {
    const file = voiceVideoFileInput.files[0];
    if (file) {
        displayFileInfo('video', file);
    }
}

function handleAudioFileSelect() {
    const file = voiceAudioFileInput.files[0];
    if (file) {
        displayFileInfo('audio', file);
    }
}

function updateVolumeValue() {
    volumeValueSpan.textContent = `${originalAudioVolumeInput.value}%`;
}

function displayFileInfo(type, file) {
    if (type === 'video') {
        videoFileInfo.innerHTML = `
            <div class="file-info-row">
                <span class="file-info-label">Name:</span>
                <span class="file-info-value">${file.name}</span>
            </div>
            <div class="file-info-row">
                <span class="file-info-label">Size:</span>
                <span class="file-info-value">${formatFileSize(file.size)}</span>
            </div>
            <div class="file-info-row">
                <span class="file-info-label">Type:</span>
                <span class="file-info-value">${file.type}</span>
            </div>
        `;
    } else if (type === 'audio') {
        audioFileInfo.innerHTML = `
            <div class="file-info-row">
                <span class="file-info-label">Name:</span>
                <span class="file-info-value">${file.name}</span>
            </div>
            <div class="file-info-row">
                <span class="file-info-label">Size:</span>
                <span class="file-info-value">${formatFileSize(file.size)}</span>
            </div>
            <div class="file-info-row">
                <span class="file-info-label">Type:</span>
                <span class="file-info-value">${file.type}</span>
            </div>
        `;
    }
    
    // Show the file info section if both files are selected
    if (voiceVideoFileInput.files[0] && voiceAudioFileInput.files[0]) {
        voiceFileInfoSection.classList.remove('hidden');
    }
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

async function startVoiceProcessing() {
    const videoFile = voiceVideoFileInput.files[0];
    const audioFile = voiceAudioFileInput.files[0];
    const outputFolderPath = outputFolderPathVoiceInput.value.trim();
    const originalAudioVolume = parseInt(originalAudioVolumeInput.value);
    
    if (!videoFile) {
        alert('Please select a video file');
        return;
    }
    
    if (!audioFile) {
        alert('Please select a voice audio file');
        return;
    }
    
    if (!outputFolderPath) {
        alert('Please select an output folder');
        return;
    }
    
    processVoiceBtn.disabled = true;
    processVoiceBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
    
    showVoiceProgressSection();
    updateVoiceProgress(0, 'Starting processing...');
    
    try {
        const formData = new FormData();
        formData.append('video_file', videoFile);
        formData.append('audio_file', audioFile);
        formData.append('output_folder_path', outputFolderPath);
        formData.append('original_audio_volume', originalAudioVolume);
        
        const response = await fetch(`${API_BASE}/api/process-voice-adder`, {
            method: 'POST',
            body: formData,
        });
        
        const data = await response.json();
        
        if (response.ok) {
            currentVoiceBatchId = data.batch_id;
            pollVoiceStatus();
        } else {
            alert('Error: ' + data.error);
            hideVoiceProgressSection();
        }
    } catch (error) {
        alert('Network error: ' + error.message);
        hideVoiceProgressSection();
    } finally {
        processVoiceBtn.disabled = false;
        processVoiceBtn.innerHTML = '<i class="fas fa-play"></i> Process Video';
    }
}

function showVoiceProgressSection() {
    voiceProgressSection.classList.remove('hidden');
    voiceResultsSection.classList.add('hidden');
}

function hideVoiceProgressSection() {
    voiceProgressSection.classList.add('hidden');
}

function updateVoiceProgress(percent, message) {
    voiceProgressFill.style.width = `${percent}%`;
    voiceProgressText.textContent = `${percent}%`;
    voiceStatusMessage.textContent = message;
}

async function pollVoiceStatus() {
    if (voiceStatusInterval) {
        clearInterval(voiceStatusInterval);
    }
    
    voiceStatusInterval = setInterval(async () => {
        try {
            const response = await fetch(`${API_BASE}/api/status/${currentVoiceBatchId}`);
            const data = await response.json();
            
            if (response.ok) {
                updateVoiceProgress(data.progress || 0, data.message || data.status);
                
                if (data.status === 'completed') {
                    clearInterval(voiceStatusInterval);
                    showVoiceResult(data.outputs[0]);
                } else if (data.status === 'error') {
                    clearInterval(voiceStatusInterval);
                    alert('Processing error: ' + data.error);
                    hideVoiceProgressSection();
                }
            } else {
                clearInterval(voiceStatusInterval);
                alert('Status error: ' + data.error);
                hideVoiceProgressSection();
            }
        } catch (error) {
            clearInterval(voiceStatusInterval);
            alert('Network error: ' + error.message);
            hideVoiceProgressSection();
        }
    }, 2000);
}

function showVoiceResult(filename) {
    voiceDownloadLink.innerHTML = `
        <a href="${API_BASE}/api/download/${currentVoiceBatchId}/${filename}" download>
            <i class="fas fa-download"></i>
            ${filename}
        </a>
    `;
    
    voiceResultsSection.classList.remove('hidden');
}

// Initialize video duration description on page load
document.addEventListener('DOMContentLoaded', function() {
    updateVideoDurationDescription();
});