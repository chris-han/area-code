'use client'

import { useState } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useCostComparison } from '@/hooks/useFocus'
import Link from 'next/link'

export default function CostComparisonPage() {
  const [startDate, setStartDate] = useState('2025-07-01')
  const [endDate, setEndDate] = useState('2025-08-01')

  const { mutate: fetchCostComparison, data, isPending, error } = useCostComparison()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    fetchCostComparison({
      billing_period_start: startDate,
      billing_period_end: endDate,
    })
  }

  return (
    <div className="p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <Link href="/finops" className="text-blue-600 hover:underline mb-2 inline-block">
            ← Back to Dashboard
          </Link>
          <h1 className="text-3xl font-bold text-gray-900">Cost Comparison</h1>
          <p className="mt-2 text-gray-600">
            Compare BilledCost, ContractedCost, EffectiveCost, and ListCost to identify savings
          </p>
        </div>

        <Card className="p-6 mb-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="startDate">Start Date</Label>
                <Input
                  id="startDate"
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                />
              </div>
              <div>
                <Label htmlFor="endDate">End Date</Label>
                <Input
                  id="endDate"
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                />
              </div>
            </div>
            <Button type="submit" disabled={isPending}>
              {isPending ? 'Loading...' : 'Run Analysis'}
            </Button>
          </form>
        </Card>

        {error && (
          <Card className="p-6 mb-6 bg-red-50 border-red-200">
            <p className="text-red-800">Error: {error.message}</p>
          </Card>
        )}

        {data && data.length > 0 && (
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">Results</h2>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead>
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Provider
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Account
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Service
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                      Effective Cost
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                      Billed Cost
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                      List Cost
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                      Discount %
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {data.map((row, idx) => (
                    <tr key={idx} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm">{row.provider_name}</td>
                      <td className="px-4 py-3 text-sm">{row.billing_account_name}</td>
                      <td className="px-4 py-3 text-sm">{row.service_name}</td>
                      <td className="px-4 py-3 text-sm text-right">
                        ${row.total_effective_cost.toFixed(2)}
                      </td>
                      <td className="px-4 py-3 text-sm text-right">
                        ${row.total_billed_cost.toFixed(2)}
                      </td>
                      <td className="px-4 py-3 text-sm text-right">
                        ${row.total_list_cost.toFixed(2)}
                      </td>
                      <td className="px-4 py-3 text-sm text-right text-green-600 font-medium">
                        {row.effective_discount.toFixed(2)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        )}

        {data && data.length === 0 && (
          <Card className="p-6 text-center text-gray-500">
            No data found for the selected date range
          </Card>
        )}
      </div>
    </div>
  )
}
