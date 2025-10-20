# Azure Billing Intelligence - DataLens Extensions

FOCUS-compliant widgets and dashboards for Azure billing analytics, built as extensions for the DataLens BI platform.

## Overview

This package provides a comprehensive set of visualization components specifically designed for Azure billing intelligence and cost optimization. All components are FOCUS (FinOps Open Cost and Usage Specification) compliant.

## Components

### Widgets

#### 1. FOCUSCostTrendWidget
Interactive line chart showing cost trends over time with FOCUS-compliant data filtering.

**Features:**
- Date range filtering
- Cost aggregation by usage date
- Total and average daily cost metrics
- Interactive filtering by service category, region, and billing account

**Usage:**
```typescript
import { FOCUSCostTrendWidget } from '@workspace/datalens-abi-extensions';

<FOCUSCostTrendWidget
  title="Cost Trends Over Time"
  height={400}
  defaultFilters={{
    dateRange: { start: '2024-01-01', end: '2024-01-31' }
  }}
  onDataChange={(data) => console.log(data)}
/>
```

#### 2. ResourceUtilizationHeatmap
Heatmap visualization showing resource utilization across services and regions.

**Features:**
- Multi-dimensional heatmap (service × region)
- Metric selection (utilization, cost, efficiency)
- Color-coded intensity visualization
- Interactive tooltips with detailed metrics

**Usage:**
```typescript
import { ResourceUtilizationHeatmap } from '@workspace/datalens-abi-extensions';

<ResourceUtilizationHeatmap
  title="Resource Utilization by Service and Region"
  height={500}
  width={800}
  defaultFilters={{
    dateRange: { start: '2024-01-01', end: '2024-01-31' }
  }}
/>
```

#### 3. ServiceCategoryBreakdown
Cost allocation visualization showing spending distribution across service categories.

**Features:**
- Service category cost breakdown
- Percentage-based visualization
- Bar chart representation
- Trend indicators (up/down/stable)

**Usage:**
```typescript
import { ServiceCategoryBreakdown } from '@workspace/datalens-abi-extensions';

<ServiceCategoryBreakdown
  title="Cost Allocation by Service Category"
  height={400}
  defaultFilters={{
    dateRange: { start: '2024-01-01', end: '2024-01-31' }
  }}
/>
```

#### 4. BudgetTrackingWidget
Budget vs actual cost analysis with variance tracking and forecasting.

**Features:**
- Budget vs actual comparison
- Forecasted spend calculation
- Variance percentage tracking
- Status indicators (on track, at risk, over budget)
- Visual progress bars

**Usage:**
```typescript
import { BudgetTrackingWidget } from '@workspace/datalens-abi-extensions';

<BudgetTrackingWidget
  title="Budget vs Actual Cost Analysis"
  height={400}
  defaultFilters={{
    dateRange: { start: '2024-01-01', end: '2024-01-31' }
  }}
/>
```

### Dashboards

#### 1. CostOptimizationDashboard
Comprehensive dashboard for Azure cost optimization analysis.

**Includes:**
- Cost trend analysis
- Service category breakdown
- Resource utilization heatmap
- Global date range filtering

**Usage:**
```typescript
import { CostOptimizationDashboard } from '@workspace/datalens-abi-extensions';

<CostOptimizationDashboard
  defaultFilters={{
    dateRange: { start: '2024-01-01', end: '2024-01-31' }
  }}
/>
```

#### 2. ResourceUtilizationDashboard
Dashboard focused on resource efficiency and utilization metrics.

**Includes:**
- Resource utilization heatmap
- Service cost distribution
- Efficiency scoring

**Usage:**
```typescript
import { ResourceUtilizationDashboard } from '@workspace/datalens-abi-extensions';

<ResourceUtilizationDashboard
  defaultFilters={{
    dateRange: { start: '2024-01-01', end: '2024-01-31' }
  }}
/>
```

#### 3. BudgetTrackingDashboard
Dashboard for budget monitoring and variance analysis.

**Includes:**
- Budget vs actual analysis
- Cost trends
- Cost breakdown by category
- Variance tracking

**Usage:**
```typescript
import { BudgetTrackingDashboard } from '@workspace/datalens-abi-extensions';

<BudgetTrackingDashboard
  defaultFilters={{
    dateRange: { start: '2024-01-01', end: '2024-01-31' }
  }}
/>
```

## API Integration

All widgets integrate with the ABI backend API endpoints:

### FOCUS Data API
- **Endpoint:** `/api/v1/focus/aggregation`
- **Method:** POST
- **Purpose:** Retrieve aggregated FOCUS billing data

### Budget Tracking API
- **Endpoint:** `/api/v1/focus/budget-tracking`
- **Method:** POST
- **Purpose:** Get budget vs actual cost analysis

## Data Types

### FOCUSFilterOptions
```typescript
interface FOCUSFilterOptions {
  dateRange: {
    start: string;  // ISO date format
    end: string;    // ISO date format
  };
  subscriptionIds?: string[];
  resourceGroups?: string[];
  serviceCategories?: string[];
  regions?: string[];
}
```

### CostTrendData
```typescript
interface CostTrendData {
  date: string;
  cost: number;
  currency: string;
  service_category?: string;
}
```

### ResourceUtilizationData
```typescript
interface ResourceUtilizationData {
  resource_id: string;
  resource_name: string;
  resource_type: string;
  utilization_percentage: number;
  cost: number;
  efficiency_score: number;
}
```

### BudgetData
```typescript
interface BudgetData {
  budget_name: string;
  budget_amount: number;
  actual_spend: number;
  forecasted_spend: number;
  variance_percentage: number;
  period: string;
}
```

## Styling

All components use shared CSS styles defined in `src/styles/widgets.css`. The styles follow a consistent design system with:

- Color palette based on Tailwind CSS
- Responsive design for mobile and desktop
- Accessible color contrasts
- Consistent spacing and typography

## Development

### Building
```bash
bun run build
```

### Development Mode
```bash
bun run dev
```

### Testing
```bash
bun test
```

## FOCUS Compliance

All widgets and dashboards are compliant with the FinOps Open Cost and Usage Specification (FOCUS) v1.0:

- **Required Dimensions:** billing_account_id, usage_date, billed_cost
- **Cost Dimensions:** effective_cost, list_cost, list_unit_price
- **Usage Dimensions:** usage_quantity, usage_unit
- **Resource Dimensions:** resource_id, resource_name, resource_type
- **Service Dimensions:** service_category, service_name
- **Geographic Dimensions:** region, availability_zone

## Requirements

- React 18+
- TypeScript 5+
- DataLens UI Kit 1.0+
- ABI Backend API

## License

Proprietary - Azure Billing Intelligence Platform
