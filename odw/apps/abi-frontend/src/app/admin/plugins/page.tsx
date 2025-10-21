'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { PluginConfigModal } from '@/components/plugin-config-modal'
import { pluginsApi } from '@/api/plugins'
import { 
  Plug, 
  Search, 
  Download, 
  Settings, 
  CheckCircle, 
  AlertCircle, 
  Clock,
  Star,
  ExternalLink
} from 'lucide-react'

export default function PluginsPage() {
  const [configModalOpen, setConfigModalOpen] = useState(false)
  const [selectedPlugin, setSelectedPlugin] = useState<string>('')

  const handleConfigurePlugin = (pluginName: string) => {
    setSelectedPlugin(pluginName)
    setConfigModalOpen(true)
  }

  const handleSaveConfig = async (config: any) => {
    try {
      await pluginsApi.configurePlugin(selectedPlugin, config)
      console.log('Plugin configuration saved successfully for', selectedPlugin)
      // You could add a toast notification here
    } catch (error) {
      console.error('Failed to save plugin configuration:', error)
      // You could add error handling/notification here
    }
  }
  const installedPlugins = [
    { 
      name: 'Azure Blob Storage Connector', 
      status: 'active', 
      version: '1.3.0',
      description: 'Connect to Azure Blob Storage for FOCUS-compliant parquet files',
      author: 'Microsoft',
      rating: 4.9,
      downloads: '15k+',
      category: 'Data Connector',
      configurable: true
    },
    { 
      name: 'FOCUS 1.2 Transformer', 
      status: 'active', 
      version: '2.2.0',
      description: 'Transform FOCUS parquet files to Moose model FOCUS 1.2 data tables',
      author: 'FinOps Foundation',
      rating: 4.9,
      downloads: '12k+',
      category: 'Transformer',
      configurable: true
    },
    { 
      name: 'ClickHouse Sink', 
      status: 'active', 
      version: '1.4.0',
      description: 'Write transformed data to ClickHouse database with SSL support',
      author: 'ClickHouse Inc.',
      rating: 4.8,
      downloads: '8k+',
      category: 'Data Sink',
      configurable: true
    },
    { 
      name: 'Azure EA Connector', 
      status: 'active', 
      version: '1.2.0',
      description: 'Connect to Azure Enterprise Agreement billing data',
      author: 'Microsoft',
      rating: 4.8,
      downloads: '10k+',
      category: 'Data Connector',
      configurable: true
    },
    { 
      name: 'GCP Billing Export', 
      status: 'active', 
      version: '0.9.2',
      description: 'Export Google Cloud Platform billing data',
      author: 'Google',
      rating: 4.6,
      downloads: '3k+',
      category: 'Data Connector',
      configurable: true
    },
    { 
      name: 'Cost Optimizer', 
      status: 'pending', 
      version: '1.5.0',
      description: 'AI-powered cost optimization recommendations',
      author: 'CostOps',
      rating: 4.7,
      downloads: '8k+',
      category: 'Analytics',
      configurable: false
    },
  ]

  const availablePlugins = [
    { 
      name: 'AWS Cost Explorer', 
      version: '1.0.1',
      description: 'Connect to AWS Cost Explorer API for billing data',
      author: 'Amazon',
      rating: 4.5,
      downloads: '15k+',
      price: 'Free'
    },
    { 
      name: 'Kubernetes Cost Monitor', 
      version: '2.3.0',
      description: 'Monitor Kubernetes cluster costs and resource usage',
      author: 'CNCF',
      rating: 4.4,
      downloads: '7k+',
      price: 'Free'
    },
    { 
      name: 'Multi-Cloud Optimizer', 
      version: '1.8.2',
      description: 'Optimize costs across multiple cloud providers',
      author: 'CloudOps Pro',
      rating: 4.6,
      downloads: '12k+',
      price: '$29/month'
    },
    { 
      name: 'Carbon Footprint Tracker', 
      version: '1.1.0',
      description: 'Track and optimize carbon emissions from cloud usage',
      author: 'GreenCloud',
      rating: 4.3,
      downloads: '2k+',
      price: '$19/month'
    },
  ]

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="h-4 w-4 text-green-600" />
      case 'pending':
        return <Clock className="h-4 w-4 text-yellow-600" />
      case 'inactive':
      default:
        return <AlertCircle className="h-4 w-4 text-red-600" />
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return <Badge variant="success">{status}</Badge>
      case 'pending':
        return <Badge variant="warning">{status}</Badge>
      case 'inactive':
      default:
        return <Badge variant="secondary">{status}</Badge>
    }
  }

  const renderStars = (rating: number) => {
    return (
      <div className="flex items-center gap-1">
        {[1, 2, 3, 4, 5].map((star) => (
          <Star
            key={star}
            className={`h-3 w-3 ${
              star <= rating ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300'
            }`}
          />
        ))}
        <span className="text-xs text-muted-foreground ml-1">{rating}</span>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Plugin Marketplace</h1>
          <p className="text-muted-foreground">
            Discover and manage data connectors and processing plugins
          </p>
        </div>
        <Button>
          <Plug className="h-4 w-4 mr-2" />
          Upload Plugin
        </Button>
      </div>

      {/* Search and Filter */}
      <Card>
        <CardContent className="p-4">
          <div className="flex gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search plugins..."
                className="pl-10"
              />
            </div>
            <select className="flex h-10 rounded-md border border-input bg-background px-3 py-2 text-sm">
              <option>All Categories</option>
              <option>Data Connectors</option>
              <option>Transformers</option>
              <option>Analytics</option>
              <option>Optimization</option>
            </select>
            <select className="flex h-10 rounded-md border border-input bg-background px-3 py-2 text-sm">
              <option>All Providers</option>
              <option>Microsoft</option>
              <option>Amazon</option>
              <option>Google</option>
              <option>Community</option>
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Installed Plugins */}
      <Card>
        <CardHeader>
          <CardTitle>Installed Plugins ({installedPlugins.length})</CardTitle>
          <CardDescription>
            Manage your currently installed plugins
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            {installedPlugins.map((plugin) => (
              <Card key={plugin.name} className="border-2">
                <CardContent className="p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-2">
                      {getStatusIcon(plugin.status)}
                      <h3 className="font-semibold">{plugin.name}</h3>
                    </div>
                    {getStatusBadge(plugin.status)}
                  </div>
                  
                  <p className="text-sm text-muted-foreground mb-3">
                    {plugin.description}
                  </p>
                  
                  <div className="flex items-center justify-between text-xs text-muted-foreground mb-3">
                    <span>v{plugin.version}</span>
                    <span>by {plugin.author}</span>
                  </div>
                  
                  <div className="flex items-center justify-between mb-3">
                    {renderStars(plugin.rating)}
                    <span className="text-xs text-muted-foreground">{plugin.downloads}</span>
                  </div>
                  
                  <div className="flex gap-2">
                    <Button 
                      variant="outline" 
                      size="sm" 
                      className="flex-1"
                      onClick={() => handleConfigurePlugin(plugin.name)}
                      disabled={!plugin.configurable}
                    >
                      <Settings className="h-3 w-3 mr-1" />
                      Configure
                    </Button>
                    <Button variant="outline" size="sm">
                      <ExternalLink className="h-3 w-3" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Available Plugins */}
      <Card>
        <CardHeader>
          <CardTitle>Available Plugins</CardTitle>
          <CardDescription>
            Discover new plugins to extend your capabilities
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            {availablePlugins.map((plugin) => (
              <Card key={plugin.name} className="border">
                <CardContent className="p-4">
                  <div className="flex items-start justify-between mb-3">
                    <h3 className="font-semibold">{plugin.name}</h3>
                    <Badge variant="outline">{plugin.price}</Badge>
                  </div>
                  
                  <p className="text-sm text-muted-foreground mb-3">
                    {plugin.description}
                  </p>
                  
                  <div className="flex items-center justify-between text-xs text-muted-foreground mb-3">
                    <span>v{plugin.version}</span>
                    <span>by {plugin.author}</span>
                  </div>
                  
                  <div className="flex items-center justify-between mb-3">
                    {renderStars(plugin.rating)}
                    <span className="text-xs text-muted-foreground">{plugin.downloads}</span>
                  </div>
                  
                  <div className="flex gap-2">
                    <Button size="sm" className="flex-1">
                      <Download className="h-3 w-3 mr-1" />
                      Install
                    </Button>
                    <Button variant="outline" size="sm">
                      <ExternalLink className="h-3 w-3" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Plugin Categories */}
      <Card>
        <CardHeader>
          <CardTitle>Browse by Category</CardTitle>
          <CardDescription>
            Explore plugins organized by functionality
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <div className="text-center p-4 border rounded-lg hover:bg-muted/50 cursor-pointer">
              <Plug className="h-8 w-8 mx-auto mb-2 text-primary" />
              <h4 className="font-medium">Data Connectors</h4>
              <p className="text-xs text-muted-foreground">12 plugins</p>
            </div>
            <div className="text-center p-4 border rounded-lg hover:bg-muted/50 cursor-pointer">
              <Settings className="h-8 w-8 mx-auto mb-2 text-primary" />
              <h4 className="font-medium">Transformers</h4>
              <p className="text-xs text-muted-foreground">8 plugins</p>
            </div>
            <div className="text-center p-4 border rounded-lg hover:bg-muted/50 cursor-pointer">
              <CheckCircle className="h-8 w-8 mx-auto mb-2 text-primary" />
              <h4 className="font-medium">Analytics</h4>
              <p className="text-xs text-muted-foreground">15 plugins</p>
            </div>
            <div className="text-center p-4 border rounded-lg hover:bg-muted/50 cursor-pointer">
              <Star className="h-8 w-8 mx-auto mb-2 text-primary" />
              <h4 className="font-medium">Optimization</h4>
              <p className="text-xs text-muted-foreground">6 plugins</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Configuration Modal */}
      <PluginConfigModal
        pluginName={selectedPlugin}
        isOpen={configModalOpen}
        onClose={() => setConfigModalOpen(false)}
        onSave={handleSaveConfig}
      />
    </div>
  )
}