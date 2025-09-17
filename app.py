from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
import os
import uuid
import threading
import time
import sys
import logging
from werkzeug.utils import secure_filename
from video_processor import VideoProcessor
from config import *

# Import cache cleanup function
from merge_videos import cleanup_old_cache_files

# Add parent directory to path to import merge_videos and merge_video_audio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from merge_videos import merge_videos_with_trims
from merge_video_audio import process_video_audio, start_processing_thread

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

app.config['SECRET_KEY'] = SECRET_KEY
app.config['DEBUG'] = DEBUG

# Initialize video processor
video_processor = VideoProcessor(TEMP_FOLDER, OUTPUT_FOLDER)

# Store batch status
batch_status = {}

# Clean up old cache files on startup
if ENABLE_CACHING:
    logging.info("Cleaning up old cache files...")
    cleanup_old_cache_files()
    logging.info("Cache cleanup completed")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/scan-folder', methods=['POST'])
def scan_folder():
    try:
        data = request.get_json()
        if not data or 'folder_path' not in data:
            return jsonify({'error': 'Missing folder_path'}), 400
        
        folder_path = data['folder_path']
        if not os.path.exists(folder_path):
            return jsonify({'error': 'Folder does not exist'}), 400
        
        videos = video_processor.scan_folder(folder_path)
        return jsonify({'videos': videos})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/scan-audio-folder', methods=['POST'])
def scan_audio_folder():
    try:
        data = request.get_json()
        if not data or 'folder_path' not in data:
            return jsonify({'error': 'Missing folder_path'}), 400
        
        folder_path = data['folder_path']
        if not os.path.exists(folder_path):
            return jsonify({'error': 'Folder does not exist'}), 400
        
        audios = video_processor.scan_audio_folder(folder_path)
        return jsonify({'audios': audios})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/process-batch', methods=['POST'])
