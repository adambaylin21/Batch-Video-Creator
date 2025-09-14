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
    
    def select_videos(self, videos, count):
        """Randomly select videos"""
        if len(videos) <= count:
            return videos
        return random.sample(videos, count)
    
    def process_batch(self, folder_path, video_count, video_duration, output_count, progress_callback=None, output_folder=None):
        """Process batch of videos"""
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
                # Set trim parameters: start from 0, end at video_duration or video duration (whichever is smaller)
                end_time = min(video_duration, video['duration'])
                trims[temp_filename] = {'start': 0, 'end': end_time}
            
            # Merge videos
            final_output_path = os.path.join(output_folder, f"output_{i+1}_{uuid.uuid4()}.mp4")
            try:
                if progress_callback:
                    progress_callback(overall_progress, "Merging videos...")
                
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