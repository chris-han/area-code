/**
 * Azure Blob Storage Plugin Integration Example
 * Shows how to integrate the Azure Blob Storage plugin into DataLens
 */

import React, { useState } from 'react';
import { AzureBlobStorageManager } from '../plugins/AzureBlobStorageManager';

export const AzureBlobStorageExample: React.FC = () => {
  const [showManager, setShowManager] = useState(false);

  return (
    <div className="azure-blob-storage-example">
      <div className="example-header">
        <h2>Azure Blob Storage Integration</h2>
        <p>
          This example demonstrates how to integrate Azure Blob Storage as a data source 
          for FOCUS-compliant billing data within DataLens.
        </p>
        
        <div className="example-info">
          <h3>Pre-configured Connection Details:</h3>
          <ul>
            <li><strong>Account URL:</strong> https://finopsbilling.blob.core.chinacloudapi.cn</li>
            <li><strong>Data Format:</strong> FOCUS-compliant Parquet files</li>
            <li><strong>Use Case:</strong> NCEI (National Cloud Economics Intelligence) data source</li>
            <li><strong>Container Support:</strong> Primary and optional secondary containers</li>
            <li><strong>Storage:</strong> Configuration stored in PostgreSQL</li>
          </ul>
        </div>

        <button
          onClick={() => setShowManager(!showManager)}
          className="toggle-manager-button"
        >
          {showManager ? 'Hide' : 'Show'} Azure Blob Storage Manager
        </button>
      </div>

      {showManager && (
        <div className="manager-container">
          <AzureBlobStorageManager />
        </div>
      )}

      <div className="example-features">
        <h3>Key Features:</h3>
        <div className="features-grid">
          <div className="feature-card">
            <h4>🔧 Configuration UI</h4>
            <p>User-friendly interface for setting up Azure Blob Storage connections with validation</p>
          </div>
          
          <div className="feature-card">
            <h4>🧪 Connection Testing</h4>
            <p>Built-in connection testing to verify access to Azure Blob Storage containers</p>
          </div>
          
          <div className="feature-card">
            <h4>📊 FOCUS Compliance</h4>
            <p>Automatic validation of FOCUS specification compliance for billing data</p>
          </div>
          
          <div className="feature-card">
            <h4>🔄 Automated Sync</h4>
            <p>Configurable sync frequency (hourly, daily, weekly) with manual sync option</p>
          </div>
          
          <div className="feature-card">
            <h4>💾 PostgreSQL Storage</h4>
            <p>All plugin configurations are securely stored in PostgreSQL database</p>
          </div>
          
          <div className="feature-card">
            <h4>📈 Monitoring</h4>
            <p>Track sync history, status, and data processing metrics</p>
          </div>
          
          <div className="feature-card">
            <h4>📦 Dual Container Support</h4>
            <p>Configure primary and optional secondary containers for backup or additional data sources</p>
          </div>
        </div>
      </div>

      <div className="example-code">
        <h3>Integration Code Example:</h3>
        <pre><code>{`import { AzureBlobStorageManager } from '@workspace/datalens-abi-extensions';

// Basic usage
<AzureBlobStorageManager />

// With custom styling
<AzureBlobStorageManager className="custom-azure-manager" />

// Programmatic configuration
const service = new AzureBlobStorageService();
const config = {
  name: "NCEI Production Data",
  accountUrl: "https://finopsbilling.blob.core.chinacloudapi.cn",
  sasToken: "sv=2024-11-04&ss=bfqt...",
  containerName: "billing-data",
  secondaryContainer: "backup-billing-data", // Optional secondary container
  pathPrefix: "focus-data/",
  syncFrequency: "daily",
  isActive: true
};

await service.saveConfiguration(config);`}</code></pre>
      </div>
    </div>
  );
};

export default AzureBlobStorageExample;