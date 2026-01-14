"""
Antigravity OAuth Client for Agent-Zero

This module provides Google Pro subscription access via the Cloudcode/Antigravity API,

"""

import os
import json
import time
import logging
import webbrowser
from pathlib import Path
from typing import Optional, Generator, List, Dict, Any, Callable, Tuple
from urllib.parse import urlencode

import requests
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

from python.helpers import dotenv

logger = logging.getLogger(__name__)

# OAuth Configuration
SCOPES = [
    'https://www.googleapis.com/auth/cloud-platform',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/cclog',
    'https://www.googleapis.com/auth/experimentsandconfigs'
]

# Antigravity API Configuration
ANTIGRAVITY_ENDPOINTS = [
    'https://daily-cloudcode-pa.sandbox.googleapis.com',      # dev
    'https://autopush-cloudcode-pa.sandbox.googleapis.com',   # staging
    'https://cloudcode-pa.googleapis.com'                     # prod
]
ANTIGRAVITY_API_VERSION = 'v1internal'
ANTIGRAVITY_HEADERS = {
    'User-Agent': 'google-api-nodejs-client/9.15.1',
    'X-Goog-Api-Client': 'google-cloud-sdk vscode_cloudshelleditor/0.1',
}
ANTIGRAVITY_DEFAULT_PROJECT_ID = 'rising-fact-p41fc'

# Token cache location
TOKEN_CACHE_DIR = Path.home() / '.agent-zero'
TOKEN_CACHE_FILE = TOKEN_CACHE_DIR / 'token.json'


def get_client_config() -> Dict[str, Any]:
    """Build OAuth client config from environment variables."""
    client_id = dotenv.get_dotenv_value("GOOGLE_CLIENT_ID")
    client_secret = dotenv.get_dotenv_value("GOOGLE_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        raise ValueError(
            "OAuth credentials not configured. "
            "Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in settings or .env file."
        )
    
    return {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost:8080/", "urn:ietf:wg:oauth:2.0:oob"]
        }
    }


def load_cached_credentials() -> Optional[Credentials]:
    """Load cached OAuth credentials from disk."""
    if not TOKEN_CACHE_FILE.exists():
        return None
    
    try:
        creds = Credentials.from_authorized_user_file(str(TOKEN_CACHE_FILE), SCOPES)
        
        # Refresh if expired
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            save_credentials(creds)
        
        return creds if creds and creds.valid else None
    except Exception as e:
        logger.warning(f"Failed to load cached credentials: {e}")
        return None


def save_credentials(creds: Credentials) -> None:
    """Save OAuth credentials to disk."""
    TOKEN_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(TOKEN_CACHE_FILE, 'w') as f:
        f.write(creds.to_json())
    
    logger.info(f"Credentials saved to {TOKEN_CACHE_FILE}")


def clear_credentials() -> bool:
    """Clear cached OAuth credentials."""
    if TOKEN_CACHE_FILE.exists():
        TOKEN_CACHE_FILE.unlink()
        return True
    return False


def authenticate() -> Credentials:
    """
    Run OAuth flow for authentication.
    Uses console-based flow that works in Docker/headless environments.
    Prints auth URL and accepts authorization code.
    """
    # Check for cached credentials first
    creds = load_cached_credentials()
    if creds:
        logger.info("Using cached credentials")
        return creds
    
    # Build OAuth flow
    client_config = get_client_config()
    flow = InstalledAppFlow.from_client_config(
        client_config, 
        SCOPES,
        redirect_uri='urn:ietf:wg:oauth:2.0:oob'  # Out-of-band flow for console
    )
    
    # Generate auth URL
    auth_url, _ = flow.authorization_url(
        prompt='consent',
        access_type='offline'
    )
    
    print("\n" + "=" * 60)
    print("🔐 GOOGLE AUTHENTICATION REQUIRED")
    print("=" * 60)
    print("\n📋 Open this URL in your browser:\n")
    print(auth_url)
    print("\n" + "-" * 60)
    print("After signing in, Google will show you an authorization code.")
    print("Copy that code and paste it below:")
    print("-" * 60 + "\n")
    
    code = input("Authorization code: ").strip()
    
    # Exchange code for credentials
    flow.fetch_token(code=code)
    creds = flow.credentials
    
    # Save for future use
    save_credentials(creds)
    
    # Get user info
    user_info = get_user_info(creds.token)
    if user_info:
        print(f"\n✅ Authenticated as: {user_info.get('email', 'Unknown')}\n")
    
    return creds


