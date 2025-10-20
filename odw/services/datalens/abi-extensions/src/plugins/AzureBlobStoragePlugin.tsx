/**
 * Azure Blob Storage Plugin for NCEI Data Source
 * Handles FOCUS-compliant parquet files from Azure Blob Storage
 */

import React, { useState, useEffect } from 'react';

interface AzureBlobStorageConfig {
  id?: string;
  name: string;
  accountUrl: string;
  sasToken: string;
  containerName: string;
  secondaryContainer?: string;
  pathPrefix?: string;
  syncFrequency: 'hourly' | 'daily' | 'weekly' | 'manual';
  isActive: boolean;
  lastSync?: string;
  description?: string;
}

interface AzureBlobStoragePluginProps {
  config?: AzureBlobStorageConfig;
  onSave: (config: AzureBlobStorageConfig) => Promise<void>;
  onTest: (config: AzureBlobStorageConfig) => Promise<boolean>;
  onCancel: () => void;
  mode: 'create' | 'edit';
}

export const AzureBlobStoragePlugin: React.FC<AzureBlobStoragePluginProps> = ({
  config,
  onSave,
  onTest,
  onCancel,
  mode
}) => {
  const [formData, setFormData] = useState<AzureBlobStorageConfig>({
    name: '',
    accountUrl: 'https://finopsbilling.blob.core.chinacloudapi.cn',
    sasToken: 'sv=2024-11-04&ss=bfqt&srt=sco&sp=rltfx&se=2045-10-19T12:52:39Z&st=2025-10-19T04:37:39Z&spr=https&sig=g44Cxk0eqgrn5N6DrZF8s60a3qaWp6cWLnPaNJtXw40%3D',
    containerName: '',
    secondaryContainer: '',
    pathPrefix: 'focus-data/',
    syncFrequency: 'daily',
    isActive: true,
    description: 'NCEI Azure Blob Storage data source for FOCUS-compliant billing data',
    ...config
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [testing, setTesting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);

  useEffect(() => {
    if (config) {
      setFormData({ ...formData, ...config });
    }
  }, [config]);

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Connection name is required';
    }

    if (!formData.accountUrl.trim()) {
      newErrors.accountUrl = 'Account URL is required';
    } else if (!formData.accountUrl.startsWith('https://')) {
      newErrors.accountUrl = 'Account URL must start with https://';
    }

    if (!formData.sasToken.trim()) {
      newErrors.sasToken = 'SAS token is required';
    }

    if (!formData.containerName.trim()) {
      newErrors.containerName = 'Container name is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleTestConnection = async () => {
    if (!validateForm()) {
      return;
    }

    setTesting(true);
    setTestResult(null);

    try {
      const success = await onTest(formData);
      setTestResult({
        success,
        message: success ? 'Connection successful! Found FOCUS-compliant data.' : 'Connection failed. Please check your configuration.'
      });
    } catch (error) {
      setTestResult({
        success: false,
        message: error instanceof Error ? error.message : 'Connection test failed'
      });
    } finally {
      setTesting(false);
    }
  };

  const handleSave = async () => {
    if (!validateForm()) {
      return;
    }

    setSaving(true);
    try {
      await onSave(formData);
    } catch (error) {
      console.error('Failed to save configuration:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleInputChange = (field: keyof AzureBlobStorageConfig, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  return (
    <div className="azure-blob-storage-plugin">
      <div className="plugin-header">
        <h3>{mode === 'create' ? 'Add Azure Blob Storage Connection' : 'Edit Azure Blob Storage Connection'}</h3>
        <p>Configure connection to Azure Blob Storage for FOCUS-compliant billing data</p>
      </div>

      <div className="plugin-form">
        <div className="form-section">
          <h4>Connection Details</h4>
          
          <div className="form-group">
            <label htmlFor="name">Connection Name *</label>
            <input
              id="name"
              type="text"
              value={formData.name}
              onChange={(e) => handleInputChange('name', e.target.value)}
              placeholder="e.g., NCEI Production Billing Data"
              className={errors.name ? 'error' : ''}
            />
            {errors.name && <span className="error-message">{errors.name}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="description">Description</label>
            <textarea
              id="description"
              value={formData.description || ''}
              onChange={(e) => handleInputChange('description', e.target.value)}
              placeholder="Optional description for this connection"
              rows={3}
            />
          </div>
        </div>

        <div className="form-section">
          <h4>Azure Blob Storage Configuration</h4>
          
          <div className="form-group">
            <label htmlFor="accountUrl">Storage Account URL *</label>
            <input
              id="accountUrl"
              type="text"
              value={formData.accountUrl}
              onChange={(e) => handleInputChange('accountUrl', e.target.value)}
              placeholder="https://youraccount.blob.core.windows.net"
              className={errors.accountUrl ? 'error' : ''}
            />
            {errors.accountUrl && <span className="error-message">{errors.accountUrl}</span>}
            <small className="field-help">The base URL of your Azure Storage account</small>
          </div>

          <div className="form-group">
            <label htmlFor="sasToken">SAS Token *</label>
            <textarea
              id="sasToken"
              value={formData.sasToken}
              onChange={(e) => handleInputChange('sasToken', e.target.value)}
              placeholder="sv=2024-11-04&ss=bfqt&srt=sco&sp=rltfx..."
              className={errors.sasToken ? 'error' : ''}
              rows={3}
            />
            {errors.sasToken && <span className="error-message">{errors.sasToken}</span>}
            <small className="field-help">Shared Access Signature token with read permissions</small>
          </div>

          <div className="form-group">
            <label htmlFor="containerName">Primary Container Name *</label>
            <input
              id="containerName"
              type="text"
              value={formData.containerName}
              onChange={(e) => handleInputChange('containerName', e.target.value)}
              placeholder="billing-data"
              className={errors.containerName ? 'error' : ''}
            />
            {errors.containerName && <span className="error-message">{errors.containerName}</span>}
            <small className="field-help">Name of the primary blob container containing FOCUS data</small>
          </div>

          <div className="form-group">
            <label htmlFor="secondaryContainer">Secondary Container Name</label>
            <input
              id="secondaryContainer"
              type="text"
              value={formData.secondaryContainer || ''}
              onChange={(e) => handleInputChange('secondaryContainer', e.target.value)}
              placeholder="backup-billing-data"
            />
            <small className="field-help">Optional secondary container for backup or additional data sources</small>
          </div>

          <div className="form-group">
            <label htmlFor="pathPrefix">Path Prefix</label>
            <input
              id="pathPrefix"
              type="text"
              value={formData.pathPrefix || ''}
              onChange={(e) => handleInputChange('pathPrefix', e.target.value)}
              placeholder="focus-data/"
            />
            <small className="field-help">Optional path prefix to filter files (e.g., "focus-data/")</small>
          </div>
        </div>

        <div className="form-section">
          <h4>Sync Configuration</h4>
          
          <div className="form-group">
            <label htmlFor="syncFrequency">Sync Frequency</label>
            <select
              id="syncFrequency"
              value={formData.syncFrequency}
              onChange={(e) => handleInputChange('syncFrequency', e.target.value)}
            >
              <option value="hourly">Hourly</option>
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="manual">Manual Only</option>
            </select>
            <small className="field-help">How often to check for new FOCUS data files</small>
          </div>

          <div className="form-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={formData.isActive}
                onChange={(e) => handleInputChange('isActive', e.target.checked)}
              />
              <span>Enable automatic sync</span>
            </label>
            <small className="field-help">When enabled, data will be synced according to the frequency above</small>
          </div>

          {formData.lastSync && (
            <div className="form-group">
              <label>Last Sync</label>
              <div className="readonly-field">
                {new Date(formData.lastSync).toLocaleString()}
              </div>
            </div>
          )}
        </div>

        {testResult && (
          <div className={`test-result ${testResult.success ? 'success' : 'error'}`}>
            <div className="test-result-icon">
              {testResult.success ? '✓' : '✗'}
            </div>
            <div className="test-result-message">
              {testResult.message}
            </div>
          </div>
        )}

        <div className="form-actions">
          <button
            type="button"
            onClick={handleTestConnection}
            disabled={testing}
            className="test-button"
          >
            {testing ? 'Testing...' : 'Test Connection'}
          </button>
          
          <div className="action-buttons">
            <button
              type="button"
              onClick={onCancel}
              className="cancel-button"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleSave}
              disabled={saving}
              className="save-button"
            >
              {saving ? 'Saving...' : 'Save Configuration'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AzureBlobStoragePlugin;