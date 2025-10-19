/**
 * Plugin Configuration Component
 * 
 * Interface for configuring plugin settings and testing connections
 */

import React, { useState, useEffect } from 'react';
import { Save, TestTube, AlertCircle, CheckCircle, Settings, Eye, EyeOff } from 'lucide-react';

interface ConfigField {
  name: string;
  type: string;
  description: string;
  required?: boolean;
  default?: any;
  enum?: string[];
  minimum?: number;
  maximum?: number;
  pattern?: string;
  format?: string;
}

interface ConfigSchema {
  type: string;
  properties: Record<string, ConfigField>;
  required?: string[];
}

interface Plugin {
  id: string;
  name: string;
  display_name: string;
  description: string;
  version: string;
  config_schema: ConfigSchema;
  default_config?: Record<string, any>;
}

interface ValidationError {
  field: string;
  message: string;
}

interface PluginConfigurationProps {
  plugin: Plugin;
  currentConfig?: Record<string, any>;
  onSave: (config: Record<string, any>) => void;
  onCancel: () => void;
  onTest?: (config: Record<string, any>) => Promise<boolean>;
}

const PluginConfiguration: React.FC<PluginConfigurationProps> = ({
  plugin,
  currentConfig = {},
  onSave,
  onCancel,
  onTest
}) => {
  const [config, setConfig] = useState<Record<string, any>>(currentConfig);
  const [errors, setErrors] = useState<ValidationError[]>([]);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);
  const [showPasswords, setShowPasswords] = useState<Record<string, boolean>>({});

  useEffect(() => {
    // Initialize config with defaults
    const initialConfig = { ...plugin.default_config, ...currentConfig };
    setConfig(initialConfig);
  }, [plugin, currentConfig]);

  const validateConfig = (): ValidationError[] => {
    const validationErrors: ValidationError[] = [];
    const schema = plugin.config_schema;

    // Check required fields
    if (schema.required) {
      for (const fieldName of schema.required) {
        if (!config[fieldName] || config[fieldName] === '') {
          validationErrors.push({
            field: fieldName,
            message: `${fieldName} is required`
          });
        }
      }
    }

    // Validate field types and constraints
    Object.entries(schema.properties).forEach(([fieldName, fieldSchema]) => {
      const value = config[fieldName];
      
      if (value !== undefined && value !== null && value !== '') {
        // Type validation
        if (fieldSchema.type === 'integer' && !Number.isInteger(Number(value))) {
          validationErrors.push({
            field: fieldName,
            message: `${fieldName} must be an integer`
          });
        }
        
        if (fieldSchema.type === 'number' && isNaN(Number(value))) {
          validationErrors.push({
            field: fieldName,
            message: `${fieldName} must be a number`
          });
        }

        // Range validation
        if (fieldSchema.minimum !== undefined && Number(value) < fieldSchema.minimum) {
          validationErrors.push({
            field: fieldName,
            message: `${fieldName} must be at least ${fieldSchema.minimum}`
          });
        }

        if (fieldSchema.maximum !== undefined && Number(value) > fieldSchema.maximum) {
          validationErrors.push({
            field: fieldName,
            message: `${fieldName} must be at most ${fieldSchema.maximum}`
          });
        }

        // Pattern validation
        if (fieldSchema.pattern && typeof value === 'string') {
          const regex = new RegExp(fieldSchema.pattern);
          if (!regex.test(value)) {
            validationErrors.push({
              field: fieldName,
              message: `${fieldName} format is invalid`
            });
          }
        }

        // Enum validation
        if (fieldSchema.enum && !fieldSchema.enum.includes(value)) {
          validationErrors.push({
            field: fieldName,
            message: `${fieldName} must be one of: ${fieldSchema.enum.join(', ')}`
          });
        }
      }
    });

    return validationErrors;
  };

  const handleFieldChange = (fieldName: string, value: any) => {
    setConfig(prev => ({ ...prev, [fieldName]: value }));
    
    // Clear field-specific errors
    setErrors(prev => prev.filter(error => error.field !== fieldName));
    setTestResult(null);
  };

  const handleSave = () => {
    const validationErrors = validateConfig();
    
    if (validationErrors.length > 0) {
      setErrors(validationErrors);
      return;
    }

    setErrors([]);
    onSave(config);
  };

  const handleTest = async () => {
    if (!onTest) return;

    const validationErrors = validateConfig();
    if (validationErrors.length > 0) {
      setErrors(validationErrors);
      return;
    }

    setTesting(true);
    setTestResult(null);

    try {
      const success = await onTest(config);
      setTestResult({
        success,
        message: success ? 'Connection test successful' : 'Connection test failed'
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

  const togglePasswordVisibility = (fieldName: string) => {
    setShowPasswords(prev => ({
      ...prev,
      [fieldName]: !prev[fieldName]
    }));
  };

  const renderField = (fieldName: string, fieldSchema: ConfigField) => {
    const value = config[fieldName] || '';
    const error = errors.find(e => e.field === fieldName);
    const isPassword = fieldSchema.format === 'password';
    const showPassword = showPasswords[fieldName];

    return (
      <div key={fieldName} className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          {fieldName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
          {fieldSchema.required && <span className="text-red-500 ml-1">*</span>}
        </label>
        
        {fieldSchema.description && (
          <p className="text-sm text-gray-500 mb-2">{fieldSchema.description}</p>
        )}

        <div className="relative">
          {fieldSchema.enum ? (
            <select
              value={value}
              onChange={(e) => handleFieldChange(fieldName, e.target.value)}
              className={`w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                error ? 'border-red-300' : 'border-gray-300'
              }`}
            >
              <option value="">Select an option</option>
              {fieldSchema.enum.map(option => (
                <option key={option} value={option}>{option}</option>
              ))}
            </select>
          ) : fieldSchema.type === 'boolean' ? (
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={Boolean(value)}
                onChange={(e) => handleFieldChange(fieldName, e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="ml-2 text-sm text-gray-700">
                {fieldSchema.description || 'Enable this option'}
              </span>
            </label>
          ) : (
            <>
              <input
                type={
                  isPassword && !showPassword ? 'password' :
                  fieldSchema.type === 'integer' || fieldSchema.type === 'number' ? 'number' :
                  'text'
                }
                value={value}
                onChange={(e) => handleFieldChange(fieldName, e.target.value)}
                placeholder={fieldSchema.default ? `Default: ${fieldSchema.default}` : ''}
                min={fieldSchema.minimum}
                max={fieldSchema.maximum}
                className={`w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                  error ? 'border-red-300' : 'border-gray-300'
                } ${isPassword ? 'pr-10' : ''}`}
              />
              
              {isPassword && (
                <button
                  type="button"
                  onClick={() => togglePasswordVisibility(fieldName)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              )}
            </>
          )}
        </div>

        {error && (
          <p className="mt-1 text-sm text-red-600 flex items-center">
            <AlertCircle className="w-4 h-4 mr-1" />
            {error.message}
          </p>
        )}
      </div>
    );
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center space-x-3 mb-4">
          <Settings className="w-8 h-8 text-blue-600" />
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Configure Plugin</h1>
            <p className="text-gray-600">{plugin.display_name} v{plugin.version}</p>
          </div>
        </div>
        
        {plugin.description && (
          <p className="text-gray-700 bg-gray-50 p-4 rounded-md">{plugin.description}</p>
        )}
      </div>

      {/* Test Result */}
      {testResult && (
        <div className={`mb-6 p-4 rounded-md flex items-center space-x-2 ${
          testResult.success ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
        }`}>
          {testResult.success ? (
            <CheckCircle className="w-5 h-5" />
          ) : (
            <AlertCircle className="w-5 h-5" />
          )}
          <span className="font-medium">{testResult.message}</span>
        </div>
      )}

      {/* Configuration Form */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-6">Configuration Settings</h2>
        
        <form onSubmit={(e) => { e.preventDefault(); handleSave(); }}>
          {Object.entries(plugin.config_schema.properties).map(([fieldName, fieldSchema]) =>
            renderField(fieldName, fieldSchema)
          )}

          {/* Actions */}
          <div className="flex items-center justify-between pt-6 border-t border-gray-200">
            <div className="flex space-x-3">
              <button
                type="submit"
                disabled={errors.length > 0}
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
              >
                <Save className="w-4 h-4" />
                <span>Save Configuration</span>
              </button>

              {onTest && (
                <button
                  type="button"
                  onClick={handleTest}
                  disabled={testing || errors.length > 0}
                  className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
                >
                  {testing ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  ) : (
                    <TestTube className="w-4 h-4" />
                  )}
                  <span>{testing ? 'Testing...' : 'Test Connection'}</span>
                </button>
              )}
            </div>

            <button
              type="button"
              onClick={onCancel}
              className="border border-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>

      {/* Configuration Preview */}
      <div className="mt-6 bg-gray-50 rounded-lg p-4">
        <h3 className="text-sm font-medium text-gray-900 mb-2">Configuration Preview</h3>
        <pre className="text-xs text-gray-600 overflow-x-auto">
          {JSON.stringify(config, null, 2)}
        </pre>
      </div>
    </div>
  );
};

export default PluginConfiguration;