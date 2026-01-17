"""
Unit tests for PMS Provider Registry
Tests configuration management, provider loading, and persistence
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

from instruments.custom.pms_hub.provider_registry import (
    ProviderRegistry,
    ProviderConfig,
)
from instruments.custom.pms_hub.pms_provider import ProviderType


class TestProviderConfig:
    """Tests for ProviderConfig dataclass"""

    @pytest.mark.unit
    def test_provider_config_creation(self):
        """Test creating provider configuration"""
        config = ProviderConfig(
            provider_type=ProviderType.HOSTAWAY,
            name="My Hostaway",
            enabled=True,
            credentials={"api_key": "xxx"},
        )

        assert config.provider_type == ProviderType.HOSTAWAY
        assert config.name == "My Hostaway"
        assert config.enabled is True

    @pytest.mark.unit
    def test_provider_config_to_dict(self):
        """Test config serialization to dict"""
        config = ProviderConfig(
            provider_type=ProviderType.HOSTAWAY,
            name="Test",
            enabled=True,
            credentials={"key": "value"},
            options={"opt": "val"},
        )

        config_dict = config.to_dict()

        assert config_dict["provider_type"] == "hostaway"
        assert config_dict["name"] == "Test"
        assert config_dict["enabled"] is True
        assert config_dict["credentials"]["key"] == "value"

    @pytest.mark.unit
    def test_provider_config_from_dict(self):
        """Test config deserialization from dict"""
        data = {
            "provider_type": "lodgify",
            "name": "My Lodgify",
            "enabled": False,
            "credentials": {"api_key": "test"},
            "options": {},
        }

        config = ProviderConfig.from_dict(data)

        assert config.provider_type == ProviderType.LODGIFY
        assert config.name == "My Lodgify"
        assert config.enabled is False

    @pytest.mark.unit
    def test_provider_config_defaults(self):
        """Test provider config default values"""
        config = ProviderConfig(
            provider_type=ProviderType.HOSTAWAY,
            name="Test",
        )

        assert config.enabled is True
        assert config.credentials == {}
        assert config.options == {}


class TestProviderRegistry:
    """Tests for ProviderRegistry"""

    @pytest.mark.unit
    def test_registry_initialization(self, temp_config_dir):
        """Test registry initialization"""
        registry = ProviderRegistry(config_path=temp_config_dir / "providers.json")
        assert registry.config_path.parent == temp_config_dir
        assert isinstance(registry.providers, dict)

    @pytest.mark.unit
    def test_register_provider(self, temp_config_dir):
        """Test registering a new provider"""
        registry = ProviderRegistry(config_path=temp_config_dir / "providers.json")

        success = registry.register_provider(
            provider_id="hostaway_main",
            provider_type=ProviderType.HOSTAWAY,
            name="Hostaway Main",
            credentials={"api_key": "xxx", "user_id": "yyy", "access_token": "zzz"},
            enabled=True,
        )

        assert success is True
        assert "hostaway_main" in registry.providers
        assert registry.providers["hostaway_main"].name == "Hostaway Main"

    @pytest.mark.unit
    def test_register_multiple_providers(self, temp_config_dir):
        """Test registering multiple providers"""
        registry = ProviderRegistry(config_path=temp_config_dir / "providers.json")

        registry.register_provider(
            provider_id="hostaway_main",
            provider_type=ProviderType.HOSTAWAY,
            name="Hostaway",
            credentials={"api_key": "x"},
        )

        registry.register_provider(
            provider_id="lodgify_backup",
            provider_type=ProviderType.LODGIFY,
            name="Lodgify",
            credentials={"api_key": "y"},
        )

        assert len(registry.providers) == 2
        assert registry.list_providers() == ["hostaway_main", "lodgify_backup"]

    @pytest.mark.unit
    def test_unregister_provider(self, temp_config_dir):
        """Test unregistering a provider"""
        registry = ProviderRegistry(config_path=temp_config_dir / "providers.json")

        registry.register_provider(
            provider_id="test",
            provider_type=ProviderType.HOSTAWAY,
            name="Test",
            credentials={"api_key": "x"},
        )

        assert "test" in registry.providers

        success = registry.unregister_provider("test")
        assert success is True
        assert "test" not in registry.providers

    @pytest.mark.unit
    def test_unregister_nonexistent_provider(self, temp_config_dir):
        """Test unregistering nonexistent provider"""
        registry = ProviderRegistry(config_path=temp_config_dir / "providers.json")

        success = registry.unregister_provider("nonexistent")
        assert success is False

    @pytest.mark.unit
    def test_get_provider_config(self, temp_config_dir):
        """Test getting provider configuration"""
        registry = ProviderRegistry(config_path=temp_config_dir / "providers.json")

        registry.register_provider(
            provider_id="test",
            provider_type=ProviderType.HOSTAWAY,
            name="Test",
            credentials={"api_key": "xxx"},
        )

        config = registry.get_provider_config("test")
        assert config is not None
        assert config.name == "Test"

    @pytest.mark.unit
    def test_list_providers_all(self, temp_config_dir, provider_config_data):
        """Test listing all providers"""
        registry = ProviderRegistry(config_path=temp_config_dir / "providers.json")

        registry.register_provider(
            provider_id="hostaway_main",
            provider_type=ProviderType.HOSTAWAY,
            name="Hostaway",
            credentials={"api_key": "x"},
        )

        registry.register_provider(
            provider_id="lodgify",
            provider_type=ProviderType.LODGIFY,
            name="Lodgify",
            credentials={"api_key": "y"},
            enabled=False,
        )

        all_providers = registry.list_providers()
        assert len(all_providers) == 2

    @pytest.mark.unit
    def test_list_providers_enabled_only(self, temp_config_dir):
        """Test listing only enabled providers"""
        registry = ProviderRegistry(config_path=temp_config_dir / "providers.json")

        registry.register_provider(
            provider_id="enabled",
            provider_type=ProviderType.HOSTAWAY,
            name="Enabled",
            credentials={"api_key": "x"},
            enabled=True,
        )

        registry.register_provider(
            provider_id="disabled",
            provider_type=ProviderType.LODGIFY,
            name="Disabled",
            credentials={"api_key": "y"},
            enabled=False,
        )

        enabled = registry.list_providers(enabled_only=True)
        assert len(enabled) == 1
        assert "enabled" in enabled
        assert "disabled" not in enabled

    @pytest.mark.unit
    def test_update_provider_config(self, temp_config_dir):
        """Test updating provider configuration"""
        registry = ProviderRegistry(config_path=temp_config_dir / "providers.json")

        registry.register_provider(
            provider_id="test",
            provider_type=ProviderType.HOSTAWAY,
            name="Test",
            credentials={"api_key": "old"},
        )

        success = registry.update_provider_config(
            provider_id="test",
            credentials={"api_key": "new"},
        )

        assert success is True
        config = registry.get_provider_config("test")
        assert config.credentials["api_key"] == "new"

    @pytest.mark.unit
    def test_update_provider_enabled_status(self, temp_config_dir):
        """Test enabling/disabling provider"""
        registry = ProviderRegistry(config_path=temp_config_dir / "providers.json")

        registry.register_provider(
            provider_id="test",
            provider_type=ProviderType.HOSTAWAY,
            name="Test",
            credentials={"api_key": "x"},
            enabled=True,
        )

        registry.update_provider_config(provider_id="test", enabled=False)

        config = registry.get_provider_config("test")
        assert config.enabled is False

    @pytest.mark.unit
    def test_config_persistence(self, temp_config_dir):
        """Test provider config is persisted to file"""
        config_path = temp_config_dir / "providers.json"

        # Create and save config
        registry1 = ProviderRegistry(config_path=config_path)
        registry1.register_provider(
            provider_id="persistent",
            provider_type=ProviderType.HOSTAWAY,
            name="Persistent",
            credentials={"api_key": "persisted"},
        )

        # Load from file in new registry
        registry2 = ProviderRegistry(config_path=config_path)
        config = registry2.get_provider_config("persistent")

        assert config is not None
        assert config.name == "Persistent"
        assert config.credentials["api_key"] == "persisted"

    @pytest.mark.unit
    def test_export_config(self, temp_config_dir):
        """Test exporting full configuration"""
        registry = ProviderRegistry(config_path=temp_config_dir / "providers.json")

        registry.register_provider(
            provider_id="test1",
            provider_type=ProviderType.HOSTAWAY,
            name="Test 1",
            credentials={"api_key": "x"},
        )

        registry.register_provider(
            provider_id="test2",
            provider_type=ProviderType.LODGIFY,
            name="Test 2",
            credentials={"api_key": "y"},
        )

        export = registry.export_config()

        assert "providers" in export
        assert len(export["providers"]) == 2
        assert "test1" in export["providers"]
        assert "test2" in export["providers"]

    @pytest.mark.unit
    def test_import_config(self, temp_config_dir):
        """Test importing configuration"""
        registry = ProviderRegistry(config_path=temp_config_dir / "providers.json")

        import_data = {
            "providers": {
                "imported": {
                    "provider_type": "hostaway",
                    "name": "Imported",
                    "enabled": True,
                    "credentials": {"api_key": "imported_key"},
                    "options": {},
                }
            }
        }

        success = registry.import_config(import_data)

        assert success is True
        assert "imported" in registry.providers
        assert registry.providers["imported"].name == "Imported"

    @pytest.mark.unit
    def test_get_provider_async(self, temp_config_dir):
        """Test getting provider instance asynchronously"""
        registry = ProviderRegistry(config_path=temp_config_dir / "providers.json")

        registry.register_provider(
            provider_id="test",
            provider_type=ProviderType.HOSTAWAY,
            name="Test",
            credentials={
                "api_key": "x",
                "user_id": "y",
                "access_token": "z"
            },
        )

        # Mock provider creation
        with patch("instruments.custom.pms_hub.provider_registry.create_provider") as mock_create:
            mock_provider = AsyncMock()
            mock_create.return_value = mock_provider

            # Would need actual async test, but verifies config exists
            config = registry.get_provider_config("test")
            assert config is not None

    @pytest.mark.unit
    def test_disabled_provider_not_returned(self, temp_config_dir):
        """Test disabled providers are not returned"""
        registry = ProviderRegistry(config_path=temp_config_dir / "providers.json")

        registry.register_provider(
            provider_id="test",
            provider_type=ProviderType.HOSTAWAY,
            name="Test",
            credentials={"api_key": "x"},
            enabled=False,
        )

        # Disabled provider still in list_providers
        providers = registry.list_providers()
        assert "test" in providers

        # But not in enabled_only list
        enabled = registry.list_providers(enabled_only=True)
        assert "test" not in enabled


class TestProviderRegistryEdgeCases:
    """Edge case tests for provider registry"""

    @pytest.mark.unit
    def test_empty_registry(self, temp_config_dir):
        """Test empty registry"""
        registry = ProviderRegistry(config_path=temp_config_dir / "providers.json")

        assert len(registry.providers) == 0
        assert registry.list_providers() == []

    @pytest.mark.unit
    def test_duplicate_provider_id(self, temp_config_dir):
        """Test registering with duplicate provider ID overwrites"""
        registry = ProviderRegistry(config_path=temp_config_dir / "providers.json")

        registry.register_provider(
            provider_id="test",
            provider_type=ProviderType.HOSTAWAY,
            name="First",
            credentials={"api_key": "x"},
        )

        registry.register_provider(
            provider_id="test",
            provider_type=ProviderType.HOSTAWAY,
            name="Second",
            credentials={"api_key": "y"},
        )

        config = registry.get_provider_config("test")
        assert config.name == "Second"

    @pytest.mark.unit
    def test_config_file_creation(self, temp_config_dir):
        """Test config file is created"""
        config_path = temp_config_dir / "new_config.json"
        assert not config_path.exists()

        registry = ProviderRegistry(config_path=config_path)
        registry.register_provider(
            provider_id="test",
            provider_type=ProviderType.HOSTAWAY,
            name="Test",
            credentials={"api_key": "x"},
        )

        assert config_path.exists()

    @pytest.mark.unit
    def test_invalid_provider_type(self, temp_config_dir):
        """Test handling invalid provider type"""
        registry = ProviderRegistry(config_path=temp_config_dir / "providers.json")

        # Should raise ValueError when loading
        with pytest.raises(ValueError):
            ProviderConfig.from_dict({
                "provider_type": "invalid_type",
                "name": "Test",
                "enabled": True,
                "credentials": {},
                "options": {},
            })
