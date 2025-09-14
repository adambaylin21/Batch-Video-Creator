# Video-Audio Merger Tab Implementation Plan

## Overview
This document outlines the implementation plan for adding a new tab to the Batch Video Creator application that allows users to merge videos with randomly selected audio tracks.

## Current Application Structure
- Flask backend with API endpoints for video processing
- Single-page HTML interface with Tailwind CSS styling
- JavaScript for client-side interactions and API communication
- Existing functionality for batch video creation from multiple video segments

## New Feature Requirements
- Add a tabbed interface to switch between existing functionality and new video-audio merging
- Allow users to select three folders: videos, audio files, and output location
- Process each video by merging with a randomly selected audio file
- Auto-trim audio to match video length
- Provide progress tracking and download functionality

## Implementation Plan

### 1. UI Modifications (HTML, CSS, JavaScript)

#### HTML Structure Changes
- Add tab navigation bar at the top of the main content area
- Wrap existing content in a tab pane for "Batch Video Creator"
- Create new tab pane for "Video-Audio Merger" with:
  - Folder selection section with three inputs (video folder, audio folder, output folder)
  - File lists section to display discovered videos and audio files
  - Processing button and progress tracking
  - Results section for downloads

#### CSS Changes
- Add styles for tab navigation (active/inactive states)
- Style tab content containers
- Ensure responsive design for mobile devices

#### JavaScript Changes
- Implement tab switching functionality
- Add event handlers for new tab elements
- Create functions for:
  - Scanning audio folders
  - Processing video-audio merging
  - Displaying audio file list
  - Progress tracking for the new functionality

### 2. Backend Changes (Flask)

#### New API Endpoints
- `/api/scan-audio-folder` - Scan a folder for audio files (mp3, ogg, etc.)
- `/api/process-video-audio-batch` - Process video-audio merging

#### New Backend Logic
- Create a function to scan folders for audio files
- Implement video-audio merging logic based on `merge_video_audio.py`
- Add support for random audio selection
- Implement audio trimming to match video duration
- Integrate with existing progress tracking system

#### File Structure
- Create `audio_video_processor.py` for the new processing logic
- Modify `app.py` to add new API endpoints
- Update `config.py` if needed for new configuration options

### 3. Implementation Details

#### Tab Navigation Implementation
```html
<div class="tab-nav">
    <button class="tab-btn active" data-tab="batch-creator">Batch Video Creator</button>
    <button class="tab-btn" data-tab="video-audio-merger">Video-Audio Merger</button>
</div>

<div class="tab-content">
    <div id="batch-creator" class="tab-pane active">
        <!-- Existing content -->
    </div>
    <div id="video-audio-merger" class="tab-pane">
        <!-- New content -->
    </div>
</div>
```

#### Video-Audio Merger Tab Structure
```html
<section class="card">
    <h2><i class="fas fa-folder-open"></i> Select Folders</h2>
    <div class="form-group">
        <label for="video-folder-path">Video Folder Path</label>
        <input type="text" id="video-folder-path" placeholder="Example: /Users/username/Videos">
        <small>Enter the full path to the folder containing your MP4 videos</small>
    </div>
    <div class="form-group">
        <label for="audio-folder-path">Audio Folder Path</label>
        <input type="text" id="audio-folder-path" placeholder="Example: /Users/username/Music">
        <small>Enter the full path to the folder containing your MP3/OGG audio files</small>
    </div>
    <div class="form-group">
        <label for="output-folder-path-va">Output Folder Path</label>
        <input type="text" id="output-folder-path-va" placeholder="Example: /Users/username/Desktop/outputs">
        <small>Enter the full path where you want to save the merged videos</small>
    </div>
    <button id="scan-va-btn"><i class="fas fa-search"></i> Scan Folders</button>
</section>

<section id="va-file-list-section" class="card hidden">
    <h2><i class="fas fa-file"></i> Found Files</h2>
    <div class="file-counts">
        <div id="video-count-va" class="info"></div>
        <div id="audio-count-va" class="info"></div>
    </div>
    <div class="file-lists">
        <div class="file-list-container">
            <h3>Video Files</h3>
            <div id="video-list-va" class="file-grid"></div>
        </div>
        <div class="file-list-container">
            <h3>Audio Files</h3>
            <div id="audio-list-va" class="file-grid"></div>
        </div>
    </div>
    <button id="process-va-btn"><i class="fas fa-play"></i> Start Processing</button>
</section>

<!-- Progress and Results sections similar to existing ones -->
```

#### Backend Processing Logic
1. Scan video folder for MP4 files
2. Scan audio folder for MP3/OGG files
3. For each video file:
   - Randomly select an audio file
   - Load video and get duration
   - Load audio and trim to video duration
   - Merge video with trimmed audio
   - Save to output folder
4. Track progress and provide status updates
5. Generate download links for completed files

### 4. Testing Plan
- Test tab switching functionality
- Test folder selection and scanning
- Test video-audio merging with various file types
- Test progress tracking and error handling
- Test download functionality
- Test with large files and folders

### 5. Timeline
1. UI modifications: 2-3 days
2. Backend implementation: 2-3 days
3. Testing and bug fixes: 1-2 days
4. Documentation: 1 day

## Risks and Mitigations
- **File compatibility issues**: Test with various video and audio formats
- **Performance issues with large files**: Implement proper error handling and progress tracking
- **Memory usage**: Ensure proper cleanup of temporary files
- **Browser compatibility**: Test across different browsers

## Success Criteria
- Users can switch between tabs without issues
- Video-audio merging works correctly with various file types
- Audio is properly trimmed to match video duration
- Progress tracking works accurately
- Downloads work correctly
- Error handling provides clear feedback to users