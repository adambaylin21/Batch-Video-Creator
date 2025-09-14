# Batch Video Creator Implementation Plan

## 1. Folder Structure Setup

### 1.1 Create Directory Structure
```
batch-creator/
├── app.py                 # Main Flask application
├── video_processor.py     # Video processing logic
├── config.py             # Configuration settings
├── static/
│   ├── css/
│   │   └── style.css     # Custom styles
│   └── js/
│       └── main.js       # Frontend JavaScript
├── templates/
│   └── index.html        # Main UI template
├── temp/                 # Temporary processing files
├── outputs/              # Output videos
├── requirements.txt      # Python dependencies
├── README.md            # Documentation
├── plan.md              # This plan
└── architecture.md      # Architecture diagrams
```

### 1.2 Requirements
- Copy requirements from parent project
- Add any additional dependencies if needed

## 2. Backend Implementation

### 2.1 config.py
```python
import os

# Flask Configuration
SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-123'
DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'

# Video Processing Configuration
DEFAULT_VIDEO_COUNT = 5
DEFAULT_VIDEO_DURATION = 10  # seconds - target duration for each video segment
DEFAULT_OUTPUT_COUNT = 1
MAX_VIDEO_COUNT = 20
MAX_OUTPUT_COUNT = 10

# File Paths
TEMP_FOLDER = 'temp'
OUTPUT_FOLDER = 'outputs'
ALLOWED_EXTENSIONS = {'mp4'}

# Video Processing
VIDEO_CODEC = 'libx264'
AUDIO_CODEC = 'aac'
TARGET_HEIGHT = 720
```

### 2.2 video_processor.py
```python
import os
import random
import uuid
import logging
from moviepy.editor import VideoFileClip
from merge_videos import merge_videos_with_trims

class VideoProcessor:
    def __init__(self, temp_folder, output_folder):
        self.temp_folder = temp_folder
        self.output_folder = output_folder
        os.makedirs(temp_folder, exist_ok=True)
        os.makedirs(output_folder, exist_ok=True)
    
    def scan_folder(self, folder_path):
        """Scan folder for videos and return metadata"""
        videos = []
        for filename in os.listdir(folder_path):
            if filename.lower().endswith('.mp4'):
                file_path = os.path.join(folder_path, filename)
                try:
                    with VideoFileClip(file_path) as clip:
                        videos.append({
                            'name': filename,
                            'path': file_path,
                            'duration': clip.duration
                        })
                except Exception as e:
                    logging.warning(f"Failed to read {filename}: {e}")
        return videos
    
    def select_videos(self, videos, count):
        """Randomly select videos"""
        if len(videos) <= count:
            return videos
        return random.sample(videos, count)
    
    def process_batch(self, folder_path, video_count, video_duration, output_count):
        """Process batch of videos"""
        # Scan all videos
        all_videos = self.scan_folder(folder_path)
        
        if not all_videos:
            raise ValueError("No videos found in the specified folder")
        
        outputs = []
        for i in range(output_count):
            # Select random videos
            selected_videos = self.select_videos(all_videos, video_count)
            
            # Create unique batch folder
            batch_folder = os.path.join(self.temp_folder, f"batch_{uuid.uuid4()}")
            os.makedirs(batch_folder, exist_ok=True)
            
            # Prepare files for merging
            files = []
            trims = {}
            
            for video in selected_videos:
                # Copy file to temp folder with UUID name
                temp_filename = f"{uuid.uuid4()}.mp4"
                temp_path = os.path.join(batch_folder, temp_filename)
                
                # Create symlink or copy file
                if hasattr(os, 'symlink'):
                    os.symlink(video['path'], temp_path)
                else:
                    import shutil
                    shutil.copy2(video['path'], temp_path)
                
                files.append(temp_filename)
                # Set trim parameters: start from 0, end at video_duration or video duration (whichever is smaller)
                end_time = min(video_duration, video['duration'])
                trims[temp_filename] = {'start': 0, 'end': end_time}
            
            # Merge videos
            output_path = os.path.join(self.output_folder, f"output_{i+1}_{uuid.uuid4()}.mp4")
            try:
                merge_videos_with_trims(files, trims, batch_folder, self.output_folder)
                
                # Rename output file
                final_output_path = os.path.join(self.output_folder, f"output_{i+1}_{uuid.uuid4()}.mp4")
                os.rename(output_path, final_output_path)
                outputs.append(os.path.basename(final_output_path))
            finally:
                # Clean up temp folder
                import shutil
                shutil.rmtree(batch_folder, ignore_errors=True)
        
        return outputs
```

