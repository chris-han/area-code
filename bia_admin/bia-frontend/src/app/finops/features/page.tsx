'use client'

import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { useSupportedFeatures } from '@/hooks/useFocus'
import Link from 'next/link'

export default function FeaturesPage() {
  const { data: features, isLoading, error } = useSupportedFeatures()

  return (
    <div className="p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <Link href="/finops" className="text-blue-600 hover:underline mb-2 inline-block">
            ← Back to Dashboard
          </Link>
          <h1 className="text-3xl font-bold text-gray-900">FOCUS Supported Features</h1>
          <p className="mt-2 text-gray-600">
            Explore all 18 FOCUS specification supported features
          </p>
        </div>

        {isLoading && (
          <Card className="p-6 text-center text-gray-500">
            Loading features...
          </Card>
        )}

        {error && (
          <Card className="p-6 bg-red-50 border-red-200">
            <p className="text-red-800">Error: {error.message}</p>
          </Card>
        )}

        {features && features.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {features.map((feature) => (
              <Link key={feature.id} href={`/finops/features/${feature.id}`}>
                <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer h-full">
                  <div className="flex justify-between items-start mb-3">
                    <h3 className="text-lg font-semibold text-gray-900">
                      {feature.name}
                    </h3>
                    <Badge variant="outline">v{feature.introduced_version}</Badge>
                  </div>
                  <p className="text-sm text-gray-600 mb-4">{feature.description}</p>
                  <div className="space-y-2">
                    <div>
                      <span className="text-xs font-medium text-gray-500">Required Columns:</span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {feature.dependent_columns.slice(0, 3).map((col) => (
                          <Badge key={col} variant="secondary" className="text-xs">
                            {col}
                          </Badge>
                        ))}
                        {feature.dependent_columns.length > 3 && (
                          <Badge variant="secondary" className="text-xs">
                            +{feature.dependent_columns.length - 3} more
                          </Badge>
                        )}
                      </div>
                    </div>
                  </div>
                </Card>
              </Link>
            ))}
          </div>
        )}

        {features && features.length === 0 && (
          <Card className="p-6 text-center text-gray-500">
            No features available
          </Card>
        )}
      </div>
    </div>
  )
}
