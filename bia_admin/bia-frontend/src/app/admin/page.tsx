import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  Settings, 
  Plug, 
  Database, 
  Shield, 
  Monitor,
  ExternalLink,
  CheckCircle,
  AlertCircle,
  Clock
} from 'lucide-react'

export default function AdminPage() {
  const services = [
    { name: 'ClickHouse', status: 'healthy', url: 'http://localhost:8123' },
    { name: 'Temporal', status: 'healthy', url: 'http://localhost:8080' },
    { name: 'Redis', status: 'healthy', url: 'http://localhost:6379' },
    { name: 'MinIO', status: 'healthy', url: 'http://localhost:9501' },
    { name: 'Kafdrop', status: 'warning', url: 'http://localhost:9999' },
  ]

  const plugins = [
    { name: 'Azure EA Connector', status: 'active', version: '1.2.0' },
    { name: 'AWS Cost Explorer', status: 'inactive', version: '1.0.1' },
    { name: 'GCP Billing Export', status: 'active', version: '0.9.2' },
    { name: 'FOCUS Transformer', status: 'active', version: '2.1.0' },
    { name: 'Cost Optimizer', status: 'pending', version: '1.5.0' },
  ]

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'active':
        return <CheckCircle className="h-4 w-4 text-green-600" />
      case 'warning':
      case 'pending':
        return <Clock className="h-4 w-4 text-yellow-600" />
      case 'inactive':
      default:
        return <AlertCircle className="h-4 w-4 text-red-600" />
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'active':
        return <Badge variant="success">{status}</Badge>
      case 'warning':
      case 'pending':
        return <Badge variant="warning">{status}</Badge>
      case 'inactive':
      default:
        return <Badge variant="secondary">{status}</Badge>
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">System Administration</h1>
        <p className="text-muted-foreground">
          Manage plugins, connections, and system settings
        </p>
      </div>

      {/* System Health Overview */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">System Health</CardTitle>
            <Monitor className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">Healthy</div>
            <p className="text-xs text-muted-foreground">
              All services operational
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Plugins</CardTitle>
            <Plug className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">3</div>
            <p className="text-xs text-muted-foreground">
              2 pending updates
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Data Sources</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">2</div>
            <p className="text-xs text-muted-foreground">
              Azure EA, S3 Storage
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Security</CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">Secure</div>
            <p className="text-xs text-muted-foreground">
              All connections encrypted
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Infrastructure Services */}
      <Card>
        <CardHeader>
          <CardTitle>Infrastructure Services</CardTitle>
          <CardDescription>
            Status and management links for core system components
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {services.map((service) => (
              <div key={service.name} className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex items-center gap-3">
                  {getStatusIcon(service.status)}
                  <div>
                    <h4 className="font-medium">{service.name}</h4>
                    <p className="text-sm text-muted-foreground">{service.url}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {getStatusBadge(service.status)}
                  <Button variant="outline" size="sm" asChild>
                    <a href={service.url} target="_blank" rel="noopener noreferrer">
                      <ExternalLink className="h-3 w-3 mr-1" />
                      Open
                    </a>
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Plugin Management */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Plugin Management</CardTitle>
              <CardDescription>
                Manage data connectors and processing plugins
              </CardDescription>
            </div>
            <Button>
              <Plug className="h-4 w-4 mr-2" />
              Browse Marketplace
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {plugins.map((plugin) => (
              <div key={plugin.name} className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex items-center gap-3">
                  {getStatusIcon(plugin.status)}
                  <div>
                    <h4 className="font-medium">{plugin.name}</h4>
                    <p className="text-sm text-muted-foreground">Version {plugin.version}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {getStatusBadge(plugin.status)}
                  <Button variant="outline" size="sm">
                    <Settings className="h-3 w-3 mr-1" />
                    Configure
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Connection Manager</CardTitle>
            <CardDescription>
              Manage Azure, ClickHouse, and storage connections
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button className="w-full">
              <Database className="h-4 w-4 mr-2" />
              Manage Connections
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>System Logs</CardTitle>
            <CardDescription>
              View system logs and troubleshoot issues
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button variant="outline" className="w-full">
              <Monitor className="h-4 w-4 mr-2" />
              View Logs
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Security Settings</CardTitle>
            <CardDescription>
              Configure authentication and access controls
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button variant="outline" className="w-full">
              <Shield className="h-4 w-4 mr-2" />
              Security Settings
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}