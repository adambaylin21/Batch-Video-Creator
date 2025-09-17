from PIL import Image
import logging
import os
import uuid
import hashlib
import shutil
import concurrent.futures
import time
from datetime import datetime, timedelta
from moviepy.editor import VideoFileClip, concatenate_videoclips, vfx
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from werkzeug.utils import secure_filename
from config import *

# Patch for Pillow compatibility with MoviePy
try:
    if not hasattr(Image, 'ANTIALIAS'):
        Image.ANTIALIAS = Image.Resampling.LANCZOS
    logging.info("Applied PIL ANTIALIAS patch to LANCZOS")
except ImportError:
    logging.warning("PIL not available, skipping ANTIALIAS patch")
except Exception as e:
    logging.warning(f"Failed to apply PIL patch: {e}")

ALLOWED_EXTENSIONS = {'mp4'}

# Create cache folder if it doesn't exist
os.makedirs(VIDEO_CACHE_FOLDER, exist_ok=True)

# GPU acceleration check
def is_gpu_acceleration_available():
    """Check if GPU acceleration is available."""
    if not ENABLE_GPU_ACCELERATION:
        return False
    
    try:
        import subprocess
        result = subprocess.run(['ffmpeg', '-encoders'], capture_output=True, text=True)
        return GPU_CODEC in result.stdout
    except Exception as e:
        logging.warning(f"Error checking GPU acceleration availability: {e}")
        return False

# Cache cleanup function
def cleanup_old_cache_files():
    """Remove cache files older than CLEANUP_CACHE_DAYS."""
    if not ENABLE_CACHING:
        return
        
    try:
        now = time.time()
        cutoff_time = now - (CLEANUP_CACHE_DAYS * 86400)  # 86400 seconds = 1 day
        
        for filename in os.listdir(VIDEO_CACHE_FOLDER):
            file_path = os.path.join(VIDEO_CACHE_FOLDER, filename)
            if os.path.isfile(file_path):
                file_mtime = os.path.getmtime(file_path)
                if file_mtime < cutoff_time:
                    os.remove(file_path)
                    logging.info(f"Removed old cache file: {filename}")
    except Exception as e:
        logging.warning(f"Error cleaning up cache files: {e}")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_video_hash(file_path, trim_info=None):
    """Generate a hash for a video file based on its path and trim info."""
    hash_input = file_path
    if trim_info:
        hash_input += f"_{trim_info.get('start', 0)}_{trim_info.get('end', 'full')}"
    
    return hashlib.md5(hash_input.encode()).hexdigest()

def get_cache_path(file_hash):
    """Get the cache file path for a given hash."""
    return os.path.join(VIDEO_CACHE_FOLDER, f"{file_hash}.mp4")

def is_video_cached(file_hash):
    """Check if a video is already cached."""
    if not ENABLE_CACHING:
        return False
    cache_path = get_cache_path(file_hash)
    return os.path.exists(cache_path)

def validate_video(file_path):
    """Validate video file and return metadata."""
    try:
        with VideoFileClip(file_path) as clip:
            if clip.fps == 0 or clip.size[0] == 0 or clip.duration == 0:
                return None
            
            return {
                'fps': clip.fps,
                'size': clip.size,
                'duration': clip.duration
            }
    except Exception as e:
        logging.warning(f"Failed to validate video {file_path}: {e}")
        return None

def normalize_video(input_path, output_path, trim_info=None):
    """Normalize video to standard format, fps, and resolution."""
    try:
        # Check if input file exists
        if not os.path.exists(input_path):
            logging.error(f"Input file does not exist: {input_path}")
            return False
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Check if input file is a valid video
        try:
            with VideoFileClip(input_path) as clip:
                if clip.duration <= 0:
                    logging.error(f"Video has invalid duration: {clip.duration}")
                    return False
                
                # Apply trim if specified
                if trim_info:
                    start = float(trim_info.get('start', 0))
                    end = float(trim_info.get('end')) if trim_info.get('end') else clip.duration
                    if start >= end:
                        logging.error(f'Invalid trim times: start ({start}) >= end ({end})')
                        return False
                    clip = clip.subclip(start, end)
                
                # Normalize FPS
                if clip.fps != TARGET_FPS:
                    clip = clip.set_fps(TARGET_FPS)
                
                # Normalize resolution
                if TARGET_WIDTH:
                    clip = clip.resize((TARGET_WIDTH, TARGET_HEIGHT))
                else:
                    clip = clip.resize(height=TARGET_HEIGHT)
                
                # Apply video quality settings
                bitrate = VIDEO_BITRATE
                crf = CRF_VALUE
                
                # Adjust quality based on settings
                if VIDEO_QUALITY == 'low':
                    crf = 28  # Higher CRF = lower quality, smaller file
                    bitrate = '1000k'
                elif VIDEO_QUALITY == 'high':
                    crf = 18  # Lower CRF = higher quality, larger file
                    bitrate = '4000k'
                
                # Determine codec based on GPU availability
                use_gpu = is_gpu_acceleration_available()
                codec = GPU_CODEC if use_gpu else FALLBACK_CPU_CODEC
                
                # Set encoding parameters based on GPU availability
                if use_gpu:
                    # GPU-specific parameters
                    encoding_params = {
                        'codec': codec,
                        'preset': GPU_ENCODING_PRESET,
                        'audio_codec': None,  # Disable audio processing
                        'bitrate': GPU_BITRATE,
                        'verbose': False,
                        'logger': None
                    }
                    logging.info(f"Using GPU acceleration with codec: {codec}")
                else:
                    # CPU-specific parameters
                    encoding_params = {
                        'codec': codec,
                        'preset': VIDEO_PRESET,
                        'audio_codec': None,  # Disable audio processing
                        'bitrate': bitrate,
                        'verbose': False,
                        'logger': None,
                        'threads': MAX_WORKERS
                    }
                    logging.info(f"Using CPU-based encoding with codec: {codec}")
                
                # Write normalized video with selected parameters
                clip.write_videofile(output_path, **encoding_params)
                
                return True
        except Exception as clip_error:
            logging.error(f"Error processing video clip from {input_path}: {clip_error}")
            return False
    except Exception as e:
        logging.error(f"Failed to normalize video {input_path}: {e}")
        return False

