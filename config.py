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