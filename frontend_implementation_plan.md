# Frontend Implementation Plan for Batch Voice Processing

## Overview
This document outlines the implementation plan for modifying the frontend to support both single and batch voice processing modes in the Voice Adder tab.

## HTML Modifications

### Location
Update the Voice Adder tab in `templates/index.html` (around line 251-314).

### Implementation Details

#### 1. Add Mode Selector
Replace the current file selection section with a mode selector and conditional sections:

```html
<!-- Voice Adder Tab -->
<div id="voice-adder" class="tab-pane">
    <!-- Mode Selection -->
    <section class="card">
        <h2><i class="fas fa-microphone"></i> Processing Mode</h2>
        <div class="form-group">
            <label>Select Processing Mode</label>
            <div class="mode-selector">
                <label class="mode-option">
                    <input type="radio" name="voice-mode" value="single" checked> Single File
                </label>
                <label class="mode-option">
                    <input type="radio" name="voice-mode" value="batch"> Batch Processing
                </label>
            </div>
        </div>
    </section>
    
    <!-- Single File Mode Section -->
    <div id="voice-single-section">
        <!-- File Selection -->
        <section class="card">
            <h2><i class="fas fa-microphone"></i> Select Files</h2>
            <div class="form-group">
                <label for="voice-video-file">Video File</label>
                <input type="file" id="voice-video-file" accept="video/mp4">
                <small>Select a MP4 video file</small>
            </div>
            <div class="form-group">
                <label for="voice-audio-file">Voice Audio File</label>
                <input type="file" id="voice-audio-file" accept="audio/mp3,audio/ogg,audio/wav">
                <small>Select a voice audio file (MP3, OGG, or WAV)</small>
            </div>
        </section>
    </div>
    
    <!-- Batch Processing Mode Section -->
    <div id="voice-batch-section" class="hidden">
        <!-- Folder Selection -->
        <section class="card">
            <h2><i class="fas fa-microphone"></i> Select Folders</h2>
            <div class="form-group">
                <label for="voice-video-folder-path">Video Folder Path</label>
                <input type="text" id="voice-video-folder-path" placeholder="Example: /Users/username/Videos">
                <small>Enter the full path to the folder containing your MP4 videos</small>
            </div>
            <div class="form-group">
                <label for="voice-audio-folder-path">Voice Audio Folder Path</label>
                <input type="text" id="voice-audio-folder-path" placeholder="Example: /Users/username/VoiceAudios">
                <small>Enter the full path to the folder containing your voice audio files</small>
            </div>
            <button id="scan-voice-folders-btn"><i class="fas fa-search"></i> Scan Folders</button>
        </section>
        
        <!-- File Lists Section (hidden initially) -->
        <div id="voice-batch-file-list-section" class="card hidden">
            <h2><i class="fas fa-file"></i> Found Files</h2>
            <div id="voice-batch-info" class="info-box">
                <h3><i class="fas fa-info-circle"></i> Batch Processing Information</h3>
                <ul>
                    <li>Videos and audio files will be paired sequentially (first video with first audio, etc.)</li>
                    <li>If there are different numbers of files, only the minimum number of pairs will be processed</li>
                    <li>The same volume settings will be applied to all videos</li>
                </ul>
            </div>
            <div class="file-counts">
                <div id="voice-video-count" class="info"></div>
                <div id="voice-audio-count" class="info"></div>
                <div id="voice-pairs-count" class="info"></div>
            </div>
            <div class="file-lists">
                <div class="file-list-container">
                    <h3>Video Files</h3>
                    <div id="voice-video-list" class="file-grid"></div>
                </div>
                <div class="file-list-container">
                    <h3>Voice Audio Files</h3>
                    <div id="voice-audio-list" class="file-grid"></div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Shared Settings Section -->
    <section class="card">
        <h2><i class="fas fa-sliders-h"></i> Settings</h2>
        <div class="form-group">
            <label for="original-audio-volume">Original Audio Volume</label>
            <div class="volume-control">
                <input type="range" id="original-audio-volume" min="0" max="100" value="30">
                <span id="volume-value">30%</span>
            </div>
            <small>Adjust the volume of the original video audio (0-100%)</small>
        </div>
        <div class="form-group">
            <label for="output-folder-path-voice">Output Folder Path</label>
            <input type="text" id="output-folder-path-voice" placeholder="Example: /Users/username/Desktop/outputs">
            <small>Enter the full path where you want to save the output video(s)</small>
        </div>
        <button id="process-voice-btn"><i class="fas fa-play"></i> Process Video</button>
    </section>
    
    <!-- File Info Section (for single mode) -->
    <div id="voice-file-info-section" class="card hidden">
        <h2><i class="fas fa-info-circle"></i> File Information</h2>
        <div class="file-info-container">
            <div class="file-info-item">
                <h3>Video File</h3>
                <div id="video-file-info" class="file-details"></div>
            </div>
            <div class="file-info-item">
                <h3>Voice Audio File</h3>
                <div id="audio-file-info" class="file-details"></div>
            </div>
        </div>
    </div>
    
    <!-- Progress Section -->
    <div id="voice-progress-section" class="card hidden">
        <h2><i class="fas fa-tasks"></i> Processing Status</h2>
        <div class="progress-container">
            <div class="progress-bar">
                <div class="progress-fill-voice"></div>
            </div>
            <div class="progress-text-voice">0%</div>
        </div>
        <div id="voice-status-message"></div>
    </div>
    
    <!-- Results Section -->
    <div id="voice-results-section" class="card hidden">
        <h2><i class="fas fa-download"></i> Download Results</h2>
        <div id="voice-download-link" class="download-container"></div>
    </div>
</div>
```

