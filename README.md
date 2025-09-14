# Batch Video Creator

A standalone program for creating multiple video variations by randomly selecting and merging videos from a specified folder.

## Features

- **Folder Scanning**: Automatically scan a folder for MP4 videos
- **Smart Selection**: Randomly select videos based on configurable criteria
- **Batch Processing**: Create multiple video variations in a single operation
- **Video Trimming**: Trim each video to a specified target duration
- **Progress Tracking**: Real-time progress updates during processing
- **Download Management**: Easy download of all generated videos

## Requirements

- Python 3.7+
- Flask
- MoviePy
- Pillow
- Modern web browser

## Architecture

The Batch Video Creator consists of:

1. **Backend (Flask Application)**
   - API endpoints for video processing
   - Integration with existing merge_videos.py functionality
   - Background processing for long-running tasks

2. **Frontend (Web Interface)**
   - Folder selection
   - Configuration options
   - Progress tracking
   - Download management

3. **Video Processing Engine**
   - Video scanning and metadata extraction
   - Random video selection
   - Video merging using existing functionality

## Installation

1. Navigate to the batch-creator directory:
   ```bash
   cd batch-creator
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Start the application:
   ```bash
   python app.py
   ```

2. Open your browser and navigate to `http://localhost:5001`

3. Use the interface to:
   - Select input and output folder paths
   - Configure processing options
   - Start the batch processing
   - Download the resulting videos

## Configuration Options

- **Input Folder Path**: Path to folder containing source videos
- **Output Folder Path**: Path to save the merged videos
- **Videos per Output**: Number of videos to merge in each output (1-20)
- **Video Duration**: Duration in seconds to cut each video (0.1+ seconds)
- **Number of Outputs**: How many merged videos to create (1-10)

## API Endpoints

### POST /api/scan-folder
Scans the specified folder and returns video information.

**Request:**
```json
{
  "folder_path": "/path/to/videos"
}
```

**Response:**
```json
{
  "videos": [
    {
      "name": "video1.mp4",
      "path": "/path/to/videos/video1.mp4",
      "duration": 30.5
    }
  ]
}
```

### POST /api/process-batch
Starts the batch processing.

**Request:**
```json
{
  "input_folder_path": "/path/to/videos",
  "output_folder_path": "/path/to/save/outputs",
  "video_count": 5,
  "video_duration": 10,
  "output_count": 3
}
```

**Response:**
```json
{
  "batch_id": "uuid",
  "message": "Processing started"
}
```

### GET /api/status/<batch_id>
Returns processing status.

**Response:**
```json
{
  "status": "processing|completed|error",
  "progress": 50,
  "outputs": ["output1.mp4", ...],
  "error": null
}
```

### GET /api/download/<batch_id>/<filename>
Downloads the processed video.

## File Structure

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
├── README.md            # This documentation
├── plan.md              # Detailed plan
├── architecture.md      # Architecture diagrams
└── implementation_plan.md # Implementation details
```

## Integration with Existing Code

The Batch Video Creator integrates with the existing `merge_videos.py` file by:

1. Importing the `merge_videos_with_trims` function
2. Preparing video files in temporary locations
3. Setting trim parameters (start=0, end=video_duration) for each video
4. Calling the merge function with appropriate parameters
5. Handling cleanup of temporary files

## Development

### Adding New Features

1. Backend Changes:
   - Modify `app.py` for new API endpoints
   - Update `video_processor.py` for new processing logic
   - Adjust `config.py` for new configuration options

2. Frontend Changes:
   - Update `templates/index.html` for new UI elements
   - Modify `static/js/main.js` for new functionality
   - Adjust `static/css/style.css` for styling

### Testing

1. Unit Tests:
   - Test individual components in isolation
   - Mock external dependencies

2. Integration Tests:
   - Test API endpoints
   - Test frontend-backend communication

3. User Acceptance Tests:
   - Test with real video files
   - Verify output quality

## Troubleshooting

### Common Issues

1. **Folder Not Found**
   - Ensure the folder path is correct
   - Check file permissions

2. **No Videos Found**
   - Verify the folder contains MP4 files
   - Check file extensions

3. **Video Duration Issues**
   - Ensure video duration is greater than 0
   - Note that videos shorter than the specified duration will be used in their entirety

4. **Processing Errors**
   - Ensure videos are not corrupted
   - Check available disk space

4. **Performance Issues**
   - Reduce batch size for large videos
   - Ensure sufficient RAM is available

## License

This project is part of the Video Merger Pro application.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Support

For issues and questions, please refer to the main project documentation.