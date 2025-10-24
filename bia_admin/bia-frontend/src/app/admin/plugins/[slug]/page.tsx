import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  ArrowLeft,
  Download,
  Star,
  CheckCircle,
  AlertCircle,
  Settings,
  FileText,
  ExternalLink,
  Shield,
  Zap
} from 'lucide-react'
import Link from 'next/link'

interface PluginPageProps {
  params: {
    slug: string
  }
}

export default function PluginPage({ params }: PluginPageProps) {
  const pluginData = {
    'azure-blob-storage-connector': {
      name: 'Azure Blob Storage Connector',
      version: '1.3.0',
      author: 'Microsoft',
      description: 'Connect to Azure Blob Storage for FOCUS-compliant parquet files with enterprise-grade security and performance.',
      longDescription: 'The Azure Blob Storage Connector enables seamless integration with Azure Blob Storage to ingest FOCUS-compliant billing data stored in parquet format. This plugin supports SAS token authentication, automatic file discovery, and batch processing for optimal performance.',
      rating: 4.9,
      downloads: '15k+',
      category: 'Data Connector',
      status: 'active',
      lastUpdated: '2024-01-15',
      features: [
        'SAS token authentication',
        'Automatic parquet file discovery',
        'Batch processing support',
        'Container path filtering',
        'Connection testing',
        'Error handling and retry logic'
      ],
      requirements: [
        'Azure Storage Account with Blob service',
        'Valid SAS token with read permissions',
        'FOCUS-compliant parquet files',
        'Network connectivity to Azure'
      ],
      configuration: [
        'Storage Account Name',
        'SAS Token (with read permissions)',
        'Data Container Name',
        'Optional Path Prefix'
      ]
    },
    'clickhouse-sink': {
      name: 'ClickHouse Sink',
      version: '1.4.0',
      author: 'ClickHouse Inc.',
      description: 'Write transformed data to ClickHouse database with SSL support and enterprise features.',
      longDescription: 'The ClickHouse Sink plugin provides high-performance data ingestion into ClickHouse databases with support for SSL/TLS encryption, batch processing, and automatic table creation. Optimized for FOCUS 1.2 data models with Moose integration.',
      rating: 4.8,
      downloads: '8k+',
      category: 'Data Sink',
      status: 'active',
      lastUpdated: '2024-01-20',
      features: [
        'SSL/TLS encrypted connections',
        'Configurable batch processing',
        'Automatic table creation',
        'Connection pooling and retry logic',
        'Moose model compatibility',
        'Performance monitoring and metrics'
      ],
      requirements: [
        'ClickHouse server (version 21.3+)',
        'Valid database credentials',
        'Network connectivity to ClickHouse host',
        'SSL certificate (if using SSL)'
      ],
      configuration: [
        'Database Name',
        'Username and Password',
        'Host and Port',
        'SSL Configuration',
        'Table Name',
        'Batch Size Settings'
      ]
    },
    'focus-12-transformer': {
      name: 'FOCUS 1.2 Transformer',
      version: '2.2.0',
      author: 'FinOps Foundation',
      description: 'Transform FOCUS parquet files to canonical FOCUS 1.2 data tables with full schema validation.',
      longDescription: 'The FOCUS 1.2 Transformer converts FOCUS-compliant parquet files into canonical FOCUS 1.2 data tables optimized for analytics and reporting. It includes comprehensive schema validation, data type conversion, and performance optimization features.',
      rating: 4.9,
      downloads: '12k+',
      category: 'Transformer',
      status: 'active',
      lastUpdated: '2024-01-18',
      features: [
        'FOCUS 1.2 schema compliance',
        'Automatic data type conversion',
        'Schema validation and error reporting',
        'Batch processing with configurable size',
        'Multiple compression formats',
        'Performance optimization'
      ],
      requirements: [
        'FOCUS-compliant input data',
        'ClickHouse database connection',
        'Sufficient memory for batch processing',
        'Valid FOCUS schema definitions'
      ],
      configuration: [
        'Input Format (Parquet, CSV, JSON)',
        'Output Format (Parquet, CSV)',
        'FOCUS Version (1.0, 1.1, 1.2)',
        'Compression Type',
        'Batch Size',
        'Schema Validation Toggle'
      ]
    }
  }

  const plugin = pluginData[params.slug as keyof typeof pluginData]

  if (!plugin) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="outline" size="sm" asChild>
            <Link href="/admin/plugins">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Plugins
            </Link>
          </Button>
          <div>
            <h1 className="text-3xl font-bold">Plugin Not Found</h1>
            <p className="text-muted-foreground">The requested plugin could not be found.</p>
          </div>
        </div>
      </div>
    )
  }

  const renderStars = (rating: number) => {
    return (
      <div className="flex items-center gap-1">
        {[1, 2, 3, 4, 5].map((star) => (
          <Star
            key={star}
            className={`h-4 w-4 ${
              star <= rating ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300'
            }`}
          />
        ))}
        <span className="text-sm text-muted-foreground ml-2">{rating}</span>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="outline" size="sm" asChild>
          <Link href="/admin/plugins">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Plugins
          </Link>
        </Button>
      </div>

      {/* Plugin Header */}
      <div className="flex items-start justify-between">
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold">{plugin.name}</h1>
            <Badge variant="success">{plugin.status}</Badge>
          </div>
          <p className="text-lg text-muted-foreground">{plugin.description}</p>
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <span>v{plugin.version}</span>
            <span>•</span>
            <span>by {plugin.author}</span>
            <span>•</span>
            <span>{plugin.downloads} downloads</span>
            <span>•</span>
            <span>Updated {new Date(plugin.lastUpdated).toLocaleDateString()}</span>
          </div>
          <div className="flex items-center gap-4">
            {renderStars(plugin.rating)}
            <Badge variant="outline">{plugin.category}</Badge>
          </div>
        </div>
        <div className="flex gap-2">
          <Button>
            <Settings className="h-4 w-4 mr-2" />
            Configure
          </Button>
          <Button variant="outline">
            <ExternalLink className="h-4 w-4 mr-2" />
            Documentation
          </Button>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Description */}
          <Card>
            <CardHeader>
              <CardTitle>About</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">{plugin.longDescription}</p>
            </CardContent>
          </Card>

          {/* Features */}
          <Card>
            <CardHeader>
              <CardTitle>Features</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-2">
                {plugin.features.map((feature, index) => (
                  <div key={index} className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <span className="text-sm">{feature}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Configuration */}
          <Card>
            <CardHeader>
              <CardTitle>Configuration Parameters</CardTitle>
              <CardDescription>
                Required and optional configuration settings
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {plugin.configuration.map((config, index) => (
                  <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center gap-2">
                      <Settings className="h-4 w-4 text-muted-foreground" />
                      <span className="font-medium">{config}</span>
                    </div>
                    <Badge variant="outline">Required</Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button className="w-full">
                <Settings className="h-4 w-4 mr-2" />
                Configure Plugin
              </Button>
              <Button variant="outline" className="w-full">
                <Zap className="h-4 w-4 mr-2" />
                Test Connection
              </Button>
              <Button variant="outline" className="w-full">
                <FileText className="h-4 w-4 mr-2" />
                View Logs
              </Button>
            </CardContent>
          </Card>

          {/* Requirements */}
          <Card>
            <CardHeader>
              <CardTitle>Requirements</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {plugin.requirements.map((requirement, index) => (
                  <div key={index} className="flex items-start gap-2">
                    <AlertCircle className="h-4 w-4 text-yellow-600 mt-0.5" />
                    <span className="text-sm">{requirement}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Security */}
          <Card>
            <CardHeader>
              <CardTitle>Security</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <Shield className="h-4 w-4 text-green-600" />
                  <span className="text-sm">Encrypted connections</span>
                </div>
                <div className="flex items-center gap-2">
                  <Shield className="h-4 w-4 text-green-600" />
                  <span className="text-sm">Token-based authentication</span>
                </div>
                <div className="flex items-center gap-2">
                  <Shield className="h-4 w-4 text-green-600" />
                  <span className="text-sm">Audit logging</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Version Info */}
          <Card>
            <CardHeader>
              <CardTitle>Version Information</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span>Current Version:</span>
                  <Badge variant="outline">v{plugin.version}</Badge>
                </div>
                <div className="flex justify-between">
                  <span>Last Updated:</span>
                  <span>{new Date(plugin.lastUpdated).toLocaleDateString()}</span>
                </div>
                <div className="flex justify-between">
                  <span>Downloads:</span>
                  <span>{plugin.downloads}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}