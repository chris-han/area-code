import React, { useState } from 'react';
import { PluginMetadata, PluginConfiguration, DataSourceConnector } from '../types/focus-types';

interface PluginManagementDashboardProps {
  installedPlugins: PluginMetadata[];
  configurations: PluginConfiguration[];
  onRefresh: () => void;
  onConfigurePlugin: (plugin: PluginMetadata) => void;
}

export const PluginManagementDashboard: React.FC<PluginManagementDashboardProps> = ({
  installedPlugins,
  configurations,
  onRefresh,
  onConfigurePlugin
}) => {
  const [selectedPlugin, setSelectedPlugin] = useState<string | null>(null);
  const [connectors, setConnectors] = useState<DataSourceConnector[]>([]);
  const [loadingConnectors, setLoadingConnectors] = useState(false);

  const handlePluginSelect = async (pluginId: string) => {
    setSelectedPlugin(pluginId);
    await loadConnectors(pluginId);
  };

  const loadConnectors = async (pluginId: string) => {
    try {
      setLoadingConnectors(true);
      const plugin = installedPlugins.find(p => p.id === pluginId);
      if (!plugin) return;

      const response = await fetch(`/api/v1/plugins/${plugin.name}/connectors`);
      if (response.ok) {
        const data = await response.json();
        setConnectors(data.connectors || []);
      }
    } catch (error) {
      console.error('Failed to load connectors:', error);
    } finally {
      setLoadingConnectors(false);
    }
  };

  const handleTogglePlugin = async (plugin: PluginMetadata) => {
    try {
      const action = plugin.isActive ? 'deactivate' : 'activate';
      const response = await fetch(`/api/v1/plugins/${plugin.name}/${action}`, {
        method: 'POST'
      });

      if (response.ok) {
        onRefresh();
      }
    } catch (error) {
      console.error(`Failed to ${plugin.isActive ? 'deactivate' : 'activate'} plugin:`, error);
    }
  };

  const handleUninstallPlugin = async (plugin: PluginMetadata) => {
    if (!confirm(`Are you sure you want to uninstall ${plugin.name}?`)) {
      return;
    }

    try {
      const response = await fetch(`/api/v1/plugins/${plugin.name}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        onRefresh();
        if (selectedPlugin === plugin.id) {
          setSelectedPlugin(null);
        }
      }
    } catch (error) {
      console.error('Failed to uninstall plugin:', error);
    }
  };

  const handleSyncConnector = async (connector: DataSourceConnector) => {
    try {
      const response = await fetch(`/api/v1/connectors/${connector.id}/sync`, {
        method: 'POST'
      });

      if (response.ok) {
        await loadConnectors(selectedPlugin!);
      }
    } catch (error) {
      console.error('Failed to sync connector:', error);
    }
  };

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'active':
      case 'connected':
        return 'green';
      case 'inactive':
      case 'disconnected':
        return 'gray';
      case 'error':
        return 'red';
      case 'testing':
        return 'yellow';
      default:
        return 'gray';
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleString();
  };

  return (
    <div className="plugin-management-dashboard">
      <div className="dashboard-header">
        <h3>Installed Plugins</h3>
        <button onClick={onRefresh} className="refresh-button">
          Refresh
        </button>
      </div>

      <div className="dashboard-content">
        <div className="plugins-list">
          {installedPlugins.length === 0 ? (
            <div className="no-plugins">
              <p>No plugins installed yet.</p>
            </div>
          ) : (
            installedPlugins.map(plugin => (
              <div
                key={plugin.id}
                className={`plugin-item ${selectedPlugin === plugin.id ? 'selected' : ''}`}
                onClick={() => handlePluginSelect(plugin.id)}
              >
                <div className="plugin-header">
                  <div className="plugin-info">
                    {plugin.iconUrl && (
                      <img src={plugin.iconUrl} alt={plugin.name} className="plugin-icon-small" />
                    )}
                    <div>
                      <h4>{plugin.name}</h4>
                      <span className="plugin-version">v{plugin.version}</span>
                    </div>
                  </div>
                  <div className="plugin-status">
                    <span className={`status-badge ${getStatusColor(plugin.isActive ? 'active' : 'inactive')}`}>
                      {plugin.isActive ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                </div>

                <div className="plugin-actions">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleTogglePlugin(plugin);
                    }}
                    className="toggle-button"
                  >
                    {plugin.isActive ? 'Deactivate' : 'Activate'}
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onConfigurePlugin(plugin);
                    }}
                    className="configure-button"
                  >
                    Configure
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleUninstallPlugin(plugin);
                    }}
                    className="uninstall-button"
                  >
                    Uninstall
                  </button>
                </div>
              </div>
            ))
          )}
        </div>

        <div className="plugin-details">
          {selectedPlugin ? (
            <>
              <h3>Data Source Connectors</h3>
              {loadingConnectors ? (
                <div className="loading">Loading connectors...</div>
              ) : connectors.length === 0 ? (
                <div className="no-connectors">
                  <p>No connectors configured for this plugin.</p>
                  <button
                    onClick={() => {
                      const plugin = installedPlugins.find(p => p.id === selectedPlugin);
                      if (plugin) onConfigurePlugin(plugin);
                    }}
                    className="primary-button"
                  >
                    Add Connector
                  </button>
                </div>
              ) : (
                <div className="connectors-list">
                  {connectors.map(connector => (
                    <div key={connector.id} className="connector-card">
                      <div className="connector-header">
                        <h4>{connector.name}</h4>
                        <span className={`status-badge ${getStatusColor(connector.status)}`}>
                          {connector.status}
                        </span>
                      </div>

                      <div className="connector-info">
                        <div className="info-row">
                          <span className="label">Type:</span>
                          <span className="value">{connector.type}</span>
                        </div>
                        <div className="info-row">
                          <span className="label">Last Sync:</span>
                          <span className="value">{formatDate(connector.lastSync)}</span>
                        </div>
                        {connector.recordsProcessed !== undefined && (
                          <div className="info-row">
                            <span className="label">Records Processed:</span>
                            <span className="value">{connector.recordsProcessed.toLocaleString()}</span>
                          </div>
                        )}
                        {connector.syncFrequency && (
                          <div className="info-row">
                            <span className="label">Sync Frequency:</span>
                            <span className="value">{connector.syncFrequency}</span>
                          </div>
                        )}
                      </div>

                      <div className="connector-actions">
                        <button
                          onClick={() => handleSyncConnector(connector)}
                          className="sync-button"
                          disabled={connector.status === 'error'}
                        >
                          Sync Now
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </>
          ) : (
            <div className="no-selection">
              <p>Select a plugin to view its connectors and configuration.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PluginManagementDashboard;
