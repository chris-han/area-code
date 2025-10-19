/**
 * Cost Optimization Dashboard
 * FOCUS-compliant dashboard for Azure cost optimization analysis
 */

import React, { useState } from 'react';
import FOCUSCostTrendWidget from '../widgets/FOCUSCostTrendWidget';
import ServiceCategoryBreakdown from '../widgets/ServiceCategoryBreakdown';
import ResourceUtilizationHeatmap from '../widgets/ResourceUtilizationHeatmap';
import { FOCUSFilterOptions } from '../types/focus-types';

interface CostOptimizationDashboardProps {
  defaultFilters?: Partial<FOCUSFilterOptions>;
}

const CostOptimizationDashboard: React.FC<CostOptimizationDashboardProps> = ({
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
    <div className="cost-optimization-dashboard">
      <div className="dashboard-header">
        <h1>Azure Cost Optimization Dashboard</h1>
        <p>FOCUS-compliant billing analytics and cost optimization insights</p>
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
          <FOCUSCostTrendWidget
            title="Cost Trends Over Time"
            height={400}
            defaultFilters={globalFilters}
          />
        </div>

        <div className="grid-item half-width">
          <ServiceCategoryBreakdown
            title="Cost by Service Category"
            height={400}
            defaultFilters={globalFilters}
          />
        </div>

        <div className="grid-item half-width">
          <ResourceUtilizationHeatmap
            title="Resource Utilization Heatmap"
            height={400}
            width={600}
            defaultFilters={globalFilters}
          />
        </div>
      </div>

      <style jsx>{`
        .cost-optimization-dashboard {
          padding: 24px;
          background: #f9fafb;
          min-height: 100vh;
        }

        .dashboard-header {
          margin-bottom: 24px;
        }

        .dashboard-header h1 {
          font-size: 28px;
          font-weight: 700;
          color: #111827;
          margin: 0 0 8px 0;
        }

        .dashboard-header p {
          font-size: 14px;
          color: #6b7280;
          margin: 0;
        }

        .dashboard-filters {
          background: white;
          padding: 16px;
          border-radius: 8px;
          margin-bottom: 24px;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        .filter-group {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .filter-group label {
          font-weight: 500;
          color: #374151;
        }

        .filter-group input {
          padding: 8px 12px;
          border: 1px solid #d1d5db;
          border-radius: 6px;
          font-size: 14px;
        }

        .dashboard-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 24px;
        }

        .grid-item {
          background: white;
          border-radius: 8px;
          padding: 16px;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        .grid-item.full-width {
          grid-column: 1 / -1;
        }

        .grid-item.half-width {
          grid-column: span 1;
        }

        @media (max-width: 1024px) {
          .dashboard-grid {
            grid-template-columns: 1fr;
          }

          .grid-item.half-width {
            grid-column: 1;
          }
        }
      `}</style>
    </div>
  );
};

export default CostOptimizationDashboard;
