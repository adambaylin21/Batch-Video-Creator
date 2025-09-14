# Batch Video Creator Program Plan

## Overview
This program will create a standalone batch video creator that can:
- Take a folder path containing multiple videos
- Randomly select videos based on specified quantity
- Merge selected videos into complete videos
- Generate multiple variations as specified
- Save output videos to a custom path

## Architecture

### Backend Components
1. **batch_creator.py** - Main Flask application
   - Routes for API endpoints
   - Video processing logic
   - Integration with merge_videos.py

2. **video_processor.py** - Video processing utilities
   - Video selection logic with random selection
   - Integration with existing merge functionality

3. **config.py** - Configuration settings
   - Default settings for video processing
   - Environment variables

### Frontend Components
1. **index.html** - User interface
   - Folder selection input
   - Configuration options (video count, min duration, output count)
   - Progress tracking
   - Download functionality

### Folder Structure
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
└── README.md            # Documentation
```

## Key Features

### 1. Video Selection
- Scan specified folder for MP4 videos
- Randomly select specified number of videos
- Handle edge cases (insufficient videos, etc.)

### 2. Configuration Options
- **Video Count**: Number of videos to select for each merge (default: 5)
- **Minimum Duration**: Minimum duration in seconds for videos to be considered (default: 10)
- **Output Count**: Number of merged videos to create (default: 1)

### 3. Processing Workflow
1. User selects input folder path and output folder path
2. User configures parameters (video count, video duration, output count)
3. System scans and validates videos from input folder
4. For each output requested:
   - Randomly select videos
   - Trim each selected video to the specified duration (using start=0, end=target_duration)
   - Merge trimmed videos using existing merge_videos.py functionality
   - Save to specified output folder
5. Provide download links for all outputs

### 4. Progress Tracking
- Real-time progress updates
- Processing status for each batch
- Error handling and reporting

## Integration with Existing Code

### Using merge_videos.py
The batch creator will use the existing `merge_videos_with_trims` function from `merge_videos.py`:
- Import the function directly
- Pass file paths instead of uploaded files
- Handle temporary file cleanup
- Use same video processing parameters (720p resize, etc.)

### Dependencies
Reuse existing dependencies from requirements.txt:
- Flask
- Flask-CORS
- moviepy
- Pillow
- Werkzeug

## API Endpoints

### 1. POST /api/scan-folder
Scans the specified folder and returns video information
- Request: `{ "folder_path": "/path/to/videos" }`
- Response: `{ "videos": [{ "name": "video1.mp4", "duration": 30.5, "path": "/path/to/video1.mp4" }, ...] }`

### 2. POST /api/process-batch
Starts the batch processing
- Request: `{ "folder_path": "/path/to/videos", "video_count": 5, "min_duration": 10, "output_count": 3 }`
- Response: `{ "batch_id": "uuid", "message": "Processing started" }`

### 3. GET /api/status/<batch_id>
Returns processing status
- Response: `{ "status": "processing|completed|error", "progress": 50, "outputs": ["output1.mp4", ...] }`

### 4. GET /api/download/<batch_id>/<filename>
Downloads the processed video

## Implementation Steps

1. Create folder structure
2. Implement video processing logic
3. Create Flask application with API endpoints
4. Design and implement user interface
5. Add progress tracking
6. Test with sample videos
7. Create documentation

## Error Handling

- Invalid folder paths
- Insufficient videos matching criteria
- Video processing errors
- File system errors
- Memory management for large videos

## Performance Considerations

- Efficient video scanning
- Memory management for large batches
- Concurrent processing where possible
- Cleanup of temporary files