import pytest
import time
import json
from unittest.mock import MagicMock, patch
from python.helpers.security import SecurityManager, SecurityVaultManager
from python.helpers.proactive import ProactiveManager

class TestSecurityIdentity:

    @pytest.fixture(autouse=True)
    def setup_security(self):
        # Reset state before each test
        SecurityManager._authorized_sessions = {}
        SecurityManager._rate_limits = {}
        SecurityManager.ENFORCE_PASSKEY = True

    def test_tool_authorization_unauthorized(self):
        """Test that high-risk tools are blocked when not authorized."""
        tool = "run_in_terminal"
        assert SecurityManager.is_tool_authorized(tool, user_id="test_user") is False

    def test_tool_authorization_authorized(self):
        """Test that high-risk tools are allowed after authorization."""
        user_id = "test_user"
        SecurityManager.set_authorized(user_id)
        assert SecurityManager.is_tool_authorized("run_in_terminal", user_id=user_id) is True

    def test_panic_lock(self):
        """Test that panic lock revokes authorization."""
        user_id = "test_user"
        SecurityManager.set_authorized(user_id)
        assert SecurityManager.is_tool_authorized("email", user_id=user_id) is True
        
        SecurityManager.panic_lock(user_id)
        assert SecurityManager.is_tool_authorized("email", user_id=user_id) is False

    def test_rate_limiter(self):
        """Test simple rate limiting logic."""
        from flask import Flask
        app = Flask(__name__)
        # Ensure rate limits are clear for test
        SecurityManager._rate_limits = {}
        
        with app.test_request_context(environ_base={'REMOTE_ADDR': '127.0.0.1'}):
            # Allow 3 attempts in 60s
            for i in range(3):
                result = SecurityManager.check_rate_limit("test_action", limit=3)
                assert result is True
            
            # 4th attempt should fail
            assert SecurityManager.check_rate_limit("test_action", limit=3) is False

    def test_heuristic_velocity(self):
        """Test the anomaly detection velocity check."""
        SecurityManager._action_history = []
        # Simulate 15 quick actions
        for _ in range(15):
            assert SecurityManager.check_heuristics("test_user") is True
        
        # 16th should trigger panic lock and return False
        assert SecurityManager.check_heuristics("test_user") is False
        # Verify user is now unauthorized
        assert SecurityManager.is_tool_authorized("run_in_terminal", user_id="test_user") is False

    def test_zero_knowledge_vault(self):
        """Test the cryptographic encryption/decryption of the storage vault."""
        secret_data = "Super Secret API Key 12345"
        encrypted = SecurityManager.encrypt_data(secret_data)
        assert encrypted != secret_data
        
        decrypted = SecurityManager.decrypt_data(encrypted)
        assert decrypted == secret_data

    def test_network_sentinel(self):
        """Test the network sentinel detection logic."""
        # Safe tool call
        assert SecurityManager.check_network_sentinel("bash", {"command": "ls -la"}) is True
        
        # Suspicious tool call (curl/external access)
        assert SecurityManager.check_network_sentinel("run_in_terminal", {"command": "curl http://example.com"}) is False
        assert SecurityManager.check_network_sentinel("run_command", {"args": "wget 1.2.3.4"}) is False

    def test_vault_secrets(self, tmp_path):
        """Test vault storage and retrieval using a temporary path."""
        vault_file = tmp_path / "vault.json"
        with patch.object(SecurityVaultManager, 'VAULT_PATH', str(vault_file)):
            SecurityVaultManager.set_secret("test_key", "test_value")
            assert SecurityVaultManager.get_secret("test_key") == "test_value"
            assert SecurityVaultManager.get_secret("missing_key") is None

    @patch('python.helpers.proactive.webpush')
    @patch('python.helpers.proactive.WorkflowEngineDatabase')
    def test_proactive_push_trigger(self, mock_db, mock_webpush):
        """Test that proactive notifications trigger the webpush library."""
        ProactiveManager.ENABLED = True
        
        # Mock database response for subscription
        mock_conn = MagicMock()
        mock_db.return_value._get_conn.return_value = mock_conn
        mock_cursor = mock_conn.cursor.return_value
        mock_cursor.fetchone.return_value = ['{"endpoint": "test"}']
        
        success = ProactiveManager.send_push("test_user", "Title", "Body")
        
        assert success is True
        assert mock_webpush.called
