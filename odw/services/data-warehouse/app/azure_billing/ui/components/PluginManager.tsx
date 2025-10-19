/**
 * Plugin Manager Component
 * 
 * Main component that orchestrates the plugin marketplace, configuration, and dashboard
 */

import React, { useState } from 'react';
import { Package, Settings, BarChart3, ArrowLeft } from 'lucide-react';
import PluginMarketplace from './PluginMarketplace';
import PluginConfiguration from './PluginConfiguration';
import PluginDashboard from './PluginDashboard';

interface Plugin {
  id: string;
  name: string;
  display_name: string;
  description: string;
  version: string;
  author: string;
  category: string;
  tags: string[];
  plugin_type: string;
  rating: number;
  review_count: number;
  download_count: number;
  is_official: boolean;
  is_verified: boolean;
  icon_url?: string;
  status: 'active' | 'deprecated' | 'disabled';
  config_schema: any;
  default_config?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

type ViewMode = 'marketplace' | 'dashboard' | 'configure';

interface ConfigurationState {
  plugin: Plugin;
  installationId?: string;
  currentConfig?: Record<string, any>;
}

const PluginManager: React.FC = () => {
  const [currentView, setCurrentView] = useState<ViewMode>('marketplace');
  const [configurationState, setConfigurationState] = useState<ConfigurationState | null>(null);

  const handlePluginInstall = (plugin: Plugin) => {
    console.log('Plugin installed:', plugin.name);
    // Could show a success notification here
  };

  const handlePluginConfigure = async (plugin: Plugin, installationId?: string) => {
    try {
      // Load current configuration if installation ID is provided
      let currentConfig = plugin.default_config;
      
      if (installationId) {
        const response = await fetch(`/api/v1/plugins/installations/${installationId}/config`);
        if (response.ok) {
          const configData = await response.json();
          currentConfig = configData.config;
        }
      }

      setConfigurationState({
        plugin,
        installationId,
        currentConfig
      });
      setCurrentView('configure');
    } catch (error) {
      console.error('Failed to load plugin configuration:', error);
    }
  };

  const handlePluginUninstall = (plugin: Plugin) => {
    console.log('Plugin uninstalled:', plugin.name);
    // Could show a confirmation dialog and success notification here
  };

  const handleConfigurationSave = async (config: Record<string, any>) => {
    if (!configurationState) return;

    try {
      const { plugin, installationId } = configurationState;
      
      if (installationId) {
        // Update existing installation configuration
        const response = await fetch(`/api/v1/plugins/installations/${installationId}/config`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ config })
        });
        
        if (!response.ok) throw new Error('Failed to update configuration');
      } else {
        // Install plugin with configuration
        const response = await fetch(`/api/v1/plugins/${plugin.id}/install`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ config, auto_activate: true })
        });
        
        if (!response.ok) throw new Error('Failed to install plugin');
      }

      // Return to previous view
      setCurrentView('dashboard');
      setConfigurationState(null);
    } catch (error) {
      console.error('Failed to save configuration:', error);
    }
  };

  const handleConfigurationCancel = () => {
    setCurrentView('marketplace');
    setConfigurationState(null);
  };

  const handleConfigurationTest = async (config: Record<string, any>): Promise<boolean> => {
    if (!configurationState) return false;

    try {
      const response = await fetch(`/api/v1/plugins/${configurationState.plugin.id}/test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ config })
      });

      const result = await response.json();
      return result.success || false;
    } catch (error) {
      console.error('Configuration test failed:', error);
      return false;
    }
  };

  const handleDashboardConfigure = (installationId: string) => {
    // Load plugin details and configure
    fetch(`/api/v1/plugins/installations/${installationId}`)
      .then(response => response.json())
      .then(installation => {
        return fetch(`/api/v1/plugins/${installation.plugin_id}`);
      })
      .then(response => response.json())
      .then(plugin => {
        handlePluginConfigure(plugin, installationId);
      })
      .catch(error => {
        console.error('Failed to load plugin for configuration:', error);
      });
  };

  const handleDashboardUninstall = async (installationId: string) => {
    try {
      const response = await fetch(`/api/v1/plugins/installations/${installationId}`, {
        method: 'DELETE'
      });
      
      if (!response.ok) throw new Error('Failed to uninstall plugin');
      
      console.log('Plugin uninstalled successfully');
    } catch (error) {
      console.error('Failed to uninstall plugin:', error);
    }
  };

  const renderNavigation = () => (
    <div className="bg-white border-b border-gray-200 mb-6">
      <div className="max-w-7xl mx-auto px-6">
        <nav className="flex space-x-8">
          <button
            onClick={() => setCurrentView('marketplace')}
            className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
              currentView === 'marketplace'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <div className="flex items-center space-x-2">
              <Package className="w-4 h-4" />
              <span>Marketplace</span>
            </div>
          </button>
          
          <button
            onClick={() => setCurrentView('dashboard')}
            className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
              currentView === 'dashboard'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <div className="flex items-center space-x-2">
              <BarChart3 className="w-4 h-4" />
              <span>Dashboard</span>
            </div>
          </button>
        </nav>
      </div>
    </div>
  );

  const renderConfigurationHeader = () => (
    <div className="bg-white border-b border-gray-200 mb-6">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <button
          onClick={() => setCurrentView('marketplace')}
          className="flex items-center space-x-2 text-gray-600 hover:text-gray-900 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Marketplace</span>
        </button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {currentView === 'configure' ? renderConfigurationHeader() : renderNavigation()}
      
      <div className="max-w-7xl mx-auto">
        {currentView === 'marketplace' && (
          <PluginMarketplace
            onPluginInstall={handlePluginInstall}
            onPluginConfigure={handlePluginConfigure}
            onPluginUninstall={handlePluginUninstall}
          />
        )}
        
        {currentView === 'dashboard' && (
          <PluginDashboard
            onConfigurePlugin={handleDashboardConfigure}
            onUninstallPlugin={handleDashboardUninstall}
          />
        )}
        
        {currentView === 'configure' && configurationState && (
          <PluginConfiguration
            plugin={configurationState.plugin}
            currentConfig={configurationState.currentConfig}
            onSave={handleConfigurationSave}
            onCancel={handleConfigurationCancel}
            onTest={handleConfigurationTest}
          />
        )}
      </div>
    </div>
  );
};

export default PluginManager;