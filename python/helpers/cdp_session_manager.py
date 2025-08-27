"""
CDP Session Manager
Handles Chrome DevTools Protocol connections for external browser control
"""

import asyncio
import json
import logging
import time
import uuid
import websockets
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass
from enum import Enum


class CDPError(Exception):
    """CDP-specific error"""
    pass


@dataclass
class CDPCommand:
    """Represents a CDP command"""
    method: str
    params: Dict[str, Any]
    id: int = None
    
    def __post_init__(self):
        if self.id is None:
            self.id = int(time.time() * 1000000) % 1000000  # Microsecond-based ID
    
    def to_json(self) -> str:
        """Serialize command to JSON"""
        return json.dumps({
            "id": self.id,
            "method": self.method,
            "params": self.params
        })


@dataclass 
class CDPResponse:
    """Represents a CDP response"""
    id: int
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_json(cls, json_str: str) -> 'CDPResponse':
        """Create CDPResponse from JSON string"""
        data = json.loads(json_str)
        return cls(
            id=data.get("id"),
            result=data.get("result"),
            error=data.get("error")
        )
    
    def is_success(self) -> bool:
        """Check if response indicates success"""
        return self.error is None
    
    def get_result(self) -> Any:
        """Get result data or raise error"""
        if not self.is_success():
            raise CDPError(f"CDP Error {self.error['code']}: {self.error['message']}")
        return self.result


