import { NEXT_PUBLIC_API_BASE_URL, NEXT_PUBLIC_MOOSE_CONSUMPTION_BASE_URL } from '@/lib/env'

export class ApiClient {
  private baseURL: string
  private proxyPrefix?: string

  constructor(baseURL: string = NEXT_PUBLIC_API_BASE_URL, proxyPrefix?: string) {
    this.baseURL = baseURL
    this.proxyPrefix = proxyPrefix
  }

  async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const isBrowser = typeof window !== 'undefined'
    let url: string

    if (isBrowser && this.proxyPrefix) {
      // Use Next.js API route proxy
      url = `${this.proxyPrefix}${endpoint}`
    } else if (isBrowser) {
      // Direct browser request (for services with CORS enabled)
      url = `${this.baseURL}${endpoint}`
    } else {
      // Server-side request
      url = `${this.baseURL}${endpoint}`
    }
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    }

    try {
      const response = await fetch(url, config)
      
      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`HTTP ${response.status}: ${errorText || response.statusText}`)
      }
      
      const contentType = response.headers.get('content-type')
      if (contentType && contentType.includes('application/json')) {
        return await response.json()
      }
      
      return await response.text() as unknown as T
    } catch (error) {
      console.error('API request failed:', { url, error })
      throw error
    }
  }

  async get<T>(endpoint: string, params?: Record<string, string>): Promise<T> {
    const url = params 
      ? `${endpoint}?${new URLSearchParams(params).toString()}`
      : endpoint
    
    return this.request<T>(url, { method: 'GET' })
  }

  async post<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  async put<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  async patch<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' })
  }
}

// BIA Backend API - use Next.js proxy for CORS
export const biaClient = new ApiClient(NEXT_PUBLIC_API_BASE_URL, '/api/bia')

// Moose Consumption API - direct connection (CORS enabled)
export const mooseClient = new ApiClient(NEXT_PUBLIC_MOOSE_CONSUMPTION_BASE_URL)

// Backwards-compatible exports
export const apiClient = biaClient
export const consumptionClient = mooseClient
