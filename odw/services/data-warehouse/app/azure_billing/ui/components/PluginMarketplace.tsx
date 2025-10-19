/**
 * Plugin Marketplace Component
 * 
 * Main marketplace interface for plugin discovery, browsing, and management
 */

import React, { useState, useEffect } from 'react';
import { Search, Filter, Grid, List, Star, Download, Settings, AlertCircle } from 'lucide-react';

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
  created_at: string;
  updated_at: string;
}

interface PluginInstallation {
  id: string;
  plugin_id: string;
  installation_id: string;
  status: 'installed' | 'active' | 'disabled' | 'failed' | 'uninstalled';
  health_status: 'healthy' | 'unhealthy' | 'unknown';
  installed_at: string;
  last_used?: string;
}

interface PluginMarketplaceProps {
  onPluginInstall: (plugin: Plugin) => void;
  onPluginConfigure: (plugin: Plugin) => void;
  onPluginUninstall: (plugin: Plugin) => void;
}

const PluginMarketplace: React.FC<PluginMarketplaceProps> = ({
  onPluginInstall,
  onPluginConfigure,
  onPluginUninstall
}) => {
  const [plugins, setPlugins] = useState<Plugin[]>([]);
  const [installations, setInstallations] = useState<PluginInstallation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Filters and search
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [showOnlyInstalled, setShowOnlyInstalled] = useState(false);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  
  // Categories and types
  const categories = [
    { value: 'all', label: 'All Categories' },
    { value: 'data_source', label: 'Data Sources' },
    { value: 'transformation', label: 'Transformations' },
    { value: 'output', label: 'Output Connectors' },
    { value: 'utility', label: 'Utilities' },
    { value: 'analytics', label: 'Analytics' },
    { value: 'security', label: 'Security' }
  ];
  
  const pluginTypes = [
    { value: 'all', label: 'All Types' },
    { value: 'data_source', label: 'Data Source' },
    { value: 'transformation', label: 'Transformation' },
    { value: 'output', label: 'Output' },
    { value: 'utility', label: 'Utility' }
  ];

  useEffect(() => {
    loadPlugins();
    loadInstallations();
  }, []);

  const loadPlugins = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/plugins');
      if (!response.ok) throw new Error('Failed to load plugins');
      const data = await response.json();
      setPlugins(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load plugins');
    } finally {
      setLoading(false);
    }
  };

  const loadInstallations = async () => {
    try {
      const response = await fetch('/api/v1/plugins/installations');
      if (!response.ok) throw new Error('Failed to load installations');
      const data = await response.json();
      setInstallations(data);
    } catch (err) {
      console.error('Failed to load installations:', err);
    }
  };

  const getPluginInstallation = (pluginId: string): PluginInstallation | undefined => {
    return installations.find(inst => inst.plugin_id === pluginId);
  };

  const isPluginInstalled = (pluginId: string): boolean => {
    const installation = getPluginInstallation(pluginId);
    return installation?.status === 'installed' || installation?.status === 'active';
  };

  const filteredPlugins = plugins.filter(plugin => {
    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      if (!plugin.name.toLowerCase().includes(query) &&
          !plugin.display_name.toLowerCase().includes(query) &&
          !plugin.description.toLowerCase().includes(query) &&
          !plugin.tags.some(tag => tag.toLowerCase().includes(query))) {
        return false;
      }
    }

    // Category filter
    if (selectedCategory !== 'all' && plugin.category !== selectedCategory) {
      return false;
    }

    // Type filter
    if (selectedType !== 'all' && plugin.plugin_type !== selectedType) {
      return false;
    }

    // Installed filter
    if (showOnlyInstalled && !isPluginInstalled(plugin.id)) {
      return false;
    }

    return true;
  });

  const handleInstallPlugin = async (plugin: Plugin) => {
    try {
      const response = await fetch(`/api/v1/plugins/${plugin.id}/install`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ auto_activate: true })
      });
      
      if (!response.ok) throw new Error('Installation failed');
      
      await loadInstallations();
      onPluginInstall(plugin);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Installation failed');
    }
  };

  const handleUninstallPlugin = async (plugin: Plugin) => {
    try {
      const installation = getPluginInstallation(plugin.id);
      if (!installation) return;

      const response = await fetch(`/api/v1/plugins/installations/${installation.installation_id}`, {
        method: 'DELETE'
      });
      
      if (!response.ok) throw new Error('Uninstallation failed');
      
      await loadInstallations();
      onPluginUninstall(plugin);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Uninstallation failed');
    }
  };

  const renderStars = (rating: number) => {
    return Array.from({ length: 5 }, (_, i) => (
      <Star
        key={i}
        className={`w-4 h-4 ${i < Math.floor(rating) ? 'text-yellow-400 fill-current' : 'text-gray-300'}`}
      />
    ));
  };

  const renderPluginCard = (plugin: Plugin) => {
    const installation = getPluginInstallation(plugin.id);
    const installed = isPluginInstalled(plugin.id);

    return (
      <div key={plugin.id} className="bg-white rounded-lg shadow-md border border-gray-200 hover:shadow-lg transition-shadow">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center space-x-3">
              {plugin.icon_url ? (
                <img src={plugin.icon_url} alt={plugin.name} className="w-10 h-10 rounded" />
              ) : (
                <div className="w-10 h-10 bg-blue-100 rounded flex items-center justify-center">
                  <span className="text-blue-600 font-semibold text-lg">
                    {plugin.display_name.charAt(0)}
                  </span>
                </div>
              )}
              <div>
                <h3 className="text-lg font-semibold text-gray-900">{plugin.display_name}</h3>
                <p className="text-sm text-gray-500">by {plugin.author}</p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              {plugin.is_official && (
                <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded">
                  Official
                </span>
              )}
              {plugin.is_verified && (
                <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded">
                  Verified
                </span>
              )}
            </div>
          </div>

          {/* Description */}
          <p className="text-gray-600 text-sm mb-4 line-clamp-2">{plugin.description}</p>

          {/* Tags */}
          <div className="flex flex-wrap gap-2 mb-4">
            {plugin.tags.slice(0, 3).map(tag => (
              <span key={tag} className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                {tag}
              </span>
            ))}
            {plugin.tags.length > 3 && (
              <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                +{plugin.tags.length - 3} more
              </span>
            )}
          </div>

          {/* Stats */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-1">
                {renderStars(plugin.rating)}
                <span className="text-sm text-gray-500">({plugin.review_count})</span>
              </div>
              <div className="flex items-center space-x-1">
                <Download className="w-4 h-4 text-gray-400" />
                <span className="text-sm text-gray-500">{plugin.download_count.toLocaleString()}</span>
              </div>
            </div>
            <span className="text-sm text-gray-500">v{plugin.version}</span>
          </div>

          {/* Installation Status */}
          {installation && (
            <div className="mb-4">
              <div className={`flex items-center space-x-2 px-3 py-2 rounded-md ${
                installation.status === 'active' ? 'bg-green-50 text-green-700' :
                installation.status === 'installed' ? 'bg-blue-50 text-blue-700' :
                installation.status === 'failed' ? 'bg-red-50 text-red-700' :
                'bg-gray-50 text-gray-700'
              }`}>
                {installation.health_status === 'unhealthy' && (
                  <AlertCircle className="w-4 h-4" />
                )}
                <span className="text-sm font-medium">
                  Status: {installation.status}
                  {installation.health_status !== 'unknown' && ` (${installation.health_status})`}
                </span>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex space-x-2">
            {!installed ? (
              <button
                onClick={() => handleInstallPlugin(plugin)}
                className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors text-sm font-medium"
              >
                Install
              </button>
            ) : (
              <>
                <button
                  onClick={() => onPluginConfigure(plugin)}
                  className="flex-1 bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700 transition-colors text-sm font-medium flex items-center justify-center space-x-1"
                >
                  <Settings className="w-4 h-4" />
                  <span>Configure</span>
                </button>
                <button
                  onClick={() => handleUninstallPlugin(plugin)}
                  className="px-4 py-2 border border-red-300 text-red-700 rounded-md hover:bg-red-50 transition-colors text-sm font-medium"
                >
                  Uninstall
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    );
  };

  const renderPluginList = (plugin: Plugin) => {
    const installation = getPluginInstallation(plugin.id);
    const installed = isPluginInstalled(plugin.id);

    return (
      <div key={plugin.id} className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4 flex-1">
            {plugin.icon_url ? (
              <img src={plugin.icon_url} alt={plugin.name} className="w-8 h-8 rounded" />
            ) : (
              <div className="w-8 h-8 bg-blue-100 rounded flex items-center justify-center">
                <span className="text-blue-600 font-semibold text-sm">
                  {plugin.display_name.charAt(0)}
                </span>
              </div>
            )}
            
            <div className="flex-1">
              <div className="flex items-center space-x-2">
                <h3 className="font-semibold text-gray-900">{plugin.display_name}</h3>
                <span className="text-sm text-gray-500">v{plugin.version}</span>
                {plugin.is_official && (
                  <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded">
                    Official
                  </span>
                )}
              </div>
              <p className="text-sm text-gray-600 mt-1">{plugin.description}</p>
              <div className="flex items-center space-x-4 mt-2">
                <div className="flex items-center space-x-1">
                  {renderStars(plugin.rating)}
                  <span className="text-xs text-gray-500">({plugin.review_count})</span>
                </div>
                <span className="text-xs text-gray-500">{plugin.download_count.toLocaleString()} downloads</span>
                <span className="text-xs text-gray-500">by {plugin.author}</span>
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {installation && (
              <span className={`px-2 py-1 text-xs font-medium rounded ${
                installation.status === 'active' ? 'bg-green-100 text-green-800' :
                installation.status === 'installed' ? 'bg-blue-100 text-blue-800' :
                installation.status === 'failed' ? 'bg-red-100 text-red-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {installation.status}
              </span>
            )}
            
            {!installed ? (
              <button
                onClick={() => handleInstallPlugin(plugin)}
                className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700 transition-colors"
              >
                Install
              </button>
            ) : (
              <div className="flex space-x-1">
                <button
                  onClick={() => onPluginConfigure(plugin)}
                  className="bg-gray-600 text-white px-3 py-1 rounded text-sm hover:bg-gray-700 transition-colors"
                >
                  Configure
                </button>
                <button
                  onClick={() => handleUninstallPlugin(plugin)}
                  className="border border-red-300 text-red-700 px-3 py-1 rounded text-sm hover:bg-red-50 transition-colors"
                >
                  Uninstall
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Plugin Marketplace</h1>
        <p className="text-gray-600">Discover and install plugins to extend ABI functionality</p>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <AlertCircle className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <p className="mt-1 text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
          {/* Search */}
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="Search plugins..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Filters */}
          <div className="flex items-center space-x-4">
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {categories.map(cat => (
                <option key={cat.value} value={cat.value}>{cat.label}</option>
              ))}
            </select>

            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {pluginTypes.map(type => (
                <option key={type.value} value={type.value}>{type.label}</option>
              ))}
            </select>

            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={showOnlyInstalled}
                onChange={(e) => setShowOnlyInstalled(e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">Installed only</span>
            </label>

            {/* View Mode */}
            <div className="flex border border-gray-300 rounded-md">
              <button
                onClick={() => setViewMode('grid')}
                className={`p-2 ${viewMode === 'grid' ? 'bg-blue-100 text-blue-600' : 'text-gray-400'}`}
              >
                <Grid className="w-4 h-4" />
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`p-2 ${viewMode === 'list' ? 'bg-blue-100 text-blue-600' : 'text-gray-400'}`}
              >
                <List className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Results */}
      <div className="mb-4">
        <p className="text-sm text-gray-600">
          Showing {filteredPlugins.length} of {plugins.length} plugins
        </p>
      </div>

      {/* Plugin Grid/List */}
      {viewMode === 'grid' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredPlugins.map(renderPluginCard)}
        </div>
      ) : (
        <div className="space-y-4">
          {filteredPlugins.map(renderPluginList)}
        </div>
      )}

      {/* Empty State */}
      {filteredPlugins.length === 0 && (
        <div className="text-center py-12">
          <Filter className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No plugins found</h3>
          <p className="mt-1 text-sm text-gray-500">
            Try adjusting your search criteria or filters.
          </p>
        </div>
      )}
    </div>
  );
};

export default PluginMarketplace;