/**
 * Cost Optimization Recommendations Widget
 * FOCUS-compliant cost optimization recommendations and insights
 */

import React, { useState, useEffect } from 'react';
import { FOCUSFilterOptions } from '../types/focus-types';
import { formatFOCUSCurrency } from '../utils/focus-helpers';

interface CostOptimizationRecommendation {
  id: string;
  type: 'rightsizing' | 'unused_resources' | 'reserved_instances' | 'storage_optimization' | 'scheduling';
  title: string;
  description: string;
  resource_id?: string;
  resource_name?: string;
  service_category: string;
  current_cost: number;
  potential_savings: number;
  confidence_level: 'high' | 'medium' | 'low';
  implementation_effort: 'low' | 'medium' | 'high';
  impact: 'low' | 'medium' | 'high';
  recommendation_details: string;
  action_items: string[];
  estimated_implementation_time: string;
  risk_level: 'low' | 'medium' | 'high';
  created_at: string;
  expires_at?: string;
}

interface CostOptimizationRecommendationsProps {
  filters?: FOCUSFilterOptions;
  maxRecommendations?: number;
  showFilters?: boolean;
  onRecommendationSelect?: (recommendation: CostOptimizationRecommendation) => void;
  className?: string;
}

export const CostOptimizationRecommendations: React.FC<CostOptimizationRecommendationsProps> = ({
  filters,
  maxRecommendations = 10,
  showFilters = true,
  onRecommendationSelect,
  className
}) => {
  const [recommendations, setRecommendations] = useState<CostOptimizationRecommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedType, setSelectedType] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'savings' | 'confidence' | 'impact'>('savings');
  const [expandedRecommendation, setExpandedRecommendation] = useState<string | null>(null);

  useEffect(() => {
    loadRecommendations();
  }, [filters, selectedType, sortBy]);

  const loadRecommendations = async () => {
    try {
      setLoading(true);
      setError(null);

      const queryParams = new URLSearchParams();
      
      if (filters?.dateRange) {
        queryParams.append('start_date', filters.dateRange.start);
        queryParams.append('end_date', filters.dateRange.end);
      }
      
      if (filters?.subscriptionIds?.length) {
        queryParams.append('subscription_ids', filters.subscriptionIds.join(','));
      }
      
      if (filters?.serviceCategories?.length) {
        queryParams.append('service_categories', filters.serviceCategories.join(','));
      }
      
      if (selectedType !== 'all') {
        queryParams.append('type', selectedType);
      }
      
      queryParams.append('sort_by', sortBy);
      queryParams.append('limit', maxRecommendations.toString());

      const response = await fetch(`/api/v1/cost-optimization/recommendations?${queryParams}`);
      
      if (!response.ok) {
        throw new Error('Failed to load cost optimization recommendations');
      }

      const data = await response.json();
      setRecommendations(data.recommendations || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load recommendations');
    } finally {
      setLoading(false);
    }
  };

  const handleDismissRecommendation = async (recommendationId: string) => {
    try {
      const response = await fetch(`/api/v1/cost-optimization/recommendations/${recommendationId}/dismiss`, {
        method: 'POST'
      });

      if (response.ok) {
        setRecommendations(prev => prev.filter(r => r.id !== recommendationId));
      }
    } catch (error) {
      console.error('Failed to dismiss recommendation:', error);
    }
  };

  const handleImplementRecommendation = async (recommendationId: string) => {
    try {
      const response = await fetch(`/api/v1/cost-optimization/recommendations/${recommendationId}/implement`, {
        method: 'POST'
      });

      if (response.ok) {
        await loadRecommendations();
      }
    } catch (error) {
      console.error('Failed to implement recommendation:', error);
    }
  };

  const getRecommendationTypeIcon = (type: string): string => {
    switch (type) {
      case 'rightsizing':
        return '📊';
      case 'unused_resources':
        return '🗑️';
      case 'reserved_instances':
        return '💰';
      case 'storage_optimization':
        return '💾';
      case 'scheduling':
        return '⏰';
      default:
        return '💡';
    }
  };

  const getConfidenceBadgeColor = (confidence: string): string => {
    switch (confidence) {
      case 'high':
        return 'green';
      case 'medium':
        return 'yellow';
      case 'low':
        return 'red';
      default:
        return 'gray';
    }
  };

  const getImpactBadgeColor = (impact: string): string => {
    switch (impact) {
      case 'high':
        return 'green';
      case 'medium':
        return 'yellow';
      case 'low':
        return 'gray';
      default:
        return 'gray';
    }
  };

  const formatSavingsPercentage = (currentCost: number, potentialSavings: number): string => {
    if (currentCost === 0) return '0%';
    const percentage = (potentialSavings / currentCost) * 100;
    return `${percentage.toFixed(1)}%`;
  };

  const totalPotentialSavings = recommendations.reduce((sum, rec) => sum + rec.potential_savings, 0);

  if (loading) {
    return (
      <div className={`cost-optimization-recommendations loading ${className || ''}`}>
        <div className="loading-spinner" />
        <p>Loading cost optimization recommendations...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`cost-optimization-recommendations error ${className || ''}`}>
        <div className="error-message">
          <h3>Error Loading Recommendations</h3>
          <p>{error}</p>
          <button onClick={loadRecommendations} className="retry-button">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`cost-optimization-recommendations ${className || ''}`}>
      <div className="recommendations-header">
        <div className="header-info">
          <h3>Cost Optimization Recommendations</h3>
          <div className="summary-stats">
            <div className="stat">
              <span className="stat-label">Total Recommendations:</span>
              <span className="stat-value">{recommendations.length}</span>
            </div>
            <div className="stat">
              <span className="stat-label">Potential Monthly Savings:</span>
              <span className="stat-value savings">{formatFOCUSCurrency(totalPotentialSavings)}</span>
            </div>
          </div>
        </div>

        {showFilters && (
          <div className="recommendations-filters">
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="filter-select"
            >
              <option value="all">All Types</option>
              <option value="rightsizing">Right-sizing</option>
              <option value="unused_resources">Unused Resources</option>
              <option value="reserved_instances">Reserved Instances</option>
              <option value="storage_optimization">Storage Optimization</option>
              <option value="scheduling">Scheduling</option>
            </select>

            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="filter-select"
            >
              <option value="savings">Sort by Savings</option>
              <option value="confidence">Sort by Confidence</option>
              <option value="impact">Sort by Impact</option>
            </select>

            <button onClick={loadRecommendations} className="refresh-button">
              Refresh
            </button>
          </div>
        )}
      </div>

      <div className="recommendations-list">
        {recommendations.length === 0 ? (
          <div className="no-recommendations">
            <p>No cost optimization recommendations found.</p>
          </div>
        ) : (
          recommendations.map(recommendation => (
            <div
              key={recommendation.id}
              className={`recommendation-card ${expandedRecommendation === recommendation.id ? 'expanded' : ''}`}
              onClick={() => onRecommendationSelect?.(recommendation)}
            >
              <div className="recommendation-header">
                <div className="recommendation-title">
                  <span className="type-icon">{getRecommendationTypeIcon(recommendation.type)}</span>
                  <h4>{recommendation.title}</h4>
                </div>
                <div className="recommendation-badges">
                  <span className={`confidence-badge ${getConfidenceBadgeColor(recommendation.confidence_level)}`}>
                    {recommendation.confidence_level} confidence
                  </span>
                  <span className={`impact-badge ${getImpactBadgeColor(recommendation.impact)}`}>
                    {recommendation.impact} impact
                  </span>
                </div>
              </div>

              <div className="recommendation-content">
                <p className="recommendation-description">{recommendation.description}</p>
                
                <div className="recommendation-metrics">
                  <div className="metric">
                    <span className="metric-label">Current Cost:</span>
                    <span className="metric-value">{formatFOCUSCurrency(recommendation.current_cost)}</span>
                  </div>
                  <div className="metric">
                    <span className="metric-label">Potential Savings:</span>
                    <span className="metric-value savings">
                      {formatFOCUSCurrency(recommendation.potential_savings)}
                      <span className="percentage">
                        ({formatSavingsPercentage(recommendation.current_cost, recommendation.potential_savings)})
                      </span>
                    </span>
                  </div>
                  <div className="metric">
                    <span className="metric-label">Implementation Effort:</span>
                    <span className="metric-value">{recommendation.implementation_effort}</span>
                  </div>
                  <div className="metric">
                    <span className="metric-label">Est. Time:</span>
                    <span className="metric-value">{recommendation.estimated_implementation_time}</span>
                  </div>
                </div>

                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setExpandedRecommendation(
                      expandedRecommendation === recommendation.id ? null : recommendation.id
                    );
                  }}
                  className="expand-button"
                >
                  {expandedRecommendation === recommendation.id ? 'Show Less' : 'Show Details'}
                </button>

                {expandedRecommendation === recommendation.id && (
                  <div className="recommendation-details">
                    <div className="details-section">
                      <h5>Recommendation Details</h5>
                      <p>{recommendation.recommendation_details}</p>
                    </div>

                    <div className="details-section">
                      <h5>Action Items</h5>
                      <ul>
                        {recommendation.action_items.map((item, index) => (
                          <li key={index}>{item}</li>
                        ))}
                      </ul>
                    </div>

                    <div className="details-section">
                      <h5>Risk Assessment</h5>
                      <span className={`risk-badge ${recommendation.risk_level}`}>
                        {recommendation.risk_level} risk
                      </span>
                    </div>
                  </div>
                )}
              </div>

              <div className="recommendation-actions">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleImplementRecommendation(recommendation.id);
                  }}
                  className="implement-button"
                >
                  Implement
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDismissRecommendation(recommendation.id);
                  }}
                  className="dismiss-button"
                >
                  Dismiss
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default CostOptimizationRecommendations;