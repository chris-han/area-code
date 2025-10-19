/**
 * Service Category Breakdown Widget
 * FOCUS-compliant cost allocation visualization
 */

import React, { useState, useEffect } from 'react';
import { FOCUSFilterOptions, ServiceBreakdownData } from '../types/focus-types';
import { formatFOCUSCurrency } from '../utils/focus-helpers';

interface ServiceCategoryBreakdownProps {
  title?: string;
  height?: number;
  defaultFilters?: Partial<FOCUSFilterOptions>;
  onDataChange?: (data: ServiceBreakdownData[]) => void;
}

const ServiceCategoryBreakdown: React.FC<ServiceCategoryBreakdownProps> = ({
  title = "Cost Allocation by Service Category",
  height = 400,
  defaultFilters = {},
  onDataChange
}) => {
  const [data, setData] = useState<ServiceBreakdownData[]>([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState<FOCUSFilterOptions>({
    dateRange: {
      start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      end: new Date().toISOString().split('T')[0]
    },
    ...defaultFilters
  });

  useEffect(() => {
    fetchBreakdownData();
  }, [filters]);

  const fetchBreakdownData = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/focus/aggregation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          group_by: ['service_category', 'service_name'],
          metrics: ['total_cost'],
          start_date: filters.dateRange.start,
          end_date: filters.dateRange.end
        })
      });

      const result = await response.json();
      const results = result.results || [];
      
      const totalCost = results.reduce((sum: number, item: any) => 
        sum + item.metrics.total_cost, 0);

      const breakdownData: ServiceBreakdownData[] = results.map((item: any) => ({
        service_category: item.dimensions.service_category,
        service_name: item.dimensions.service_name,
        cost: item.metrics.total_cost,
        percentage: (item.metrics.total_cost / totalCost) * 100,
        trend: 'stable' as const
      }));

      breakdownData.sort((a, b) => b.cost - a.cost);
      setData(breakdownData);
      onDataChange?.(breakdownData);
    } catch (error) {
      console.error('Failed to fetch breakdown data:', error);
    } finally {
      setLoading(false);
    }
  };

  const totalCost = data.reduce((sum, item) => sum + item.cost, 0);

  return (
    <div className="service-category-breakdown" style={{ height }}>
      <div className="widget-header">
        <h3>{title}</h3>
        <div className="total-cost">
          Total: {formatFOCUSCurrency(totalCost)}
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

      <div className="breakdown-list">
        {loading ? (
          <div className="loading">Loading breakdown data...</div>
        ) : (
          data.map((item, index) => (
            <div key={`${item.service_category}-${index}`} className="breakdown-item">
              <div className="item-header">
                <span className="category-name">{item.service_category}</span>
                <span className="category-cost">{formatFOCUSCurrency(item.cost)}</span>
              </div>
              <div className="item-bar">
                <div 
                  className="bar-fill" 
                  style={{ 
                    width: `${item.percentage}%`,
                    backgroundColor: `hsl(${index * 36}, 70%, 50%)`
                  }}
                />
              </div>
              <div className="item-details">
                <span className="service-name">{item.service_name}</span>
                <span className="percentage">{item.percentage.toFixed(1)}%</span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default ServiceCategoryBreakdown;
