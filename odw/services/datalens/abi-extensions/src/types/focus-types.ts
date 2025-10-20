/**
 * FOCUS Specification Types for DataLens ABI Extensions
 */

export interface FOCUSBillingData {
  billing_account_id: string;
  usage_date: string;
  billed_cost: number;
  service_category: string;
  service_name: string;
  resource_type: string;
  resource_id?: string;
  resource_name?: string;
  region?: string;
  availability_zone?: string;
  subscription_id?: string;
  resource_group?: string;
  tags?: Record<string, string>;
  currency: string;
  pricing_unit?: string;
  usage_quantity?: number;
  usage_unit?: string;
}

export interface FOCUSFilterOptions {
  dateRange: {
    start: string;
    end: string;
  };
  subscriptionIds?: string[];
  resourceGroups?: string[];
  serviceCategories?: string[];
  regions?: string[];
}

export interface CostTrendData {
  date: string;
  cost: number;
  currency: string;
  service_category?: string;
}

export interface ResourceUtilizationData {
  resource_id: string;
  resource_name: string;
  resource_type: string;
  utilization_percentage: number;
  cost: number;
  efficiency_score: number;
}

export interface BudgetData {
  budget_name: string;
  budget_amount: number;
  actual_spend: number;
  forecasted_spend: number;
  variance_percentage: number;
  period: string;
}

export interface ServiceBreakdownData {
  service_category: string;
  service_name: string;
  cost: number;
  percentage: number;
  trend: 'up' | 'down' | 'stable';
}

/**
 * Plugin Marketplace Types
 */
export interface PluginMetadata {
  id: string;
  name: string;
  version: string;
  description: string;
  author: string;
  category: 'billing' | 'storage' | 'analytics' | 'custom';
  tags: string[];
  iconUrl?: string;
  documentationUrl?: string;
  configSchema: Record<string, any>;
  isInstalled: boolean;
  isConfigured: boolean;
  isActive: boolean;
  downloadCount?: number;
  rating?: number;
  lastUpdated: string;
}

export interface PluginConfiguration {
  pluginName: string;
  connectorName: string;
  config: Record<string, any>;
  isValid: boolean;
  lastTested?: string;
  connectionStatus: 'connected' | 'disconnected' | 'error' | 'testing';
  errorMessage?: string;
}

export interface DataSourceConnector {
  id: string;
  name: string;
  type: string;
  pluginName: string;
  configuration: Record<string, any>;
  status: 'active' | 'inactive' | 'error';
  lastSync?: string;
  recordsProcessed?: number;
  syncFrequency?: string;
}

export interface PluginInstallationRequest {
  pluginName: string;
  version?: string;
  autoActivate?: boolean;
}

export interface PluginConfigurationRequest {
  pluginName: string;
  connectorName: string;
  configuration: Record<string, any>;
  testConnection?: boolean;
}