### 2.3 app.py
```python
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import uuid
import threading
import time
from video_processor import VideoProcessor
from config import *

app = Flask(__name__)
CORS(app)

app.config['SECRET_KEY'] = SECRET_KEY
app.config['DEBUG'] = DEBUG

# Initialize video processor
video_processor = VideoProcessor(TEMP_FOLDER, OUTPUT_FOLDER)

# Store batch status
batch_status = {}

@app.route('/')
def index():
    return send_file('templates/index.html')

@app.route('/api/scan-folder', methods=['POST'])
def scan_folder():
    try:
        data = request.get_json()
        if not data or 'folder_path' not in data:
            return jsonify({'error': 'Missing folder_path'}), 400
        
        folder_path = data['folder_path']
        if not os.path.exists(folder_path):
            return jsonify({'error': 'Folder does not exist'}), 400
        
        videos = video_processor.scan_folder(folder_path)
        return jsonify({'videos': videos})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/process-batch', methods=['POST'])
def process_batch():
    try:
        data = request.get_json()
        if not data or 'folder_path' not in data:
            return jsonify({'error': 'Missing required parameters'}), 400
        
        folder_path = data['folder_path']
        video_count = int(data.get('video_count', DEFAULT_VIDEO_COUNT))
        video_duration = float(data.get('video_duration', DEFAULT_VIDEO_DURATION))
        output_count = int(data.get('output_count', DEFAULT_OUTPUT_COUNT))
        
        # Validate parameters
        if video_count < 1 or video_count > MAX_VIDEO_COUNT:
            return jsonify({'error': f'video_count must be between 1 and {MAX_VIDEO_COUNT}'}), 400
        
        if video_duration <= 0:
            return jsonify({'error': 'video_duration must be positive'}), 400
        
        if output_count < 1 or output_count > MAX_OUTPUT_COUNT:
            return jsonify({'error': f'output_count must be between 1 and {MAX_OUTPUT_COUNT}'}), 400
        
        # Create batch ID
        batch_id = str(uuid.uuid4())
        
        # Initialize batch status
        batch_status[batch_id] = {
            'status': 'processing',
            'progress': 0,
            'outputs': [],
            'error': None
        }
        
        # Start processing in background
        def process():
            try:
                outputs = video_processor.process_batch(
                    folder_path, video_count, video_duration, output_count
                )
                
                batch_status[batch_id].update({
                    'status': 'completed',
                    'progress': 100,
                    'outputs': outputs
                })
            except Exception as e:
                batch_status[batch_id].update({
                    'status': 'error',
                    'error': str(e)
                })
        
        thread = threading.Thread(target=process)
        thread.daemon = True
        thread.start()
        
        return jsonify({'batch_id': batch_id, 'message': 'Processing started'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/status/<batch_id>')
def get_status(batch_id):
    if batch_id not in batch_status:
        return jsonify({'error': 'Batch not found'}), 404
    
    return jsonify(batch_status[batch_id])

@app.route('/api/download/<batch_id>/<filename>')
def download_file(batch_id, filename):
    if batch_id not in batch_status:
        return jsonify({'error': 'Batch not found'}), 404
    
    if batch_status[batch_id]['status'] != 'completed':
        return jsonify({'error': 'Batch not completed'}), 400
    
    file_path = os.path.join(OUTPUT_FOLDER, filename)
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    
    return send_file(file_path, as_attachment=True, download_name=filename)

if __name__ == '__main__':
    app.run(debug=DEBUG, host='0.0.0.0', port=5001)
```

