'use client'

import { useState, useEffect } from 'react'
import { useWorkflows } from '@/hooks/useWorkflows'

export function DebugWorkflows() {
  const [mounted, setMounted] = useState(false)
  const { data: workflows, isLoading, error, isError } = useWorkflows()

  useEffect(() => {
    setMounted(true)
  }, [])

  console.log('🐛 Debug Workflows:', {
    workflows,
    isLoading,
    error,
    isError,
    timestamp: new Date().toISOString()
  })

  if (!mounted) {
    return (
      <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg mb-4">
        <h3 className="font-bold text-yellow-800 mb-2">🐛 Debug Information</h3>
        <div className="text-sm">⏳ Initializing...</div>
      </div>
    )
  }

  return (
    <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg mb-4">
      <h3 className="font-bold text-yellow-800 mb-2">🐛 Debug Information</h3>
      <div className="text-sm space-y-1">
        <div>Loading: {isLoading ? '✅ Yes' : '❌ No'}</div>
        <div>Error: {isError ? `❌ ${error?.message}` : '✅ None'}</div>
        <div>Data: {workflows ? `✅ ${workflows.length} workflows` : '❌ No data'}</div>
        <div>Timestamp: {new Date().toLocaleTimeString()}</div>
      </div>
      {workflows && (
        <details className="mt-2">
          <summary className="cursor-pointer text-yellow-700">Raw Data</summary>
          <pre className="mt-2 p-2 bg-yellow-100 rounded text-xs overflow-auto">
            {JSON.stringify(workflows, null, 2)}
          </pre>
        </details>
      )}
    </div>
  )
}