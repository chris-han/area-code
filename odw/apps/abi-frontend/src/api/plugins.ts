import { biaClient } from './client'
import { PluginMetadata } from '@/types'

export const pluginsApi = {
  // Get all available plugins
  getPlugins: async (): Promise<PluginMetadata[]> => {
    const response = await biaClient.post<{ plugins: any[] }>('/api/v1/plugins/list', {})
    return (response?.plugins ?? []).map((plugin) => ({
      name: plugin?.display_name ?? plugin?.name ?? 'Unknown Plugin',
      version: plugin?.version ?? '1.0.0',
      description: plugin?.description ?? '',
      author: plugin?.author ?? 'Unknown',
      category: plugin?.category ?? 'general',
      tags: plugin?.tags ?? [],
      iconUrl: plugin?.icon_url ?? undefined,
      documentationUrl: plugin?.documentation_url ?? undefined,
      configSchema: plugin?.config_schema ?? {},
      isInstalled: plugin?.status === 'active',
      isConfigured: plugin?.status === 'active',
      isActive: plugin?.status === 'active',
    }))
  },

  // Get plugin installations
  getPluginInstallations: async (): Promise<any[]> => {
    const response = await biaClient.post<{ installations: any[] }>('/api/v1/plugins/installations', {})
    return response?.installations ?? []
  },

  // Install a plugin
  installPlugin: async (pluginName: string, config?: any): Promise<any> => {
    return biaClient.post<any>('/api/v1/plugins/install', {
      plugin_id: pluginName,
      config,
    })
  },

  // Configure a plugin
  configurePlugin: async (pluginName: string, config: any): Promise<any> => {
    return biaClient.put<any>('/api/v1/plugins/configuration', {
      plugin_name: pluginName,
      config,
    })
  },

  // Get plugin configuration
  getPluginConfiguration: async (pluginName: string): Promise<any> => {
    try {
      const response = await biaClient.get<any>('/api/v1/plugins/configuration', {
        plugin_name: pluginName,
      })
      if (response && typeof response === 'object') {
        if ('config' in response) {
          return response.config
        }
        return response
      }
      return null
    } catch (error) {
      if (error instanceof Error && /^HTTP 404/i.test(error.message)) {
        return null
      }
      throw error
    }
  },

  // Test a plugin
  testPlugin: async (pluginName: string, config?: any): Promise<any> => {
    const result = await biaClient.post<any>('/api/v1/plugins/test', {
      plugin_name: pluginName,
      config,
    })
    if (!result) return result
    // Ensure legacy test_results shape for UI compatibility
    if (!result.test_results) {
      result.test_results = {
        connection_test: result.connection_test,
        authentication_test: result.authentication_test,
        data_access_test: result.data_access_test,
        database: result.database,
        host: result.host,
        latency_ms: result.latency_ms,
      }
    }
    return result
  },

  // Get plugin status
  getPluginStatus: async (pluginName: string): Promise<any> => {
    return biaClient.post<any>('/api/v1/plugins/status', {
      installation_ids: [],
      plugin_name: pluginName,
      detailed: true,
    })
  }
}