## CSS Modifications

### Location
Add these styles to `static/css/style.css`.

### Implementation Details

```css
/* Mode Selector Styles */
.mode-selector {
    display: flex;
    gap: 10px;
    margin-top: 10px;
}

.mode-option {
    display: flex;
    align-items: center;
    padding: 10px 20px;
    background-color: #f0f0f0;
    border-radius: 5px;
    cursor: pointer;
    transition: background-color 0.3s;
}

.mode-option:hover {
    background-color: #e0e0e0;
}

.mode-option input[type="radio"] {
    margin-right: 8px;
}

.mode-option:has(input:checked) {
    background-color: #007bff;
    color: white;
}

/* Batch Info Box */
.info-box {
    background-color: #f8f9fa;
    border-left: 4px solid #007bff;
    padding: 15px;
    margin-bottom: 20px;
    border-radius: 4px;
}

.info-box h3 {
    margin-top: 0;
    color: #007bff;
}

.info-box ul {
    margin-bottom: 0;
    padding-left: 20px;
}

.info-box li {
    margin-bottom: 5px;
}

/* File List Styles for Batch Mode */
.file-lists {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin-top: 20px;
}

.file-list-container {
    border: 1px solid #ddd;
    border-radius: 5px;
    padding: 15px;
}

.file-list-container h3 {
    margin-top: 0;
    margin-bottom: 15px;
    color: #333;
    border-bottom: 1px solid #eee;
    padding-bottom: 10px;
}

.file-grid {
    display: grid;
    gap: 10px;
    max-height: 300px;
    overflow-y: auto;
}

.file-item {
    display: flex;
    align-items: center;
    padding: 8px;
    background-color: #f9f9f9;
    border-radius: 4px;
    transition: background-color 0.2s;
}

.file-item:hover {
    background-color: #f0f0f0;
}

.file-item i {
    margin-right: 10px;
    color: #007bff;
}

.file-info h4 {
    margin: 0;
    font-size: 14px;
    font-weight: 500;
}

.file-info p {
    margin: 0;
    font-size: 12px;
    color: #666;
}

/* File Counts Styling */
.file-counts {
    display: flex;
    gap: 20px;
    margin: 15px 0;
}

.file-counts .info {
    padding: 8px 15px;
    background-color: #e9ecef;
    border-radius: 4px;
    font-weight: 500;
}

/* Download Container for Batch Results */
.download-container {
    display: grid;
    gap: 10px;
}

.download-item {
    display: flex;
    align-items: center;
    padding: 10px;
    background-color: #f8f9fa;
    border-radius: 4px;
    transition: background-color 0.2s;
}

.download-item:hover {
    background-color: #e9ecef;
}

.download-item a {
    display: flex;
    align-items: center;
    text-decoration: none;
    color: #007bff;
    width: 100%;
}

.download-item i {
    margin-right: 10px;
}
```

