# Backend Implementation Plan for Batch Voice Processing

## Overview
This document outlines the implementation plan for adding batch voice processing functionality to the existing Voice Adder feature.

## API Endpoint Implementation

### New Endpoint: `/api/process-voice-batch`

#### Location
Add this endpoint to `app.py` after the existing `/api/process-voice-adder` endpoint (around line 361).

#### Implementation Details

```python
@app.route('/api/process-voice-batch', methods=['POST'])
def process_voice_batch():
    try:
        data = request.get_json()
        if not data or 'video_folder_path' not in data or 'audio_folder_path' not in data:
            return jsonify({'error': 'Missing required parameters'}), 400
        
        video_folder_path = data['video_folder_path']
        audio_folder_path = data['audio_folder_path']
        output_folder_path = data.get('output_folder_path', OUTPUT_FOLDER)
        original_audio_volume = data.get('original_audio_volume', 30)
        
        # Validate folder paths
        if not os.path.exists(video_folder_path):
            return jsonify({'error': 'Video folder does not exist'}), 400
        
        if not os.path.exists(audio_folder_path):
            return jsonify({'error': 'Audio folder does not exist'}), 400
        
        # Validate output folder path
        if not os.path.exists(output_folder_path):
            os.makedirs(output_folder_path, exist_ok=True)
        
        # Validate volume parameter
        try:
            original_audio_volume = int(original_audio_volume)
            if original_audio_volume < 0 or original_audio_volume > 100:
                return jsonify({'error': 'Original audio volume must be between 0 and 100'}), 400
        except ValueError:
            return jsonify({'error': 'Invalid original audio volume value'}), 400
        
        # Create batch ID
        batch_id = str(uuid.uuid4())
        
        # Initialize batch status
        batch_status[batch_id] = {
            'status': 'processing',
            'progress': 0,
            'outputs': [],
            'error': None,
            'output_folder_path': output_folder_path
        }
        
        # Start processing in background
        def process():
            try:
                # Create a callback function to update progress
                def progress_callback(progress, message=None):
                    batch_status[batch_id]['progress'] = progress
                    if message:
                        batch_status[batch_id]['message'] = message
                
                outputs = video_processor.process_voice_batch(
                    video_folder_path, audio_folder_path, output_folder_path, 
                    progress_callback, original_audio_volume
                )
                
                batch_status[batch_id].update({
                    'status': 'completed',
                    'progress': 100,
                    'message': 'Processing completed',
                    'outputs': outputs
                })
            except Exception as e:
                batch_status[batch_id].update({
                    'status': 'error',
                    'progress': 0,
                    'error': str(e),
                    'message': f'Error: {str(e)}'
                })
        
        thread = threading.Thread(target=process)
        thread.daemon = True
        thread.start()
        
        return jsonify({'batch_id': batch_id, 'message': 'Batch processing started'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

## VideoProcessor Class Modifications

### New Method: `process_voice_batch`

#### Location
Add this method to the `VideoProcessor` class in `video_processor.py` after the existing `process_voice_adder` method (around line 297).

#### Implementation Details

```python
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
```

## Error Handling

### Mismatched File Quantities
The implementation already handles mismatched quantities by processing only the minimum number of pairs. This is communicated to the user through the progress callback.

### Validation
- Validate folder paths exist
- Validate volume parameter is between 0-100
- Validate that folders contain at least one video and one audio file

## Progress Tracking
The implementation uses the same progress tracking mechanism as other batch processes:
- Progress updates are sent through the progress_callback
- Overall progress is calculated based on the number of pairs to process
- Each pair contributes proportionally to the total progress

## File Naming
- Output files will use the existing naming convention from `merge_video_with_voice`
- Each output file will have a unique UUID to avoid conflicts

## Summary
This implementation adds batch voice processing capability by:
1. Adding a new API endpoint that accepts folder paths
2. Creating a new VideoProcessor method that handles batch processing
3. Implementing sequential pairing of videos and audio files
4. Providing proper error handling and progress tracking
5. Reusing existing single-file processing logic for each pair

The implementation follows the existing patterns in the codebase and integrates seamlessly with the current architecture.