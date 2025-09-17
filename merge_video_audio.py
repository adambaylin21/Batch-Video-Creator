import os
import uuid
import threading
import time
import random
import subprocess
import logging
from werkzeug.utils import secure_filename
from moviepy.editor import VideoFileClip, AudioFileClip
from config import *

ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'webm'}
ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'ogg'}

def allowed_video_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS

def allowed_audio_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_AUDIO_EXTENSIONS

def is_gpu_acceleration_available():
    """Check if GPU acceleration is available."""
    if not ENABLE_GPU_ACCELERATION:
        return False
    
    try:
        import shutil
        
        # Check if ffmpeg is available
        ffmpeg_path = shutil.which('ffmpeg')
        if not ffmpeg_path:
            logging.info("FFmpeg not found in PATH")
            return False
        
        logging.info(f"FFmpeg found at: {ffmpeg_path}")
        
        # Run ffmpeg to check for GPU encoders
        result = subprocess.run([ffmpeg_path, '-encoders'], capture_output=True, text=True)
        if result.returncode != 0:
            logging.warning(f"FFmpeg command failed with return code: {result.returncode}")
            return False
        
        # Check if GPU codec is available
        gpu_available = GPU_CODEC in result.stdout
        logging.info(f"GPU codec {GPU_CODEC} available: {gpu_available}")
        
        # List available encoders for debugging
        available_encoders = [line.split()[1] for line in result.stdout.split('\n') if 'encoding:' in line and 'V' in line.split('\t')]
        logging.info(f"Available video encoders: {available_encoders[:10]}...")  # Show first 10
        
        return gpu_available
    except Exception as e:
        logging.warning(f"Error checking GPU acceleration availability: {e}")
        return False

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

def process_video_audio(job_id, video_path, audio_path, output_folder, processing_status, audio_trim_mode='fixed'):
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
        else:
            # Audio and video durations are equal, no trimming needed
            print(f"Audio and video durations are equal: {audio_clip.duration}s")
        
        # Set trimmed audio to video
        final_video = video_clip.set_audio(audio_clip)
        print(f"Final video duration: {final_video.duration} seconds")
        
        if job_id in processing_status:
            processing_status[job_id]['progress'] = 80
        
        # Generate output path
        output_filename = f"merged_{job_id}.mp4"
        output_path = os.path.join(output_folder, output_filename)
        
        # Determine codec based on GPU availability
        use_gpu = is_gpu_acceleration_available()
        codec = GPU_CODEC if use_gpu else FALLBACK_CPU_CODEC
        
        # Set encoding parameters based on GPU availability
        if use_gpu:
            # GPU-specific parameters
            encoding_params = {
                'codec': codec,
                'audio_codec': 'aac',
                'preset': GPU_ENCODING_PRESET,
                'bitrate': GPU_BITRATE,
                'verbose': False,
                'logger': None
            }
            logging.info(f"Using GPU acceleration with codec: {codec}")
        else:
            # CPU-specific parameters
            encoding_params = {
                'codec': codec,
                'audio_codec': 'aac',
                'bitrate': VIDEO_BITRATE,
                'verbose': False,
                'logger': None,
                'threads': MAX_WORKERS
            }
            logging.info(f"Using CPU-based encoding with codec: {codec}")
        
        # Export the final video with selected parameters
        final_video.write_videofile(output_path, **encoding_params)
        
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

