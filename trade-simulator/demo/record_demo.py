#!/usr/bin/env python
"""
Demo Recording Script

This script captures a screen recording of the trading simulator in action.
It requires the 'pyscreenrec' package for screen recording.

Usage:
    python record_demo.py
"""

import os
import sys
import time
import subprocess
import threading

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import PySimpleGUI
        print("PySimpleGUI is installed.")
    except ImportError:
        print("PySimpleGUI is not installed. Please install it with: pip install PySimpleGUI>=5.0.10")
        return False
    
    # Check if ffmpeg is installed
    try:
        subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("ffmpeg is installed.")
    except FileNotFoundError:
        print("ffmpeg is not installed. Please install it to record the demo.")
        return False
    
    return True

def start_simulator():
    """Start the trading simulator application."""
    simulator_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'app.py')
    
    # Start the simulator in a separate process
    process = subprocess.Popen([sys.executable, simulator_path])
    
    return process

def record_screen(output_path, duration=20):
    """
    Record the screen for a specified duration.
    
    Args:
        output_path (str): Path to save the recording
        duration (int): Recording duration in seconds
    """
    try:
        # Use ffmpeg to record the screen
        cmd = [
            'ffmpeg',
            '-f', 'x11grab',  # Use X11 screen capture
            '-s', '1024x768',  # Screen size
            '-i', ':0.0',      # Display to capture
            '-framerate', '10',  # Lower framerate for smaller file
            '-t', str(duration),  # Duration
            '-pix_fmt', 'rgb24',
            '-y',  # Overwrite output file
            output_path
        ]
        
        # Start recording
        print(f"Recording screen for {duration} seconds...")
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"Recording saved to {output_path}")
        
    except Exception as e:
        print(f"Error recording screen: {e}")

def main():
    """Main function to record the demo."""
    # Check dependencies
    if not check_dependencies():
        return
    
    # Define output path
    output_path = os.path.join(os.path.dirname(__file__), 'live_update.gif')
    
    # Start the simulator
    simulator = start_simulator()
    
    try:
        # Wait for the simulator to start
        print("Waiting for simulator to start...")
        time.sleep(5)
        
        # Record the screen
        record_screen(output_path, duration=20)
        
    finally:
        # Terminate the simulator
        simulator.terminate()
        print("Simulator terminated.")

if __name__ == "__main__":
    main()