## 3. Frontend Implementation

### 3.1 templates/index.html
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Batch Video Creator</title>
    <link href="https://cdn.tailwindcss.com" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>Batch Video Creator</h1>
            <p>Create multiple video variations from your video library</p>
        </header>
        
        <main>
            <!-- Folder Selection -->
            <section class="card">
                <h2><i class="fas fa-folder-open"></i> Select Video Folder</h2>
                <div class="form-group">
                    <label for="input-folder-path">Input Folder Path</label>
                    <input type="text" id="input-folder-path" placeholder="/path/to/videos">
                    <button id="browse-input-btn"><i class="fas fa-folder"></i> Browse</button>
                </div>
                <div class="form-group">
                    <label for="output-folder-path">Output Folder Path</label>
                    <input type="text" id="output-folder-path" placeholder="/path/to/save/outputs">
                    <button id="browse-output-btn"><i class="fas fa-folder"></i> Browse</button>
                </div>
                <button id="scan-btn"><i class="fas fa-search"></i> Scan Folder</button>
            </section>
            
            <!-- Video List -->
            <section id="video-list-section" class="card hidden">
                <h2><i class="fas fa-video"></i> Found Videos</h2>
                <div id="video-count" class="info"></div>
                <div id="video-list" class="video-grid"></div>
            </section>
            
            <!-- Configuration -->
            <section id="config-section" class="card hidden">
                <h2><i class="fas fa-cog"></i> Configuration</h2>
                <div class="config-grid">
                    <div class="form-group">
                        <label for="video-duration">Video Duration (seconds)</label>
                        <input type="number" id="video-duration" min="0.1" step="0.1" value="10">
                        <small>Each video will be cut to this duration (start from 0s)</small>
                    </div>
                    <div class="form-group">
                        <label for="output-count">Number of Outputs</label>
                        <input type="number" id="output-count" min="1" max="10" value="1">
                        <small>How many merged videos to create</small>
                    </div>
                </div>
                <button id="process-btn"><i class="fas fa-play"></i> Start Processing</button>
            </section>
            
            <!-- Progress -->
            <section id="progress-section" class="card hidden">
                <h2><i class="fas fa-tasks"></i> Processing Status</h2>
                <div class="progress-container">
                    <div class="progress-bar">
                        <div class="progress-fill"></div>
                    </div>
                    <div class="progress-text">0%</div>
                </div>
                <div id="status-message"></div>
            </section>
            
            <!-- Results -->
            <section id="results-section" class="card hidden">
                <h2><i class="fas fa-download"></i> Download Results</h2>
                <div id="download-links" class="download-grid"></div>
            </section>
        </main>
    </div>
    
    <script src="/static/js/main.js"></script>
</body>
</html>
```

### 3.2 static/css/style.css
```css
/* Custom styles for Batch Video Creator */
:root {
    --primary: #6366f1;
    --primary-dark: #4f46e5;
    --secondary: #8b5cf6;
    --gradient: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
    --dark-bg: #0f172a;
    --card-bg: #1e293b;
    --text-primary: #f1f5f9;
    --text-secondary: #94a3b8;
}

body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--dark-bg);
    color: var(--text-primary);
    min-height: 100vh;
    margin: 0;
    padding: 20px;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
}

header {
    text-align: center;
    margin-bottom: 40px;
}

header h1 {
    font-size: 2.5rem;
    background: var(--gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 10px;
}

header p {
    color: var(--text-secondary);
    font-size: 1.1rem;
}

.card {
    background: var(--card-bg);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 24px;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
}

.card h2 {
    margin-top: 0;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 10px;
}

.form-group {
    margin-bottom: 20px;
}

.form-group label {
    display: block;
    margin-bottom: 8px;
    font-weight: 500;
}

.form-group input {
    width: 100%;
    padding: 10px;
    border-radius: 8px;
    border: 1px solid #334155;
    background: #1e293b;
    color: var(--text-primary);
    font-size: 16px;
}

.form-group small {
    display: block;
    margin-top: 5px;
    color: var(--text-secondary);
    font-size: 14px;
}

button {
    padding: 12px 24px;
    border-radius: 8px;
    border: none;
    background: var(--gradient);
    color: white;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.3s ease;
}

button:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 20px -5px rgba(99, 102, 241, 0.5);
}

