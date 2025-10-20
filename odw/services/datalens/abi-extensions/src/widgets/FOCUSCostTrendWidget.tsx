/**
 * FOCUS Cost Trend Widget
 * 
 * Interactive widget for displaying cost trends over time
 * with FOCUS-compliant data filtering and visualization
 */

import React, { useState, useEffect } from 'react';
import { FOCUSFilterOptions, CostTrendData } from '../types/focus-types';
import { buildFOCUSQuery, formatFOCUSCurrency } from '../utils/focus-helpers';

interface FOCUSCostTrendWidgetProps {
  title?: string;
  height?: number;
  defaultFilters?: Partial<FOCUSFilterOptions>;
  onDataChange?: (data: CostTrendData[]) => void;
}

const FOCUSCostTrendWidget: React.FC<FOCUSCostTrendWidgetProps> = ({
  title = "Cost Trends",
  height = 400,
  defaultFilters = {},
  onDataChange
}) => {
  const [data, setData] = useState<CostTrendData[]>([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState<FOCUSFilterOptions>({
    dateRange: {
      start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      end: new Date().toISOString().split('T')[0]
    },
    ...defaultFilters
  });

  useEffect(() => {
    fetchCostTrendData();
  }, [filters]);

  const fetchCostTrendData = async () => {
    setLoading(true);
    try {
      const query = `
        SELECT 
          usage_date as date,
          sum(billed_cost) as cost,
          any(currency) as currency
        FROM focus_billing_data
        WHERE usage_date >= '${filters.dateRange.start}'
          AND usage_date <= '${filters.dateRange.end}'
        GROUP BY usage_date
        ORDER BY usage_date
      `;

      // This would integrate with DataLens query execution
      const response = await fetch('/api/v1/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      });

      const result = await response.json();
      const trendData: CostTrendData[] = result.data || [];
      
      setData(trendData);
      onDataChange?.(trendData);
    } catch (error) {
      console.error('Failed to fetch cost trend data:', error);
    } finally {
      setLoading(false);
    }
  };

  const totalCost = data.reduce((sum, item) => sum + item.cost, 0);
  const avgDailyCost = data.length > 0 ? totalCost / data.length : 0;

  return (
    <div className="focus-cost-trend-widget" style={{ height }}>
      <div className="widget-header">
        <h3>{title}</h3>
        <div className="widget-metrics">
          <div className="metric">
            <span className="metric-label">Total Cost</span>
            <span className="metric-value">
              {formatFOCUSCurrency(totalCost, data[0]?.currency)}
            </span>
          </div>
          <div className="metric">
            <span className="metric-label">Avg Daily</span>
            <span className="metric-value">
              {formatFOCUSCurrency(avgDailyCost, data[0]?.currency)}
            </span>
          </div>
        </div>
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

      <div className="widget-content">
        {loading ? (
          <div className="loading">Loading cost trend data...</div>
        ) : (
          <div className="chart-container">
            {/* Chart implementation would integrate with DataLens charting */}
            <svg width="100%" height={height - 120}>
              {data.map((point, index) => (
                <g key={point.date}>
                  <circle
                    cx={50 + (index * 20)}
                    cy={height - 150 - (point.cost / Math.max(...data.map(d => d.cost)) * 100)}
                    r="3"
                    fill="#2563eb"
                  />
                  {index > 0 && (
                    <line
                      x1={50 + ((index - 1) * 20)}
                      y1={height - 150 - (data[index - 1].cost / Math.max(...data.map(d => d.cost)) * 100)}
                      x2={50 + (index * 20)}
                      y2={height - 150 - (point.cost / Math.max(...data.map(d => d.cost)) * 100)}
                      stroke="#2563eb"
                      strokeWidth="2"
                    />
                  )}
                </g>
              ))}
            </svg>
          </div>
        )}
      </div>
    </div>
  );
};

export default FOCUSCostTrendWidget;