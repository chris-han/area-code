/**
 * Budget Tracking Dashboard
 * FOCUS-compliant dashboard for budget monitoring and variance analysis
 */

import React, { useState } from 'react';
import BudgetTrackingWidget from '../widgets/BudgetTrackingWidget';
import FOCUSCostTrendWidget from '../widgets/FOCUSCostTrendWidget';
import ServiceCategoryBreakdown from '../widgets/ServiceCategoryBreakdown';
import { FOCUSFilterOptions } from '../types/focus-types';

interface BudgetTrackingDashboardProps {
  defaultFilters?: Partial<FOCUSFilterOptions>;
}

const BudgetTrackingDashboard: React.FC<BudgetTrackingDashboardProps> = ({
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
    <div className="budget-tracking-dashboard">
      <div className="dashboard-header">
        <h1>Budget Tracking & Variance Analysis</h1>
        <p>FOCUS-compliant budget monitoring and cost forecasting</p>
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
          <BudgetTrackingWidget
            title="Budget vs Actual Analysis"
            height={500}
            defaultFilters={globalFilters}
          />
        </div>

        <div className="grid-item half-width">
          <FOCUSCostTrendWidget
            title="Cost Trends"
            height={400}
            defaultFilters={globalFilters}
          />
        </div>

        <div className="grid-item half-width">
          <ServiceCategoryBreakdown
            title="Cost Breakdown"
            height={400}
            defaultFilters={globalFilters}
          />
        </div>
      </div>
    </div>
  );
};

export default BudgetTrackingDashboard;