def merge_video_with_voice(video_path, audio_path, output_folder, progress_callback=None, original_audio_volume=30):
    """
    Merge video with voice audio, adjusting original video audio volume and trimming video to match audio duration.
    Returns output_path.
    Raises Exception on errors.
    """
    try:
        if progress_callback:
            progress_callback(10, "Loading video and audio files...")
        
        # Load video and audio clips
        video_clip = VideoFileClip(video_path)
        voice_audio_clip = AudioFileClip(audio_path)
        
        if progress_callback:
            progress_callback(20, "Processing video and audio...")
        
        # Get durations
        video_duration = video_clip.duration
        voice_duration = voice_audio_clip.duration
        print(f"Video duration: {video_duration} seconds")
        print(f"Voice audio duration: {voice_duration} seconds")
        
        # Trim video to match voice audio duration
        if video_duration > voice_duration:
            # Video is longer than voice audio, trim video
            final_duration = voice_duration
            video_clip = video_clip.subclip(0, final_duration)
            print(f"Trimmed video to: {final_duration} seconds")
        elif video_duration < voice_duration:
            # Video is shorter than voice audio, trim voice audio
            voice_audio_clip = voice_audio_clip.subclip(0, video_duration)
            print(f"Trimmed voice audio to: {video_duration} seconds")
            final_duration = video_duration
        else:
            # Durations are equal, no trimming needed
            final_duration = video_duration
            print(f"Video and voice audio durations are equal: {final_duration} seconds")
        
        if progress_callback:
            progress_callback(40, "Adjusting audio volumes...")
        
        # Get original audio from video if it exists
        original_audio = video_clip.audio
        
        # Adjust original audio volume
        if original_audio:
            # Convert volume percentage to multiplier (e.g., 30% -> 0.3)
            volume_multiplier = original_audio_volume / 100.0
            original_audio = original_audio.volumex(volume_multiplier)
            print(f"Adjusted original audio volume to: {original_audio_volume}%")
        else:
            print("No original audio found in video")
        
        if progress_callback:
            progress_callback(60, "Merging audio tracks...")
        
        # Combine original audio (if exists) with voice audio
        if original_audio:
            # Mix original audio with voice audio
            original_audio = original_audio.set_duration(final_duration)
            voice_audio_clip = voice_audio_clip.set_duration(final_duration)
            
            # If both audios have the same duration, we can use CompositeAudioClip
            try:
                from moviepy.audio.AudioClip import CompositeAudioClip
                combined_audio = CompositeAudioClip([original_audio, voice_audio_clip])
            except Exception as e:
                # Fallback: use the voice audio as primary
                print(f"Error using CompositeAudioClip: {e}")
                combined_audio = voice_audio_clip
        else:
            # No original audio, just use voice audio
            combined_audio = voice_audio_clip
        
        if progress_callback:
            progress_callback(80, "Creating final video...")
        
        # Set combined audio to video
        final_video = video_clip.set_audio(combined_audio)
        
        # Generate output path
        output_filename = f"voice_added_{uuid.uuid4()}.mp4"
        output_path = os.path.join(output_folder, output_filename)
        
        # Determine codec based on GPU availability
        use_gpu = is_gpu_acceleration_available()
        codec = GPU_CODEC if use_gpu else FALLBACK_CPU_CODEC
        
        # Set encoding parameters based on GPU availability
        if use_gpu:
            # GPU-specific parameters
            encoding_params = {
                'codec': codec,
                'audio_codec': 'aac',
                'preset': GPU_ENCODING_PRESET,
                'bitrate': GPU_BITRATE,
                'verbose': False,
                'logger': None
            }
            logging.info(f"Using GPU acceleration for voice merge with codec: {codec}")
        else:
            # CPU-specific parameters
            encoding_params = {
                'codec': codec,
                'audio_codec': 'aac',
                'bitrate': VIDEO_BITRATE,
                'verbose': False,
                'logger': None,
                'threads': MAX_WORKERS
            }
            logging.info(f"Using CPU-based encoding for voice merge with codec: {codec}")
        
        # Export the final video with selected parameters
        final_video.write_videofile(output_path, **encoding_params)
        
        if progress_callback:
            progress_callback(90, "Finalizing...")
        
        # Close clips to free memory
        video_clip.close()
        voice_audio_clip.close()
        if original_audio:
            original_audio.close()
        if combined_audio:
            combined_audio.close()
        final_video.close()
        
        if progress_callback:
            progress_callback(100, "Processing completed!")
        
        return output_path
        
    except Exception as e:
        # Ensure clips are closed even on error
        try:
            if 'video_clip' in locals():
                video_clip.close()
            if 'voice_audio_clip' in locals():
                voice_audio_clip.close()
            if 'original_audio' in locals() and original_audio:
                original_audio.close()
            if 'combined_audio' in locals() and combined_audio:
                combined_audio.close()
            if 'final_video' in locals():
                final_video.close()
        except:
            pass
        
        raise e