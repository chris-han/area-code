import React from 'react';
import { PluginMarketplace } from './PluginMarketplace';

/**
 * Integration component for the Plugin Marketplace within DataLens
 * 
 * This component provides the main entry point for plugin management
 * functionality within the DataLens interface. It can be embedded
 * as a tab, modal, or dedicated page within the DataLens UI.
 */

interface PluginMarketplaceIntegrationProps {
  /** Whether to show the marketplace in a modal or inline */
  mode?: 'modal' | 'inline';
  /** Optional callback when marketplace is closed (for modal mode) */
  onClose?: () => void;
  /** Custom CSS class for styling */
  className?: string;
}

export const PluginMarketplaceIntegration: React.FC<PluginMarketplaceIntegrationProps> = ({
  mode = 'inline',
  onClose,
  className
}) => {
  if (mode === 'modal') {
    return (
      <div className="plugin-marketplace-modal">
        <div className="modal-backdrop" onClick={onClose} />
        <div className="modal-content">
          <div className="modal-header">
            <h2>Plugin Marketplace</h2>
            <button onClick={onClose} className="close-button">×</button>
          </div>
          <div className="modal-body">
            <PluginMarketplace className={className} />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`plugin-marketplace-integration ${className || ''}`}>
      <PluginMarketplace />
    </div>
  );
};

export default PluginMarketplaceIntegration;