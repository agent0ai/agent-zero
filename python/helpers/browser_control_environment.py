"""
Browser Control Environment Manager
Handles Xvfb virtual display and Chrome browser process management for browser control PoC
"""

import subprocess
import psutil
import time
import socket
import logging
import os
import signal
from typing import Optional, Dict, Any
from pathlib import Path


class BrowserEnvironment:
    """Manages virtual display and browser processes for browser control"""
    
    def __init__(self, display: str = ":99", debug_port: int = 9222, user_data_dir: str = "/tmp/browser_profile"):
        self.display = display
        self.debug_port = debug_port
        self.user_data_dir = user_data_dir
        self.xvfb_process: Optional[subprocess.Popen] = None
        self.chrome_process: Optional[subprocess.Popen] = None
        self.logger = logging.getLogger(__name__)
        
    def start_xvfb(self, screen_resolution: str = "1920x1080x24") -> bool:
        """Start Xvfb virtual display server"""
        try:
            if self.is_xvfb_running():
                self.logger.info(f"Xvfb already running on display {self.display}")
                return True
                
            # Start Xvfb process
            cmd = [
                'Xvfb', self.display,
                '-screen', '0', screen_resolution,
                '-ac',  # disable access control restrictions
                '+extension', 'GLX',  # enable GLX extension
                '+render',  # enable render extension
                '-noreset'  # don't reset after last client exits
            ]
            
            self.logger.info(f"Starting Xvfb with command: {' '.join(cmd)}")
            self.xvfb_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid  # Create new process group
            )
            
            # Wait for Xvfb to start
            time.sleep(2)
            
            if self.xvfb_process.poll() is None:
                self.logger.info(f"Xvfb started successfully on display {self.display}")
                return True
            else:
                stdout, stderr = self.xvfb_process.communicate()
                self.logger.error(f"Xvfb failed to start: {stderr.decode()}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to start Xvfb: {str(e)}")
            return False
    
    def start_chrome(self, headless: bool = False) -> bool:
        """Start Chrome browser with remote debugging"""
        try:
            if self.is_chrome_running():
                self.logger.info(f"Chrome already running on port {self.debug_port}")
                return True
            
            # Ensure user data directory exists
            Path(self.user_data_dir).mkdir(parents=True, exist_ok=True)
            
            # Find Chrome executable
            chrome_executable = self._find_chrome_executable()
            if not chrome_executable:
                self.logger.error("Chrome/Chromium executable not found")
                return False
            
            # Build Chrome command
            cmd = [
                chrome_executable,
                f'--remote-debugging-port={self.debug_port}',
                f'--user-data-dir={self.user_data_dir}',
                '--no-first-run',
                '--no-default-browser-check',
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-extensions',
                '--disable-plugins',
                '--disable-web-security',
                '--allow-running-insecure-content'
            ]
            
            if headless:
                cmd.append('--headless=new')
            
            # Set display environment
            env = os.environ.copy()
            env['DISPLAY'] = self.display
            
            self.logger.info(f"Starting Chrome with command: {' '.join(cmd)}")
            self.chrome_process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid  # Create new process group
            )
            
            # Wait for Chrome to start and debug port to become available
            for _ in range(30):  # Wait up to 30 seconds
                if self._is_port_open('localhost', self.debug_port):
                    self.logger.info(f"Chrome started successfully on port {self.debug_port}")
                    return True
                time.sleep(1)
            
            # If we get here, Chrome didn't start properly
            stdout, stderr = self.chrome_process.communicate()
            self.logger.error(f"Chrome failed to start or debug port not accessible: {stderr.decode()}")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to start Chrome: {str(e)}")
            return False
    
    def stop_all(self) -> bool:
        """Stop all managed processes"""
        success = True
        
        # Stop Chrome
        if not self.stop_chrome():
            success = False
            
        # Stop Xvfb
        if not self.stop_xvfb():
            success = False
            
        return success
    
    def stop_chrome(self) -> bool:
        """Stop Chrome browser process"""
        try:
            if self.chrome_process:
                self.logger.info("Stopping Chrome process...")
                os.killpg(os.getpgid(self.chrome_process.pid), signal.SIGTERM)
                
                # Wait for graceful termination
                try:
                    self.chrome_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.logger.warning("Chrome didn't terminate gracefully, forcing kill")
                    os.killpg(os.getpgid(self.chrome_process.pid), signal.SIGKILL)
                    
                self.chrome_process = None
                self.logger.info("Chrome process stopped")
                
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop Chrome: {str(e)}")
            return False
    
    def stop_xvfb(self) -> bool:
        """Stop Xvfb virtual display server"""
        try:
            if self.xvfb_process:
                self.logger.info("Stopping Xvfb process...")
                os.killpg(os.getpgid(self.xvfb_process.pid), signal.SIGTERM)
                
                # Wait for graceful termination
                try:
                    self.xvfb_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.logger.warning("Xvfb didn't terminate gracefully, forcing kill")
                    os.killpg(os.getpgid(self.xvfb_process.pid), signal.SIGKILL)
                    
                self.xvfb_process = None
                self.logger.info("Xvfb process stopped")
                
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop Xvfb: {str(e)}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        status = {
            'xvfb_running': self.is_xvfb_running(),
            'chrome_running': self.is_chrome_running(),
            'debug_port_accessible': self._is_port_open('localhost', self.debug_port),
            'display_available': self._is_display_available(),
            'overall_healthy': False
        }
        
        # Overall health is true if all components are working
        status['overall_healthy'] = all([
            status['xvfb_running'],
            status['chrome_running'], 
            status['debug_port_accessible'],
            status['display_available']
        ])
        
        return status
    
    def is_xvfb_running(self) -> bool:
        """Check if Xvfb is running"""
        if self.xvfb_process and self.xvfb_process.poll() is None:
            return True
        return False
    
    def is_chrome_running(self) -> bool:
        """Check if Chrome is running"""
        if self.chrome_process and self.chrome_process.poll() is None:
            return True
        return False
    
    def _find_chrome_executable(self) -> Optional[str]:
        """Find available Chrome/Chromium executable"""
        executables = ['google-chrome', 'chromium', 'chromium-browser', 'chrome']
        
        for executable in executables:
            try:
                result = subprocess.run(['which', executable], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    return executable.strip()
            except Exception:
                continue
        
        return None
    
    def _is_port_open(self, host: str, port: int) -> bool:
        """Check if a port is open and accessible"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def _is_display_available(self) -> bool:
        """Check if the X display is available"""
        try:
            env = os.environ.copy()
            env['DISPLAY'] = self.display
            result = subprocess.run(['xdpyinfo'], 
                                  env=env, capture_output=True, timeout=5)
            return result.returncode == 0
        except Exception:
            return False
    
    def get_debug_url(self) -> str:
        """Get Chrome remote debugging URL"""
        return f"http://localhost:{self.debug_port}"
    
    def get_status_info(self) -> Dict[str, Any]:
        """Get detailed status information"""
        health = self.health_check()
        return {
            'display': self.display,
            'debug_port': self.debug_port,
            'debug_url': self.get_debug_url(),
            'user_data_dir': self.user_data_dir,
            'xvfb_pid': self.xvfb_process.pid if self.xvfb_process else None,
            'chrome_pid': self.chrome_process.pid if self.chrome_process else None,
            'health': health
        }


# Global instance for singleton pattern
_browser_environment_instance: Optional[BrowserEnvironment] = None


def get_browser_environment() -> BrowserEnvironment:
    """Get or create global browser environment instance"""
    global _browser_environment_instance
    if _browser_environment_instance is None:
        _browser_environment_instance = BrowserEnvironment()
    return _browser_environment_instance


def cleanup_browser_environment():
    """Clean up global browser environment instance"""
    global _browser_environment_instance
    if _browser_environment_instance:
        _browser_environment_instance.stop_all()
        _browser_environment_instance = None