# Random Audio Start Position Implementation Plan

## Overview
This document outlines the implementation plan for adding random audio start position functionality to the video-audio merging feature.

## Current Implementation Analysis
The current implementation in `merge_video_audio.py` always starts audio from the beginning (0s) and trims it to match the video duration:

```python
# Lines 97-100 in merge_video_audio.py
# Trim audio to match video duration
if audio_clip.duration > video_duration:
    audio_clip = audio_clip.subclip(0, video_duration)  # Always starts from 0s
```

## Required Changes

### 1. Backend Changes

#### a. Modify `merge_video_audio.py`
- Add `audio_trim_mode` parameter to `process_video_audio` function
- Implement random audio start position logic when `audio_trim_mode` is "random"
- Ensure proper error handling when audio is shorter than video

**Changes needed:**
```python
def process_video_audio(job_id, video_path, audio_path, output_folder, processing_status, audio_trim_mode='fixed'):
    # ... existing code ...
    
    # Trim audio to match video duration
    if audio_clip.duration > video_duration:
        if audio_trim_mode == 'random':
            # Calculate random start position
            max_start_time = audio_clip.duration - video_duration
            start_time = random.uniform(0, max_start_time)
            end_time = start_time + video_duration
            audio_clip = audio_clip.subclip(start_time, end_time)
            print(f"Random audio trim: {start_time:.2f}s to {end_time:.2f}s")
        else:
            # Default behavior (fixed mode)
            audio_clip = audio_clip.subclip(0, video_duration)
            print(f"Fixed audio trim: 0s to {video_duration}s")
    elif audio_clip.duration < video_duration:
        # Handle case where audio is shorter than video
        if audio_trim_mode == 'random':
            # For random mode with short audio, we could loop the audio
            # For now, we'll just use the entire audio and let moviepy handle it
            print(f"Audio is shorter than video. Using entire audio: {audio_clip.duration}s")
        else:
            # Fixed mode - use entire audio
            print(f"Audio is shorter than video. Using entire audio: {audio_clip.duration}s")
    # else: durations are equal, no trimming needed
    
    # ... rest of the function ...
```

#### b. Modify `video_processor.py`
- Update `process_video_audio_batch` function to accept and pass `audio_trim_mode` parameter
- Set default value to 'fixed' for backward compatibility

**Changes needed:**
```python
def process_video_audio_batch(self, video_folder_path, audio_folder_path, output_folder, progress_callback=None, audio_trim_mode='fixed'):
    # ... existing code ...
    
    try:
        # Process video with audio
        output_path = process_video_audio(
            job_id, video['path'], selected_audio['path'], output_folder, processing_status, audio_trim_mode
        )
        
        # ... rest of the function ...
```

#### c. Modify `app.py`
- Update `/api/process-video-audio-batch` endpoint to accept `audio_trim_mode` parameter
- Add validation for the parameter

**Changes needed:**
```python
@app.route('/api/process-video-audio-batch', methods=['POST'])
def process_video_audio_batch():
    try:
        data = request.get_json()
        if not data or 'video_folder_path' not in data or 'audio_folder_path' not in data:
            return jsonify({'error': 'Missing required parameters'}), 400
        
        # ... existing code ...
        
        # Add audio_trim_mode parameter with default value 'fixed'
        audio_trim_mode = data.get('audio_trim_mode', 'fixed')
        
        # Validate audio_trim_mode value
        if audio_trim_mode not in ['fixed', 'random']:
            return jsonify({'error': 'audio_trim_mode must be either "fixed" or "random"'}), 400
        
        # ... existing code ...
        
        # Start processing in background
        def process():
            try:
                # Create a callback function to update progress
                def progress_callback(progress, message=None):
                    batch_status[batch_id]['progress'] = progress
                    if message:
                        batch_status[batch_id]['message'] = message
                
                outputs = video_processor.process_video_audio_batch(
                    video_folder_path, audio_folder_path, output_folder, progress_callback, audio_trim_mode
                )
                
                # ... rest of the function ...
```

### 2. Frontend Changes

#### a. Modify `templates/index.html`
- Add a select dropdown for audio trim mode in the Video-Audio Merger tab
- Position it after the folder selection section

**Changes needed:**
```html
<!-- In the Video-Audio Merger tab -->
<section id="va-file-list-section" class="card hidden">
    <h2><i class="fas fa-file"></i> Found Files</h2>
    <!-- Add this new section before the file lists -->
    <div class="form-group">
        <label for="audio-trim-mode">Audio Trim Mode</label>
        <select id="audio-trim-mode" class="form-select">
            <option value="fixed">Fixed Mode (start from 0s)</option>
            <option value="random">Random Mode (random start position)</option>
        </select>
        <small>Select how audio should be trimmed when merged with videos</small>
    </div>
    <!-- Rest of the existing content -->
    <div class="file-counts">
        <div id="video-count-va" class="info"></div>
        <div id="audio-count-va" class="info"></div>
    </div>
    <!-- ... existing code ... -->
</section>
```

#### b. Modify `static/js/main.js`
- Add a new variable to reference the audio trim mode select element
- Update `startVAProcessing` function to include the audio trim mode in the API request

**Changes needed:**
```javascript
// Add to DOM Elements section (around line 49)
const audioTrimModeSelect = document.getElementById('audio-trim-mode');

// Update startVAProcessing function
async function startVAProcessing() {
    const videoFolderPath = videoFolderPathInput.value.trim();
    const audioFolderPath = audioFolderPathInput.value.trim();
    const outputFolderPath = outputFolderPathInputVA.value.trim();
    const audioTrimMode = audioTrimModeSelect.value;
    
    // ... existing validation code ...
    
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
            }),
        });
        
        // ... rest of the function ...
```

## Implementation Order
1. Modify `merge_video_audio.py` to support random audio start position
2. Update `video_processor.py` to pass the audio trim mode parameter
3. Update `app.py` to accept the new parameter in the API endpoint
4. Add UI controls to `templates/index.html`
5. Update `static/js/main.js` to handle the new UI control

## Testing Considerations
- Test with videos shorter than audio files
- Test with videos longer than audio files
- Test both fixed and random modes
- Ensure backward compatibility (default to fixed mode)