def get_user_info(access_token: str) -> Optional[Dict[str, Any]]:
    """Get user info from Google."""
    try:
        response = requests.get(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        logger.warning(f"Failed to get user info: {e}")
    return None


def get_access_token() -> Optional[str]:
    """Get the current access token, authenticating if needed."""
    creds = load_cached_credentials()
    if not creds:
        creds = authenticate()
    return creds.token if creds else None


def is_authenticated() -> bool:
    """Check if user is authenticated with valid credentials."""
    creds = load_cached_credentials()
    return creds is not None and creds.valid


def generate_auth_url(redirect_uri: str = "http://localhost:50001/oauth_callback") -> str:
    """
    Generate OAuth authorization URL for web-based login.
    
    Args:
        redirect_uri: URL where Google will redirect after authentication
    
    Returns:
        The authorization URL to redirect the user to
    """
    client_id = dotenv.get_dotenv_value("GOOGLE_CLIENT_ID")
    if not client_id:
        raise ValueError("GOOGLE_CLIENT_ID not configured")
    
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': ' '.join(SCOPES),
        'access_type': 'offline',
        'prompt': 'consent'
    }
    
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"


def exchange_code_for_tokens(code: str, redirect_uri: str = "http://localhost:50001/oauth_callback") -> Dict[str, Any]:
    """
    Exchange authorization code for access and refresh tokens.
    
    Args:
        code: Authorization code from Google OAuth callback
        redirect_uri: Must match the redirect_uri used in generate_auth_url
    
    Returns:
        Dict with access_token, refresh_token, etc.
    """
    client_id = dotenv.get_dotenv_value("GOOGLE_CLIENT_ID")
    client_secret = dotenv.get_dotenv_value("GOOGLE_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        raise ValueError("OAuth credentials not configured")
    
    response = requests.post(
        'https://oauth2.googleapis.com/token',
        data={
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }
    )
    
    if not response.ok:
        raise ValueError(f"Token exchange failed: {response.text}")
    
    tokens = response.json()
    
    # Save as credentials
    creds = Credentials(
        token=tokens.get('access_token'),
        refresh_token=tokens.get('refresh_token'),
        token_uri='https://oauth2.googleapis.com/token',
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES
    )
    save_credentials(creds)
    
    return tokens


def get_auth_status() -> Dict[str, Any]:
    """
    Get current authentication status for UI.
    
    Returns:
        Dict with is_authenticated, email, name
    """
    creds = load_cached_credentials()
    if not creds or not creds.valid:
        return {'is_authenticated': False}
    
    user_info = get_user_info(creds.token)
    return {
        'is_authenticated': True,
        'email': user_info.get('email') if user_info else None,
        'name': user_info.get('name') if user_info else None
    }


class AntigravityClient:
    """
    Client for the Cloudcode/Antigravity API.
    Handles project context and content generation.
    """
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.project_id: Optional[str] = None
        self._project_context_cached = False
    
    def _get_headers(self) -> Dict[str, str]:
        """Build request headers."""
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            **ANTIGRAVITY_HEADERS,
            'Client-Metadata': json.dumps({
                'ideType': 'IDE_UNSPECIFIED',
                'platform': 'PLATFORM_UNSPECIFIED',
                'pluginType': 'GEMINI'
            })
        }
    
    def load_project_context(self) -> str:
        """
        Call loadCodeAssist API to get project ID.
        Falls back to default project if API fails.
        """
        if self._project_context_cached and self.project_id:
            return self.project_id
        
        metadata = {
            'ideType': 'IDE_UNSPECIFIED',
            'platform': 'PLATFORM_UNSPECIFIED',
            'pluginType': 'GEMINI'
        }
        
        for endpoint in ANTIGRAVITY_ENDPOINTS:
            url = f"{endpoint}/{ANTIGRAVITY_API_VERSION}:loadCodeAssist"
            logger.info(f"Calling loadCodeAssist: {url}")
            
            try:
                response = requests.post(
                    url,
                    headers=self._get_headers(),
                    json={'metadata': metadata},
                    timeout=10
                )
                
                if not response.ok:
                    logger.warning(f"loadCodeAssist failed: {response.status_code}")
                    continue
                
                data = response.json()
                logger.info(f"loadCodeAssist response: {json.dumps(data, indent=2)}")
                
                # Extract project ID
                project_id = data.get('cloudaicompanionProject')
                if isinstance(project_id, dict):
                    project_id = project_id.get('id')
                
                if project_id:
                    self.project_id = project_id
                    self._project_context_cached = True
                    return project_id
                
                # Try onboarding if no project
                if data.get('allowedTiers'):
                    tier_id = data.get('currentTier', {}).get('id') or \
                              data.get('allowedTiers', [{}])[0].get('id') or 'free-tier'
                    
                    onboard_url = f"{endpoint}/{ANTIGRAVITY_API_VERSION}:onboardUser"
                    onboard_response = requests.post(
                        onboard_url,
                        headers=self._get_headers(),
                        json={'tierId': tier_id, 'metadata': metadata},
                        timeout=10
                    )
                    
                    if onboard_response.ok:
                        onboard_data = onboard_response.json()
                        managed_id = onboard_data.get('response', {}).get('cloudaicompanionProject', {}).get('id')
                        if onboard_data.get('done') and managed_id:
                            self.project_id = managed_id
                            self._project_context_cached = True
                            return managed_id
            
            except requests.RequestException as e:
                logger.warning(f"loadCodeAssist error: {e}")
                continue
        
        # Fallback to default project
        logger.warning(f"Using fallback project: {ANTIGRAVITY_DEFAULT_PROJECT_ID}")
        self.project_id = ANTIGRAVITY_DEFAULT_PROJECT_ID
        self._project_context_cached = True
        return self.project_id
    
    def generate_content(
        self,
        contents: List[Dict[str, Any]],
        model: str = 'gemini-3-flash-preview',
        temperature: float = 0.7,
        system_instruction: Optional[str] = None
    ) -> str:
        """
        Generate content from Antigravity API (non-streaming).
        Returns the full response text.
        """
        full_response = ""
        for chunk in self.generate_content_stream(
            contents=contents,
            model=model,
            temperature=temperature,
            system_instruction=system_instruction
        ):
            full_response += chunk
        return full_response
    
    def generate_content_stream(
        self,
        contents: List[Dict[str, Any]],
        model: str = 'gemini-3-flash-preview',
        temperature: float = 0.7,
        system_instruction: Optional[str] = None
    ) -> Generator[str, None, None]:
        """
        Stream content generation from Antigravity API.
        Yields text chunks as they arrive.
        """
        import uuid
        
        project_id = self.load_project_context()
        request_id = f"agent-zero-{uuid.uuid4()}"
        
        # Build request body
        body = {
            'project': project_id,
            'model': model,
            'userAgent': 'agent-zero',
            'requestId': request_id,
            'request': {
                'contents': contents,
                'generationConfig': {
                    'temperature': temperature
                }
            }
        }
        
        if system_instruction:
            body['request']['systemInstruction'] = {
                'parts': [{'text': system_instruction}]
            }
        
        # Try endpoints in order
        GCP_PERMISSION_ERROR_PATTERNS = [
            'PERMISSION_DENIED',
            'does not have permission',
            'Cloud AI Companion API has not been used',
            'has not been enabled'
        ]
        
        for endpoint in ANTIGRAVITY_ENDPOINTS:
            api_url = f"{endpoint}/v1internal:streamGenerateContent?alt=sse"
            logger.info(f"Trying endpoint: {endpoint}")
            
            max_retries = 10
            for attempt in range(max_retries):
                try:
                    response = requests.post(
                        api_url,
                        headers={
                            **self._get_headers(),
                            'Accept': 'text/event-stream'
                        },
                        json=body,
                        stream=True,
                        timeout=60
                    )
                    
                    if response.ok:
                        logger.info(f"✅ Success with: {endpoint}")
                        
                        # Process SSE stream
                        for line in response.iter_lines(decode_unicode=True):
                            if line and line.startswith('data: '):
                                data = line[6:]
                                if data == '[DONE]':
                                    return
                                
                                try:
                                    parsed = json.loads(data)
                                    # Unwrap Antigravity response
                                    unwrapped = parsed.get('response', parsed)
                                    parts = unwrapped.get('candidates', [{}])[0].get('content', {}).get('parts', [])
                                    
                                    for part in parts:
                                        if 'text' in part:
                                            yield part['text']
                                except json.JSONDecodeError:
                                    continue
                        return
                    
                    # Handle permission errors with retry
                    if response.status_code == 403:
                        error_text = response.text
                        if any(p in error_text for p in GCP_PERMISSION_ERROR_PATTERNS):
                            if attempt < max_retries - 1:
                                delay = min(200 * (2 ** attempt), 2000) / 1000
                                logger.info(f"GCP permission error, retry {attempt + 1}/{max_retries}")
                                time.sleep(delay)
                                continue
                    
                    logger.warning(f"Request failed: {response.status_code}")
                    break
                
                except requests.RequestException as e:
                    logger.error(f"Network error: {e}")
                    break
        
        raise Exception("All Antigravity endpoints failed")


