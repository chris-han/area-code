import React, { useState, useEffect } from 'react';
import { PluginMetadata, PluginInstallationRequest, PluginConfigurationRequest } from '../types/focus-types';

interface PluginInstallationWizardProps {
  plugin: PluginMetadata;
  onComplete: () => void;
  onCancel: () => void;
}

type WizardStep = 'install' | 'configure' | 'test' | 'complete';

export const PluginInstallationWizard: React.FC<PluginInstallationWizardProps> = ({
  plugin,
  onComplete,
  onCancel
}) => {
  const [currentStep, setCurrentStep] = useState<WizardStep>('install');
  const [installing, setInstalling] = useState(false);
  const [configuring, setConfiguring] = useState(false);
  const [testing, setTesting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [configuration, setConfiguration] = useState<Record<string, any>>({});
  const [connectorName, setConnectorName] = useState('');
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (plugin.configSchema && plugin.configSchema.properties) {
      const defaultConfig: Record<string, any> = {};
      Object.entries(plugin.configSchema.properties).forEach(([key, schema]: [string, any]) => {
        if (schema.default !== undefined) {
          defaultConfig[key] = schema.default;
        }
      });
      setConfiguration(defaultConfig);
    }
  }, [plugin]);

  const handleInstall = async () => {
    try {
      setInstalling(true);
      setError(null);

      const installRequest: PluginInstallationRequest = {
        pluginName: plugin.name,
        version: plugin.version,
        autoActivate: false
      };

      const response = await fetch('/api/v1/plugins/install', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(installRequest)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Installation failed');
      }

      setCurrentStep('configure');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Installation failed');
    } finally {
      setInstalling(false);
    }
  };

  const validateConfiguration = (): boolean => {
    const errors: Record<string, string> = {};
    
    if (!connectorName.trim()) {
      errors.connectorName = 'Connector name is required';
    }

    if (plugin.configSchema && plugin.configSchema.required) {
      plugin.configSchema.required.forEach((field: string) => {
        if (!configuration[field] || configuration[field] === '') {
          errors[field] = `${field} is required`;
        }
      });
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleConfigure = async () => {
    if (!validateConfiguration()) {
      return;
    }

    try {
      setConfiguring(true);
      setError(null);

      const configRequest: PluginConfigurationRequest = {
        pluginName: plugin.name,
        connectorName: connectorName.trim(),
        configuration,
        testConnection: false
      };

      const response = await fetch('/api/v1/plugins/configure', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(configRequest)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Configuration failed');
      }

      setCurrentStep('test');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Configuration failed');
    } finally {
      setConfiguring(false);
    }
  };

  const handleTestConnection = async () => {
    try {
      setTesting(true);
      setError(null);

      const testRequest: PluginConfigurationRequest = {
        pluginName: plugin.name,
        connectorName: connectorName.trim(),
        configuration,
        testConnection: true
      };

      const response = await fetch('/api/v1/plugins/test-connection', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(testRequest)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Connection test failed');
      }

      const result = await response.json();
      if (result.success) {
        setCurrentStep('complete');
      } else {
        throw new Error(result.message || 'Connection test failed');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Connection test failed');
    } finally {
      setTesting(false);
    }
  };

  const renderConfigurationForm = () => {
    if (!plugin.configSchema || !plugin.configSchema.properties) {
      return <p>No configuration required for this plugin.</p>;
    }

    return (
      <div className="configuration-form">
        <div className="form-group">
          <label htmlFor="connectorName">Connector Name *</label>
          <input
            id="connectorName"
            type="text"
            value={connectorName}
            onChange={(e) => setConnectorName(e.target.value)}
            placeholder="Enter a unique name for this connector"
            className={validationErrors.connectorName ? 'error' : ''}
          />
          {validationErrors.connectorName && (
            <span className="error-message">{validationErrors.connectorName}</span>
          )}
        </div>

        {Object.entries(plugin.configSchema.properties).map(([key, schema]: [string, any]) => {
          const isRequired = plugin.configSchema.required?.includes(key);
          const hasError = validationErrors[key];

          return (
            <div key={key} className="form-group">
              <label htmlFor={key}>
                {schema.title || key} {isRequired && '*'}
              </label>
              
              {schema.description && (
                <p className="field-description">{schema.description}</p>
              )}

              {schema.type === 'string' && schema.enum ? (
                <select
                  id={key}
                  value={configuration[key] || ''}
                  onChange={(e) => setConfiguration(prev => ({ ...prev, [key]: e.target.value }))}
                  className={hasError ? 'error' : ''}
                >
                  <option value="">Select {schema.title || key}</option>
                  {schema.enum.map((option: string) => (
                    <option key={option} value={option}>{option}</option>
                  ))}
                </select>
              ) : schema.type === 'boolean' ? (
                <input
                  id={key}
                  type="checkbox"
                  checked={configuration[key] || false}
                  onChange={(e) => setConfiguration(prev => ({ ...prev, [key]: e.target.checked }))}
                />
              ) : schema.type === 'number' ? (
                <input
                  id={key}
                  type="number"
                  value={configuration[key] || ''}
                  onChange={(e) => setConfiguration(prev => ({ ...prev, [key]: Number(e.target.value) }))}
                  placeholder={schema.placeholder}
                  className={hasError ? 'error' : ''}
                />
              ) : (
                <input
                  id={key}
                  type={schema.format === 'password' ? 'password' : 'text'}
                  value={configuration[key] || ''}
                  onChange={(e) => setConfiguration(prev => ({ ...prev, [key]: e.target.value }))}
                  placeholder={schema.placeholder}
                  className={hasError ? 'error' : ''}
                />
              )}

              {hasError && (
                <span className="error-message">{hasError}</span>
              )}
            </div>
          );
        })}
      </div>
    );
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 'install':
        return (
          <div className="step-content">
            <h3>Install Plugin</h3>
            <div className="plugin-info">
              <h4>{plugin.name} v{plugin.version}</h4>
              <p>{plugin.description}</p>
              <p><strong>Author:</strong> {plugin.author}</p>
              <p><strong>Category:</strong> {plugin.category}</p>
            </div>
            {error && <div className="error-message">{error}</div>}
            <div className="step-actions">
              <button onClick={onCancel} className="cancel-button">Cancel</button>
              <button onClick={handleInstall} disabled={installing} className="primary-button">
                {installing ? 'Installing...' : 'Install Plugin'}
              </button>
            </div>
          </div>
        );

      case 'configure':
        return (
          <div className="step-content">
            <h3>Configure Plugin</h3>
            <p>Configure the connection settings for {plugin.name}.</p>
            {renderConfigurationForm()}
            {error && <div className="error-message">{error}</div>}
            <div className="step-actions">
              <button onClick={onCancel} className="cancel-button">Cancel</button>
              <button onClick={handleConfigure} disabled={configuring} className="primary-button">
                {configuring ? 'Saving...' : 'Save Configuration'}
              </button>
            </div>
          </div>
        );

      case 'test':
        return (
          <div className="step-content">
            <h3>Test Connection</h3>
            <p>Test the connection to ensure the plugin is configured correctly.</p>
            <div className="test-info">
              <p><strong>Plugin:</strong> {plugin.name}</p>
              <p><strong>Connector:</strong> {connectorName}</p>
            </div>
            {error && <div className="error-message">{error}</div>}
            <div className="step-actions">
              <button onClick={() => setCurrentStep('configure')} className="back-button">
                Back to Configuration
              </button>
              <button onClick={handleTestConnection} disabled={testing} className="primary-button">
                {testing ? 'Testing...' : 'Test Connection'}
              </button>
            </div>
          </div>
        );

      case 'complete':
        return (
          <div className="step-content">
            <h3>Installation Complete</h3>
            <div className="success-message">
              <p>✓ Plugin {plugin.name} has been successfully installed and configured!</p>
              <p>Connector "{connectorName}" is ready to use.</p>
            </div>
            <div className="step-actions">
              <button onClick={onComplete} className="primary-button">
                Finish
              </button>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  const getStepNumber = (step: WizardStep): number => {
    const steps: WizardStep[] = ['install', 'configure', 'test', 'complete'];
    return steps.indexOf(step) + 1;
  };

  return (
    <div className="plugin-installation-wizard">
      <div className="wizard-progress">
        <div className="progress-steps">
          {(['install', 'configure', 'test', 'complete'] as WizardStep[]).map((step, index) => (
            <div
              key={step}
              className={`progress-step ${getStepNumber(currentStep) > index + 1 ? 'completed' : ''} ${currentStep === step ? 'active' : ''}`}
            >
              <div className="step-number">{index + 1}</div>
              <div className="step-label">{step.charAt(0).toUpperCase() + step.slice(1)}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="wizard-content">
        {renderStepContent()}
      </div>
    </div>
  );
};

export default PluginInstallationWizard;
