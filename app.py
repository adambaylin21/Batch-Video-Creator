from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
import os
import uuid
import threading
import time
import sys
from video_processor import VideoProcessor
from config import *

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

if __name__ == '__main__':
    app.run(debug=DEBUG, host='0.0.0.0', port=5001)