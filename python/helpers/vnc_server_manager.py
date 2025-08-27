"""
VNC Server Manager
Manages VNC server setup and configuration for remote browser access
"""

import subprocess
import psutil
import time
import socket
import logging
import os
import signal
from typing import Optional, Dict, Any, List
from pathlib import Path
from dataclasses import dataclass


@dataclass
class VNCConfig:
    """VNC server configuration"""
    display: str
    port: int
    password: Optional[str]
    geometry: str
    shared: bool
    forever: bool
    auth_method: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "display": self.display,
            "port": self.port,
            "password": bool(self.password),  # Don't expose actual password
            "geometry": self.geometry,
            "shared": self.shared,
            "forever": self.forever,
            "auth_method": self.auth_method
        }


class VNCServerManager:
    """Manages VNC server processes for remote desktop access"""
    
    def __init__(self, 
                 display: str = ":99", 
                 vnc_port: int = 5900,
                 password: Optional[str] = None,
                 geometry: str = "1920x1080"):
        self.display = display
        self.vnc_port = vnc_port
        self.password = password
        self.geometry = geometry
        self.vnc_process: Optional[subprocess.Popen] = None
        self.logger = logging.getLogger(__name__)
        
        # VNC configuration
        self.config = VNCConfig(
            display=display,
            port=vnc_port,
            password=password,
            geometry=geometry,
            shared=True,  # Allow multiple connections
            forever=True,  # Keep running after client disconnects
            auth_method="password" if password else "none"
        )
    
    def start_vnc_server(self) -> bool:
        """Start VNC server for the specified display"""
        try:
            if self.is_vnc_running():
                self.logger.info(f"VNC server already running on port {self.vnc_port}")
                return True
            
            # Check if display is available
            if not self._is_display_available():
                self.logger.error(f"Display {self.display} is not available")
                return False
            
            # Build VNC command
            cmd = self._build_vnc_command()
            
            self.logger.info(f"Starting VNC server with command: {' '.join(cmd)}")
            
            # Start VNC process
            self.vnc_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid  # Create new process group
            )
            
            # Wait for VNC server to start
            time.sleep(2)
            
            if self.vnc_process.poll() is None and self._is_port_available('localhost', self.vnc_port, check_listening=True):
                self.logger.info(f"VNC server started successfully on port {self.vnc_port}")
                return True
            else:
                stdout, stderr = self.vnc_process.communicate()
                self.logger.error(f"VNC server failed to start: {stderr.decode()}")
                return False
        
        except Exception as e:
            self.logger.error(f"Failed to start VNC server: {str(e)}")
            return False
    
    def stop_vnc_server(self) -> bool:
        """Stop VNC server"""
        try:
            if self.vnc_process:
                self.logger.info("Stopping VNC server process...")
                
                # Try graceful termination first
                os.killpg(os.getpgid(self.vnc_process.pid), signal.SIGTERM)
                
                # Wait for graceful termination
                try:
                    self.vnc_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.logger.warning("VNC server didn't terminate gracefully, forcing kill")
                    os.killpg(os.getpgid(self.vnc_process.pid), signal.SIGKILL)
                
                self.vnc_process = None
                self.logger.info("VNC server stopped")
            
            # Also kill any remaining VNC processes on our port/display
            self._cleanup_vnc_processes()
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to stop VNC server: {str(e)}")
            return False
    
    def restart_vnc_server(self) -> bool:
        """Restart VNC server"""
        self.logger.info("Restarting VNC server...")
        
        if not self.stop_vnc_server():
            self.logger.error("Failed to stop VNC server for restart")
            return False
        
        time.sleep(1)  # Allow cleanup
        
        return self.start_vnc_server()
    
    def is_vnc_running(self) -> bool:
        """Check if VNC server is running"""
        if self.vnc_process and self.vnc_process.poll() is None:
            return True
        
        # Also check if port is in use by any VNC process
        return self._is_port_available('localhost', self.vnc_port, check_listening=True)
    
    def get_vnc_status(self) -> Dict[str, Any]:
        """Get VNC server status"""
        is_running = self.is_vnc_running()
        
        status = {
            "running": is_running,
            "display": self.display,
            "port": self.vnc_port,
            "pid": self.vnc_process.pid if self.vnc_process else None,
            "config": self.config.to_dict(),
            "connections": self._get_active_connections() if is_running else 0,
            "uptime": self._get_uptime() if is_running else 0
        }
        
        if is_running:
            status["connection_url"] = f"vnc://localhost:{self.vnc_port}"
        
        return status
    
    def get_vnc_configuration(self) -> Dict[str, Any]:
        """Get VNC server configuration"""
        return self.config.to_dict()
    
    def update_configuration(self, **kwargs) -> bool:
        """Update VNC server configuration"""
        restart_needed = False
        
        if 'display' in kwargs and kwargs['display'] != self.display:
            self.display = kwargs['display']
            self.config.display = self.display
            restart_needed = True
        
        if 'vnc_port' in kwargs and kwargs['vnc_port'] != self.vnc_port:
            self.vnc_port = kwargs['vnc_port']
            self.config.port = self.vnc_port
            restart_needed = True
        
        if 'password' in kwargs:
            self.password = kwargs['password']
            self.config.password = self.password
            self.config.auth_method = "password" if self.password else "none"
            restart_needed = True
        
        if 'geometry' in kwargs and kwargs['geometry'] != self.geometry:
            self.geometry = kwargs['geometry']
            self.config.geometry = self.geometry
            restart_needed = True
        
        # If VNC is running and restart is needed, restart it
        if restart_needed and self.is_vnc_running():
            self.logger.info("Configuration changed, restarting VNC server")
            return self.restart_vnc_server()
        
        return True
    
    def _build_vnc_command(self) -> List[str]:
        """Build VNC server command"""
        cmd = [
            'x11vnc',
            '-display', self.display,
            '-rfbport', str(self.vnc_port),
            '-geometry', self.geometry,
            '-shared',  # Allow multiple clients
            '-forever',  # Keep running after client disconnects
            '-noxdamage',  # Disable X damage extension for stability
            '-noxfixes',   # Disable X fixes extension
            '-noxrecord',  # Disable X record extension
            '-noxshm',     # Disable X shared memory
            '-noxrandr',   # Disable X RandR extension
            '-bg'          # Run in background
        ]
        
        # Add authentication
        if self.password:
            # Create password file
            passwd_file = self._create_password_file()
            if passwd_file:
                cmd.extend(['-passwd', passwd_file])
            else:
                self.logger.warning("Failed to create password file, running without authentication")
                cmd.append('-nopw')  # No password required
        else:
            cmd.append('-nopw')  # No password required
        
        # Add additional security options
        cmd.extend([
            '-no6',        # Disable IPv6
            '-noipv6',     # Disable IPv6
            '-localhost',  # Only allow localhost connections
        ])
        
        return cmd
    
    def _create_password_file(self) -> Optional[str]:
        """Create VNC password file"""
        try:
            # Create temporary password file
            passwd_dir = Path("/tmp/vnc_passwords")
            passwd_dir.mkdir(exist_ok=True, mode=0o700)
            
            passwd_file = passwd_dir / f"passwd_{self.vnc_port}"
            
            # Use vncpasswd to create password file
            proc = subprocess.Popen(
                ['vncpasswd', '-f'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            stdout, stderr = proc.communicate(input=self.password.encode())
            
            if proc.returncode == 0:
                with open(passwd_file, 'wb') as f:
                    f.write(stdout)
                
                # Set proper permissions
                passwd_file.chmod(0o600)
                
                return str(passwd_file)
            else:
                self.logger.error(f"Failed to create VNC password file: {stderr.decode()}")
                return None
        
        except Exception as e:
            self.logger.error(f"Exception creating password file: {str(e)}")
            return None
    
    def _is_display_available(self) -> bool:
        """Check if X display is available"""
        try:
            env = os.environ.copy()
            env['DISPLAY'] = self.display
            result = subprocess.run(['xdpyinfo'], env=env, capture_output=True, timeout=5)
            return result.returncode == 0
        except Exception:
            return False
    
    def _is_port_available(self, host: str, port: int, check_listening: bool = False) -> bool:
        """Check if port is available or listening"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            
            if check_listening:
                # Check if something is listening on the port
                result = sock.connect_ex((host, port))
                sock.close()
                return result == 0  # Connected means something is listening
            else:
                # Check if port is free
                result = sock.bind((host, port))
                sock.close()
                return True  # Bind succeeded, port is free
        
        except Exception:
            return False if not check_listening else True
    
    def _cleanup_vnc_processes(self):
        """Clean up any remaining VNC processes"""
        try:
            # Kill x11vnc processes using our display
            subprocess.run([
                'pkill', '-f', f'x11vnc.*{self.display}'
            ], capture_output=True, check=False)
            
            # Kill processes using our port
            subprocess.run([
                'pkill', '-f', f'x11vnc.*{self.vnc_port}'
            ], capture_output=True, check=False)
        
        except Exception as e:
            self.logger.warning(f"Error during VNC process cleanup: {e}")
    
    def _get_active_connections(self) -> int:
        """Get number of active VNC connections"""
        try:
            # Use netstat to count connections to our VNC port
            result = subprocess.run([
                'netstat', '-an'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                count = 0
                for line in lines:
                    if f':{self.vnc_port}' in line and 'ESTABLISHED' in line:
                        count += 1
                return count
        
        except Exception:
            pass
        
        return 0
    
    def _get_uptime(self) -> float:
        """Get VNC server uptime in seconds"""
        if self.vnc_process:
            try:
                ps_process = psutil.Process(self.vnc_process.pid)
                return time.time() - ps_process.create_time()
            except:
                pass
        return 0.0
    
    def take_display_screenshot(self) -> Optional[bytes]:
        """Take screenshot of the VNC display"""
        try:
            # Use x11vnc to take screenshot
            cmd = [
                'x11vnc',
                '-display', self.display,
                '-rawfb', 'snap:',  # Take snapshot
                '-quiet',
                '-viewonly',
                '-once'
            ]
            
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            
            if result.returncode == 0:
                return result.stdout
            else:
                self.logger.error(f"Screenshot failed: {result.stderr.decode()}")
                return None
        
        except Exception as e:
            self.logger.error(f"Screenshot exception: {str(e)}")
            return None
    
    def get_display_info(self) -> Dict[str, Any]:
        """Get information about the display"""
        try:
            env = os.environ.copy()
            env['DISPLAY'] = self.display
            
            result = subprocess.run(['xdpyinfo'], env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                output = result.stdout
                info = {
                    "display": self.display,
                    "available": True,
                    "dimensions": "unknown",
                    "depth": "unknown"
                }
                
                # Parse xdpyinfo output
                for line in output.split('\n'):
                    if 'dimensions:' in line:
                        info["dimensions"] = line.split('dimensions:')[1].split('pixels')[0].strip()
                    elif 'depth:' in line and 'root' in line:
                        info["depth"] = line.split('depth:')[1].split()[0]
                
                return info
            else:
                return {"display": self.display, "available": False, "error": result.stderr}
        
        except Exception as e:
            return {"display": self.display, "available": False, "error": str(e)}


# Global VNC server manager instance
_vnc_server_instance: Optional[VNCServerManager] = None


def get_vnc_server_manager(display: str = ":99", port: int = 5900) -> VNCServerManager:
    """Get or create global VNC server manager instance"""
    global _vnc_server_instance
    if _vnc_server_instance is None or _vnc_server_instance.display != display:
        _vnc_server_instance = VNCServerManager(display=display, vnc_port=port)
    return _vnc_server_instance


def cleanup_vnc_server():
    """Clean up global VNC server instance"""
    global _vnc_server_instance
    if _vnc_server_instance:
        _vnc_server_instance.stop_vnc_server()
        _vnc_server_instance = None