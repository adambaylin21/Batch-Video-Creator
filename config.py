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
VIDEO_CACHE_FOLDER = os.path.join('temp', 'video_cache')
ALLOWED_EXTENSIONS = {'mp4'}
ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'ogg', 'wav'}

# Video Processing Optimization
VIDEO_CODEC = 'libx264'
VIDEO_PRESET = 'fast'  # Encoding preset for faster processing
TARGET_FPS = 30  # Target FPS for all videos
TARGET_HEIGHT = 720
TARGET_WIDTH = None  # None to maintain aspect ratio
MAX_WORKERS = min(8, (os.cpu_count() or 1) + 4)  # Optimal thread pool size
TRANSITION_DURATION = 0.3  # Duration of video transitions in seconds
ENABLE_CACHING = True  # Enable video caching for faster processing
CLEANUP_CACHE_DAYS = 7  # Clean up cache files older than this many days

# Video Quality Settings
VIDEO_BITRATE = '2000k'  # Target bitrate for output videos
VIDEO_QUALITY = 'medium'  # Options: 'low', 'medium', 'high'
CRF_VALUE = 23  # Constant Rate Factor (lower = better quality, higher = smaller file)

# GPU Acceleration Settings
ENABLE_GPU_ACCELERATION = True  # Enable/disable GPU acceleration
GPU_CODEC = 'h264_nvenc'  # GPU-based codec for NVIDIA
FALLBACK_CPU_CODEC = 'libx264'  # Fallback to CPU-based codec when GPU not available
GPU_ENCODING_PRESET = 'fast'  # Encoding preset for GPU
GPU_RATE_CONTROL = 'cbr'  # Rate control method for GPU
GPU_BITRATE = '2000k'  # Target bitrate for GPU encoding

# Performance Optimization Settings
MAX_WORKERS = min(16, (os.cpu_count() or 1) + 4)  # Increased thread pool size
FFMPEG_BUFFER_SIZE = '2M'  # Buffer size for FFmpeg processing

# Quality Profiles for performance/quality balance
QUALITY_PROFILES = {
    'fastest': {
        'preset': 'ultrafast',
        'crf': 28,
        'height': 360,
        'fps': 24
    },
    'balanced': {
        'preset': 'veryfast',
        'crf': 26,
        'height': 480,
        'fps': 24
    },
    'quality': {
        'preset': 'fast',
        'crf': 23,
        'height': 720,
        'fps': 30
    }
}