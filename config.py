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