## JavaScript Modifications

### Location
Update the JavaScript functions in `static/js/main.js` (around line 921-1216).

### Implementation Details

#### 1. Add New DOM Elements
Add these to the DOM Elements section (around line 72-87):

```javascript
// Voice Adder mode elements
const voiceModeInputs = document.querySelectorAll('input[name="voice-mode"]');
const voiceSingleSection = document.getElementById('voice-single-section');
const voiceBatchSection = document.getElementById('voice-batch-section');
const voiceVideoFolderPathInput = document.getElementById('voice-video-folder-path');
const voiceAudioFolderPathInput = document.getElementById('voice-audio-folder-path');
const scanVoiceFoldersBtn = document.getElementById('scan-voice-folders-btn');
const voiceBatchFileListSection = document.getElementById('voice-batch-file-list-section');
const voiceVideoCount = document.getElementById('voice-video-count');
const voiceAudioCount = document.getElementById('voice-audio-count');
const voicePairsCount = document.getElementById('voice-pairs-count');
const voiceVideoList = document.getElementById('voice-video-list');
const voiceAudioList = document.getElementById('voice-audio-list');
```

#### 2. Add Mode Switching Event Listeners
Add these to the Event Listeners section (around line 159):

```javascript
// Voice Adder mode switching
voiceModeInputs.forEach(input => {
    input.addEventListener('change', handleVoiceModeChange);
});

// Batch mode event listeners
scanVoiceFoldersBtn.addEventListener('click', scanVoiceFolders);
```

#### 3. Add New Functions

```javascript
// Voice Adder mode switching
function handleVoiceModeChange() {
    const selectedMode = document.querySelector('input[name="voice-mode"]:checked').value;
    const processBtn = document.getElementById('process-voice-btn');
    
    if (selectedMode === 'single') {
        voiceSingleSection.classList.remove('hidden');
        voiceBatchSection.classList.add('hidden');
        voiceFileInfoSection.classList.remove('hidden');
        processBtn.innerHTML = '<i class="fas fa-play"></i> Process Video';
    } else {
        voiceSingleSection.classList.add('hidden');
        voiceBatchSection.classList.remove('hidden');
        voiceFileInfoSection.classList.add('hidden');
        processBtn.innerHTML = '<i class="fas fa-play"></i> Process Batch';
    }
}

// Batch mode folder scanning
async function scanVoiceFolders() {
    const videoFolderPath = voiceVideoFolderPathInput.value.trim();
    const audioFolderPath = voiceAudioFolderPathInput.value.trim();
    
    if (!videoFolderPath) {
        alert('Please enter a video folder path');
        return;
    }
    
    if (!audioFolderPath) {
        alert('Please enter an audio folder path');
        return;
    }
    
    scanVoiceFoldersBtn.disabled = true;
    scanVoiceFoldersBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Scanning...';
    
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
            displayVoiceBatchFiles(videoData.videos, audioData.audios);
            voiceBatchFileListSection.classList.remove('hidden');
        } else {
            alert('Error: ' + (videoData.error || audioData.error));
        }
    } catch (error) {
        alert('Network error: ' + error.message);
    } finally {
        scanVoiceFoldersBtn.disabled = false;
        scanVoiceFoldersBtn.innerHTML = '<i class="fas fa-search"></i> Scan Folders';
    }
}

function displayVoiceBatchFiles(videos, audios) {
    const numPairs = Math.min(videos.length, audios.length);
    
    voiceVideoCount.textContent = `Found ${videos.length} videos`;
    voiceAudioCount.textContent = `Found ${audios.length} audio files`;
    voicePairsCount.textContent = `Will process ${numPairs} pairs`;
    
    voiceVideoList.innerHTML = videos.map((video, index) => `
        <div class="file-item ${index < numPairs ? 'will-process' : 'will-skip'}">
            <i class="fas fa-file-video"></i>
            <div class="file-info">
                <h4>${video.name}</h4>
                <p>Duration: ${formatDuration(video.duration)}</p>
            </div>
            ${index >= numPairs ? '<span class="skip-badge">Will be skipped</span>' : ''}
        </div>
    `).join('');
    
    voiceAudioList.innerHTML = audios.map((audio, index) => `
        <div class="file-item ${index < numPairs ? 'will-process' : 'will-skip'}">
            <i class="fas fa-file-audio"></i>
            <div class="file-info">
                <h4>${audio.name}</h4>
                <p>Duration: ${formatDuration(audio.duration)}</p>
            </div>
            ${index >= numPairs ? '<span class="skip-badge">Will be skipped</span>' : ''}
        </div>
    `).join('');
}
```

