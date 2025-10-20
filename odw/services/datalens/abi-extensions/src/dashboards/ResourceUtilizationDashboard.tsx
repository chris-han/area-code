/**
 * Resource Utilization Dashboard
 * FOCUS-compliant dashboard for resource efficiency analysis
 */

import React, { useState } from 'react';
import ResourceUtilizationHeatmap from '../widgets/ResourceUtilizationHeatmap';
import ServiceCategoryBreakdown from '../widgets/ServiceCategoryBreakdown';
import { FOCUSFilterOptions } from '../types/focus-types';

interface ResourceUtilizationDashboardProps {
  defaultFilters?: Partial<FOCUSFilterOptions>;
}

const ResourceUtilizationDashboard: React.FC<ResourceUtilizationDashboardProps> = ({
  defaultFilters = {}
}) => {
  const [globalFilters, setGlobalFilters] = useState<FOCUSFilterOptions>({
    dateRange: {
      start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      end: new Date().toISOString().split('T')[0]
    },
    ...defaultFilters
  });

  return (
    <div className="resource-utilization-dashboard">
      <div className="dashboard-header">
        <h1>Resource Utilization Analysis</h1>
        <p>FOCUS-compliant resource efficiency and utilization metrics</p>
      </div>

      <div className="dashboard-filters">
        <div className="filter-group">
          <label>Date Range</label>
          <input
            type="date"
            value={globalFilters.dateRange.start}
            onChange={(e) => setGlobalFilters({
              ...globalFilters,
              dateRange: { ...globalFilters.dateRange, start: e.target.value }
            })}
          />
          <span>to</span>
          <input
            type="date"
            value={globalFilters.dateRange.end}
            onChange={(e) => setGlobalFilters({
              ...globalFilters,
              dateRange: { ...globalFilters.dateRange, end: e.target.value }
            })}
          />
        </div>
      </div>

      <div className="dashboard-grid">
        <div className="grid-item full-width">
          <ResourceUtilizationHeatmap
            title="Resource Utilization by Service and Region"
            height={500}
            width={1200}
            defaultFilters={globalFilters}
          />
        </div>

        <div className="grid-item full-width">
          <ServiceCategoryBreakdown
            title="Service Cost Distribution"
            height={400}
            defaultFilters={globalFilters}
          />
        </div>
      </div>
    </div>
  );
};

export default ResourceUtilizationDashboard;
