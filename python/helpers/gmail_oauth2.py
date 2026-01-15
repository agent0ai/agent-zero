"""
Gmail API OAuth2 Authentication Handler
Manages OAuth2 credentials and token refresh for Gmail API access
"""

import os
import json
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import pickle
import base64

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow, Flow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    # Graceful degradation if google libraries not installed
    Request = None
    Credentials = None
    InstalledAppFlow = None
    Flow = None
    build = None
    HttpError = Exception


class GmailOAuth2Handler:
    """Handles OAuth2 authentication for Gmail API"""
    
    # Gmail API scopes
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.modify',
        'https://www.googleapis.com/auth/gmail.labels',
        'https://www.googleapis.com/auth/gmail.compose'
    ]
    
    def __init__(self, credentials_dir: str = "data/gmail_credentials"):
        """
        Initialize OAuth2 handler
        
        Args:
            credentials_dir: Directory to store OAuth2 credentials and tokens
        """
        self.credentials_dir = Path(credentials_dir)
        self.credentials_dir.mkdir(parents=True, exist_ok=True)
        self.accounts = {}  # account_name -> credentials
        self._load_all_accounts()
    
    def _load_all_accounts(self):
        """Load all saved account credentials"""
        for token_file in self.credentials_dir.glob("token_*.pickle"):
            account_name = token_file.stem.replace("token_", "")
            try:
                creds = self._load_credentials(account_name)
                if creds:
                    self.accounts[account_name] = creds
            except Exception as e:
                print(f"Warning: Failed to load credentials for {account_name}: {e}")
    
    def _get_token_path(self, account_name: str) -> Path:
        """Get path to token file for account"""
        return self.credentials_dir / f"token_{account_name}.pickle"
    
    def _load_credentials(self, account_name: str) -> Optional[Credentials]:
        """
        Load credentials for a specific account
        
        Args:
            account_name: Name/identifier for the account
            
        Returns:
            Credentials object or None
        """
        if Credentials is None:
            raise ImportError("Google OAuth2 libraries not installed. Run: pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client")
        
        token_path = self.credentials_dir / f"token_{account_name}.pickle"
        
        if not token_path.exists():
            return None
        
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
        
        # Refresh if expired
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                self._save_credentials(account_name, creds)
            except Exception as e:
                print(f"Failed to refresh credentials for {account_name}: {e}")
                return None
        
        return creds
    
    def _save_credentials(self, account_name: str, creds: Credentials):
        """
        Save credentials for an account
        
        Args:
            account_name: Name/identifier for the account
            creds: Credentials object to save
        """
        token_path = self.credentials_dir / f"token_{account_name}.pickle"
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)
    
    def _get_token_path(self, account_name: str) -> Path:
        """Get path to token file for an account"""
        return self.credentials_dir / f"token_{account_name}.pickle"
    
    def get_authorization_url(self, credentials_json: str, state: str, redirect_uri: str = None) -> str:
        """
        Get OAuth2 authorization URL for web-based flow
        
        Args:
            credentials_json: Path to credentials.json or JSON string content
            state: CSRF protection token
            redirect_uri: OAuth2 callback URL (defaults to current server + /gmail_oauth_callback)
            
        Returns:
            Authorization URL to redirect user to
        """
        if Flow is None:
            raise ImportError("Google OAuth2 libraries not installed")
        
        # Parse credentials_json (can be path or JSON string)
        if os.path.exists(credentials_json):
            flow = Flow.from_client_secrets_file(
                credentials_json,
                scopes=self.SCOPES,
                state=state
            )
        else:
            # Assume it's JSON content
            import json
            client_config = json.loads(credentials_json)
            flow = Flow.from_client_config(
                client_config,
                scopes=self.SCOPES,
                state=state
            )
        
        # Set redirect URI
        if not redirect_uri:
            # Use current Flask server + callback endpoint
            from python.helpers import runtime
            host = runtime.get_web_ui_host() or "localhost"
            port = runtime.get_web_ui_port()
            redirect_uri = f"http://{host}:{port}/gmail_oauth_callback"
        
        flow.redirect_uri = redirect_uri
        
        # Generate authorization URL
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'  # Force consent screen to get refresh token
        )
        
        return auth_url
    
    def complete_authorization(self, account_name: str, credentials_json: str, 
                              authorization_code: str, state: str, 
                              redirect_uri: str = None) -> str:
        """
        Complete OAuth2 authorization and save credentials
        
        Args:
            account_name: Name/identifier for the account
            credentials_json: Path to credentials.json or JSON string content
            authorization_code: Authorization code from OAuth2 callback
            state: CSRF protection token
            redirect_uri: OAuth2 callback URL (must match initial request)
            
        Returns:
            Email address of authenticated account
        """
        if Flow is None:
            raise ImportError("Google OAuth2 libraries not installed")
        
        # Parse credentials_json (can be path or JSON string)
        if os.path.exists(credentials_json):
            flow = Flow.from_client_secrets_file(
                credentials_json,
                scopes=self.SCOPES,
                state=state
            )
        else:
            # Assume it's JSON content
            import json
            client_config = json.loads(credentials_json)
            flow = Flow.from_client_config(
                client_config,
                scopes=self.SCOPES,
                state=state
            )
        
        # Set redirect URI
        if not redirect_uri:
            from python.helpers import runtime
            host = runtime.get_web_ui_host() or "localhost"
            port = runtime.get_web_ui_port()
            redirect_uri = f"http://{host}:{port}/gmail_oauth_callback"
        
        flow.redirect_uri = redirect_uri
        
        # Exchange authorization code for credentials
        flow.fetch_token(code=authorization_code)
        creds = flow.credentials
        
        # Save credentials
        self._save_credentials(account_name, creds)
        self.accounts[account_name] = creds
        
        # Get email address
        email = self._get_account_email(account_name)
        
        return email
    
    def authenticate_account(self, account_name: str, credentials_json_path: str = None) -> Dict:
        """
        Authenticate a Gmail account via OAuth2
        
        Args:
            account_name: Name/identifier for the account (e.g., "sales", "support")
            credentials_json_path: Path to credentials.json from Google Cloud Console
            
        Returns:
            Dict with authentication status
        """
        if InstalledAppFlow is None:
            return {
                "success": False,
                "error": "Google OAuth2 libraries not installed",
                "install_command": "pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client"
            }
        
        # Check for existing credentials
        creds = self._load_credentials(account_name)
        
        if not creds or not creds.valid:
            # Use provided credentials.json or look for default
            if not credentials_json_path:
                credentials_json_path = self.credentials_dir / "credentials.json"
            
            if not Path(credentials_json_path).exists():
                return {
                    "success": False,
                    "error": "credentials.json not found",
                    "help": "Download OAuth2 credentials from Google Cloud Console"
                }
            
            try:
                # Start OAuth2 flow
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_json_path, self.SCOPES
                )
                creds = flow.run_local_server(port=0)
                
                # Save credentials
                self._save_credentials(account_name, creds)
                self.accounts[account_name] = creds
                
            except Exception as e:
                return {
                    "success": False,
                    "error": f"OAuth2 authentication failed: {str(e)}"
                }
        
        return {
            "success": True,
            "account_name": account_name,
            "email": self._get_account_email(account_name),
            "scopes": self.SCOPES
        }
    
    def _get_account_email(self, account_name: str) -> Optional[str]:
        """Get email address for authenticated account"""
        try:
            service = self.get_gmail_service(account_name)
            profile = service.users().getProfile(userId='me').execute()
            return profile.get('emailAddress')
        except:
            return None
    
    def get_gmail_service(self, account_name: str):
        """
        Get Gmail API service for an account
        
        Args:
            account_name: Name/identifier for the account
            
        Returns:
            Gmail API service object
        """
        if build is None:
            raise ImportError("Google API libraries not installed")
        
        creds = self.accounts.get(account_name)
        
        if not creds:
            creds = self._load_credentials(account_name)
            if creds:
                self.accounts[account_name] = creds
        
        if not creds or not creds.valid:
            raise ValueError(f"No valid credentials for account: {account_name}")
        
        return build('gmail', 'v1', credentials=creds)
    
    def list_accounts(self) -> List[Dict]:
        """
        List all authenticated accounts
        
        Returns:
            List of account info dicts
        """
        accounts_info = []
        
        for account_name in self.accounts.keys():
            email = self._get_account_email(account_name)
            accounts_info.append({
                "account_name": account_name,
                "email": email,
                "authenticated": True
            })
        
        return accounts_info
    
    def remove_account(self, account_name: str) -> bool:
        """
        Remove account credentials
        
        Args:
            account_name: Name/identifier for the account
            
        Returns:
            True if removed successfully
        """
        token_path = self.credentials_dir / f"token_{account_name}.pickle"
        
        if token_path.exists():
            token_path.unlink()
        
        if account_name in self.accounts:
            del self.accounts[account_name]
        
        return True
    
    def get_account_status(self, account_name: str) -> Dict:
        """
        Get status of an account
        
        Args:
            account_name: Name/identifier for the account
            
        Returns:
            Dict with account status
        """
        try:
            creds = self.accounts.get(account_name) or self._load_credentials(account_name)
            
            if not creds:
                return {
                    "account_name": account_name,
                    "authenticated": False,
                    "valid": False,
                    "error": "No credentials found"
                }
            
            return {
                "account_name": account_name,
                "email": self._get_account_email(account_name),
                "authenticated": True,
                "valid": creds.valid,
                "expired": creds.expired if hasattr(creds, 'expired') else False,
                "has_refresh_token": bool(creds.refresh_token) if hasattr(creds, 'refresh_token') else False,
                "scopes": self.SCOPES
            }
        except Exception as e:
            return {
                "account_name": account_name,
                "authenticated": False,
                "valid": False,
                "error": str(e)
            }