#### 4. Modify Existing Functions

```javascript
// Modify startVoiceProcessing function
async function startVoiceProcessing() {
    const selectedMode = document.querySelector('input[name="voice-mode"]:checked').value;
    const outputFolderPath = outputFolderPathVoiceInput.value.trim();
    const originalAudioVolume = parseInt(originalAudioVolumeInput.value);
    
    if (!outputFolderPath) {
        alert('Please select an output folder');
        return;
    }
    
    if (selectedMode === 'single') {
        await startSingleVoiceProcessing(outputFolderPath, originalAudioVolume);
    } else {
        await startBatchVoiceProcessing(outputFolderPath, originalAudioVolume);
    }
}

async function startSingleVoiceProcessing(outputFolderPath, originalAudioVolume) {
    const videoFile = voiceVideoFileInput.files[0];
    const audioFile = voiceAudioFileInput.files[0];
    
    if (!videoFile) {
        alert('Please select a video file');
        return;
    }
    
    if (!audioFile) {
        alert('Please select a voice audio file');
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

async function startBatchVoiceProcessing(outputFolderPath, originalAudioVolume) {
    const videoFolderPath = voiceVideoFolderPathInput.value.trim();
    const audioFolderPath = voiceAudioFolderPathInput.value.trim();
    
    if (!videoFolderPath) {
        alert('Please select a video folder');
        return;
    }
    
    if (!audioFolderPath) {
        alert('Please select an audio folder');
        return;
    }
    
    processVoiceBtn.disabled = true;
    processVoiceBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
    
    showVoiceProgressSection();
    updateVoiceProgress(0, 'Starting batch processing...');
    
    try {
        const response = await fetch(`${API_BASE}/api/process-voice-batch`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                video_folder_path: videoFolderPath,
                audio_folder_path: audioFolderPath,
                output_folder_path: outputFolderPath,
                original_audio_volume: originalAudioVolume,
            }),
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
        processVoiceBtn.innerHTML = '<i class="fas fa-play"></i> Process Batch';
    }
}

// Modify showVoiceResult function to handle multiple files
function showVoiceResult(outputs) {
    if (Array.isArray(outputs)) {
        // Batch mode - multiple outputs
        voiceDownloadLink.innerHTML = outputs.map(filename => `
            <div class="download-item">
                <a href="${API_BASE}/api/download/${currentVoiceBatchId}/${filename}" download>
                    <i class="fas fa-download"></i>
                    ${filename}
                </a>
            </div>
        `).join('');
    } else {
        // Single mode - one output
        voiceDownloadLink.innerHTML = `
            <div class="download-item">
                <a href="${API_BASE}/api/download/${currentVoiceBatchId}/${outputs}" download>
                    <i class="fas fa-download"></i>
                    ${outputs}
                </a>
            </div>
        `;
    }
    
    voiceResultsSection.classList.remove('hidden');
}
```

## Summary
This frontend implementation plan:
1. Adds a mode selector to switch between single and batch processing
2. Creates conditional UI sections for each mode
3. Implements folder scanning and file listing for batch mode
4. Adds appropriate styling for the new UI elements
5. Updates JavaScript to handle both processing modes
6. Reuses existing progress tracking and result display components

The implementation follows the existing patterns in the codebase and provides a seamless user experience for both single and batch voice processing.