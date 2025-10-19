import React, { useState, useEffect } from 'react';
import { PluginMetadata, PluginConfiguration } from '../types/focus-types';
import { PluginDiscovery } from './PluginDiscovery';
import { PluginInstallationWizard } from './PluginInstallationWizard';
import { PluginManagementDashboard } from './PluginManagementDashboard';

interface PluginMarketplaceProps {
  className?: string;
}

type MarketplaceView = 'discovery' | 'installation' | 'management';

export const PluginMarketplace: React.FC<PluginMarketplaceProps> = ({ className }) => {
  const [currentView, setCurrentView] = useState<MarketplaceView>('discovery');
  const [selectedPlugin, setSelectedPlugin] = useState<PluginMetadata | null>(null);
  const [availablePlugins, setAvailablePlugins] = useState<PluginMetadata[]>([]);
  const [installedPlugins, setInstalledPlugins] = useState<PluginMetadata[]>([]);
  const [configurations, setConfigurations] = useState<PluginConfiguration[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadPluginData();
  }, []);

  const loadPluginData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load available plugins from marketplace
      const availableResponse = await fetch('/api/v1/plugins/marketplace');
      if (!availableResponse.ok) {
        throw new Error('Failed to load available plugins');
      }
      const availableData = await availableResponse.json();
      setAvailablePlugins(availableData.plugins || []);

      // Load installed plugins
      const installedResponse = await fetch('/api/v1/plugins/installed');
      if (!installedResponse.ok) {
        throw new Error('Failed to load installed plugins');
      }
      const installedData = await installedResponse.json();
      setInstalledPlugins(installedData.plugins || []);

      // Load plugin configurations
      const configResponse = await fetch('/api/v1/plugins/configurations');
      if (!configResponse.ok) {
        throw new Error('Failed to load plugin configurations');
      }
      const configData = await configResponse.json();
      setConfigurations(configData.configurations || []);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load plugin data');
    } finally {
      setLoading(false);
    }
  };

  const handlePluginInstall = (plugin: PluginMetadata) => {
    setSelectedPlugin(plugin);
    setCurrentView('installation');
  };

  const handleInstallationComplete = async () => {
    await loadPluginData();
    setCurrentView('management');
    setSelectedPlugin(null);
  };

  const handleInstallationCancel = () => {
    setCurrentView('discovery');
    setSelectedPlugin(null);
  };

  const handleViewChange = (view: MarketplaceView) => {
    setCurrentView(view);
    setSelectedPlugin(null);
  };

  if (loading) {
    return (
      <div className={`plugin-marketplace ${className || ''}`}>
        <div className="loading-container">
          <div className="loading-spinner" />
          <p>Loading plugin marketplace...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`plugin-marketplace ${className || ''}`}>
        <div className="error-container">
          <h3>Error Loading Plugin Marketplace</h3>
          <p>{error}</p>
          <button onClick={loadPluginData} className="retry-button">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`plugin-marketplace ${className || ''}`}>
      <div className="marketplace-header">
        <h2>Plugin Marketplace</h2>
        <div className="marketplace-nav">
          <button
            className={`nav-button ${currentView === 'discovery' ? 'active' : ''}`}
            onClick={() => handleViewChange('discovery')}
          >
            Discover Plugins
          </button>
          <button
            className={`nav-button ${currentView === 'management' ? 'active' : ''}`}
            onClick={() => handleViewChange('management')}
          >
            Manage Plugins ({installedPlugins.length})
          </button>
        </div>
      </div>

      <div className="marketplace-content">
        {currentView === 'discovery' && (
          <PluginDiscovery
            availablePlugins={availablePlugins}
            installedPlugins={installedPlugins}
            onInstallPlugin={handlePluginInstall}
            onRefresh={loadPluginData}
          />
        )}

        {currentView === 'installation' && selectedPlugin && (
          <PluginInstallationWizard
            plugin={selectedPlugin}
            onComplete={handleInstallationComplete}
            onCancel={handleInstallationCancel}
          />
        )}

        {currentView === 'management' && (
          <PluginManagementDashboard
            installedPlugins={installedPlugins}
            configurations={configurations}
            onRefresh={loadPluginData}
            onConfigurePlugin={(plugin) => {
              setSelectedPlugin(plugin);
              setCurrentView('installation');
            }}
          />
        )}
      </div>
    </div>
  );
};

export default PluginMarketplace;