import os
import uuid
import threading
import time
from werkzeug.utils import secure_filename
from moviepy.editor import VideoFileClip, AudioFileClip

ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'webm'}
ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'ogg'}

def allowed_video_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS

def allowed_audio_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_AUDIO_EXTENSIONS

def validate_and_upload_single(video_file, audio_file, upload_folder, job_id):
    """
    Validate and upload single video and audio files, return paths.
    Raises ValueError on errors.
    """
    if video_file.filename == '' or audio_file.filename == '':
        raise ValueError('No files selected')
    
    if not (allowed_video_file(video_file.filename) and allowed_audio_file(audio_file.filename)):
        raise ValueError('Unsupported file format')
    
    video_filename = secure_filename(video_file.filename)
    audio_filename = secure_filename(audio_file.filename)
    
    video_path = os.path.join(upload_folder, f"{job_id}_video_{video_filename}")
    audio_path = os.path.join(upload_folder, f"{job_id}_audio_{audio_filename}")
    
    video_file.save(video_path)
    audio_file.save(audio_path)
    
    return video_path, audio_path

def validate_and_upload_batch(videos, audios, upload_folder, batch_id):
    """
    Validate and upload batch of video and audio files, return list of (job_id, video_path, audio_path).
    Raises ValueError on errors.
    """
    if len(videos) != len(audios):
        raise ValueError('Number of video and audio files must match')
    
    if len(videos) == 0:
        raise ValueError('No files uploaded')
    
    batch_jobs = []
    for i, (video_file, audio_file) in enumerate(zip(videos, audios)):
        if video_file.filename == '' or audio_file.filename == '':
            continue
        
        if not (allowed_video_file(video_file.filename) and allowed_audio_file(audio_file.filename)):
            continue
        
        job_id = f"{batch_id}_{i}"
        video_filename = secure_filename(video_file.filename)
        audio_filename = secure_filename(audio_file.filename)
        
        video_path = os.path.join(upload_folder, f"{job_id}_video_{video_filename}")
        audio_path = os.path.join(upload_folder, f"{job_id}_audio_{audio_filename}")
        
        video_file.save(video_path)
        audio_file.save(audio_path)
        
        batch_jobs.append((job_id, video_path, audio_path))
    
    if not batch_jobs:
        raise ValueError('No valid file pairs found')
    
    return batch_jobs

def process_video_audio(job_id, video_path, audio_path, output_folder, processing_status):
    """
    Process single video+audio pair, update status, return output_path.
    Raises Exception on errors.
    """
    try:
        # Update progress
        if job_id in processing_status:
            processing_status[job_id]['progress'] = 10
        
        # Load video and audio clips
        video_clip = VideoFileClip(video_path)
        audio_clip = AudioFileClip(audio_path)
        
        if job_id in processing_status:
            processing_status[job_id]['progress'] = 30
        
        # Get video duration
        video_duration = video_clip.duration
        print(f"Video duration: {video_duration} seconds")
        print(f"Original audio duration: {audio_clip.duration} seconds")
        
        # Trim audio to match video duration
        if audio_clip.duration > video_duration:
            audio_clip = audio_clip.subclip(0, video_duration)
            print(f"Trimmed audio to: {audio_clip.duration} seconds")
        
        # Set trimmed audio to video
        final_video = video_clip.set_audio(audio_clip)
        print(f"Final video duration: {final_video.duration} seconds")
        
        if job_id in processing_status:
            processing_status[job_id]['progress'] = 80
        
        # Generate output path
        output_filename = f"merged_{job_id}.mp4"
        output_path = os.path.join(output_folder, output_filename)
        
        # Export the final video
        final_video.write_videofile(output_path, codec='libx264', audio_codec='aac', verbose=False, logger=None)
        
        if job_id in processing_status:
            processing_status[job_id]['progress'] = 100
            processing_status[job_id]['status'] = 'completed'
            processing_status[job_id]['output_path'] = output_path
        
        # Close clips to free memory
        video_clip.close()
        audio_clip.close()
        final_video.close()
        
        return output_path
        
    except Exception as e:
        if job_id in processing_status:
            processing_status[job_id]['status'] = 'error'
            processing_status[job_id]['error'] = str(e)
        raise

def cleanup_files(video_path, audio_path, job_id, output_folder, processing_status):
    """
    Clean up temporary files after processing.
    """
    try:
        # Wait a bit before cleanup to ensure download is possible
        time.sleep(300)  # 5 minutes
        
        # Remove input files
        if os.path.exists(video_path):
            os.remove(video_path)
        if os.path.exists(audio_path):
            os.remove(audio_path)
        
        # Remove output file after additional time
        output_filename = f"merged_{job_id}.mp4"
        output_path = os.path.join(output_folder, output_filename)
        if os.path.exists(output_path):
            time.sleep(3600)  # 1 hour after input cleanup
            os.remove(output_path)
        
        # Clean up processing status
        if job_id in processing_status:
            del processing_status[job_id]
        
    except Exception as e:
        print(f"Cleanup error: {e}")

def start_processing_thread(job_id, video_path, audio_path, output_folder, processing_status):
    """
    Start a background thread for processing.
    """
    thread = threading.Thread(target=process_video_audio, args=(job_id, video_path, audio_path, output_folder, processing_status))
    thread.daemon = True
    thread.start()
    
    # Start cleanup thread after processing
    def start_cleanup():
        thread.join()  # Wait for processing to finish
        cleanup_thread = threading.Thread(target=cleanup_files, args=(video_path, audio_path, job_id, output_folder, processing_status))
        cleanup_thread.daemon = True
        cleanup_thread.start()
    
    cleanup_starter = threading.Thread(target=start_cleanup)
    cleanup_starter.daemon = True
    cleanup_starter.start()