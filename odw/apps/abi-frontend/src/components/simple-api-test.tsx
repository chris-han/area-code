'use client'

import { useState, useEffect } from 'react'

export function SimpleApiTest() {
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [mounted, setMounted] = useState(false)

  const testApi = async () => {
    setLoading(true)
    setError(null)

    try {
      console.log('🧪 Testing API call...')

      const response = await fetch('/api/bia/api/v1/workflows/list', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({}),
      })

      console.log('📡 Response status:', response.status)
      console.log('📡 Response ok:', response.ok)

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()
      console.log('✅ API Response:', data)
      setResult(data)
    } catch (err: any) {
      console.error('❌ API Error:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (mounted) {
      testApi()
    }
  }, [mounted])

  if (!mounted) {
    return (
      <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg mb-4">
        <h3 className="font-bold text-blue-800 mb-2">🧪 Direct API Test</h3>
        <div className="text-sm">⏳ Initializing...</div>
      </div>
    )
  }

  return (
    <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg mb-4">
      <h3 className="font-bold text-blue-800 mb-2">🧪 Direct API Test</h3>

      <div className="text-sm space-y-2">
        <div>Status: {loading ? '⏳ Loading...' : '✅ Complete'}</div>

        {error && (
          <div className="text-red-600">❌ Error: {error}</div>
        )}

        {result && (
          <div className="text-green-600">
            ✅ Success: {result.total} workflows found
          </div>
        )}

        <button
          onClick={testApi}
          disabled={loading}
          className="px-3 py-1 bg-blue-500 text-white rounded text-sm hover:bg-blue-600 disabled:opacity-50"
        >
          {loading ? 'Testing...' : 'Test Again'}
        </button>
      </div>

      {result && (
        <details className="mt-2">
          <summary className="cursor-pointer text-blue-700">Raw Response</summary>
          <pre className="mt-2 p-2 bg-blue-100 rounded text-xs overflow-auto">
            {JSON.stringify(result, null, 2)}
          </pre>
        </details>
      )}
    </div>
  )
}