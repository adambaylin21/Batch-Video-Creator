from PIL import Image
import logging
import os
import uuid
from moviepy.editor import VideoFileClip, concatenate_videoclips
from werkzeug.utils import secure_filename

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

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
    Raises ValueError or Exception on errors.
    """
    clips = []
    try:
        for filename in files:
            if filename not in trims:
                raise ValueError(f'No trim data for {filename}')
            trim = trims[filename]
            start = float(trim.get('start', 0))
            end_raw = trim.get('end')
            end = float(end_raw) if end_raw is not None else None
            
            file_path = os.path.join(upload_folder, filename)
            if not os.path.exists(file_path):
                raise ValueError(f'File not found: {filename}')
            
            clip = VideoFileClip(file_path)
            if end is None or end > clip.duration:
                end = clip.duration
            if start >= end:
                clip.close()
                raise ValueError(f'Invalid trim times for {filename}: start >= end')
            
            # Check if clip has video
            if clip.fps == 0 or clip.size[0] == 0:
                clip.close()
                raise ValueError(f'Invalid video: {filename}')
            
            trimmed_clip = clip.subclip(start, end).resize(height=720)  # Resize to 720p height, preserve aspect
            clips.append(trimmed_clip)
    except Exception as e:
        # Close any open clips
        for c in clips:
            c.close()
        raise
    
    if not clips:
        raise ValueError('No valid clips to merge')
    
    try:
        final_clip = concatenate_videoclips(clips)
        output_filename = 'merged.mp4'
        output_path = os.path.join(output_folder, output_filename)
        final_clip.write_videofile(output_path, codec='libx264', audio_codec='aac', verbose=False, logger=None)
        
        # Close clips to free memory
        for clip in clips:
            clip.close()
        final_clip.close()
    except Exception as e:
        for clip in clips:
            clip.close()
        raise
    
    # Clean up input files
    for filename in files:
        input_path = os.path.join(upload_folder, filename)
        if os.path.exists(input_path):
            os.remove(input_path)
    
    return output_path