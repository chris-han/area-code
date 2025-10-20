/**
 * Anomaly Detection Widget
 * FOCUS-compliant anomaly detection for cost and usage patterns
 */

import React, { useState, useEffect } from 'react';
import { FOCUSFilterOptions } from '../types/focus-types';
import { formatFOCUSCurrency } from '../utils/focus-helpers';

interface AnomalyData {
  date: string;
  service_category: string;
  expected_cost: number;
  actual_cost: number;
  anomaly_score: number;
  severity: 'low' | 'medium' | 'high';
  description: string;
}

interface AnomalyDetectionWidgetProps {
  title?: string;
  height?: number;
  defaultFilters?: Partial<FOCUSFilterOptions>;
  onAnomalyDetected?: (anomalies: AnomalyData[]) => void;
}

const AnomalyDetectionWidget: React.FC<AnomalyDetectionWidgetProps> = ({
  title = "Cost Anomaly Detection",
  height = 400,
  defaultFilters = {},
  onAnomalyDetected
}) => {
  const [anomalies, setAnomalies] = useState<AnomalyData[]>([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState<FOCUSFilterOptions>({
    dateRange: {
      start: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      end: new Date().toISOString().split('T')[0]
    },
    ...defaultFilters
  });

  useEffect(() => {
    fetchAnomalies();
  }, [filters]);

  const fetchAnomalies = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/focus/anomaly-detection', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          start_date: filters.dateRange.start,
          end_date: filters.dateRange.end,
          sensitivity: 'medium',
          service_categories: filters.serviceCategories
        })
      });

      const result = await response.json();
      const anomalyData: AnomalyData[] = result.anomalies || [];
      
      setAnomalies(anomalyData);
      onAnomalyDetected?.(anomalyData);
    } catch (error) {
      console.error('Failed to fetch anomaly data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high': return '#ef4444';
      case 'medium': return '#f59e0b';
      case 'low': return '#10b981';
      default: return '#6b7280';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'high': return '🚨';
      case 'medium': return '⚠️';
      case 'low': return '💡';
      default: return 'ℹ️';
    }
  };

  const highSeverityCount = anomalies.filter(a => a.severity === 'high').length;
  const totalImpact = anomalies.reduce((sum, a) => sum + Math.abs(a.actual_cost - a.expected_cost), 0);

  return (
    <div className="anomaly-detection-widget" style={{ height }}>
      <div className="widget-header">
        <h3>{title}</h3>
        <div className="anomaly-summary">
          <div className="summary-item">
            <span className="summary-label">High Priority</span>
            <span className="summary-value" style={{ color: '#ef4444' }}>
              {highSeverityCount}
            </span>
          </div>
          <div className="summary-item">
            <span className="summary-label">Total Impact</span>
            <span className="summary-value">
              {formatFOCUSCurrency(totalImpact)}
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

      <div className="anomaly-list">
        {loading ? (
          <div className="loading">Detecting anomalies...</div>
        ) : anomalies.length === 0 ? (
          <div className="no-anomalies">
            <span className="no-anomalies-icon">✅</span>
            <p>No significant anomalies detected in the selected period.</p>
          </div>
        ) : (
          anomalies.map((anomaly, index) => (
            <div key={`${anomaly.date}-${index}`} className="anomaly-item">
              <div className="anomaly-header">
                <span className="anomaly-icon">
                  {getSeverityIcon(anomaly.severity)}
                </span>
                <div className="anomaly-info">
                  <span className="anomaly-service">{anomaly.service_category}</span>
                  <span className="anomaly-date">{anomaly.date}</span>
                </div>
                <span 
                  className="anomaly-severity"
                  style={{ color: getSeverityColor(anomaly.severity) }}
                >
                  {anomaly.severity.toUpperCase()}
                </span>
              </div>

              <div className="anomaly-details">
                <p className="anomaly-description">{anomaly.description}</p>
                <div className="anomaly-metrics">
                  <div className="metric">
                    <span className="metric-label">Expected</span>
                    <span className="metric-value">
                      {formatFOCUSCurrency(anomaly.expected_cost)}
                    </span>
                  </div>
                  <div className="metric">
                    <span className="metric-label">Actual</span>
                    <span className="metric-value">
                      {formatFOCUSCurrency(anomaly.actual_cost)}
                    </span>
                  </div>
                  <div className="metric">
                    <span className="metric-label">Variance</span>
                    <span 
                      className="metric-value"
                      style={{ 
                        color: anomaly.actual_cost > anomaly.expected_cost ? '#ef4444' : '#10b981'
                      }}
                    >
                      {anomaly.actual_cost > anomaly.expected_cost ? '+' : ''}
                      {formatFOCUSCurrency(anomaly.actual_cost - anomaly.expected_cost)}
                    </span>
                  </div>
                  <div className="metric">
                    <span className="metric-label">Score</span>
                    <span className="metric-value">
                      {anomaly.anomaly_score.toFixed(2)}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      <style jsx>{`
        .anomaly-detection-widget {
          border: 1px solid #e5e7eb;
          border-radius: 8px;
          padding: 16px;
          background: white;
        }

        .anomaly-summary {
          display: flex;
          gap: 24px;
        }

        .summary-item {
          display: flex;
          flex-direction: column;
          align-items: flex-end;
        }

        .summary-label {
          font-size: 12px;
          color: #6b7280;
          margin-bottom: 4px;
        }

        .summary-value {
          font-size: 18px;
          font-weight: 600;
          color: #111827;
        }

        .anomaly-list {
          max-height: ${height - 120}px;
          overflow-y: auto;
        }

        .no-anomalies {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          height: 200px;
          color: #6b7280;
        }

        .no-anomalies-icon {
          font-size: 48px;
          margin-bottom: 16px;
        }

        .anomaly-item {
          padding: 16px;
          border: 1px solid #e5e7eb;
          border-radius: 8px;
          margin-bottom: 12px;
          background: #f9fafb;
        }

        .anomaly-header {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 12px;
        }

        .anomaly-icon {
          font-size: 20px;
        }

        .anomaly-info {
          flex: 1;
          display: flex;
          flex-direction: column;
        }

        .anomaly-service {
          font-weight: 600;
          color: #111827;
          font-size: 14px;
        }

        .anomaly-date {
          font-size: 12px;
          color: #6b7280;
        }

        .anomaly-severity {
          font-weight: 600;
          font-size: 12px;
          padding: 4px 8px;
          border-radius: 4px;
          background: rgba(0, 0, 0, 0.05);
        }

        .anomaly-description {
          font-size: 14px;
          color: #374151;
          margin-bottom: 12px;
          line-height: 1.4;
        }

        .anomaly-metrics {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 16px;
        }

        @media (max-width: 768px) {
          .anomaly-metrics {
            grid-template-columns: repeat(2, 1fr);
          }
        }
      `}</style>
    </div>
  );
};

export default AnomalyDetectionWidget;