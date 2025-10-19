/**
 * Budget Tracking Widget
 * FOCUS-compliant budget vs actual cost visualization
 */

import React, { useState, useEffect } from 'react';
import { FOCUSFilterOptions, BudgetData } from '../types/focus-types';
import { formatFOCUSCurrency } from '../utils/focus-helpers';

interface BudgetTrackingWidgetProps {
  title?: string;
  height?: number;
  defaultFilters?: Partial<FOCUSFilterOptions>;
  onDataChange?: (data: BudgetData[]) => void;
}

const BudgetTrackingWidget: React.FC<BudgetTrackingWidgetProps> = ({
  title = "Budget vs Actual Cost Analysis",
  height = 400,
  defaultFilters = {},
  onDataChange
}) => {
  const [data, setData] = useState<BudgetData[]>([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState<FOCUSFilterOptions>({
    dateRange: {
      start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      end: new Date().toISOString().split('T')[0]
    },
    ...defaultFilters
  });

  useEffect(() => {
    fetchBudgetData();
  }, [filters]);

  const fetchBudgetData = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/focus/budget-tracking', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          start_date: filters.dateRange.start,
          end_date: filters.dateRange.end,
          billing_account_ids: filters.subscriptionIds
        })
      });

      const result = await response.json();
      const budgetData: BudgetData[] = result.budgets || [];
      
      setData(budgetData);
      onDataChange?.(budgetData);
    } catch (error) {
      console.error('Failed to fetch budget data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getVarianceColor = (variance: number) => {
    if (variance > 10) return '#ef4444'; // Red - over budget
    if (variance > 0) return '#f59e0b'; // Orange - approaching budget
    return '#10b981'; // Green - under budget
  };

  const getVarianceStatus = (variance: number) => {
    if (variance > 10) return 'Over Budget';
    if (variance > 0) return 'At Risk';
    return 'On Track';
  };

  return (
    <div className="budget-tracking-widget" style={{ height }}>
      <div className="widget-header">
        <h3>{title}</h3>
      </div>

      <div className="widget-filters">
        <input
          type="date"
          value={filters.dateRange.start}
          onChange={(e) => setFilters({
            ...filters,
            dateRange: { ...filters.dateRange, start: e.target.value }
          })}
        />
        <input
          type="date"
          value={filters.dateRange.end}
          onChange={(e) => setFilters({
            ...filters,
            dateRange: { ...filters.dateRange, end: e.target.value }
          })}
        />
      </div>

      <div className="budget-list">
        {loading ? (
          <div className="loading">Loading budget data...</div>
        ) : (
          data.map((budget, index) => (
            <div key={`${budget.budget_name}-${index}`} className="budget-item">
              <div className="budget-header">
                <span className="budget-name">{budget.budget_name}</span>
                <span 
                  className="budget-status"
                  style={{ color: getVarianceColor(budget.variance_percentage) }}
                >
                  {getVarianceStatus(budget.variance_percentage)}
                </span>
              </div>

              <div className="budget-metrics">
                <div className="metric">
                  <span className="metric-label">Budget</span>
                  <span className="metric-value">
                    {formatFOCUSCurrency(budget.budget_amount)}
                  </span>
                </div>
                <div className="metric">
                  <span className="metric-label">Actual</span>
                  <span className="metric-value">
                    {formatFOCUSCurrency(budget.actual_spend)}
                  </span>
                </div>
                <div className="metric">
                  <span className="metric-label">Forecast</span>
                  <span className="metric-value">
                    {formatFOCUSCurrency(budget.forecasted_spend)}
                  </span>
                </div>
                <div className="metric">
                  <span className="metric-label">Variance</span>
                  <span 
                    className="metric-value"
                    style={{ color: getVarianceColor(budget.variance_percentage) }}
                  >
                    {budget.variance_percentage > 0 ? '+' : ''}
                    {budget.variance_percentage.toFixed(1)}%
                  </span>
                </div>
              </div>

              <div className="budget-bar">
                <div 
                  className="bar-actual" 
                  style={{ 
                    width: `${Math.min((budget.actual_spend / budget.budget_amount) * 100, 100)}%`,
                    backgroundColor: getVarianceColor(budget.variance_percentage)
                  }}
                />
                <div 
                  className="bar-forecast" 
                  style={{ 
                    width: `${Math.min((budget.forecasted_spend / budget.budget_amount) * 100, 100)}%`,
                    backgroundColor: `${getVarianceColor(budget.variance_percentage)}40`
                  }}
                />
              </div>

              <div className="budget-period">
                Period: {budget.period}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default BudgetTrackingWidget;
