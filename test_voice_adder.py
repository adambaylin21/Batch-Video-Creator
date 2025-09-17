#!/usr/bin/env python3
"""
Test script to verify the Voice Adder functionality integration
"""

import sys
import os

def test_imports():
    """Test if all required modules can be imported without errors"""
    print("Testing imports...")
    
    try:
        # Test Flask and required imports
        from flask import Flask, request, jsonify, send_file, render_template
        from flask_cors import CORS
        print("✓ Flask imports successful")
    except ImportError as e:
        print(f"✗ Flask import failed: {e}")
        return False
    
    try:
        # Test video processing imports
        from moviepy.editor import VideoFileClip, AudioFileClip
        print("✓ MoviePy imports successful")
    except ImportError as e:
        print(f"✗ MoviePy import failed: {e}")
        return False
    
    try:
        # Test application modules
        from app import app
        from video_processor import VideoProcessor
        from merge_video_audio import merge_video_with_voice
        print("✓ Application module imports successful")
    except ImportError as e:
        print(f"✗ Application module import failed: {e}")
        return False
    
    return True

def test_app_creation():
    """Test if the Flask app can be created without errors"""
    print("\nTesting Flask app creation...")
    
    try:
        from app import app
        
        # Test if app is created
        if app is not None:
            print("✓ Flask app created successfully")
            
            # Test if routes are registered
            routes = [rule.rule for rule in app.url_map.iter_rules()]
            if '/api/process-voice-adder' in routes:
                print("✓ Voice adder route is registered")
            else:
                print("✗ Voice adder route is missing")
                return False
                
            return True
        else:
            print("✗ Flask app creation failed")
            return False
    except Exception as e:
        print(f"✗ Flask app creation failed: {e}")
        return False

def test_video_processor():
    """Test if VideoProcessor class can be instantiated and has the voice adder method"""
    print("\nTesting VideoProcessor...")
    
    try:
        from video_processor import VideoProcessor
        from config import TEMP_FOLDER, OUTPUT_FOLDER
        
        # Create temp and output folders if they don't exist
        os.makedirs(TEMP_FOLDER, exist_ok=True)
        os.makedirs(OUTPUT_FOLDER, exist_ok=True)
        
        # Test VideoProcessor instantiation
        processor = VideoProcessor(TEMP_FOLDER, OUTPUT_FOLDER)
        print("✓ VideoProcessor instantiated successfully")
        
        # Test if process_voice_adder method exists
        if hasattr(processor, 'process_voice_adder'):
            print("✓ process_voice_adder method exists")
        else:
            print("✗ process_voice_adder method is missing")
            return False
            
        return True
    except Exception as e:
        print(f"✗ VideoProcessor test failed: {e}")
        return False

def test_merge_function():
    """Test if merge_video_with_voice function exists and can be imported"""
    print("\nTesting merge_video_with_voice function...")
    
    try:
        from merge_video_audio import merge_video_with_voice
        
        # Test if function exists
        if callable(merge_video_with_voice):
            print("✓ merge_video_with_voice function is callable")
        else:
            print("✗ merge_video_with_voice is not callable")
            return False
            
        return True
    except Exception as e:
        print(f"✗ merge_video_with_voice test failed: {e}")
        return False

def test_html_structure():
    """Test if the HTML file contains the Voice Adder tab"""
    print("\nTesting HTML structure...")
    
    try:
        with open('templates/index.html', 'r') as f:
            html_content = f.read()
        
        # Check if Voice Adder tab button exists
        if 'data-tab="voice-adder"' in html_content:
            print("✓ Voice Adder tab button found")
        else:
            print("✗ Voice Adder tab button missing")
            return False
        
        # Check if Voice Adder tab pane exists
        if 'id="voice-adder"' in html_content:
            print("✓ Voice Adder tab pane found")
        else:
            print("✗ Voice Adder tab pane missing")
            return False
        
        # Check if volume slider exists
        if 'id="original-audio-volume"' in html_content:
            print("✓ Volume slider found")
        else:
            print("✗ Volume slider missing")
            return False
        
        return True
    except Exception as e:
        print(f"✗ HTML structure test failed: {e}")
        return False

def test_javascript_functionality():
    """Test if the JavaScript file contains Voice Adder functionality"""
    print("\nTesting JavaScript functionality...")
    
    try:
        with open('static/js/main.js', 'r') as f:
            js_content = f.read()
        
        # Check if Voice Adder DOM elements exist
        if 'voiceVideoFileInput' in js_content:
            print("✓ Voice Adder DOM elements found")
        else:
            print("✗ Voice Adder DOM elements missing")
            return False
        
        # Check if Voice Adder event listeners exist
        if 'handleVideoFileSelect' in js_content:
            print("✓ Voice Adder event listeners found")
        else:
            print("✗ Voice Adder event listeners missing")
            return False
        
        # Check if Voice Adder API call exists
        if 'startVoiceProcessing' in js_content:
            print("✓ Voice Adder API call found")
        else:
            print("✗ Voice Adder API call missing")
            return False
        
        return True
    except Exception as e:
        print(f"✗ JavaScript functionality test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=== Voice Adder Integration Test ===\n")
    
    tests = [
        test_imports,
        test_app_creation,
        test_video_processor,
        test_merge_function,
        test_html_structure,
        test_javascript_functionality
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n=== Test Results ===")
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed! Voice Adder functionality is properly integrated.")
        return 0
    else:
        print("✗ Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())