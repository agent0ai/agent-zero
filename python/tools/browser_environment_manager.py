"""
Browser Environment Manager Tool
CLI tool for managing browser control environment lifecycle
"""

from datetime import datetime
from python.helpers.tool import Tool, Response
from python.helpers.browser_control_environment import get_browser_environment, cleanup_browser_environment
from python.helpers.print_style import PrintStyle
import asyncio
import json


class BrowserEnvironmentManager(Tool):
    """Tool for managing browser control environment processes"""

    async def execute(self, action: str = "status", **kwargs):
        """
        Manage browser control environment lifecycle.

        Args:
            action (str): Action to perform - "start", "stop", "status", "restart", "health"
            display (str): X display to use (default: :99)  
            debug_port (int): Chrome remote debugging port (default: 9222)
            user_data_dir (str): Chrome user data directory (default: /tmp/browser_profile)
            headless (bool): Run Chrome in headless mode (default: False)
        """
        
        display = kwargs.get('display', ':99')
        debug_port = kwargs.get('debug_port', 9222)
        user_data_dir = kwargs.get('user_data_dir', '/tmp/browser_profile')
        headless = kwargs.get('headless', False)
        
        # Get environment manager instance
        env = get_browser_environment()
        
        # Configure instance if parameters provided
        if display != ':99':
            env.display = display
        if debug_port != 9222:
            env.debug_port = debug_port
        if user_data_dir != '/tmp/browser_profile':
            env.user_data_dir = user_data_dir

        try:
            if action == "start":
                return await self._start_environment(env, headless)
            elif action == "stop":
                return await self._stop_environment(env)
            elif action == "restart":
                return await self._restart_environment(env, headless)
            elif action == "status":
                return await self._get_status(env)
            elif action == "health":
                return await self._health_check(env)
            else:
                return Response(
                    message=f"Invalid action '{action}'. Available actions: start, stop, restart, status, health",
                    break_loop=False
                )
        except Exception as e:
            return Response(
                message=f"Browser environment manager error: {str(e)}",
                break_loop=False
            )

    async def _start_environment(self, env, headless: bool) -> Response:
        """Start the browser control environment"""
        PrintStyle().print("Starting browser control environment...", color=PrintStyle.BLUE)
        
        # Start Xvfb
        if not env.start_xvfb():
            return Response(
                message="Failed to start Xvfb virtual display server",
                break_loop=False
            )
        
        PrintStyle().print(f"✓ Xvfb started on display {env.display}", color=PrintStyle.GREEN)
        
        # Start Chrome
        if not env.start_chrome(headless=headless):
            env.stop_xvfb()  # Clean up Xvfb if Chrome fails
            return Response(
                message="Failed to start Chrome browser with remote debugging",
                break_loop=False
            )
        
        PrintStyle().print(f"✓ Chrome started with remote debugging on port {env.debug_port}", color=PrintStyle.GREEN)
        
        # Get status info
        status = env.get_status_info()
        
        message = f"""Browser control environment started successfully!

Display: {status['display']}  
Chrome Debug Port: {status['debug_port']}
Debug URL: {status['debug_url']}
User Data Dir: {status['user_data_dir']}
Xvfb PID: {status['xvfb_pid']}
Chrome PID: {status['chrome_pid']}

The environment is ready for browser-use integration and VNC access."""

        return Response(
            message=message,
            break_loop=False
        )

    async def _stop_environment(self, env) -> Response:
        """Stop the browser control environment"""
        PrintStyle().print("Stopping browser control environment...", color=PrintStyle.BLUE)
        
        success = env.stop_all()
        
        if success:
            PrintStyle().print("✓ Browser control environment stopped", color=PrintStyle.GREEN)
            cleanup_browser_environment()
            return Response(
                message="Browser control environment stopped successfully",
                break_loop=False
            )
        else:
            return Response(
                message="Some components failed to stop cleanly. Check logs for details.",
                break_loop=False
            )

    async def _restart_environment(self, env, headless: bool) -> Response:
        """Restart the browser control environment"""
        PrintStyle().print("Restarting browser control environment...", color=PrintStyle.BLUE)
        
        # Stop first
        env.stop_all()
        await asyncio.sleep(2)  # Wait for cleanup
        
        # Then start
        return await self._start_environment(env, headless)

    async def _get_status(self, env) -> Response:
        """Get detailed status of the browser control environment"""
        status = env.get_status_info()
        health = status['health']
        
        status_text = "🟢 HEALTHY" if health['overall_healthy'] else "🔴 UNHEALTHY"
        
        message = f"""Browser Control Environment Status: {status_text}

Configuration:
  Display: {status['display']}
  Debug Port: {status['debug_port']} 
  Debug URL: {status['debug_url']}
  User Data Dir: {status['user_data_dir']}

Process Status:
  Xvfb PID: {status['xvfb_pid'] or 'Not running'}
  Chrome PID: {status['chrome_pid'] or 'Not running'}

Health Check:
  Xvfb Running: {'✓' if health['xvfb_running'] else '✗'}
  Chrome Running: {'✓' if health['chrome_running'] else '✗'}
  Debug Port Accessible: {'✓' if health['debug_port_accessible'] else '✗'}
  Display Available: {'✓' if health['display_available'] else '✗'}"""

        return Response(
            message=message,
            break_loop=False
        )

    async def _health_check(self, env) -> Response:
        """Perform comprehensive health check"""
        PrintStyle().print("Performing health check...", color=PrintStyle.BLUE)
        
        health = env.health_check()
        
        # Create detailed health report
        report = {
            "timestamp": datetime.now().isoformat(),  # Would use actual timestamp
            "overall_status": "healthy" if health['overall_healthy'] else "unhealthy",
            "components": {
                "xvfb": {
                    "status": "running" if health['xvfb_running'] else "stopped",
                    "healthy": health['xvfb_running']
                },
                "chrome": {
                    "status": "running" if health['chrome_running'] else "stopped", 
                    "healthy": health['chrome_running']
                },
                "debug_port": {
                    "accessible": health['debug_port_accessible'],
                    "healthy": health['debug_port_accessible']
                },
                "display": {
                    "available": health['display_available'],
                    "healthy": health['display_available']
                }
            }
        }
        
        # Format message
        status_icon = "🟢" if health['overall_healthy'] else "🔴"
        message = f"{status_icon} Health Check Results:\n\n{json.dumps(report, indent=2)}"
        
        if not health['overall_healthy']:
            message += "\n\n⚠️  Some components are unhealthy. Consider restarting the environment."
        
        return Response(
            message=message,
            break_loop=False
        )