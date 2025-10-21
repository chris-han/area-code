import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { pluginsApi } from '@/api/plugins'

export function usePlugins() {
  return useQuery({
    queryKey: ['plugins'],
    queryFn: pluginsApi.getPlugins,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

export function usePluginInstallations() {
  return useQuery({
    queryKey: ['plugin-installations'],
    queryFn: pluginsApi.getPluginInstallations,
    refetchInterval: 30000, // Refetch every 30 seconds
  })
}

export function usePluginStatus(pluginName: string) {
  return useQuery({
    queryKey: ['plugin-status', pluginName],
    queryFn: () => pluginsApi.getPluginStatus(pluginName),
    enabled: !!pluginName,
    refetchInterval: 10000,
  })
}

export function usePluginConfiguration(pluginName: string) {
  return useQuery({
    queryKey: ['plugin-configuration', pluginName],
    queryFn: () => pluginsApi.getPluginConfiguration(pluginName),
    enabled: !!pluginName,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

export function useInstallPlugin() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ pluginName, config }: { pluginName: string; config?: any }) => 
      pluginsApi.installPlugin(pluginName, config),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plugins'] })
      queryClient.invalidateQueries({ queryKey: ['plugin-installations'] })
    },
  })
}

export function useConfigurePlugin() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ pluginName, config }: { pluginName: string; config: any }) => 
      pluginsApi.configurePlugin(pluginName, config),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['plugin-status', variables.pluginName] })
      queryClient.invalidateQueries({ queryKey: ['plugin-installations'] })
      queryClient.invalidateQueries({ queryKey: ['plugin-configuration', variables.pluginName] })
    },
  })
}

export function useTestPlugin() {
  return useMutation({
    mutationFn: (pluginName: string) => pluginsApi.testPlugin(pluginName),
  })
}
