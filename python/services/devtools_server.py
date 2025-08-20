#!/usr/bin/env python3
"""
DevTools Frontend Server for Manual Browser Control

This server provides a web interface that proxies Chrome DevTools,
allowing manual browser control through Agent Zero's UI.
"""

import http.server
import socketserver
import json
import urllib.request
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DevToolsHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler that serves DevTools frontend and proxies requests to Chrome."""
    
    def __init__(self, *args, cdp_port=9222, **kwargs):
        self.cdp_port = cdp_port
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests - serve DevTools UI or proxy to Chrome."""
        if self.path == '/':
            self.send_devtools_page()
        elif self.path.startswith('/devtools'):
            # Proxy DevTools requests to Chrome
            self.proxy_to_chrome()
        else:
            super().do_GET()
    
    def send_devtools_page(self):
        """Send the main DevTools interface page."""
        try:
            # Get available tabs from Chrome
            with urllib.request.urlopen(f'http://localhost:{self.cdp_port}/json') as response:
                tabs = json.loads(response.read())
            
            # Find the first page tab
            tab_url = None
            for tab in tabs:
                if tab.get('type') == 'page':
                    devtools_url = tab.get('devtoolsFrontendUrl')
                    if devtools_url:
                        # Convert to full URL
                        tab_url = f"http://localhost:{self.cdp_port}{devtools_url}"
                        break
            
            if not tab_url:
                # No suitable tab found, show error
                html = self._get_error_page("No browser tabs available for control.", 
                                          "Please open a browser tab first.")
            else:
                # Create DevTools interface
                html = self._get_devtools_page(tab_url)
            
            self._send_html_response(html, 200)
            
        except Exception as e:
            logger.error(f"Error serving DevTools page: {e}")
            error_html = self._get_error_page("Browser Control Error", 
                                            f"Could not connect to browser: {str(e)}")
            self._send_html_response(error_html, 500)
    
    def _get_devtools_page(self, tab_url):
        """Generate the main DevTools interface HTML."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Browser Control - Agent Zero</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ 
                    margin: 0; 
                    padding: 0; 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: #1e1e1e;
                    color: #ffffff;
                }}
                .header {{ 
                    background: #2c3e50; 
                    color: white; 
                    padding: 12px 20px; 
                    border-bottom: 1px solid #34495e;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }}
                .header h3 {{ 
                    margin: 0; 
                    font-size: 16px; 
                    font-weight: 600;
                }}
                .controls {{ 
                    background: #34495e; 
                    padding: 8px 20px; 
                    text-align: center;
                    border-bottom: 1px solid #4a5a6a;
                }}
                .controls button {{ 
                    background: #3498db; 
                    color: white; 
                    border: none; 
                    padding: 6px 12px; 
                    margin: 0 6px; 
                    border-radius: 4px;
                    cursor: pointer; 
                    font-size: 14px;
                    transition: background-color 0.2s;
                }}
                .controls button:hover {{ 
                    background: #2980b9; 
                }}
                .controls .info {{ 
                    color: #bdc3c7; 
                    margin-left: 20px; 
                    font-size: 14px;
                }}
                iframe {{ 
                    width: 100vw; 
                    height: calc(100vh - 80px); 
                    border: none; 
                    display: block;
                }}
                .status {{ 
                    position: absolute; 
                    top: 15px; 
                    right: 20px; 
                    background: #27ae60; 
                    color: white; 
                    padding: 4px 8px; 
                    border-radius: 12px; 
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h3>🤖 Agent Zero - Manual Browser Control</h3>
                <div class="status">Connected</div>
            </div>
            <div class="controls">
                <button onclick="refreshDevTools()">🔄 Refresh DevTools</button>
                <button onclick="openNewTab()">📄 New Tab</button>
                <button onclick="window.close()">❌ Close</button>
                <span class="info">Use Chrome DevTools below to control the browser manually</span>
            </div>
            <iframe 
                src="{tab_url}" 
                allow="camera; microphone; clipboard-read; clipboard-write; cross-origin-isolated"
                sandbox="allow-same-origin allow-scripts allow-forms allow-popups allow-top-navigation allow-downloads"
            ></iframe>
            <script>
                function refreshDevTools() {{
                    location.reload();
                }}
                
                function openNewTab() {{
                    fetch('http://localhost:{self.cdp_port}/json/new?about:blank', {{
                        method: 'POST'
                    }})
                    .then(() => {{
                        setTimeout(() => location.reload(), 1000);
                    }})
                    .catch(err => {{
                        console.error('Failed to open new tab:', err);
                        alert('Failed to open new tab. Check browser connection.');
                    }});
                }}
                
                // Auto-refresh every 30 seconds to stay connected
                setTimeout(() => {{
                    location.reload();
                }}, 30000);
            </script>
        </body>
        </html>
        """
    
    def _get_error_page(self, title, message):
        """Generate an error page HTML."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{title}</title>
            <meta charset="utf-8">
            <style>
                body {{ 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: #1e1e1e; 
                    color: #ffffff; 
                    padding: 40px; 
                    text-align: center;
                }}
                .error-container {{
                    max-width: 500px;
                    margin: 0 auto;
                    background: #2c3e50;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.3);
                }}
                h1 {{ color: #e74c3c; margin-bottom: 20px; }}
                p {{ color: #bdc3c7; line-height: 1.6; }}
                button {{
                    background: #3498db;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 4px;
                    cursor: pointer;
                    margin-top: 20px;
                }}
                button:hover {{ background: #2980b9; }}
            </style>
        </head>
        <body>
            <div class="error-container">
                <h1>🚫 {title}</h1>
                <p>{message}</p>
                <button onclick="location.reload()">🔄 Retry</button>
                <button onclick="window.close()">❌ Close</button>
            </div>
        </body>
        </html>
        """
    
    def _send_html_response(self, html, status_code):
        """Send an HTML response with proper headers."""
        self.send_response(status_code)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.send_header('Content-length', str(len(html.encode('utf-8'))))
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def proxy_to_chrome(self):
        """Proxy DevTools requests to Chrome CDP."""
        target_url = f"http://localhost:{self.cdp_port}" + self.path
        try:
            with urllib.request.urlopen(target_url) as response:
                self.send_response(response.status)
                for header, value in response.headers.items():
                    if header.lower() not in ['content-encoding', 'transfer-encoding']:
                        self.send_header(header, value)
                self.end_headers()
                self.wfile.write(response.read())
        except Exception as e:
            logger.error(f"Proxy error: {e}")
            self.send_error(502, f"Proxy error: {e}")
    
    def log_message(self, format, *args):
        """Override to use proper logging."""
        logger.info(format % args)


