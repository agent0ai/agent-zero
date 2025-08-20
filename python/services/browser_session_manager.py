import subprocess
import time
import platform
import psutil
from typing import Dict, Any, Optional
from pathlib import Path
from python.helpers import files
from python.helpers.print_style import PrintStyle


class BrowserSessionManager:
    """Manages browser sessions for manual control with cross-platform support."""
    
    def __init__(self):
        self.system = platform.system()
        self.browser_process: Optional[subprocess.Popen] = None
        self.devtools_process: Optional[subprocess.Popen] = None
        self.cdp_port = 9222
        self.devtools_port = 9223
        self.browser_data_dir = "/tmp/manual-browser-control"
        self.browser_ws_url = f"ws://localhost:{self.cdp_port}"
        self.devtools_url: Optional[str] = None
        self.is_running = False
        self.ps = PrintStyle()
    
    def _find_chrome_binary(self) -> Optional[str]:
        """Find Chrome or Chromium binary on the current system."""
        if self.system == "Darwin":  # macOS
            chrome_paths = [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "/Applications/Chromium.app/Contents/MacOS/Chromium",
                "/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary",
            ]
        elif self.system == "Linux":
            chrome_paths = [
                "/usr/bin/google-chrome",
                "/usr/bin/google-chrome-stable",
                "/usr/bin/chromium",
                "/usr/bin/chromium-browser",
                "/opt/google/chrome/chrome",
                "/snap/bin/chromium",
            ]
        elif self.system == "Windows":
            chrome_paths = [
                "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
                "C:\\Users\\%USERNAME%\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe",
            ]
        else:
            return None
        
        for path in chrome_paths:
            if Path(path).exists():
                return path
        
        return None
    
    def _start_browser(self, headless: bool = False) -> bool:
        """Start Chrome with CDP enabled."""
        chrome_binary = self._find_chrome_binary()
        if not chrome_binary:
            self.ps.error("Chrome/Chromium not found on this system")
            return False
        
        # Create browser data directory
        Path(self.browser_data_dir).mkdir(parents=True, exist_ok=True)
        
        # Chrome command with CDP
        chrome_cmd = [
            chrome_binary,
            f"--remote-debugging-port={self.cdp_port}",
            f"--user-data-dir={self.browser_data_dir}",
            "--no-first-run",
            "--disable-web-security",
            "--disable-features=VizDisplayCompositor",
            "--start-maximized",
            "about:blank"
        ]
        
        if headless:
            chrome_cmd.append("--headless")
        
        try:
            self.browser_process = subprocess.Popen(
                chrome_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Wait for browser to start
            time.sleep(3)
            
            if self.browser_process.poll() is not None:
                self.ps.error("Chrome failed to start")
                return False
            
            self.ps.info(f"Chrome started with CDP on port {self.cdp_port}")
            return True
            
        except Exception as e:
            self.ps.error(f"Failed to start Chrome: {e}")
            return False
    
    def _start_devtools_server(self) -> bool:
        """Start the DevTools frontend server."""
        try:
            # Get path to the DevTools server script
            script_path = self._get_devtools_script_path()
            
            # Start DevTools server
            self.devtools_process = subprocess.Popen([
                "python3", script_path,
                "--port", str(self.devtools_port),
                "--cdp-port", str(self.cdp_port)
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Wait for server to start
            time.sleep(2)
            
            if self.devtools_process.poll() is not None:
                self.ps.warning("DevTools server failed to start")
                return False
            
            self.devtools_url = f"http://localhost:{self.devtools_port}"
            self.ps.info(f"DevTools server started at {self.devtools_url}")
            return True
            
        except Exception as e:
            self.ps.warning(f"Could not start DevTools frontend: {e}")
            return False
    
    def _get_devtools_script_path(self) -> str:
        """Get path to the DevTools frontend server script."""
        return files.get_abs_path("python/services/devtools_server.py")
    
    def start_browser_session(self, headless: bool = False) -> Dict[str, Any]:
        """Start browser session with manual control capabilities."""
        if self.is_running:
            return self.get_connection_info()
        
        try:
            # Start browser
            if not self._start_browser(headless):
                return {"error": "Failed to start browser", "is_running": False}
            
            # Start DevTools frontend server
            if not self._start_devtools_server():
                self.ps.warning("DevTools frontend not available, using direct CDP")
            
            self.is_running = True
            
            result = {
                "cdp_url": f"http://localhost:{self.cdp_port}",
                "devtools_url": self.devtools_url,
                "is_running": True,
                "browser": {
                    "cdp_url": f"http://localhost:{self.cdp_port}",
                    "devtools_url": self.devtools_url,
                    "is_running": True
                }
            }
            
            self.ps.info("Browser session started successfully")
            return result
            
        except Exception as e:
            self.ps.error(f"Failed to start browser session: {e}")
            return {"error": str(e), "is_running": False}
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information for the browser session."""
        return {
            "cdp_url": f"http://localhost:{self.cdp_port}",
            "cdp_port": self.cdp_port,
            "devtools_url": self.devtools_url,
            "devtools_port": self.devtools_port if self.devtools_url else None,
            "is_running": self.is_running,
            "platform": self.system,
            "browser": {
                "cdp_url": f"http://localhost:{self.cdp_port}",
                "devtools_url": self.devtools_url,
                "is_running": self.is_running
            }
        }
    
    def stop_browser_session(self):
        """Stop the browser session and all related processes."""
        self.is_running = False
        
        # Stop DevTools frontend
        if self.devtools_process:
            try:
                self.devtools_process.terminate()
                self.devtools_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.devtools_process.kill()
            except Exception as e:
                self.ps.warning(f"Error stopping DevTools server: {e}")
            finally:
                self.devtools_process = None
                self.devtools_url = None
        
        # Stop browser
        if self.browser_process:
            try:
                self.browser_process.terminate()
                self.browser_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.browser_process.kill()
            except Exception as e:
                self.ps.warning(f"Error stopping browser: {e}")
            finally:
                self.browser_process = None
        
        # Kill any remaining Chrome processes on our CDP port
        self._cleanup_chrome_processes()
        
        self.ps.info("Browser session stopped")
    
    def _cleanup_chrome_processes(self):
        """Clean up any remaining Chrome processes using our CDP port."""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if 'chrome' in proc.info['name'].lower() or 'chromium' in proc.info['name'].lower():
                        cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                        if f'--remote-debugging-port={self.cdp_port}' in cmdline:
                            proc.terminate()
                            time.sleep(1)
                            if proc.is_running():
                                proc.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            self.ps.warning(f"Error cleaning up Chrome processes: {e}")


# Singleton instance
_browser_session_manager: Optional[BrowserSessionManager] = None


def get_browser_session_manager() -> BrowserSessionManager:
    """Get or create the singleton browser session manager."""
    global _browser_session_manager
    if _browser_session_manager is None:
        _browser_session_manager = BrowserSessionManager()
    return _browser_session_manager


def main():
    """Test the browser session manager."""
    manager = get_browser_session_manager()
    
    print("Starting browser session...")
    result = manager.start_browser_session(headless=False)
    print(f"Result: {result}")
    
    if result.get('is_running'):
        input("Press Enter to stop...")
        manager.stop_browser_session()
    else:
        print("Failed to start browser session")


if __name__ == "__main__":
    main()