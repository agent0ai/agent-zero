"""
CDP Command Execution Tool
Provides a tool interface for executing CDP commands directly
"""

import json
import asyncio
from typing import Dict, Any, Optional
from python.helpers.tool import Tool, Response
from python.helpers.cdp_session_manager import BrowserCDPManager, CDPError
from python.helpers.browser_control_environment import get_browser_environment
from python.helpers.print_style import PrintStyle


class CDPExecutor(Tool):
    """Tool for executing Chrome DevTools Protocol commands"""
    
    async def execute(self, method: str, params: Dict[str, Any] = None, timeout: float = 30.0, **kwargs):
        """
        Execute CDP command on connected browser.
        
        Args:
            method (str): CDP method to execute (e.g. "Page.navigate", "Runtime.evaluate")
            params (dict): Parameters for the CDP command
            timeout (float): Command timeout in seconds (default: 30.0)
            host (str): Browser host (default: localhost)
            port (int): Browser debug port (default: 9222)
        """
        
        if params is None:
            params = {}
        
        host = kwargs.get('host', 'localhost')
        port = kwargs.get('port', 9222)
        
        # Try to get port from environment if available
        try:
            env = get_browser_environment()
            if env.health_check()['overall_healthy']:
                port = env.debug_port
                PrintStyle().print(f"Using browser environment debug port: {port}", color=PrintStyle.BLUE)
        except Exception:
            pass  # Fall back to provided port
        
        cdp_manager = BrowserCDPManager(host, port)
        
        try:
            # Connect to browser
            if not await cdp_manager.connect():
                return Response(
                    message=f"Failed to connect to browser CDP on {host}:{port}",
                    break_loop=False
                )
            
            PrintStyle().print(f"Executing CDP command: {method}", color=PrintStyle.BLUE)
            
            # Execute command
            response = await cdp_manager.cdp.send_command(method, params, timeout)
            
            if response.is_success():
                result_data = response.get_result()
                
                # Format response based on command type
                if method == "Page.navigate":
                    message = f"✅ Navigation completed to: {params.get('url', 'unknown')}"
                elif method == "Runtime.evaluate":
                    expression = params.get('expression', '')
                    result_value = result_data.get('value', result_data) if result_data else None
                    message = f"✅ JavaScript executed: {expression}\nResult: {json.dumps(result_value, indent=2)}"
                elif method == "Page.captureScreenshot":
                    message = "✅ Screenshot captured successfully"
                elif method.startswith("Target."):
                    message = f"✅ Target command completed: {method}"
                else:
                    message = f"✅ CDP command completed: {method}\nResult: {json.dumps(result_data, indent=2)}"
                
                return Response(
                    message=message,
                    break_loop=False
                )
            else:
                error_info = response.error
                message = f"❌ CDP command failed: {method}\nError: {error_info['message']} (Code: {error_info['code']})"
                
                return Response(
                    message=message,
                    break_loop=False
                )
        
        except CDPError as e:
            return Response(
                message=f"❌ CDP Error: {str(e)}",
                break_loop=False
            )
        except Exception as e:
            return Response(
                message=f"❌ Unexpected error executing CDP command: {str(e)}",
                break_loop=False
            )
        finally:
            await cdp_manager.disconnect()