class DevToolsServer:
    """DevTools frontend server for manual browser control."""
    
    def __init__(self, port=9223, cdp_port=9222):
        self.port = port
        self.cdp_port = cdp_port
        self.httpd = None
    
    def start(self):
        """Start the DevTools server."""
        try:
            # Create handler with CDP port configuration
            handler_class = lambda *args, **kwargs: DevToolsHandler(*args, cdp_port=self.cdp_port, **kwargs)
            
            self.httpd = socketserver.TCPServer(("", self.port), handler_class)
            self.httpd.allow_reuse_address = True
            
            logger.info(f"DevTools frontend server started at http://localhost:{self.port}")
            logger.info(f"Proxying to Chrome CDP at localhost:{self.cdp_port}")
            
            return f"http://localhost:{self.port}"
            
        except Exception as e:
            logger.error(f"Failed to start DevTools server: {e}")
            raise
    
    def serve_forever(self):
        """Start serving requests (blocking)."""
        if self.httpd:
            try:
                self.httpd.serve_forever()
            except KeyboardInterrupt:
                logger.info("DevTools server stopped by user")
            finally:
                self.stop()
    
    def stop(self):
        """Stop the DevTools server."""
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
            self.httpd = None
            logger.info("DevTools server stopped")


def main():
    """Run the DevTools server standalone."""
    import argparse
    
    parser = argparse.ArgumentParser(description='DevTools Frontend Server for Agent Zero')
    parser.add_argument('--port', type=int, default=9223, help='Server port (default: 9223)')
    parser.add_argument('--cdp-port', type=int, default=9222, help='Chrome CDP port (default: 9222)')
    
    args = parser.parse_args()
    
    server = DevToolsServer(port=args.port, cdp_port=args.cdp_port)
    server.start()
    server.serve_forever()


if __name__ == "__main__":
    main()