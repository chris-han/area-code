/**
 * Resource Utilization Heatmap Widget
 * 
 * FOCUS-compliant heatmap visualization showing resource utilization
 * across services and regions with interactive filtering
 */

import React, { useState, useEffect } from 'react';
import { FOCUSFilterOptions, ResourceUtilizationData } from '../types/focus-types';
import { buildFOCUSQuery, formatFOCUSCurrency } from '../utils/focus-helpers';

interface ResourceUtilizationHeatmapProps {
  title?: string;
  height?: number;
  width?: number;
  defaultFilters?: Partial<FOCUSFilterOptions>;
  onDataChange?: (data: ResourceUtilizationData[]) => void;
}

interface HeatmapCell {
  service_name: string;
  region: string;
  utilization: number;
  cost: number;
  efficiency_score: number;
  color: string;
}

const ResourceUtilizationHeatmap: React.FC<ResourceUtilizationHeatmapProps> = ({
  title = "Resource Utilization by Service and Region",
  height = 500,
  width = 800,
  defaultFilters = {},
  onDataChange
}) => {
  const [data, setData] = useState<HeatmapCell[]>([]);
  const [loading, setLoading] = useState(false);
  const [services, setServices] = useState<string[]>([]);
  const [regions, setRegions] = useState<string[]>([]);
  const [selectedMetric, setSelectedMetric] = useState<'utilization' | 'cost' | 'efficiency'>('utilization');
  const [filters, setFilters] = useState<FOCUSFilterOptions>({
    dateRange: {
      start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      end: new Date().toISOString().split('T')[0]
    },
    ...defaultFilters
  });

  useEffect(() => {
    fetchHeatmapData();
  }, [filters, selectedMetric]);

  const fetchHeatmapData = async () => {
    setLoading(true);
    try {
      const query = `
        SELECT 
          service_name,
          region,
          sum(billed_cost) as total_cost,
          sum(usage_quantity) as total_usage,
          count(*) as resource_count,
          avg(billed_cost / nullIf(usage_quantity, 0)) as cost_per_unit,
          (sum(usage_quantity) / count(*)) as avg_utilization
        FROM focus_billing_data
        WHERE usage_date >= '${filters.dateRange.start}'
          AND usage_date <= '${filters.dateRange.end}'
          AND service_name IS NOT NULL
          AND region IS NOT NULL
        GROUP BY service_name, region
        HAVING total_cost > 0
        ORDER BY service_name, region
      `;

      const response = await fetch('/api/v1/focus/aggregation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          group_by: ['service_name', 'region'],
          metrics: ['total_cost', 'avg_utilization', 'efficiency_score'],
          start_date: filters.dateRange.start,
          end_date: filters.dateRange.end
        })
      });

      const result = await response.json();
      const rawData = result.results || [];
      
      // Process data into heatmap cells
      const uniqueServices = [...new Set(rawData.map((item: any) => item.dimensions.service_name))];
      const uniqueRegions = [...new Set(rawData.map((item: any) => item.dimensions.region))];
      
      setServices(uniqueServices);
      setRegions(uniqueRegions);

      // Calculate efficiency scores and colors
      const maxCost = Math.max(...rawData.map((item: any) => item.metrics.total_cost));
      const maxUtilization = Math.max(...rawData.map((item: any) => item.metrics.avg_utilization || 0));

      const heatmapData: HeatmapCell[] = rawData.map((item: any) => {
        const utilization = item.metrics.avg_utilization || 0;
        const cost = item.metrics.total_cost;
        const efficiency_score = utilization > 0 ? (cost / utilization) : 0;
        
        let color: string;
        let value: number;
        
        switch (selectedMetric) {
          case 'cost':
            value = cost / maxCost;
            color = `rgba(220, 38, 38, ${value})`;
            break;
          case 'efficiency':
            value = efficiency_score / 100;
            color = `rgba(34, 197, 94, ${value})`;
            break;
          default: // utilization
            value = utilization / maxUtilization;
            color = `rgba(59, 130, 246, ${value})`;
        }

        return {
          service_name: item.dimensions.service_name,
          region: item.dimensions.region,
          utilization,
          cost,
          efficiency_score,
          color
        };
      });

      setData(heatmapData);
      
      // Convert to ResourceUtilizationData format for callback
      const utilizationData: ResourceUtilizationData[] = heatmapData.map(cell => ({
        resource_id: `${cell.service_name}-${cell.region}`,
        resource_name: `${cell.service_name} (${cell.region})`,
        resource_type: cell.service_name,
        utilization_percentage: cell.utilization,
        cost: cell.cost,
        efficiency_score: cell.efficiency_score
      }));
      
      onDataChange?.(utilizationData);
    } catch (error) {
      console.error('Failed to fetch heatmap data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getCellData = (service: string, region: string): HeatmapCell | undefined => {
    return data.find(cell => cell.service_name === service && cell.region === region);
  };

  const cellSize = {
    width: Math.min(80, (width - 200) / regions.length),
    height: Math.min(40, (height - 150) / services.length)
  };

  return (
    <div className="resource-utilization-heatmap" style={{ height, width }}>
      <div className="widget-header">
        <h3>{title}</h3>
        <div className="widget-controls">
          <select 
            value={selectedMetric} 
            onChange={(e) => setSelectedMetric(e.target.value as any)}
            className="metric-selector"
          >
            <option value="utilization">Utilization</option>
            <option value="cost">Cost</option>
            <option value="efficiency">Efficiency</option>
          </select>
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

      <div className="heatmap-container">
        {loading ? (
          <div className="loading">Loading resource utilization data...</div>
        ) : (
          <div className="heatmap-grid">
            <svg width={width} height={height - 100}>
              {/* Column headers (regions) */}
              {regions.map((region, colIndex) => (
                <text
                  key={`region-${region}`}
                  x={150 + colIndex * cellSize.width + cellSize.width / 2}
                  y={30}
                  textAnchor="middle"
                  fontSize="12"
                  fill="#374151"
                  transform={`rotate(-45, ${150 + colIndex * cellSize.width + cellSize.width / 2}, 30)`}
                >
                  {region}
                </text>
              ))}

              {/* Row headers (services) */}
              {services.map((service, rowIndex) => (
                <text
                  key={`service-${service}`}
                  x={140}
                  y={60 + rowIndex * cellSize.height + cellSize.height / 2}
                  textAnchor="end"
                  fontSize="12"
                  fill="#374151"
                  dominantBaseline="middle"
                >
                  {service.length > 15 ? service.substring(0, 15) + '...' : service}
                </text>
              ))}

              {/* Heatmap cells */}
              {services.map((service, rowIndex) =>
                regions.map((region, colIndex) => {
                  const cellData = getCellData(service, region);
                  const x = 150 + colIndex * cellSize.width;
                  const y = 50 + rowIndex * cellSize.height;

                  return (
                    <g key={`cell-${service}-${region}`}>
                      <rect
                        x={x}
                        y={y}
                        width={cellSize.width - 1}
                        height={cellSize.height - 1}
                        fill={cellData?.color || '#f3f4f6'}
                        stroke="#e5e7eb"
                        strokeWidth="1"
                      />
                      {cellData && (
                        <title>
                          {`${service} - ${region}\n` +
                           `Cost: ${formatFOCUSCurrency(cellData.cost)}\n` +
                           `Utilization: ${cellData.utilization.toFixed(1)}%\n` +
                           `Efficiency: ${cellData.efficiency_score.toFixed(1)}`}
                        </title>
                      )}
                    </g>
                  );
                })
              )}
            </svg>

            {/* Legend */}
            <div className="heatmap-legend">
              <div className="legend-title">
                {selectedMetric === 'cost' && 'Cost Level'}
                {selectedMetric === 'utilization' && 'Utilization Level'}
                {selectedMetric === 'efficiency' && 'Efficiency Score'}
              </div>
              <div className="legend-gradient">
                <div className="legend-low">Low</div>
                <div 
                  className="legend-bar"
                  style={{
                    background: selectedMetric === 'cost' 
                      ? 'linear-gradient(to right, rgba(220, 38, 38, 0.1), rgba(220, 38, 38, 1))'
                      : selectedMetric === 'efficiency'
                      ? 'linear-gradient(to right, rgba(34, 197, 94, 0.1), rgba(34, 197, 94, 1))'
                      : 'linear-gradient(to right, rgba(59, 130, 246, 0.1), rgba(59, 130, 246, 1))'
                  }}
                />
                <div className="legend-high">High</div>
              </div>
            </div>
          </div>
        )}
      </div>

      <style jsx>{`
        .resource-utilization-heatmap {
          border: 1px solid #e5e7eb;
          border-radius: 8px;
          padding: 16px;
          background: white;
        }
        
        .widget-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
        }
        
        .widget-header h3 {
          margin: 0;
          font-size: 18px;
          font-weight: 600;
          color: #111827;
        }
        
        .widget-controls {
          display: flex;
          gap: 8px;
        }
        
        .metric-selector {
          padding: 4px 8px;
          border: 1px solid #d1d5db;
          border-radius: 4px;
          font-size: 14px;
        }
        
        .widget-filters {
          display: flex;
          gap: 8px;
          margin-bottom: 16px;
        }
        
        .widget-filters input {
          padding: 4px 8px;
          border: 1px solid #d1d5db;
          border-radius: 4px;
          font-size: 14px;
        }
        
        .heatmap-container {
          position: relative;
        }
        
        .loading {
          display: flex;
          justify-content: center;
          align-items: center;
          height: 200px;
          color: #6b7280;
        }
        
        .heatmap-legend {
          position: absolute;
          bottom: 10px;
          right: 10px;
          background: rgba(255, 255, 255, 0.9);
          padding: 8px;
          border-radius: 4px;
          border: 1px solid #e5e7eb;
        }
        
        .legend-title {
          font-size: 12px;
          font-weight: 500;
          margin-bottom: 4px;
          text-align: center;
        }
        
        .legend-gradient {
          display: flex;
          align-items: center;
          gap: 4px;
        }
        
        .legend-low, .legend-high {
          font-size: 10px;
          color: #6b7280;
        }
        
        .legend-bar {
          width: 60px;
          height: 12px;
          border-radius: 2px;
        }
      `}</style>
    </div>
  );
};

export default ResourceUtilizationHeatmap;