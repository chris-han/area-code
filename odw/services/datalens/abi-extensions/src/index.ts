/**
 * Azure Billing Intelligence Extensions for DataLens
 * 
 * This module provides FOCUS-compliant widgets and dashboards
 * specifically designed for Azure billing analytics.
 */

// Import shared styles
import './styles/widgets.css';
import './styles/plugins.css';
import './styles/plugin-management.css';
import './styles/cost-optimization.css';
import './styles/azure-blob-storage.css';

// Export widgets
export { default as FOCUSCostTrendWidget } from './widgets/FOCUSCostTrendWidget';
export { default as ResourceUtilizationHeatmap } from './widgets/ResourceUtilizationHeatmap';
export { default as ServiceCategoryBreakdown } from './widgets/ServiceCategoryBreakdown';
export { default as BudgetTrackingWidget } from './widgets/BudgetTrackingWidget';
export { default as CostOptimizationRecommendations } from './widgets/CostOptimizationRecommendations';

// Export dashboards
export { default as CostOptimizationDashboard } from './dashboards/CostOptimizationDashboard';
export { default as ResourceUtilizationDashboard } from './dashboards/ResourceUtilizationDashboard';
export { default as BudgetTrackingDashboard } from './dashboards/BudgetTrackingDashboard';

// Export plugin marketplace components
export { default as PluginMarketplace } from './plugins/PluginMarketplace';
export { default as PluginDiscovery } from './plugins/PluginDiscovery';
export { default as PluginInstallationWizard } from './plugins/PluginInstallationWizard';
export { default as PluginManagementDashboard } from './plugins/PluginManagementDashboard';
export { default as PluginMarketplaceIntegration } from './plugins/PluginMarketplaceIntegration';

// Export Azure Blob Storage plugin components
export { default as AzureBlobStoragePlugin } from './plugins/AzureBlobStoragePlugin';
export { default as AzureBlobStorageManager } from './plugins/AzureBlobStorageManager';

// Export types and utilities
export * from './types/focus-types';
export * from './utils/focus-helpers';

// Export services
export { AzureBlobStorageService } from './services/AzureBlobStorageService';