button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
}

.hidden {
    display: none;
}

.info {
    background: rgba(99, 102, 241, 0.1);
    border-left: 4px solid var(--primary);
    padding: 12px;
    border-radius: 8px;
    margin-bottom: 20px;
}

.video-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 16px;
    margin-top: 20px;
}

.video-item {
    background: #334155;
    border-radius: 8px;
    padding: 16px;
    display: flex;
    align-items: center;
    gap: 12px;
}

.video-item i {
    color: var(--primary);
    font-size: 24px;
}

.video-info h4 {
    margin: 0;
    font-size: 16px;
}

.video-info p {
    margin: 4px 0 0 0;
    font-size: 14px;
    color: var(--text-secondary);
}

.config-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
    margin-bottom: 24px;
}

.progress-container {
    margin-bottom: 20px;
}

.progress-bar {
    width: 100%;
    height: 24px;
    background: #334155;
    border-radius: 12px;
    overflow: hidden;
    margin-bottom: 10px;
}

.progress-fill {
    height: 100%;
    background: var(--gradient);
    width: 0%;
    transition: width 0.3s ease;
}

.progress-text {
    text-align: center;
    font-weight: 500;
}

.download-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 16px;
}

.download-item {
    background: #334155;
    border-radius: 8px;
    padding: 16px;
    text-align: center;
}

.download-item a {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 10px 20px;
    background: var(--gradient);
    color: white;
    text-decoration: none;
    border-radius: 6px;
    font-weight: 500;
    transition: all 0.3s ease;
}

.download-item a:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px -3px rgba(99, 102, 241, 0.5);
}

@media (max-width: 768px) {
    .config-grid {
        grid-template-columns: 1fr;
    }
    
    .video-grid {
        grid-template-columns: 1fr;
    }
    
    .download-grid {
        grid-template-columns: 1fr;
    }
}
```

### 3.3 static/js/main.js
```javascript
const API_BASE = 'http://localhost:5001';
let currentBatchId = null;
let statusInterval = null;

// DOM Elements
const inputFolderPathInput = document.getElementById('input-folder-path');
const outputFolderPathInput = document.getElementById('output-folder-path');
const browseInputBtn = document.getElementById('browse-input-btn');
const browseOutputBtn = document.getElementById('browse-output-btn');
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
browseInputBtn.addEventListener('click', browseInputFolder);
browseOutputBtn.addEventListener('click', browseOutputFolder);
scanBtn.addEventListener('click', scanFolder);
processBtn.addEventListener('click', startProcessing);

// Functions
async function browseInputFolder() {
    // Note: Browser security restrictions prevent actual folder browsing
    // This is a placeholder for the functionality
    inputFolderPathInput.value = '/path/to/your/videos';
}

async function browseOutputFolder() {
    // Note: Browser security restrictions prevent actual folder browsing
    // This is a placeholder for the functionality
    outputFolderPathInput.value = '/path/to/save/outputs';
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
                updateProgress(data.progress || 0, data.status);
                
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
```

## 4. Testing Plan

### 4.1 Unit Tests
- Test video scanning functionality
- Test random selection
- Test batch processing

### 4.2 Integration Tests
- Test API endpoints
- Test frontend-backend communication
- Test video processing pipeline

### 4.3 User Acceptance Tests
- Test with real video files
- Test with various configurations
- Test error handling

## 5. Deployment

### 5.1 Setup Instructions
1. Create virtual environment
2. Install dependencies
3. Run the application
4. Access via browser

### 5.2 Configuration
- Environment variables
- File paths
- Security settings

## 6. Documentation

### 6.1 User Guide
- How to use the batch creator
- Configuration options
- Troubleshooting

### 6.2 Developer Guide
- Architecture overview
- API documentation
- Extension points

This implementation plan provides a comprehensive guide for building the batch video creator program with all the requested features.