import os
import random
import uuid
import logging
import shutil
import sys
from moviepy.editor import VideoFileClip

# Debug: Print current Python path
logging.info(f"Current Python path: {sys.path}")
logging.info(f"Current working directory: {os.getcwd()}")
logging.info(f"File directory: {os.path.dirname(os.path.abspath(__file__))}")
logging.info(f"Parent directory exists: {os.path.exists(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))}")
logging.info(f"merge_videos.py exists in parent: {os.path.exists(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'merge_videos.py'))}")

# Add parent directory to path to import merge_videos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
logging.info(f"Python path after adding parent: {sys.path}")

from merge_videos import merge_videos_with_trims
from merge_video_audio import process_video_audio, start_processing_thread

class VideoProcessor:
    def __init__(self, temp_folder, output_folder):
        self.temp_folder = temp_folder
        self.output_folder = output_folder
        os.makedirs(temp_folder, exist_ok=True)
        os.makedirs(output_folder, exist_ok=True)
    
    def scan_folder(self, folder_path):
        """Scan folder for videos and return metadata"""
        videos = []
        if not os.path.exists(folder_path):
            raise ValueError(f"Folder does not exist: {folder_path}")
            
        for filename in os.listdir(folder_path):
            if filename.lower().endswith('.mp4'):
                file_path = os.path.join(folder_path, filename)
                try:
                    with VideoFileClip(file_path) as clip:
                        videos.append({
                            'name': filename,
                            'path': file_path,
                            'duration': clip.duration
                        })
                except Exception as e:
                    logging.warning(f"Failed to read {filename}: {e}")
        return videos
    
    def scan_audio_folder(self, folder_path):
        """Scan folder for audio files and return metadata"""
        audios = []
        if not os.path.exists(folder_path):
            raise ValueError(f"Folder does not exist: {folder_path}")
            
        for filename in os.listdir(folder_path):
            if filename.lower().endswith(('.mp3', '.ogg', '.wav')):
                file_path = os.path.join(folder_path, filename)
                try:
                    from moviepy.editor import AudioFileClip
                    with AudioFileClip(file_path) as clip:
                        audios.append({
                            'name': filename,
                            'path': file_path,
                            'duration': clip.duration
                        })
                except Exception as e:
                    logging.warning(f"Failed to read audio {filename}: {e}")
        return audios
    
    def select_videos(self, videos, count):
        """Randomly select videos"""
        if len(videos) <= count:
            return videos
        return random.sample(videos, count)
    
    def process_batch(self, folder_path, video_count, video_duration, output_count, progress_callback=None, output_folder=None, video_trim_mode='fixed'):
        """Process batch of videos with optimized processing"""
        if progress_callback:
            progress_callback(0, "Scanning for videos...")
        
        # Use provided output folder or default to self.output_folder
        output_folder = output_folder or self.output_folder
        
        # Ensure output folder exists
        os.makedirs(output_folder, exist_ok=True)
        
        # Scan all videos
        all_videos = self.scan_folder(folder_path)
        
        if not all_videos:
            raise ValueError("No videos found in the specified folder")
        
        outputs = []
        for i in range(output_count):
            # Calculate overall progress
            overall_progress = (i / output_count) * 100
            
            if progress_callback:
                progress_callback(overall_progress, f"Processing output {i+1} of {output_count}...")
            
            # Select random videos
            selected_videos = self.select_videos(all_videos, video_count)
            
            # Shuffle the selected videos for random order
            random.shuffle(selected_videos)
            
            # Create unique batch folder
            batch_folder = os.path.join(self.temp_folder, f"batch_{uuid.uuid4()}")
            os.makedirs(batch_folder, exist_ok=True)
            
            if progress_callback:
                progress_callback(overall_progress, "Preparing videos for merging...")
            
            # Prepare files for merging
            files = []
            trims = {}
            
            for video in selected_videos:
                # Copy file to temp folder with UUID name
                temp_filename = f"{uuid.uuid4()}.mp4"
                temp_path = os.path.join(batch_folder, temp_filename)
                
                # Create symlink or copy file
                if hasattr(os, 'symlink'):
                    try:
                        os.symlink(video['path'], temp_path)
                    except (OSError, NotImplementedError):
                        # Fallback to copy if symlink fails
                        shutil.copy2(video['path'], temp_path)
                else:
                    shutil.copy2(video['path'], temp_path)
                
                files.append(temp_filename)
                
                # Set trim parameters based on trim mode
                if video_trim_mode == 'fixed':
                    # Fixed mode: start from 0, end at video_duration or video duration (whichever is smaller)
                    end_time = min(video_duration, video['duration'])
                    trims[temp_filename] = {'start': 0, 'end': end_time}
                else:  # random mode
                    # Random mode: randomly select start position
                    if video['duration'] <= video_duration:
                        # Video is shorter than requested duration, use the whole video
                        trims[temp_filename] = {'start': 0, 'end': video['duration']}
                    else:
                        # Video is longer than requested duration, randomly select start position
                        max_start_time = video['duration'] - video_duration
                        start_time = random.uniform(0, max_start_time)
                        end_time = start_time + video_duration
                        trims[temp_filename] = {'start': start_time, 'end': end_time}
            
            # Merge videos with optimized processing
            final_output_path = os.path.join(output_folder, f"output_{i+1}_{uuid.uuid4()}.mp4")
            try:
                if progress_callback:
                    progress_callback(overall_progress, "Merging videos with optimized processing...")
                
                # The merge_videos_with_trims function creates a file named 'merged.mp4'
                merge_videos_with_trims(files, trims, batch_folder, output_folder)
                
                if progress_callback:
                    progress_callback(overall_progress, "Finalizing output...")
                
                # Find the actual output file (should be 'merged.mp4')
                actual_output_path = os.path.join(output_folder, 'merged.mp4')
                
                # Rename the output file to our desired name
                if os.path.exists(actual_output_path):
                    os.rename(actual_output_path, final_output_path)
                    outputs.append(os.path.basename(final_output_path))
                else:
                    # If the file doesn't exist, check for any .mp4 files in the output folder
                    mp4_files = [f for f in os.listdir(output_folder) if f.endswith('.mp4')]
                    if mp4_files:
                        # Use the most recently created .mp4 file
                        latest_file = os.path.join(output_folder, mp4_files[0])
                        os.rename(latest_file, final_output_path)
                        outputs.append(os.path.basename(final_output_path))
                    else:
                        raise FileNotFoundError("No output file was created by the merge operation")
            finally:
                # Clean up temp folder
                shutil.rmtree(batch_folder, ignore_errors=True)
        
        return outputs
    
    def process_video_audio_batch(self, video_folder_path, audio_folder_path, output_folder, progress_callback=None, audio_trim_mode='fixed', audio_selection_mode='unique'):
        """Process batch of video-audio merging"""
        if progress_callback:
            progress_callback(0, "Scanning for videos and audio files...")
        
        # Ensure output folder exists
        os.makedirs(output_folder, exist_ok=True)
        
        # Scan all videos and audio files
        all_videos = self.scan_folder(video_folder_path)
        all_audios = self.scan_audio_folder(audio_folder_path)
        
        if not all_videos:
            raise ValueError("No videos found in the specified folder")
        
        if not all_audios:
            raise ValueError("No audio files found in the specified folder")
        
        outputs = []
        total_videos = len(all_videos)
        
        # Handle audio selection based on the selected mode
        if audio_selection_mode == 'unique':
            # Create a copy of the audio list to avoid modifying the original
            available_audios = all_audios.copy()
        else:
            # For random mode, we'll use the full list for each selection
            available_audios = all_audios
        
        for i, video in enumerate(all_videos):
            # Calculate overall progress
            overall_progress = (i / total_videos) * 100
            
            if progress_callback:
                progress_callback(overall_progress, f"Processing video {i+1} of {total_videos}: {video['name']}...")
            
            # Select random audio
            if audio_selection_mode == 'unique':
                # If we've used all available audios, reset the list
                if not available_audios:
                    available_audios = all_audios.copy()
                
                # Select a random audio from the available list
                selected_audio = random.choice(available_audios)
                # Remove the selected audio from the available list to ensure it's not reused immediately
                available_audios.remove(selected_audio)
            else:
                # For random mode, just select from all audios
                selected_audio = random.choice(all_audios)
            
            if progress_callback:
                progress_callback(overall_progress, f"Selected audio: {selected_audio['name']}...")
            
            # Create unique job ID
            job_id = f"va_{uuid.uuid4()}"
            
            # Create processing status dictionary
            processing_status = {}
            processing_status[job_id] = {
                'status': 'processing',
                'progress': 0,
                'error': None
            }
            
            try:
                # Process video with audio
                output_path = process_video_audio(
                    job_id, video['path'], selected_audio['path'], output_folder, processing_status, audio_trim_mode
                )
                
                if progress_callback:
                    progress_callback(overall_progress, f"Completed: {video['name']} with {selected_audio['name']}")
                
                # Add output filename to results
                output_filename = os.path.basename(output_path)
                outputs.append(output_filename)
                
            except Exception as e:
                logging.error(f"Error processing {video['name']} with {selected_audio['name']}: {e}")
                if progress_callback:
                    progress_callback(overall_progress, f"Error processing {video['name']}: {str(e)}")
                continue
        
        return outputs
    
    def process_voice_adder(self, video_path, audio_path, output_folder, progress_callback=None, original_audio_volume=30):
        """Process video with voice audio addition"""
        if progress_callback:
            progress_callback(0, "Loading video and audio files...")
        
        # Ensure output folder exists
        os.makedirs(output_folder, exist_ok=True)
        
        # Import here to avoid issues if module not available
        from merge_video_audio import merge_video_with_voice
        
        try:
            # Process video with voice audio
            output_path = merge_video_with_voice(
                video_path, audio_path, output_folder, progress_callback, original_audio_volume
            )
            
            if progress_callback:
                progress_callback(100, "Processing completed successfully!")
            
            return output_path
            
        except Exception as e:
            logging.error(f"Error processing video with voice: {e}")
            raise
    
    def process_voice_batch(self, video_folder_path, audio_folder_path, output_folder, progress_callback=None, original_audio_volume=30):
        """Process batch of videos with voice audio addition"""
        if progress_callback:
            progress_callback(0, "Scanning for videos and audio files...")
        
        # Ensure output folder exists
        os.makedirs(output_folder, exist_ok=True)
        
        # Scan all videos and audio files
        all_videos = self.scan_folder(video_folder_path)
        all_audios = self.scan_audio_folder(audio_folder_path)
        
        if not all_videos:
            raise ValueError("No videos found in the specified folder")
        
        if not all_audios:
            raise ValueError("No audio files found in the specified folder")
        
        # Determine the number of pairs to process (minimum of videos and audios)
        num_pairs = min(len(all_videos), len(all_audios))
        
        if progress_callback:
            progress_callback(5, f"Found {len(all_videos)} videos and {len(all_audios)} audio files. Will process {num_pairs} pairs.")
        
        outputs = []
        
        # Import here to avoid issues if module not available
        from merge_video_audio import merge_video_with_voice
        
        for i in range(num_pairs):
            # Calculate overall progress
            overall_progress = 5 + (i / num_pairs) * 90  # 5% to 95%
            
            video = all_videos[i]
            audio = all_audios[i]
            
            if progress_callback:
                progress_callback(overall_progress, f"Processing video {i+1} of {num_pairs}: {video['name']} with {audio['name']}...")
            
            try:
                # Process video with voice audio
                output_path = merge_video_with_voice(
                    video['path'], audio['path'], output_folder,
                    lambda p, msg=None: progress_callback(overall_progress + (p/num_pairs), msg),
                    original_audio_volume
                )
                
                if progress_callback:
                    progress_callback(overall_progress + (100/num_pairs), f"Completed: {video['name']} with {audio['name']}")
                
                # Add output filename to results
                output_filename = os.path.basename(output_path)
                outputs.append(output_filename)
                
            except Exception as e:
                logging.error(f"Error processing {video['name']} with {audio['name']}: {e}")
                if progress_callback:
                    progress_callback(overall_progress, f"Error processing {video['name']}: {str(e)}")
                continue
        
        if progress_callback:
            progress_callback(100, f"Batch processing completed! Processed {len(outputs)} of {num_pairs} pairs.")
        
        return outputs