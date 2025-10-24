/**
 * Plugin Dashboard Component
 * 
 * Monitoring and management dashboard for installed plugins
 */

import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  Play, 
  Pause, 
  Settings, 
  Trash2,
  RefreshCw,
  BarChart3,
  TrendingUp,
  AlertCircle
} from 'lucide-react';

interface PluginStatus {
  installation_id: string;
  plugin_id: string;
  plugin_name: string;
  display_name: string;
  version: string;
  status: 'installed' | 'active' | 'disabled' | 'failed' | 'uninstalled';
  health_status: 'healthy' | 'unhealthy' | 'unknown';
  last_health_check?: string;
  installed_at: string;
  last_used?: string;
  usage_count: number;
  error_message?: string;
}

interface PluginMetrics {
  installation_id: string;
  execution_count: number;
  success_count: number;
  error_count: number;
  average_execution_time: number;
  last_execution_time?: string;
  last_error_time?: string;
  last_error_message?: string;
}

interface PluginDashboardProps {
  onConfigurePlugin: (installationId: string) => void;
  onUninstallPlugin: (installationId: string) => void;
}

const PluginDashboard: React.FC<PluginDashboardProps> = ({
  onConfigurePlugin,
  onUninstallPlugin
}) => {
  const [plugins, setPlugins] = useState<PluginStatus[]>([]);
  const [metrics, setMetrics] = useState<Record<string, PluginMetrics>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadPluginData();
    
    // Set up auto-refresh
    const interval = setInterval(loadPluginData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const loadPluginData = async () => {
    try {
      setRefreshing(true);
      
      // Load plugin statuses
      const statusResponse = await fetch('/api/v1/plugins/installations/status');
      if (!statusResponse.ok) throw new Error('Failed to load plugin status');
      const statusData = await statusResponse.json();
      setPlugins(statusData);

      // Load plugin metrics
      const metricsResponse = await fetch('/api/v1/plugins/installations/metrics');
      if (!metricsResponse.ok) throw new Error('Failed to load plugin metrics');
      const metricsData = await metricsResponse.json();
      
      // Convert metrics array to object keyed by installation_id
      const metricsMap = metricsData.reduce((acc: Record<string, PluginMetrics>, metric: PluginMetrics) => {
        acc[metric.installation_id] = metric;
        return acc;
      }, {});
      setMetrics(metricsMap);

      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load plugin data');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handlePluginAction = async (installationId: string, action: 'activate' | 'deactivate') => {
    try {
      const response = await fetch(`/api/v1/plugins/installations/${installationId}/${action}`, {
        method: 'POST'
      });
      
      if (!response.ok) throw new Error(`Failed to ${action} plugin`);
      
      // Refresh data
      await loadPluginData();
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to ${action} plugin`);
    }
  };

  const getStatusIcon = (status: string, healthStatus: string) => {
    if (status === 'active' && healthStatus === 'healthy') {
      return <CheckCircle className="w-5 h-5 text-green-500" />;
    } else if (status === 'active' && healthStatus === 'unhealthy') {
      return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
    } else if (status === 'failed') {
      return <AlertCircle className="w-5 h-5 text-red-500" />;
    } else if (status === 'disabled') {
      return <Pause className="w-5 h-5 text-gray-500" />;
    } else {
      return <Clock className="w-5 h-5 text-blue-500" />;
    }
  };

  const getStatusColor = (status: string, healthStatus: string) => {
    if (status === 'active' && healthStatus === 'healthy') return 'text-green-700 bg-green-50';
    if (status === 'active' && healthStatus === 'unhealthy') return 'text-yellow-700 bg-yellow-50';
    if (status === 'failed') return 'text-red-700 bg-red-50';
    if (status === 'disabled') return 'text-gray-700 bg-gray-50';
    return 'text-blue-700 bg-blue-50';
  };

  const formatDuration = (dateString?: string) => {
    if (!dateString) return 'Never';
    
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (days > 0) return `${days}d ago`;
    if (hours > 0) return `${hours}h ago`;
    if (minutes > 0) return `${minutes}m ago`;
    return 'Just now';
  };

  const calculateSuccessRate = (pluginMetrics?: PluginMetrics) => {
    if (!pluginMetrics || pluginMetrics.execution_count === 0) return 0;
    return (pluginMetrics.success_count / pluginMetrics.execution_count) * 100;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const activePlugins = plugins.filter(p => p.status === 'active');
  const healthyPlugins = activePlugins.filter(p => p.health_status === 'healthy');
  const unhealthyPlugins = activePlugins.filter(p => p.health_status === 'unhealthy');

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Plugin Dashboard</h1>
          <p className="text-gray-600">Monitor and manage your installed plugins</p>
        </div>
        
        <button
          onClick={loadPluginData}
          disabled={refreshing}
          className="flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
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

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Activity className="h-8 w-8 text-blue-600" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">Total Plugins</dt>
                <dd className="text-lg font-medium text-gray-900">{plugins.length}</dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <CheckCircle className="h-8 w-8 text-green-600" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">Active & Healthy</dt>
                <dd className="text-lg font-medium text-gray-900">{healthyPlugins.length}</dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <AlertTriangle className="h-8 w-8 text-yellow-600" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">Unhealthy</dt>
                <dd className="text-lg font-medium text-gray-900">{unhealthyPlugins.length}</dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <TrendingUp className="h-8 w-8 text-purple-600" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">Total Usage</dt>
                <dd className="text-lg font-medium text-gray-900">
                  {plugins.reduce((sum, p) => sum + p.usage_count, 0).toLocaleString()}
                </dd>
              </dl>
            </div>
          </div>
        </div>
      </div>

      {/* Plugin List */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Installed Plugins</h2>
        </div>
        
        <div className="divide-y divide-gray-200">
          {plugins.map((plugin) => {
            const pluginMetrics = metrics[plugin.installation_id];
            const successRate = calculateSuccessRate(pluginMetrics);
            
            return (
              <div key={plugin.installation_id} className="p-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4 flex-1">
                    {/* Status Icon */}
                    <div className="flex-shrink-0">
                      {getStatusIcon(plugin.status, plugin.health_status)}
                    </div>
                    
                    {/* Plugin Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2">
                        <h3 className="text-lg font-medium text-gray-900 truncate">
                          {plugin.display_name}
                        </h3>
                        <span className="text-sm text-gray-500">v{plugin.version}</span>
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(plugin.status, plugin.health_status)}`}>
                          {plugin.status}
                          {plugin.health_status !== 'unknown' && ` (${plugin.health_status})`}
                        </span>
                      </div>
                      
                      <div className="mt-1 flex items-center space-x-4 text-sm text-gray-500">
                        <span>Installed {formatDuration(plugin.installed_at)}</span>
                        {plugin.last_used && (
                          <span>Last used {formatDuration(plugin.last_used)}</span>
                        )}
                        <span>{plugin.usage_count.toLocaleString()} executions</span>
                      </div>
                      
                      {plugin.error_message && (
                        <div className="mt-2 text-sm text-red-600 flex items-center">
                          <AlertCircle className="w-4 h-4 mr-1" />
                          {plugin.error_message}
                        </div>
                      )}
                    </div>
                    
                    {/* Metrics */}
                    {pluginMetrics && (
                      <div className="hidden lg:flex items-center space-x-6 text-sm">
                        <div className="text-center">
                          <div className="text-lg font-semibold text-gray-900">
                            {pluginMetrics.execution_count.toLocaleString()}
                          </div>
                          <div className="text-gray-500">Executions</div>
                        </div>
                        
                        <div className="text-center">
                          <div className="text-lg font-semibold text-gray-900">
                            {successRate.toFixed(1)}%
                          </div>
                          <div className="text-gray-500">Success Rate</div>
                        </div>
                        
                        <div className="text-center">
                          <div className="text-lg font-semibold text-gray-900">
                            {pluginMetrics.average_execution_time.toFixed(2)}s
                          </div>
                          <div className="text-gray-500">Avg Time</div>
                        </div>
                      </div>
                    )}
                  </div>
                  
                  {/* Actions */}
                  <div className="flex items-center space-x-2 ml-4">
                    {plugin.status === 'active' ? (
                      <button
                        onClick={() => handlePluginAction(plugin.installation_id, 'deactivate')}
                        className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
                        title="Deactivate plugin"
                      >
                        <Pause className="w-4 h-4" />
                      </button>
                    ) : (
                      <button
                        onClick={() => handlePluginAction(plugin.installation_id, 'activate')}
                        className="p-2 text-gray-400 hover:text-green-600 transition-colors"
                        title="Activate plugin"
                      >
                        <Play className="w-4 h-4" />
                      </button>
                    )}
                    
                    <button
                      onClick={() => onConfigurePlugin(plugin.installation_id)}
                      className="p-2 text-gray-400 hover:text-blue-600 transition-colors"
                      title="Configure plugin"
                    >
                      <Settings className="w-4 h-4" />
                    </button>
                    
                    <button
                      onClick={() => onUninstallPlugin(plugin.installation_id)}
                      className="p-2 text-gray-400 hover:text-red-600 transition-colors"
                      title="Uninstall plugin"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                
                {/* Expanded Metrics for Mobile */}
                {pluginMetrics && (
                  <div className="mt-4 lg:hidden">
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div className="text-center p-3 bg-gray-50 rounded">
                        <div className="font-semibold text-gray-900">
                          {pluginMetrics.execution_count.toLocaleString()}
                        </div>
                        <div className="text-gray-500">Executions</div>
                      </div>
                      
                      <div className="text-center p-3 bg-gray-50 rounded">
                        <div className="font-semibold text-gray-900">
                          {successRate.toFixed(1)}%
                        </div>
                        <div className="text-gray-500">Success Rate</div>
                      </div>
                      
                      <div className="text-center p-3 bg-gray-50 rounded">
                        <div className="font-semibold text-gray-900">
                          {pluginMetrics.average_execution_time.toFixed(2)}s
                        </div>
                        <div className="text-gray-500">Avg Time</div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
        
        {/* Empty State */}
        {plugins.length === 0 && (
          <div className="text-center py-12">
            <BarChart3 className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No plugins installed</h3>
            <p className="mt-1 text-sm text-gray-500">
              Install plugins from the marketplace to get started.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default PluginDashboard;