def process_video_task(file_path, trim_info, output_dir):
    """Process a single video task with caching and normalization."""
    try:
        # Check if input file exists
        if not os.path.exists(file_path):
            raise ValueError(f'Input file does not exist: {file_path}')
        
        # Ensure output directory exists
        os.makedirs(VIDEO_CACHE_FOLDER, exist_ok=True)
        
        file_hash = get_video_hash(file_path, trim_info)
        cache_path = get_cache_path(file_hash)
        
        # Check if video is already cached
        if is_video_cached(file_hash):
            logging.info(f"Using cached video for {file_path}")
            return cache_path
        
        # Validate video
        metadata = validate_video(file_path)
        if not metadata:
            raise ValueError(f'Invalid video: {file_path}')
        
        # Log video metadata for debugging
        logging.info(f"Processing video: {file_path}, metadata: {metadata}")
        
        # Normalize video with fallback to original file if normalization fails
        if normalize_video(file_path, cache_path, trim_info):
            # Verify the output file was created successfully
            if os.path.exists(cache_path) and os.path.getsize(cache_path) > 0:
                return cache_path
            else:
                logging.warning(f"Normalized video file is empty or not created: {cache_path}")
                # Fall back to using the original file
                return file_path
        else:
            logging.warning(f"Failed to normalize video {file_path}, using original file")
            # Fall back to using the original file
            return file_path
    except Exception as e:
        logging.error(f"Error in process_video_task for {file_path}: {e}")
        # Fall back to using the original file
        return file_path

def apply_video_transition(clip1, clip2, transition_duration=None):
    """Apply fade transition between two video clips."""
    # Use configured transition duration if not specified
    if transition_duration is None:
        transition_duration = TRANSITION_DURATION
    
    # Apply fade out to the end of clip1
    clip1 = clip1.crossfadeout(transition_duration)
    
    # Apply fade in to the beginning of clip2
    clip2 = clip2.crossfadein(transition_duration)
    
    return clip1, clip2

def validate_and_upload_videos(files, upload_folder):
    """
    Validate and upload multiple video files, return list of saved filenames.
    Raises ValueError on errors.
    """
    if len(files) > 10:
        raise ValueError('Too many files. Max 10.')
    
    uploaded_files = []
    for file in files:
        if file.filename == '':
            continue
        if not allowed_file(file.filename):
            raise ValueError(f'Invalid file type: {file.filename}. Only MP4 allowed.')
        
        # Check size
        file_content = file.read()
        if len(file_content) > 200 * 1024 * 1024:  # 200MB
            raise ValueError(f'File too large: {file.filename}')
        
        file.seek(0)  # Reset for saving
        
        unique_filename = secure_filename(f"{uuid.uuid4()}.mp4")
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)
        uploaded_files.append(unique_filename)
    
    if not uploaded_files:
        raise ValueError('No valid files uploaded.')
    
    return uploaded_files

