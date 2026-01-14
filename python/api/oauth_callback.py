from python.helpers.api import ApiHandler, Request, Response
from python.helpers import antigravity


class OAuthCallback(ApiHandler):
    """Handle OAuth callback from Google - exchange code for tokens."""
    
    async def process(self, input: dict, request: Request) -> dict | Response:
        # Get authorization code from query params
        code = request.args.get('code')
        error = request.args.get('error')
        
        if error:
            return Response(
                self._get_close_popup_html(success=False, message=f"OAuth error: {error}"),
                status=200,
                mimetype='text/html'
            )
        
        if not code:
            return Response(
                self._get_close_popup_html(success=False, message="No authorization code received"),
                status=200,
                mimetype='text/html'
            )
        
        try:
            # Exchange code for tokens
            tokens = antigravity.exchange_code_for_tokens(code)
            
            # Get user info for display
            user_info = antigravity.get_user_info(tokens.get('access_token'))
            email = user_info.get('email', 'Unknown') if user_info else 'Unknown'
            
            return Response(
                self._get_close_popup_html(success=True, message=f"Logged in as {email}"),
                status=200,
                mimetype='text/html'
            )
            
        except Exception as e:
            return Response(
                self._get_close_popup_html(success=False, message=str(e)),
                status=200,
                mimetype='text/html'
            )
    
    def _get_close_popup_html(self, success: bool, message: str) -> str:
        """Return HTML that closes popup and notifies parent window."""
        status = "success" if success else "error"
        return f'''<!DOCTYPE html>
<html>
<head>
    <title>Google OAuth - {status.title()}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100vh;
            margin: 0;
            background: {"#1a1a2e" if success else "#2e1a1a"};
            color: white;
        }}
        .container {{
            text-align: center;
            padding: 2rem;
        }}
        .icon {{ font-size: 4rem; margin-bottom: 1rem; }}
        .message {{ font-size: 1.2rem; margin-bottom: 1rem; }}
        .note {{ color: #888; font-size: 0.9rem; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">{"✅" if success else "❌"}</div>
        <div class="message">{message}</div>
        <div class="note">This window will close automatically...</div>
    </div>
    <script>
        // Notify parent window
        if (window.opener) {{
            window.opener.postMessage({{
                type: 'oauth_complete',
                success: {str(success).lower()},
                message: '{message}'
            }}, '*');
        }}
        // Close popup after short delay
        setTimeout(function() {{
            window.close();
        }}, 2000);
    </script>
</body>
</html>'''
    
    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET"]
    
    @classmethod
    def requires_auth(cls) -> bool:
        # OAuth callback must be accessible without auth
        return False
    
    @classmethod
    def requires_csrf(cls) -> bool:
        return False