class BrowserStateInspector(Tool):
    """Tool for inspecting browser state via CDP"""
    
    async def execute(self, action: str = "info", **kwargs):
        """
        Inspect browser state and information.
        
        Args:
            action (str): Action to perform - "info", "screenshot", "cookies", "storage"
            host (str): Browser host (default: localhost)
            port (int): Browser debug port (default: 9222)
        """
        
        host = kwargs.get('host', 'localhost')
        port = kwargs.get('port', 9222)
        
        # Try to get port from environment if available
        try:
            env = get_browser_environment()
            if env.health_check()['overall_healthy']:
                port = env.debug_port
        except Exception:
            pass
        
        cdp_manager = BrowserCDPManager(host, port)
        
        try:
            if not await cdp_manager.connect():
                return Response(
                    message=f"Failed to connect to browser CDP on {host}:{port}",
                    break_loop=False
                )
            
            if action == "info":
                return await self._get_browser_info(cdp_manager)
            elif action == "screenshot":
                return await self._take_screenshot(cdp_manager)
            elif action == "cookies":
                return await self._get_cookies(cdp_manager)
            elif action == "storage":
                return await self._get_storage_info(cdp_manager)
            else:
                return Response(
                    message=f"Invalid action: {action}. Available actions: info, screenshot, cookies, storage",
                    break_loop=False
                )
        
        except Exception as e:
            return Response(
                message=f"❌ Browser state inspection failed: {str(e)}",
                break_loop=False
            )
        finally:
            await cdp_manager.disconnect()
    
    async def _get_browser_info(self, cdp_manager: BrowserCDPManager) -> Response:
        """Get comprehensive browser information"""
        try:
            page_info = await cdp_manager.get_page_info()
            browser_state = await cdp_manager.get_browser_state()
            
            message = f"""🔍 Browser Information:

📄 Page Info:
  URL: {page_info.get('url', 'unknown')}
  Title: {page_info.get('title', 'unknown')}
  Timestamp: {page_info.get('timestamp', 0)}

🍪 Cookies: {len(browser_state.get('cookies', []))} found
💾 Local Storage: {len(browser_state.get('local_storage', {}))} items

🌐 Browser State:
{json.dumps(browser_state, indent=2)}"""
            
            return Response(message=message, break_loop=False)
            
        except Exception as e:
            return Response(
                message=f"❌ Failed to get browser info: {str(e)}",
                break_loop=False
            )
    
    async def _take_screenshot(self, cdp_manager: BrowserCDPManager) -> Response:
        """Take and save screenshot"""
        try:
            screenshot_data = await cdp_manager.take_screenshot()
            
            if screenshot_data:
                # Save screenshot to file
                import time
                from pathlib import Path
                
                timestamp = int(time.time())
                filename = f"browser_screenshot_{timestamp}.png"
                filepath = Path("tmp") / "screenshots" / filename
                filepath.parent.mkdir(parents=True, exist_ok=True)
                
                with open(filepath, "wb") as f:
                    f.write(screenshot_data)
                
                return Response(
                    message=f"✅ Screenshot saved: {filepath}\nSize: {len(screenshot_data)} bytes",
                    break_loop=False
                )
            else:
                return Response(
                    message="❌ Failed to capture screenshot",
                    break_loop=False
                )
                
        except Exception as e:
            return Response(
                message=f"❌ Screenshot failed: {str(e)}",
                break_loop=False
            )
    
    async def _get_cookies(self, cdp_manager: BrowserCDPManager) -> Response:
        """Get browser cookies"""
        try:
            response = await cdp_manager.cdp.send_command("Network.getCookies")
            
            if response.is_success():
                cookies = response.get_result().get("cookies", [])
                
                message = f"🍪 Browser Cookies ({len(cookies)} found):\n\n"
                
                for cookie in cookies[:10]:  # Show first 10 cookies
                    message += f"  • {cookie.get('name', 'unknown')}: {cookie.get('value', 'unknown')[:50]}...\n"
                    message += f"    Domain: {cookie.get('domain', 'unknown')}\n"
                    message += f"    Path: {cookie.get('path', 'unknown')}\n\n"
                
                if len(cookies) > 10:
                    message += f"... and {len(cookies) - 10} more cookies"
                
                return Response(message=message, break_loop=False)
            else:
                return Response(
                    message="❌ Failed to get cookies",
                    break_loop=False
                )
                
        except Exception as e:
            return Response(
                message=f"❌ Cookie retrieval failed: {str(e)}",
                break_loop=False
            )
    
    async def _get_storage_info(self, cdp_manager: BrowserCDPManager) -> Response:
        """Get storage information"""
        try:
            # Get local storage
            ls_response = await cdp_manager.execute_javascript(
                "JSON.stringify(Object.fromEntries(Object.entries(localStorage)))"
            )
            
            # Get session storage
            ss_response = await cdp_manager.execute_javascript(
                "JSON.stringify(Object.fromEntries(Object.entries(sessionStorage)))"
            )
            
            local_storage = json.loads(ls_response) if ls_response else {}
            session_storage = json.loads(ss_response) if ss_response else {}
            
            message = f"""💾 Browser Storage:

📦 Local Storage ({len(local_storage)} items):
{json.dumps(local_storage, indent=2)}

🗂️ Session Storage ({len(session_storage)} items):
{json.dumps(session_storage, indent=2)}"""
            
            return Response(message=message, break_loop=False)
            
        except Exception as e:
            return Response(
                message=f"❌ Storage retrieval failed: {str(e)}",
                break_loop=False
            )


class CDPBatchExecutor(Tool):
    """Tool for executing multiple CDP commands in sequence"""
    
    async def execute(self, commands: list, timeout: float = 30.0, **kwargs):
        """
        Execute multiple CDP commands in sequence.
        
        Args:
            commands (list): List of CDP commands, each containing 'method' and 'params'
            timeout (float): Timeout per command in seconds
            host (str): Browser host (default: localhost)
            port (int): Browser debug port (default: 9222)
        """
        
        if not isinstance(commands, list):
            return Response(
                message="Commands parameter must be a list of command objects",
                break_loop=False
            )
        
        host = kwargs.get('host', 'localhost')
        port = kwargs.get('port', 9222)
        
        # Try to get port from environment
        try:
            env = get_browser_environment()
            if env.health_check()['overall_healthy']:
                port = env.debug_port
        except Exception:
            pass
        
        cdp_manager = BrowserCDPManager(host, port)
        results = []
        
        try:
            if not await cdp_manager.connect():
                return Response(
                    message=f"Failed to connect to browser CDP on {host}:{port}",
                    break_loop=False
                )
            
            PrintStyle().print(f"Executing {len(commands)} CDP commands in batch", color=PrintStyle.BLUE)
            
            for i, cmd in enumerate(commands):
                if not isinstance(cmd, dict) or 'method' not in cmd:
                    results.append({
                        "command_index": i,
                        "error": "Invalid command format - must contain 'method'"
                    })
                    continue
                
                method = cmd['method']
                params = cmd.get('params', {})
                
                try:
                    response = await cdp_manager.cdp.send_command(method, params, timeout)
                    
                    if response.is_success():
                        results.append({
                            "command_index": i,
                            "method": method,
                            "success": True,
                            "result": response.get_result()
                        })
                    else:
                        results.append({
                            "command_index": i,
                            "method": method,
                            "success": False,
                            "error": response.error
                        })
                
                except Exception as e:
                    results.append({
                        "command_index": i,
                        "method": method,
                        "success": False,
                        "error": str(e)
                    })
            
            # Summarize results
            successful = len([r for r in results if r.get('success', False)])
            failed = len(results) - successful
            
            message = f"📊 Batch CDP Execution Results:\n"
            message += f"  Successful: {successful}\n"
            message += f"  Failed: {failed}\n\n"
            
            message += "📋 Detailed Results:\n"
            message += json.dumps(results, indent=2)
            
            return Response(message=message, break_loop=False)
        
        except Exception as e:
            return Response(
                message=f"❌ Batch CDP execution failed: {str(e)}",
                break_loop=False
            )
        finally:
            await cdp_manager.disconnect()