# Singleton client instance
_client: Optional[AntigravityClient] = None


def get_client() -> AntigravityClient:
    """Get or create the Antigravity client singleton."""
    global _client
    
    access_token = get_access_token()
    if not access_token:
        raise ValueError("No OAuth credentials available. Please authenticate first.")
    
    if _client is None or _client.access_token != access_token:
        _client = AntigravityClient(access_token)
    
    return _client


def generate_content(
    messages: List[Dict[str, Any]],
    model: str = 'gemini-3-flash-preview',
    temperature: float = 0.7,
    system_instruction: Optional[str] = None
) -> str:
    """
    Convenience function to generate content via Antigravity API.
    
    Args:
        messages: List of message dicts with 'role' and 'content' keys
        model: Model name (default: gemini-3-flash-preview)
        temperature: Temperature for generation
        system_instruction: Optional system instruction
    
    Returns:
        Generated text response
    """
    client = get_client()
    
    # Convert messages to Antigravity format
    contents = []
    for msg in messages:
        role = 'user' if msg.get('role') in ('user', 'human') else 'model'
        contents.append({
            'role': role,
            'parts': [{'text': msg.get('content', '')}]
        })
    
    return client.generate_content(
        contents=contents,
        model=model,
        temperature=temperature,
        system_instruction=system_instruction
    )


def generate_content_stream(
    messages: List[Dict[str, Any]],
    model: str = 'gemini-3-flash-preview',
    temperature: float = 0.7,
    system_instruction: Optional[str] = None
) -> Generator[str, None, None]:
    """
    Convenience function to stream content via Antigravity API.
    
    Args:
        messages: List of message dicts with 'role' and 'content' keys
        model: Model name (default: gemini-3-flash-preview)
        temperature: Temperature for generation
        system_instruction: Optional system instruction
    
    Yields:
        Text chunks as they arrive
    """
    client = get_client()
    
    # Convert messages to Antigravity format
    contents = []
    for msg in messages:
        role = 'user' if msg.get('role') in ('user', 'human') else 'model'
        contents.append({
            'role': role,
            'parts': [{'text': msg.get('content', '')}]
        })
    
    yield from client.generate_content_stream(
        contents=contents,
        model=model,
        temperature=temperature,
        system_instruction=system_instruction
    )
