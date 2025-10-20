"""
Plugin Integration Tests

Tests plugin installation, configuration, and integration with workflows.
"""

import pytest
from datetime import datetime
from typing import Dict, Any
from unittest.mock import AsyncMock, patch

from app.azure_billing.plugins.plugin_integration import PluginIntegrationService


class TestPluginIntegration:
    """Test plugin installation and configuration testing."""
    
    @pytest.mark.asyncio
    async def test_plugin_installation_flow(self, mock_plugin_integration_service):
        """Test complete plugin installation and configuration flow."""
        
        # Test marketplace plugin listing
        plugins = await mock_plugin_integration_service.get_marketplace_plugins()
        
        # Verify plugin listing
        assert isinstance(plugins, list)
        assert len(plugins) > 0
        
        # Find Azure EA API plugin
        azure_ea_plugin = next(
            (p for p in plugins if p["id"] == "azure-ea-api"), 
            None
        )
        assert azure_ea_plugin is not None
        assert azure_ea_plugin["name"] == "Azure EA API"
        assert azure_ea_plugin["isInstalled"] is True
    
    @pytest.mark.asyncio
    async def test_plugin_configuration_validation(
        self, 
        mock_plugin_integration_service,
        sample_plugin_config
    ):
        """Test plugin configuration and validation."""
        
        plugin_name = "azure-ea-api"
        connector_name = "test-connector"
        config = sample_plugin_config["azure_ea_api"]
        
        # Test plugin configuration
        result = await mock_plugin_integration_service.configure_plugin(
            plugin_name, connector_name, config
        )
        
        # Verify configuration success
        assert result is True
    
    @pytest.mark.asyncio
    async def test_plugin_connection_testing(
        self,
        mock_plugin_integration_service,
        sample_plugin_config
    ):
        """Test plugin connection testing functionality."""
        
        plugin_name = "azure-blob-storage"
        config = sample_plugin_config["azure_blob_storage"]
        
        # Test plugin connection
        result = await mock_plugin_integration_service.test_plugin_connection(
            plugin_name, config
        )
        
        # Verify connection test results
        assert result["success"] is True
        assert "message" in result
        assert "tested_at" in result
        
        # Verify timestamp format
        tested_at = datetime.fromisoformat(result["tested_at"])
        assert isinstance(tested_at, datetime)
    
    @pytest.mark.asyncio
    async def test_plugin_installation_process(self, mock_plugin_integration_service):
        """Test plugin installation from marketplace."""
        
        plugin_name = "azure-blob-storage"
        version = "1.0.0"
        
        # Test plugin installation
        result = await mock_plugin_integration_service.install_plugin(
            plugin_name, version, auto_activate=True
        )
        
        # Verify installation success
        assert result is True
    
    @pytest.mark.asyncio
    async def test_plugin_workflow_integration(
        self,
        mock_plugin_integration_service,
        workflow_test_params
    ):
        """Test plugin integration with workflow execution."""
        
        # Get installed plugins
        plugins = await mock_plugin_integration_service.get_marketplace_plugins()
        
        # Find active plugins
        active_plugins = [p for p in plugins if p["isActive"]]
        assert len(active_plugins) > 0
        
        # Verify Azure Blob Storage plugin is active
        blob_plugin = next(
            (p for p in active_plugins if p["id"] == "azure-blob-storage"),
            None
        )
        assert blob_plugin is not None
        assert blob_plugin["isConfigured"] is True