def merge_videos_with_trims(files, trims, upload_folder, output_folder):
    """
    Merge videos with trims and resize, return output_path.
    Uses optimized processing with caching and parallel execution.
    Raises ValueError or Exception on errors.
    """
    processed_clips = []
    failed_files = []
    
    try:
        # Ensure output folder exists
        os.makedirs(output_folder, exist_ok=True)
        
        # Process videos in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = []
            
            for filename in files:
                if filename not in trims:
                    logging.warning(f'No trim data for {filename}, skipping')
                    failed_files.append(filename)
                    continue
                
                trim = trims[filename]
                file_path = os.path.join(upload_folder, filename)
                
                if not os.path.exists(file_path):
                    logging.warning(f'File not found: {filename}, skipping')
                    failed_files.append(filename)
                    continue
                
                # Submit video processing task
                future = executor.submit(process_video_task, file_path, trim, output_folder)
                futures.append((future, filename))
            
            # Collect processed video paths
            for future, filename in futures:
                try:
                    processed_path = future.result()
                    if processed_path and os.path.exists(processed_path):
                        processed_clips.append(processed_path)
                        logging.info(f"Successfully processed video: {filename}")
                    else:
                        logging.warning(f"Failed to process video {filename}, result path is invalid")
                        failed_files.append(filename)
                except Exception as e:
                    logging.error(f"Error processing video {filename}: {e}")
                    failed_files.append(filename)
        
        # Check if we have any valid clips
        if not processed_clips:
            raise ValueError('No valid clips to merge. All videos failed to process.')
        
        # Log warning if some files failed
        if failed_files:
            logging.warning(f"Failed to process {len(failed_files)} files: {failed_files}")
        
        # Load processed clips and apply transitions
        clips = []
        for i, clip_path in enumerate(processed_clips):
            try:
                clip = VideoFileClip(clip_path)
                
                # Apply transitions between clips (except for the first clip)
                if i > 0 and clips:
                    prev_clip = clips[-1]
                    prev_clip, clip = apply_video_transition(prev_clip, clip)
                    clips[-1] = prev_clip
                
                clips.append(clip)
            except Exception as e:
                logging.error(f"Error loading processed clip {clip_path}: {e}")
                # Close all previously opened clips
                for c in clips:
                    try:
                        c.close()
                    except:
                        pass
                # Skip this clip and continue with others
                logging.warning(f"Skipping problematic clip: {clip_path}")
        
        if not clips:
            raise ValueError('No valid clips to merge after loading')
        
        # Concatenate clips with transitions
        try:
            final_clip = concatenate_videoclips(clips, method="compose")
            output_filename = 'merged.mp4'
            output_path = os.path.join(output_folder, output_filename)
            
            # Apply video quality settings
            bitrate = VIDEO_BITRATE
            crf = CRF_VALUE
            
            # Adjust quality based on settings
            if VIDEO_QUALITY == 'low':
                crf = 28  # Higher CRF = lower quality, smaller file
                bitrate = '1000k'
            elif VIDEO_QUALITY == 'high':
                crf = 18  # Lower CRF = higher quality, larger file
                bitrate = '4000k'
            
            # Determine codec based on GPU availability
            use_gpu = is_gpu_acceleration_available()
            codec = GPU_CODEC if use_gpu else FALLBACK_CPU_CODEC
            
            # Set encoding parameters based on GPU availability
            if use_gpu:
                # GPU-specific parameters
                encoding_params = {
                    'codec': codec,
                    'preset': GPU_ENCODING_PRESET,
                    'audio_codec': None,  # Skip audio processing
                    'bitrate': GPU_BITRATE,
                    'verbose': False,
                    'logger': None
                }
                logging.info(f"Using GPU acceleration for final merge with codec: {codec}")
            else:
                # CPU-specific parameters
                encoding_params = {
                    'codec': codec,
                    'preset': VIDEO_PRESET,
                    'audio_codec': None,  # Skip audio processing
                    'bitrate': bitrate,
                    'verbose': False,
                    'logger': None,
                    'threads': MAX_WORKERS
                }
                logging.info(f"Using CPU-based encoding for final merge with codec: {codec}")
            
            # Write final video with selected parameters
            final_clip.write_videofile(output_path, **encoding_params)
            
            # Close clips to free memory
            for clip in clips:
                try:
                    clip.close()
                except:
                    pass
            final_clip.close()
            
            return output_path
        except Exception as e:
            # Close all clips on error
            for clip in clips:
                try:
                    clip.close()
                except:
                    pass
            if 'final_clip' in locals():
                try:
                    final_clip.close()
                except:
                    pass
            raise ValueError(f'Failed to merge clips: {e}')
            
    except Exception as e:
        # Clean up processed clips on error
        for clip_path in processed_clips:
            try:
                if os.path.exists(clip_path) and clip_path != file_path:
                    os.remove(clip_path)
            except Exception as cleanup_error:
                logging.warning(f"Error cleaning up processed clip {clip_path}: {cleanup_error}")
        raise
    finally:
        # Clean up input files
        for filename in files:
            input_path = os.path.join(upload_folder, filename)
            if os.path.exists(input_path):
                try:
                    os.remove(input_path)
                except Exception as cleanup_error:
                    logging.warning(f"Error cleaning up input file {input_path}: {cleanup_error}")