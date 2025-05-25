"""
Script Manager for EDUGuard

This module provides a centralized interface for managing all monitoring scripts
in the EDUGuard application, including posture, stress, CVS, and hydration monitoring.
"""

import os
import sys
import logging
import subprocess
import time
import threading
import traceback
from pathlib import Path
import socket

# Configure logger with more detailed output
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'script_manager.log'))
    ]
)
logger = logging.getLogger('ScriptManager')
logger.info("Script Manager initialized")

class ScriptManager:
    """
    Centralized manager for all monitoring scripts in the EDUGuard application.
    
    This class provides methods to start, stop, and check the status of all monitoring
    scripts, as well as manage the webcam server that they depend on.
    """
    
    def __init__(self):
        """Initialize the script manager"""
        self.processes = {}
        self.webcam_process = None
        self.process_lock = threading.Lock()
        
        # Get the backend directory path
        self.backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.scripts_dir = os.path.join(self.backend_dir, 'modelScrpits')
        
        logger.info(f"Backend directory: {self.backend_dir}")
        logger.info(f"Scripts directory: {self.scripts_dir}")
        
        # Ensure the scripts directory exists
        if not os.path.exists(self.scripts_dir):
            logger.warning(f"Scripts directory not found: {self.scripts_dir}")
        
        # Define script paths
        self.script_paths = {
            'webcam': os.path.join(self.scripts_dir, 'webcam_server.py'),
            'posture': os.path.join(self.scripts_dir, 'posture_detection.py'),
            'stress': os.path.join(self.scripts_dir, 'stress_detection.py'),
            'cvs': os.path.join(self.scripts_dir, 'cvs_detection.py'),
            'hydration': os.path.join(self.scripts_dir, 'hydration_detection.py')
        }
        
        # Validate script paths
        for name, path in self.script_paths.items():
            if not os.path.exists(path):
                logger.warning(f"{name.capitalize()} script not found: {path}")
            else:
                logger.info(f"Found {name} script: {path}")
    
    def start_webcam_server(self):
        """
        Start the webcam server if not already running
        
        Returns:
            tuple: (success, message)
        """
        with self.process_lock:
            try:
                # First check if webcam server is already running using socket connection
                if self._check_webcam_server_running():
                    logger.info("Webcam server is already running (detected via socket connection)")
                    
                    # If we don't have a process reference but server is running, create a dummy one
                    if not self.webcam_process or self.webcam_process.poll() is not None:
                        logger.info("Creating dummy process reference for existing webcam server")
                        # Use a safer approach that doesn't require creating an actual process
                        self.webcam_process = True  # Just use a boolean flag instead of a process
                    
                    return True, "Webcam server is already running"
                    
                # Check if our process reference thinks webcam server is running
                if self.webcam_process and self.webcam_process is not True and self.webcam_process.poll() is None:
                    logger.info("Webcam server is already running (according to process reference)")
                    return True, "Webcam server is already running"
                    
                # Start webcam server
                webcam_script = self.script_paths['webcam']
                logger.info(f"Starting webcam server: {webcam_script}")
                
                # Use a more robust approach with environment variables
                env = os.environ.copy()
                env['PYTHONUNBUFFERED'] = '1'  # Ensure Python output is unbuffered
                
                self.webcam_process = subprocess.Popen(
                    [sys.executable, webcam_script],
                    cwd=self.backend_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env,
                    universal_newlines=True  # Text mode for easier debugging
                )
                
                # Give it time to start
                logger.info("Waiting for webcam server to start...")
                time.sleep(3)
                
                # Check if it started successfully
                if self.webcam_process is not True and self.webcam_process.poll() is None:
                    logger.info("Webcam server started successfully")
                    return True, "Webcam server started successfully"
                else:
                    if self.webcam_process is not True:
                        stdout, stderr = self.webcam_process.communicate()
                        logger.error(f"Webcam server failed to start: {stderr}")
                        return False, f"Failed to start webcam server: {stderr}"
                    else:
                        return False, "Failed to start webcam server"
                    
            except Exception as e:
                logger.error(f"Error starting webcam server: {e}")
                logger.error(traceback.format_exc())
                return False, str(e)
    
    def stop_webcam_server(self):
        """
        Stop the webcam server if it's running
        
        Returns:
            tuple: (success, message)
        """
        with self.process_lock:
            try:
                if not self.webcam_process:
                    return True, "No webcam server is running"
                    
                if isinstance(self.webcam_process, bool):
                    # We're using a boolean flag, just reset it
                    self.webcam_process = None
                    logger.info("Reset webcam server reference (was using boolean flag)")
                    return True, "Webcam server reference reset"
                
                if self.webcam_process.poll() is not None:
                    self.webcam_process = None
                    return True, "Webcam server was not running"
                
                # Check if any monitoring process is using this webcam server
                active_processes = False
                for process_key, process in self.processes.items():
                    if process and process.poll() is None:
                        active_processes = True
                        logger.warning(f"Cannot stop webcam server: {process_key} monitoring is using it")
                        break
                
                if active_processes:
                    return False, "Cannot stop webcam server while monitoring processes are active"
                
                # Terminate the process
                logger.info("Terminating webcam server process")
                self.webcam_process.terminate()
                
                # Wait for it to stop
                try:
                    logger.info("Waiting for webcam server to terminate...")
                    self.webcam_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning("Webcam server didn't terminate gracefully, killing...")
                    self.webcam_process.kill()
                    self.webcam_process.wait()
                
                self.webcam_process = None
                logger.info("Webcam server stopped successfully")
                return True, "Webcam server stopped successfully"
                
            except Exception as e:
                logger.error(f"Error stopping webcam server: {e}")
                logger.error(traceback.format_exc())
                return False, str(e)
    
    def start_monitoring(self, monitoring_type, user_id, progress_report_id=None):
        """
        Start a monitoring process
        
        Args:
            monitoring_type (str): Type of monitoring ('posture', 'stress', 'cvs', 'hydration')
            user_id (str): User ID
            progress_report_id (str, optional): Progress report ID
            
        Returns:
            tuple: (success, message)
        """
        if monitoring_type not in self.script_paths:
            logger.error(f"Unknown monitoring type: {monitoring_type}")
            return False, f"Unknown monitoring type: {monitoring_type}"
        
        with self.process_lock:
            try:
                # Check if already monitoring this type for this user
                process_key = f"{monitoring_type}_{user_id}"
                if process_key in self.processes:
                    process = self.processes[process_key]
                    if process and process.poll() is None:
                        logger.warning(f"{monitoring_type.capitalize()} monitoring already active for user {user_id}")
                        return True, f"{monitoring_type.capitalize()} monitoring already active"
                    else:
                        # Process died, remove it
                        logger.info(f"Removing dead process for {monitoring_type} monitoring for user {user_id}")
                        del self.processes[process_key]
                
                # Check if webcam server is running by trying to connect to it
                webcam_running = self._check_webcam_server_running()
                logger.info(f"Webcam server socket check result: {webcam_running}")
                
                # Start webcam server if it's not already running
                if not webcam_running:
                    logger.info("Webcam server not running, starting it first")
                    webcam_success, webcam_message = self.start_webcam_server()
                    if not webcam_success:
                        logger.error(f"Failed to start webcam server: {webcam_message}")
                        return False, f"Failed to start webcam server: {webcam_message}"
                else:
                    logger.info("Webcam server already running")
                    # If webcam is running but we don't have a reference to it, create one
                    if not self.webcam_process or (not isinstance(self.webcam_process, bool) and self.webcam_process.poll() is not None):
                        logger.info("Updating webcam server process reference")
                        # Use a boolean flag instead of creating a process
                        self.webcam_process = True
                
                # Start monitoring script
                script_path = self.script_paths[monitoring_type]
                logger.info(f"Starting {monitoring_type} monitoring for user {user_id} with script: {script_path}")
                
                cmd = [sys.executable, "-u", script_path, user_id]  # -u for unbuffered output
                if progress_report_id:
                    cmd.append(progress_report_id)
                
                # Use a more robust approach with environment variables
                env = os.environ.copy()
                env['PYTHONUNBUFFERED'] = '1'  # Ensure Python output is unbuffered
                
                # Create log file for this monitoring process
                log_file_path = os.path.join(self.backend_dir, f"{monitoring_type}_{user_id}.log")
                log_file = open(log_file_path, 'w')
                
                logger.info(f"Command: {' '.join(cmd)}")
                logger.info(f"Working directory: {self.backend_dir}")
                logger.info(f"Log file: {log_file_path}")
                
                process = subprocess.Popen(
                    cmd, 
                    cwd=self.backend_dir, 
                    stdout=log_file,
                    stderr=log_file,
                    env=env,
                    universal_newlines=True  # Text mode for easier debugging
                )
                
                # Store the process
                self.processes[process_key] = process
                
                # Give it more time to start, especially for hydration monitoring
                start_time = time.time()
                startup_timeout = 10  # 10 seconds timeout
                
                logger.info(f"Waiting for {monitoring_type} monitoring process to start...")
                
                # Poll until process exits or timeout
                while process.poll() is None and (time.time() - start_time) < startup_timeout:
                    time.sleep(0.5)
                
                # Check if it's still running
                if process.poll() is None:
                    logger.info(f"{monitoring_type.capitalize()} monitoring started successfully for user {user_id}")
                    return True, f"{monitoring_type.capitalize()} monitoring started successfully"
                else:
                    # Process exited, get the error
                    log_file.close()
                    with open(log_file_path, 'r') as f:
                        error_output = f.read()
                    
                    logger.error(f"{monitoring_type.capitalize()} monitoring failed to start: {error_output}")
                    
                    if process_key in self.processes:
                        del self.processes[process_key]
                    
                    return False, f"Failed to start {monitoring_type} monitoring. Check {log_file_path} for details."
                    
            except Exception as e:
                logger.error(f"Error starting {monitoring_type} monitoring for user {user_id}: {e}")
                logger.error(traceback.format_exc())
                return False, str(e)
    
    def stop_monitoring(self, monitoring_type, user_id):
        """
        Stop a monitoring process
        
        Args:
            monitoring_type (str): Type of monitoring ('posture', 'stress', 'cvs', 'hydration')
            user_id (str): User ID
            
        Returns:
            tuple: (success, message)
        """
        if monitoring_type not in self.script_paths:
            logger.error(f"Unknown monitoring type: {monitoring_type}")
            return False, f"Unknown monitoring type: {monitoring_type}"
        
        with self.process_lock:
            try:
                process_key = f"{monitoring_type}_{user_id}"
                if process_key not in self.processes:
                    logger.info(f"No active {monitoring_type} monitoring found for user {user_id}")
                    return True, f"No active {monitoring_type} monitoring found for user {user_id}"
                
                process = self.processes[process_key]
                
                # Check if process is still running
                if process.poll() is not None:
                    logger.info(f"{monitoring_type.capitalize()} monitoring for user {user_id} is already stopped")
                    del self.processes[process_key]
                    return True, f"{monitoring_type.capitalize()} monitoring was not running"
                
                # Terminate the process
                logger.info(f"Terminating {monitoring_type} monitoring for user {user_id}")
                process.terminate()
                
                # Wait for it to stop
                try:
                    logger.info(f"Waiting for {monitoring_type} monitoring to terminate...")
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    logger.warning(f"Process for {monitoring_type} monitoring didn't terminate gracefully, killing...")
                    process.kill()
                    process.wait()
                
                # Remove from tracking
                del self.processes[process_key]
                
                logger.info(f"{monitoring_type.capitalize()} monitoring stopped for user {user_id}")
                return True, f"{monitoring_type.capitalize()} monitoring stopped successfully"
                
            except Exception as e:
                logger.error(f"Error stopping {monitoring_type} monitoring for user {user_id}: {e}")
                logger.error(traceback.format_exc())
                return False, str(e)
    
    def get_monitoring_status(self, monitoring_type, user_id):
        """
        Get monitoring status for a user
        
        Args:
            monitoring_type (str): Type of monitoring ('posture', 'stress', 'cvs', 'hydration')
            user_id (str): User ID
            
        Returns:
            dict: Status information
        """
        try:
            # Special case for webcam server status
            if monitoring_type == 'webcam':
                # Check both our process reference and socket connection
                webcam_active_process = (self.webcam_process is True) or (
                    self.webcam_process is not None and 
                    not isinstance(self.webcam_process, bool) and 
                    self.webcam_process.poll() is None
                )
                
                # Double-check with socket connection
                webcam_active_socket = self._check_webcam_server_running()
                
                webcam_active = webcam_active_process or webcam_active_socket
                
                return {
                    'webcam_server_active': webcam_active,
                    'user_id': user_id
                }
            
            process_key = f"{monitoring_type}_{user_id}"
            is_active = (process_key in self.processes and 
                        self.processes[process_key] and 
                        self.processes[process_key].poll() is None)
            
            # Check both our process reference and socket connection for webcam status
            webcam_active_process = (self.webcam_process is True) or (
                self.webcam_process is not None and 
                not isinstance(self.webcam_process, bool) and 
                self.webcam_process.poll() is None
            )
            
            # Double-check with socket connection
            webcam_active_socket = self._check_webcam_server_running()
            
            webcam_active = webcam_active_process or webcam_active_socket
            
            logger.debug(f"Status for {monitoring_type} monitoring for user {user_id}: active={is_active}, webcam={webcam_active}")
            
            return {
                'is_monitoring': is_active,
                'webcam_server_active': webcam_active,
                'monitoring_type': monitoring_type,
                'user_id': user_id
            }
        except Exception as e:
            logger.error(f"Error getting {monitoring_type} monitoring status for user {user_id}: {e}")
            logger.error(traceback.format_exc())
            return {
                'is_monitoring': False,
                'webcam_server_active': False,
                'monitoring_type': monitoring_type,
                'user_id': user_id,
                'error': str(e)
            }
    
    def cleanup(self):
        """Clean up all processes"""
        with self.process_lock:
            try:
                logger.info("Cleaning up all processes")
                
                # Stop all monitoring processes
                for process_key in list(self.processes.keys()):
                    parts = process_key.split('_')
                    if len(parts) >= 2:
                        monitoring_type = parts[0]
                        user_id = '_'.join(parts[1:])
                        logger.info(f"Stopping {monitoring_type} monitoring for user {user_id}")
                        self.stop_monitoring(monitoring_type, user_id)
                
                # Stop webcam server
                if self.webcam_process:
                    logger.info("Stopping webcam server")
                    self.stop_webcam_server()
                    
                logger.info("All processes cleaned up")
                    
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")
                logger.error(traceback.format_exc())
    
    def _check_webcam_server_running(self):
        """
        Check if webcam server is running by trying to connect to it
        
        Returns:
            bool: True if webcam server is running, False otherwise
        """
        try:
            # Try to connect to the webcam server
            HOST = '127.0.0.1'
            PORT = 9999
            
            logger.info(f"Checking if webcam server is running at {HOST}:{PORT}")
            
            # Create a socket and try to connect
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)  # 1 second timeout
            
            # Try to connect
            result = s.connect_ex((HOST, PORT))
            s.close()
            
            # If result is 0, connection was successful
            if result == 0:
                logger.info("Webcam server is running")
                return True
            else:
                logger.info("Webcam server is not running")
                return False
                
        except Exception as e:
            logger.error(f"Error checking if webcam server is running: {e}")
            logger.error(traceback.format_exc())
            return False


# Create a global instance for use across the application
script_manager = ScriptManager() 