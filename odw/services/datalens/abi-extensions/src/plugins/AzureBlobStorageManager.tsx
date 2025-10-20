/**
 * Azure Blob Storage Manager
 * Lists and manages Azure Blob Storage configurations
 */

import React, { useState, useEffect } from 'react';
import { AzureBlobStorageService, AzureBlobStorageConfig } from '../services/AzureBlobStorageService';
import AzureBlobStoragePlugin from './AzureBlobStoragePlugin';

interface AzureBlobStorageManagerProps {
  className?: string;
}

type ViewMode = 'list' | 'create' | 'edit';

export const AzureBlobStorageManager: React.FC<AzureBlobStorageManagerProps> = ({ className }) => {
  const [configurations, setConfigurations] = useState<AzureBlobStorageConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [selectedConfig, setSelectedConfig] = useState<AzureBlobStorageConfig | null>(null);
  const [syncingConfigs, setSyncingConfigs] = useState<Set<string>>(new Set());

  const service = new AzureBlobStorageService();

  useEffect(() => {
    loadConfigurations();
  }, []);

  const loadConfigurations = async () => {
    try {
      setLoading(true);
      setError(null);
      const configs = await service.getConfigurations();
      setConfigurations(configs);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load configurations');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveConfiguration = async (config: AzureBlobStorageConfig) => {
    try {
      await service.saveConfiguration(config);
      await loadConfigurations();
      setViewMode('list');
      setSelectedConfig(null);
    } catch (err) {
      throw err; // Let the plugin component handle the error
    }
  };

  const handleTestConnection = async (config: AzureBlobStorageConfig): Promise<boolean> => {
    return await service.testConnection(config);
  };

  const handleDeleteConfiguration = async (id: string) => {
    if (!confirm('Are you sure you want to delete this configuration?')) {
      return;
    }

    try {
      await service.deleteConfiguration(id);
      await loadConfigurations();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete configuration');
    }
  };

  const handleSyncData = async (configId: string) => {
    setSyncingConfigs(prev => new Set(prev).add(configId));
    
    try {
      await service.syncData(configId);
      await loadConfigurations(); // Refresh to get updated lastSync
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sync failed');
    } finally {
      setSyncingConfigs(prev => {
        const newSet = new Set(prev);
        newSet.delete(configId);
        return newSet;
      });
    }
  };

  const formatLastSync = (lastSync?: string): string => {
    if (!lastSync) return 'Never';
    return new Date(lastSync).toLocaleString();
  };

  const getStatusColor = (isActive: boolean): string => {
    return isActive ? 'green' : 'gray';
  };

  if (loading) {
    return (
      <div className={`azure-blob-storage-manager loading ${className || ''}`}>
        <div className="loading-spinner" />
        <p>Loading Azure Blob Storage configurations...</p>
      </div>
    );
  }

  if (viewMode === 'create') {
    return (
      <AzureBlobStoragePlugin
        mode="create"
        onSave={handleSaveConfiguration}
        onTest={handleTestConnection}
        onCancel={() => setViewMode('list')}
      />
    );
  }

  if (viewMode === 'edit' && selectedConfig) {
    return (
      <AzureBlobStoragePlugin
        mode="edit"
        config={selectedConfig}
        onSave={handleSaveConfiguration}
        onTest={handleTestConnection}
        onCancel={() => {
          setViewMode('list');
          setSelectedConfig(null);
        }}
      />
    );
  }

  return (
    <div className={`azure-blob-storage-manager ${className || ''}`}>
      <div className="manager-header">
        <div className="header-info">
          <h3>Azure Blob Storage Connections</h3>
          <p>Manage FOCUS-compliant data sources from Azure Blob Storage</p>
        </div>
        <button
          onClick={() => setViewMode('create')}
          className="add-button"
        >
          Add Connection
        </button>
      </div>

      {error && (
        <div className="error-message">
          <p>{error}</p>
          <button onClick={() => setError(null)} className="dismiss-error">×</button>
        </div>
      )}

      <div className="configurations-list">
        {configurations.length === 0 ? (
          <div className="no-configurations">
            <div className="empty-state">
              <h4>No Azure Blob Storage connections configured</h4>
              <p>Add your first connection to start importing FOCUS-compliant billing data.</p>
              <button
                onClick={() => setViewMode('create')}
                className="primary-button"
              >
                Add First Connection
              </button>
            </div>
          </div>
        ) : (
          configurations.map(config => (
            <div key={config.id} className="configuration-card">
              <div className="config-header">
                <div className="config-info">
                  <h4>{config.name}</h4>
                  {config.description && <p className="config-description">{config.description}</p>}
                </div>
                <div className="config-status">
                  <span className={`status-badge ${getStatusColor(config.isActive)}`}>
                    {config.isActive ? 'Active' : 'Inactive'}
                  </span>
                </div>
              </div>

              <div className="config-details">
                <div className="detail-row">
                  <span className="detail-label">Account:</span>
                  <span className="detail-value">{config.accountUrl}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Primary Container:</span>
                  <span className="detail-value">{config.containerName}</span>
                </div>
                {config.secondaryContainer && (
                  <div className="detail-row">
                    <span className="detail-label">Secondary Container:</span>
                    <span className="detail-value">{config.secondaryContainer}</span>
                  </div>
                )}
                <div className="detail-row">
                  <span className="detail-label">Sync Frequency:</span>
                  <span className="detail-value">{config.syncFrequency}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Last Sync:</span>
                  <span className="detail-value">{formatLastSync(config.lastSync)}</span>
                </div>
              </div>

              <div className="config-actions">
                <button
                  onClick={() => handleSyncData(config.id!)}
                  disabled={syncingConfigs.has(config.id!) || !config.isActive}
                  className="sync-button"
                >
                  {syncingConfigs.has(config.id!) ? 'Syncing...' : 'Sync Now'}
                </button>
                <button
                  onClick={() => {
                    setSelectedConfig(config);
                    setViewMode('edit');
                  }}
                  className="edit-button"
                >
                  Edit
                </button>
                <button
                  onClick={() => handleDeleteConfiguration(config.id!)}
                  className="delete-button"
                >
                  Delete
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default AzureBlobStorageManager;