'use client'

import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import Link from 'next/link'

const dashboardCards = [
  {
    title: 'Cost Comparison',
    description: 'Compare BilledCost, ContractedCost, EffectiveCost, and ListCost',
    href: '/finops/cost-comparison',
    icon: '💰',
    category: 'Core Analytics',
  },
  {
    title: 'Effective Cost Analysis',
    description: 'Analyze spending trends with amortized costs',
    href: '/finops/effective-cost',
    icon: '📊',
    category: 'Core Analytics',
  },
  {
    title: 'Invoice Alignment',
    description: 'Reconcile billed costs with invoices',
    href: '/finops/invoice-alignment',
    icon: '📄',
    category: 'Core Analytics',
  },
  {
    title: 'Cost Attribution',
    description: 'Tag-based cost allocation for chargeback',
    href: '/finops/cost-attribution',
    icon: '🏷️',
    category: 'Core Analytics',
  },
  {
    title: 'Resource Usage',
    description: 'Track resource consumption metrics',
    href: '/finops/resources',
    icon: '🖥️',
    category: 'Resources',
  },
  {
    title: 'Service Categorization',
    description: 'Service-level cost breakdown by category',
    href: '/finops/services',
    icon: '⚙️',
    category: 'Resources',
  },
  {
    title: 'Location Costs',
    description: 'Geographic cost distribution',
    href: '/finops/locations',
    icon: '🌍',
    category: 'Resources',
  },
  {
    title: 'Account Structure',
    description: 'Multi-account and sub-account breakdown',
    href: '/finops/accounts',
    icon: '🏢',
    category: 'Resources',
  },
  {
    title: 'Commitment Usage',
    description: 'Track commitment utilization and under-usage',
    href: '/finops/commitment-usage',
    icon: '🎯',
    category: 'Commitments',
  },
  {
    title: 'Commitment Purchases',
    description: 'Report commitment discount purchases',
    href: '/finops/commitment-purchases',
    icon: '🛒',
    category: 'Commitments',
  },
  {
    title: 'Marketplace Purchases',
    description: 'Third-party marketplace spending',
    href: '/finops/marketplace',
    icon: '🏪',
    category: 'Purchases',
  },
  {
    title: 'Unit Prices',
    description: 'Verify and compare unit prices',
    href: '/finops/unit-prices',
    icon: '💵',
    category: 'Purchases',
  },
  {
    title: 'Correction Charges',
    description: 'Identify billing corrections and adjustments',
    href: '/finops/corrections',
    icon: '🔧',
    category: 'Advanced',
  },
  {
    title: 'Recurring Charges',
    description: 'Track recurring commitment charges',
    href: '/finops/recurring',
    icon: '🔁',
    category: 'Advanced',
  },
  {
    title: 'Supported Features',
    description: 'Explore all FOCUS supported features',
    href: '/finops/features',
    icon: '✨',
    category: 'Documentation',
  },
]

export default function FinOpsPage() {
  const categories = [
    { name: 'Core Analytics', color: 'bg-blue-50 border-blue-200' },
    { name: 'Resources', color: 'bg-green-50 border-green-200' },
    { name: 'Commitments', color: 'bg-purple-50 border-purple-200' },
    { name: 'Purchases', color: 'bg-orange-50 border-orange-200' },
    { name: 'Advanced', color: 'bg-red-50 border-red-200' },
    { name: 'Documentation', color: 'bg-gray-50 border-gray-200' },
  ]

  return (
    <div className="p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">FinOps Dashboard</h1>
          <p className="mt-2 text-gray-600">
            FOCUS-compliant billing analytics and cost management - 14 consumption APIs
          </p>
        </div>

        {categories.map((category) => {
          const categoryCards = dashboardCards.filter((card) => card.category === category.name)
          if (categoryCards.length === 0) return null

          return (
            <div key={category.name} className="mb-8">
              <h2 className="text-xl font-semibold text-gray-800 mb-4">{category.name}</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {categoryCards.map((card) => (
                  <Link key={card.href} href={card.href}>
                    <Card className={`p-6 hover:shadow-lg transition-shadow cursor-pointer h-full ${category.color}`}>
                      <div className="text-4xl mb-4">{card.icon}</div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">
                        {card.title}
                      </h3>
                      <p className="text-sm text-gray-600">{card.description}</p>
                    </Card>
                  </Link>
                ))}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