def process_batch():
    try:
        data = request.get_json()
        if not data or ('folder_path' not in data and 'input_folder_path' not in data):
            return jsonify({'error': 'Missing required parameters'}), 400
        
        folder_path = data.get('folder_path', data.get('input_folder_path'))
        output_folder_path = data.get('output_folder_path', OUTPUT_FOLDER)
        
        # Validate output folder path
        if not os.path.exists(output_folder_path):
            os.makedirs(output_folder_path, exist_ok=True)
        
        # Validate numeric parameters
        video_count = data.get('video_count')
        if video_count is None:
            video_count = DEFAULT_VIDEO_COUNT
        else:
            video_count = int(video_count)
            
        video_duration = data.get('video_duration')
        if video_duration is None:
            video_duration = DEFAULT_VIDEO_DURATION
        else:
            video_duration = float(video_duration)
            
        # Add video_trim_mode parameter with default value 'fixed'
        video_trim_mode = data.get('video_trim_mode', 'fixed')
        
        # Validate video_trim_mode value
        if video_trim_mode not in ['fixed', 'random']:
            return jsonify({'error': 'video_trim_mode must be either "fixed" or "random"'}), 400
            
        output_count = data.get('output_count')
        if output_count is None:
            output_count = DEFAULT_OUTPUT_COUNT
        else:
            output_count = int(output_count)
        
        # Validate parameters
        if video_count < 1 or video_count > MAX_VIDEO_COUNT:
            return jsonify({'error': f'video_count must be between 1 and {MAX_VIDEO_COUNT}'}), 400
        
        if video_duration <= 0:
            return jsonify({'error': 'video_duration must be positive'}), 400
        
        if output_count < 1 or output_count > MAX_OUTPUT_COUNT:
            return jsonify({'error': f'output_count must be between 1 and {MAX_OUTPUT_COUNT}'}), 400
        
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
                
                outputs = video_processor.process_batch(
                    folder_path, video_count, video_duration, output_count, progress_callback, output_folder_path, video_trim_mode
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
        
        return jsonify({'batch_id': batch_id, 'message': 'Processing started'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/process-video-audio-batch', methods=['POST'])
def process_video_audio_batch():
    try:
        data = request.get_json()
        if not data or 'video_folder_path' not in data or 'audio_folder_path' not in data:
            return jsonify({'error': 'Missing required parameters'}), 400
        
        video_folder_path = data['video_folder_path']
        audio_folder_path = data['audio_folder_path']
        output_folder_path = data.get('output_folder_path', OUTPUT_FOLDER)
        
        # Add audio_trim_mode parameter with default value 'fixed'
        audio_trim_mode = data.get('audio_trim_mode', 'fixed')
        
        # Validate audio_trim_mode value
        if audio_trim_mode not in ['fixed', 'random']:
            return jsonify({'error': 'audio_trim_mode must be either "fixed" or "random"'}), 400
        
        # Add audio_selection_mode parameter with default value 'unique'
        audio_selection_mode = data.get('audio_selection_mode', 'unique')
        
        # Validate audio_selection_mode value
        if audio_selection_mode not in ['unique', 'random']:
            return jsonify({'error': 'audio_selection_mode must be either "unique" or "random"'}), 400
        
        # Validate output folder path
        if not os.path.exists(output_folder_path):
            os.makedirs(output_folder_path, exist_ok=True)
        
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
                
                outputs = video_processor.process_video_audio_batch(
                    video_folder_path, audio_folder_path, output_folder_path, progress_callback, audio_trim_mode, audio_selection_mode
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
        
        return jsonify({'batch_id': batch_id, 'message': 'Processing started'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/process-voice-adder', methods=['POST'])
def process_voice_adder():
    try:
        # Check if files are present
        if 'video_file' not in request.files or 'audio_file' not in request.files:
            return jsonify({'error': 'Missing video or audio file'}), 400
        
        video_file = request.files['video_file']
        audio_file = request.files['audio_file']
        
        # Check if files are selected
        if video_file.filename == '' or audio_file.filename == '':
            return jsonify({'error': 'No files selected'}), 400
        
        # Validate file types
        if not (video_file.filename.lower().endswith('.mp4')):
            return jsonify({'error': 'Invalid video file format. Only MP4 is supported.'}), 400
        
        if not (audio_file.filename.lower().endswith(('.mp3', '.ogg', '.wav'))):
            return jsonify({'error': 'Invalid audio file format. Only MP3, OGG, and WAV are supported.'}), 400
        
        # Get other parameters
        output_folder_path = request.form.get('output_folder_path', OUTPUT_FOLDER)
        original_audio_volume = request.form.get('original_audio_volume', '30')
        
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
        
        # Save uploaded files
        video_filename = secure_filename(f"{batch_id}_video_{video_file.filename}")
        audio_filename = secure_filename(f"{batch_id}_audio_{audio_file.filename}")
        
        video_path = os.path.join(TEMP_FOLDER, video_filename)
        audio_path = os.path.join(TEMP_FOLDER, audio_filename)
        
        # Ensure temp folder exists
        os.makedirs(TEMP_FOLDER, exist_ok=True)
        
        video_file.save(video_path)
        audio_file.save(audio_path)
        
        # Start processing in background
        def process():
            try:
                # Create a callback function to update progress
                def progress_callback(progress, message=None):
                    batch_status[batch_id]['progress'] = progress
                    if message:
                        batch_status[batch_id]['message'] = message
                
                output_path = video_processor.process_voice_adder(
                    video_path, audio_path, output_folder_path, progress_callback, original_audio_volume
                )
                
                batch_status[batch_id].update({
                    'status': 'completed',
                    'progress': 100,
                    'message': 'Processing completed',
                    'outputs': [os.path.basename(output_path)]
                })
                
                # Clean up temp files
                try:
                    os.remove(video_path)
                    os.remove(audio_path)
                except Exception as e:
                    logging.warning(f"Error cleaning up temp files: {e}")
                    
            except Exception as e:
                batch_status[batch_id].update({
                    'status': 'error',
                    'progress': 0,
                    'error': str(e),
                    'message': f'Error: {str(e)}'
                })
                
                # Clean up temp files even on error
                try:
                    if os.path.exists(video_path):
                        os.remove(video_path)
                    if os.path.exists(audio_path):
                        os.remove(audio_path)
                except Exception as cleanup_error:
                    logging.warning(f"Error cleaning up temp files after error: {cleanup_error}")
        
        thread = threading.Thread(target=process)
        thread.daemon = True
        thread.start()
        
        return jsonify({'batch_id': batch_id, 'message': 'Processing started'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/status/<batch_id>')
def get_status(batch_id):
    if batch_id not in batch_status:
        return jsonify({'error': 'Batch not found'}), 404
    
    return jsonify(batch_status[batch_id])

@app.route('/api/download/<batch_id>/<filename>')
def download_file(batch_id, filename):
    if batch_id not in batch_status:
        return jsonify({'error': 'Batch not found'}), 404
    
    if batch_status[batch_id]['status'] != 'completed':
        return jsonify({'error': 'Batch not completed'}), 400
    
    # Get the output folder path from batch status if available, otherwise use default
    if 'output_folder_path' in batch_status[batch_id]:
        output_folder = batch_status[batch_id]['output_folder_path']
    else:
        output_folder = OUTPUT_FOLDER
    
    file_path = os.path.join(output_folder, filename)
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    
    return send_file(file_path, as_attachment=True, download_name=filename)

@app.route('/api/clear-cache', methods=['POST'])
def clear_cache():
    """Clear video cache to free up disk space."""
    try:
        from merge_videos import cleanup_old_cache_files
        import shutil
        
        # Force clean all cache files
        cache_folder = VIDEO_CACHE_FOLDER
        if os.path.exists(cache_folder):
            shutil.rmtree(cache_folder)
            os.makedirs(cache_folder, exist_ok=True)
            
        return jsonify({'success': True, 'message': 'Cache cleared successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/system-info', methods=['GET'])
def get_system_info():
    """Get system information for monitoring."""
    try:
        import psutil
        
        # Get CPU and memory usage
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get cache information
        cache_size = 0
        cache_folder = VIDEO_CACHE_FOLDER
        if os.path.exists(cache_folder):
            for dirpath, dirnames, filenames in os.walk(cache_folder):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    cache_size += os.path.getsize(fp)
        
        return jsonify({
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_total': memory.total,
            'memory_available': memory.available,
            'disk_percent': disk.percent,
            'disk_total': disk.total,
            'disk_free': disk.free,
            'cache_size': cache_size,
            'cache_enabled': ENABLE_CACHING,
            'max_workers': MAX_WORKERS,
            'video_quality': VIDEO_QUALITY
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/update-settings', methods=['POST'])
def update_settings():
    """Update video processing settings."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update settings
        global VIDEO_QUALITY, ENABLE_CACHING, MAX_WORKERS
        
        if 'video_quality' in data and data['video_quality'] in ['low', 'medium', 'high']:
            VIDEO_QUALITY = data['video_quality']
            
        if 'enable_caching' in data and isinstance(data['enable_caching'], bool):
            ENABLE_CACHING = data['enable_caching']
            
        if 'max_workers' in data and isinstance(data['max_workers'], int):
            MAX_WORKERS = max(1, min(16, data['max_workers']))
        
        return jsonify({
            'success': True,
            'message': 'Settings updated successfully',
            'settings': {
                'video_quality': VIDEO_QUALITY,
                'enable_caching': ENABLE_CACHING,
                'max_workers': MAX_WORKERS
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Get application logs for debugging."""
    try:
        import tempfile
        import os
        
        # Create a temporary file to store logs
        with tempfile.NamedTemporaryFile(delete=False, suffix='.log') as temp_file:
            temp_path = temp_file.name
        
        # Redirect logs to the temporary file
        import logging
        
        # Create a new logger for this request
        logger = logging.getLogger('debug_logger')
        logger.setLevel(logging.INFO)
        
        # Create a file handler
        file_handler = logging.FileHandler(temp_path)
        file_handler.setLevel(logging.INFO)
        
        # Create a formatter and set it for the handler
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        # Add the handler to the logger
        logger.addHandler(file_handler)
        
        # Log some debug information
        logger.info(f"Video Quality: {VIDEO_QUALITY}")
        logger.info(f"Cache Enabled: {ENABLE_CACHING}")
        logger.info(f"Max Workers: {MAX_WORKERS}")
        logger.info(f"Video Codec: {VIDEO_CODEC}")
        logger.info(f"Video Preset: {VIDEO_PRESET}")
        logger.info(f"Target FPS: {TARGET_FPS}")
        logger.info(f"Target Height: {TARGET_HEIGHT}")
        logger.info(f"Video Bitrate: {VIDEO_BITRATE}")
        logger.info(f"CRF Value: {CRF_VALUE}")
        
        # Remove the handler to prevent duplicate logs in future requests
        logger.removeHandler(file_handler)
        file_handler.close()
        
        # Read the logs from the temporary file
        with open(temp_path, 'r') as log_file:
            logs = log_file.read()
        
        # Clean up the temporary file
        os.unlink(temp_path)
        
        return jsonify({'logs': logs})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=DEBUG, host='0.0.0.0', port=5001)