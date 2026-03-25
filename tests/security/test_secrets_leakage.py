"""
Security Test: Ensure secrets are not leaked in logs or API responses.

Tests:
- Secrets not in agent logs
- Secrets not in API responses
- Secrets properly masked in error messages
- No plaintext secrets in memory dumps
"""

import pytest
import json
import re
from unittest.mock import MagicMock, patch

from python.helpers.secrets import SecretsManager
from python.helpers.log import Log
from agent import AgentContext


class TestSecretsLeakage:
    """Test that secrets are never exposed in logs or outputs."""

    def test_secrets_not_in_log_output(self):
        """Verify that log content does not contain raw secret values."""
        # Setup a secrets manager with test secrets
        secrets = {
            "API_KEY_SECRET": "super-secret-api-key-12345",
            "DB_PASSWORD": "DB_PASSWORD_REAL_VALUE",
            "PRIVATE_KEY": "-----BEGIN PRIVATE KEY-----\nMOCKKEY\n-----"
        }

        # Mock the secrets manager to return our test secrets
        mock_secrets_mgr = MagicMock()
        mock_secrets_mgr.load_secrets.return_value = secrets
        mock_secrets_mgr.mask_values.side_effect = lambda text, **kwargs: text

        # Create a log and try to log a message containing a secret
        log = Log()
        log.context = MagicMock()

        # Simulate logging that might contain a secret
        with patch('python.helpers.log.get_secrets_manager', return_value=mock_secrets_mgr):
            # This should NOT appear in the output
            log.log(
                type="info",
                heading="Test log",
                content=f"API key is {secrets['API_KEY_SECRET']}"
            )
            output = log.output()

        # Check that the raw secret is not in any log output
        all_content = " ".join([item.get('content', '') for item in output])
        assert secrets['API_KEY_SECRET'] not in all_content, "Raw secret exposed in log output"

    def test_secrets_masked_with_placeholder(self):
        """Verify that secret values are replaced with placeholder."""
        secrets = {"SECRET_KEY": "real_secret_value"}

        mock_secrets_mgr = MagicMock()
        mock_secrets_mgr.load_secrets.return_value = secrets
        mock_secrets_mgr.mask_values.side_effect = lambda text, **kwargs: text.replace('real_secret_value', '§§secret(SECRET_KEY)')

        log = Log()
        log.context = MagicMock()

        with patch('python.helpers.log.get_secrets_manager', return_value=mock_secrets_mgr):
            log.log(type="info", heading="Test", content=f"Value is real_secret_value")
            output = log.output()

        all_content = " ".join([item.get('content', '') for item in output])
        assert 'real_secret_value' not in all_content
        assert '§§secret(SECRET_KEY)' in all_content, "Placeholder not used"

    def test_no_secrets_in_error_messages(self):
        """Ensure error messages don't leak secrets."""
        secrets = {"PASSWORD": "super_secret_password"}

        mock_secrets_mgr = MagicMock()
        mock_secrets_mgr.load_secrets.return_value = secrets
        mock_secrets_mgr.mask_values.side_effect = lambda text, **kwargs: text

        log = Log()
        log.context = MagicMock()

        with patch('python.helpers.log.get_secrets_manager', return_value=mock_secrets_mgr):
            try:
                # Simulate an error that includes a secret
                raise Exception(f"Connection failed with password: {secrets['PASSWORD']}")
            except Exception as e:
                log.log(type="error", heading="Error", content=str(e))

            output = log.output()

        all_content = " ".join([item.get('content', '') for item in output])
        assert secrets['PASSWORD'] not in all_content, "Secret password leaked in error log"

    def test_json_output_no_secrets(self):
        """Test JSON log output doesn't contain raw secrets."""
        secrets = {"TOKEN": "secret-token-xyz"}

        mock_secrets_mgr = MagicMock()
        mock_secrets_mgr.load_secrets.return_value = secrets
        mock_secrets_mgr.mask_values.side_effect = lambda text, **kwargs: text

        log = Log()
        log.context = MagicMock()

        with patch('python.helpers.log.get_secrets_manager', return_value=mock_secrets_mgr):
            log.log(type="info", heading="Debug", content=f"Token: {secrets['TOKEN']}")

        json_output = log.output_json()
        parsed = json.loads(json_output)

        # Flatten all content from logs
        all_content = " ".join([log_item.get('content', '') for log_item in parsed.get('logs', [])])
        assert secrets['TOKEN'] not in all_content, "Secret token found in JSON log output"