class CDPSessionManager:
    """Manages CDP connections to external browser instances"""
    
    def __init__(self, host: str = "localhost", port: int = 9222):
        self.host = host
        self.port = port
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.pending_commands: Dict[int, asyncio.Future] = {}
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.logger = logging.getLogger(__name__)
        self._connected = False
        self._listen_task: Optional[asyncio.Task] = None
        
    async def connect(self) -> bool:
        """Connect to Chrome DevTools Protocol WebSocket"""
        try:
            # First, get the WebSocket debugger URL
            ws_url = await self._get_websocket_url()
            if not ws_url:
                self.logger.error("Failed to get WebSocket URL from Chrome")
                return False
            
            # Connect to the WebSocket
            self.websocket = await websockets.connect(ws_url)
            self._connected = True
            
            # Start listening for messages
            self._listen_task = asyncio.create_task(self._listen_for_messages())
            
            self.logger.info(f"Connected to CDP WebSocket: {ws_url}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to CDP: {str(e)}")
            return False
    
    async def disconnect(self):
        """Disconnect from CDP WebSocket"""
        self._connected = False
        
        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
        
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        
        # Cancel all pending commands
        for future in self.pending_commands.values():
            if not future.done():
                future.cancel()
        self.pending_commands.clear()
        
        self.logger.info("Disconnected from CDP")
    
    def is_connected(self) -> bool:
        """Check if connected to CDP"""
        return self._connected and self.websocket is not None
    
    async def send_command(self, method: str, params: Dict[str, Any] = None, timeout: float = 30.0) -> CDPResponse:
        """Send CDP command and wait for response"""
        if not self.is_connected():
            raise CDPError("Not connected to CDP")
        
        if params is None:
            params = {}
        
        command = CDPCommand(method, params)
        
        # Create future for response
        response_future = asyncio.Future()
        self.pending_commands[command.id] = response_future
        
        try:
            # Send command
            await self.websocket.send(command.to_json())
            self.logger.debug(f"Sent CDP command: {method}")
            
            # Wait for response
            response_data = await asyncio.wait_for(response_future, timeout=timeout)
            response = CDPResponse.from_json(response_data)
            
            self.logger.debug(f"Received CDP response for {method}")
            return response
            
        except asyncio.TimeoutError:
            raise CDPError(f"CDP command {method} timed out after {timeout}s")
        except Exception as e:
            raise CDPError(f"Failed to send CDP command {method}: {str(e)}")
        finally:
            # Clean up pending command
            self.pending_commands.pop(command.id, None)
    
    def add_event_handler(self, event_name: str, handler: Callable[[Dict[str, Any]], None]):
        """Add handler for CDP events"""
        if event_name not in self.event_handlers:
            self.event_handlers[event_name] = []
        self.event_handlers[event_name].append(handler)
    
    def remove_event_handler(self, event_name: str, handler: Callable):
        """Remove event handler"""
        if event_name in self.event_handlers:
            try:
                self.event_handlers[event_name].remove(handler)
            except ValueError:
                pass
    
    async def _get_websocket_url(self) -> Optional[str]:
        """Get WebSocket URL from Chrome DevTools JSON endpoint"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://{self.host}:{self.port}/json") as response:
                    if response.status == 200:
                        tabs = await response.json()
                        if tabs:
                            # Use first available tab
                            return tabs[0].get("webSocketDebuggerUrl")
            return None
        except Exception as e:
            self.logger.error(f"Failed to get WebSocket URL: {str(e)}")
            return None
    
    async def _listen_for_messages(self):
        """Listen for incoming CDP messages"""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    
                    # Handle command responses
                    if "id" in data:
                        command_id = data["id"]
                        if command_id in self.pending_commands:
                            future = self.pending_commands[command_id]
                            if not future.done():
                                future.set_result(message)
                    
                    # Handle events
                    elif "method" in data:
                        method = data["method"]
                        params = data.get("params", {})
                        
                        # Trigger event handlers
                        if method in self.event_handlers:
                            for handler in self.event_handlers[method]:
                                try:
                                    handler(params)
                                except Exception as e:
                                    self.logger.error(f"Event handler error for {method}: {e}")
                        
                        self.logger.debug(f"Received CDP event: {method}")
                
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse CDP message: {e}")
                except Exception as e:
                    self.logger.error(f"Error processing CDP message: {e}")
        
        except websockets.exceptions.ConnectionClosed:
            self.logger.info("CDP WebSocket connection closed")
        except Exception as e:
            self.logger.error(f"Error in CDP message listener: {e}")
        finally:
            self._connected = False


class BrowserCDPManager:
    """High-level manager for browser CDP operations"""
    
    def __init__(self, host: str = "localhost", port: int = 9222):
        self.cdp = CDPSessionManager(host, port)
        self.logger = logging.getLogger(__name__)
        
    async def connect(self) -> bool:
        """Connect to browser"""
        return await self.cdp.connect()
    
    async def disconnect(self):
        """Disconnect from browser"""
        await self.cdp.disconnect()
    
    async def navigate_to(self, url: str) -> bool:
        """Navigate to URL"""
        try:
            response = await self.cdp.send_command("Page.navigate", {"url": url})
            return response.is_success()
        except Exception as e:
            self.logger.error(f"Navigation failed: {e}")
            return False
    
    async def get_page_info(self) -> Dict[str, Any]:
        """Get current page information"""
        try:
            # Get URL
            url_response = await self.cdp.send_command("Target.getTargets")
            current_url = "unknown"
            if url_response.is_success():
                targets = url_response.get_result().get("targetInfos", [])
                for target in targets:
                    if target.get("type") == "page":
                        current_url = target.get("url", "unknown")
                        break
            
            # Get title
            title_response = await self.cdp.send_command("Runtime.evaluate", {
                "expression": "document.title"
            })
            title = "unknown"
            if title_response.is_success():
                result = title_response.get_result()
                if result and "value" in result:
                    title = result["value"]
            
            return {
                "url": current_url,
                "title": title,
                "timestamp": time.time()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get page info: {e}")
            return {"url": "error", "title": "error", "timestamp": time.time()}
    
    async def take_screenshot(self) -> Optional[bytes]:
        """Take screenshot of current page"""
        try:
            response = await self.cdp.send_command("Page.captureScreenshot", {
                "format": "png",
                "quality": 80
            })
            
            if response.is_success():
                result = response.get_result()
                if "data" in result:
                    import base64
                    return base64.b64decode(result["data"])
            
            return None
            
        except Exception as e:
            self.logger.error(f"Screenshot failed: {e}")
            return None
    
    async def execute_javascript(self, expression: str) -> Any:
        """Execute JavaScript in the page"""
        try:
            response = await self.cdp.send_command("Runtime.evaluate", {
                "expression": expression,
                "returnByValue": True
            })
            
            if response.is_success():
                result = response.get_result()
                return result.get("value")
            else:
                raise CDPError(f"JavaScript execution failed: {response.error}")
                
        except Exception as e:
            self.logger.error(f"JavaScript execution failed: {e}")
            raise
    
    async def get_browser_state(self) -> Dict[str, Any]:
        """Get comprehensive browser state"""
        try:
            page_info = await self.get_page_info()
            
            # Get cookies
            cookies_response = await self.cdp.send_command("Network.getCookies")
            cookies = []
            if cookies_response.is_success():
                cookies = cookies_response.get_result().get("cookies", [])
            
            # Get local storage (if possible)
            local_storage = {}
            try:
                ls_response = await self.execute_javascript(
                    "JSON.stringify(Object.fromEntries(Object.entries(localStorage)))"
                )
                if ls_response:
                    local_storage = json.loads(ls_response)
            except:
                pass  # Local storage access might fail
            
            return {
                "page_info": page_info,
                "cookies": cookies,
                "local_storage": local_storage,
                "timestamp": time.time()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get browser state: {e}")
            return {"error": str(e), "timestamp": time.time()}