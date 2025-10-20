/**
 * Azure Blob Storage Service
 * Handles API calls for Azure Blob Storage plugin configuration
 */

export interface AzureBlobStorageConfig {
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
  createdAt?: string;
  updatedAt?: string;
}

export interface BlobFile {
  name: string;
  size: number;
  lastModified: string;
  contentType: string;
  path: string;
}

export interface SyncResult {
  success: boolean;
  filesProcessed: number;
  recordsImported: number;
  errors: string[];
  duration: number;
}

export class AzureBlobStorageService {
  private baseUrl = '/api/v1/plugins/azure-blob-storage';

  async saveConfiguration(config: AzureBlobStorageConfig): Promise<AzureBlobStorageConfig> {
    const url = config.id ? `${this.baseUrl}/configurations/${config.id}` : `${this.baseUrl}/configurations`;
    const method = config.id ? 'PUT' : 'POST';

    const response = await fetch(url, {
      method,
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(config)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to save configuration');
    }

    return response.json();
  }

  async getConfigurations(): Promise<AzureBlobStorageConfig[]> {
    const response = await fetch(`${this.baseUrl}/configurations`);
    
    if (!response.ok) {
      throw new Error('Failed to load configurations');
    }

    const data = await response.json();
    return data.configurations || [];
  }

  async getConfiguration(id: string): Promise<AzureBlobStorageConfig> {
    const response = await fetch(`${this.baseUrl}/configurations/${id}`);
    
    if (!response.ok) {
      throw new Error('Failed to load configuration');
    }

    return response.json();
  }

  async deleteConfiguration(id: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/configurations/${id}`, {
      method: 'DELETE'
    });

    if (!response.ok) {
      throw new Error('Failed to delete configuration');
    }
  }

  async testConnection(config: AzureBlobStorageConfig): Promise<boolean> {
    const response = await fetch(`${this.baseUrl}/test-connection`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(config)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Connection test failed');
    }

    const result = await response.json();
    return result.success;
  }

  async listFiles(configId: string, path?: string): Promise<BlobFile[]> {
    const url = new URL(`${this.baseUrl}/configurations/${configId}/files`);
    if (path) {
      url.searchParams.append('path', path);
    }

    const response = await fetch(url.toString());
    
    if (!response.ok) {
      throw new Error('Failed to list files');
    }

    const data = await response.json();
    return data.files || [];
  }

  async syncData(configId: string): Promise<SyncResult> {
    const response = await fetch(`${this.baseUrl}/configurations/${configId}/sync`, {
      method: 'POST'
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Sync failed');
    }

    return response.json();
  }

  async getSyncHistory(configId: string): Promise<SyncResult[]> {
    const response = await fetch(`${this.baseUrl}/configurations/${configId}/sync-history`);
    
    if (!response.ok) {
      throw new Error('Failed to load sync history');
    }

    const data = await response.json();
    return data.history || [];
  }

  async validateFOCUSCompliance(configId: string, filePath: string): Promise<{ isCompliant: boolean; issues: string[] }> {
    const response = await fetch(`${this.baseUrl}/configurations/${configId}/validate-focus`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ filePath })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'FOCUS validation failed');
    }

    return response.json();
  }
}