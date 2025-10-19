/**
 * FOCUS Specification Helper Functions
 */

import { FOCUSBillingData, FOCUSFilterOptions } from '../types/focus-types';

/**
 * Validates FOCUS billing data compliance
 */
export function validateFOCUSCompliance(data: Partial<FOCUSBillingData>): boolean {
  const requiredFields = ['billing_account_id', 'usage_date', 'billed_cost'];
  return requiredFields.every(field => data[field as keyof FOCUSBillingData] !== undefined);
}

/**
 * Formats currency values according to FOCUS specification
 */
export function formatFOCUSCurrency(amount: number, currency: string = 'USD'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(amount);
}

/**
 * Generates ClickHouse query for FOCUS data with filters
 */
export function buildFOCUSQuery(filters: FOCUSFilterOptions): string {
  let query = `
    SELECT 
      billing_account_id,
      usage_date,
      billed_cost,
      service_category,
      service_name,
      resource_type,
      resource_id,
      resource_name,
      region,
      subscription_id,
      resource_group,
      currency
    FROM focus_billing_data
    WHERE usage_date >= '${filters.dateRange.start}'
      AND usage_date <= '${filters.dateRange.end}'
  `;

  if (filters.subscriptionIds && filters.subscriptionIds.length > 0) {
    const subscriptions = filters.subscriptionIds.map(id => `'${id}'`).join(',');
    query += ` AND subscription_id IN (${subscriptions})`;
  }

  if (filters.resourceGroups && filters.resourceGroups.length > 0) {
    const resourceGroups = filters.resourceGroups.map(rg => `'${rg}'`).join(',');
    query += ` AND resource_group IN (${resourceGroups})`;
  }

  if (filters.serviceCategories && filters.serviceCategories.length > 0) {
    const categories = filters.serviceCategories.map(cat => `'${cat}'`).join(',');
    query += ` AND service_category IN (${categories})`;
  }

  if (filters.regions && filters.regions.length > 0) {
    const regions = filters.regions.map(region => `'${region}'`).join(',');
    query += ` AND region IN (${regions})`;
  }

  query += ' ORDER BY usage_date DESC';
  
  return query;
}

/**
 * Aggregates FOCUS data by service category
 */
export function aggregateByServiceCategory(data: FOCUSBillingData[]): Record<string, number> {
  return data.reduce((acc, record) => {
    const category = record.service_category;
    acc[category] = (acc[category] || 0) + record.billed_cost;
    return acc;
  }, {} as Record<string, number>);
}

/**
 * Calculates cost trends over time
 */
export function calculateCostTrends(data: FOCUSBillingData[]): Array<{date: string, cost: number}> {
  const dailyCosts = data.reduce((acc, record) => {
    const date = record.usage_date;
    acc[date] = (acc[date] || 0) + record.billed_cost;
    return acc;
  }, {} as Record<string, number>);

  return Object.entries(dailyCosts)
    .map(([date, cost]) => ({ date, cost }))
    .sort((a, b) => a.date.localeCompare(b.date));
}