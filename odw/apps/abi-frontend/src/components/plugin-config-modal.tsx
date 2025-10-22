'use client'

import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { usePluginConfiguration } from '@/hooks/usePlugins'
import { pluginsApi } from '@/api/plugins'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { 
  AlertCircle, 
  CheckCircle, 
  Eye, 
  EyeOff, 
  TestTube,
  Save,
  X
} from 'lucide-react'

// Schema for Azure Blob Storage configuration
const azureBlobConfigSchema = z.object({
  storageAccount: z.string().min(1, 'Storage account name is required'),
  sasToken: z.string().min(1, 'SAS token is required'),
  dataContainer: z.string().min(1, 'Data container name is required'),
  pathPrefix: z.string().optional(),
})

// Schema for FOCUS Transformer configuration
const focusTransformerConfigSchema = z.object({
  inputFormat: z.enum(['parquet', 'csv', 'json']).default('parquet'),
  outputModel: z.enum(['moose', 'clickhouse', 'parquet']).default('moose'),
  focusVersion: z.enum(['1.0', '1.1', '1.2']).default('1.2'),
  compressionType: z.enum(['snappy', 'gzip', 'lz4', 'none']).default('snappy'),
  batchSize: z.number().min(1000).max(1000000).default(10000),
  enableValidation: z.boolean().default(true),
  sinkPlugin: z.string().optional(),
})

// Schema for ClickHouse Sink configuration
const clickhouseSinkConfigSchema = z.object({
  dbName: z.string().min(1, 'Database name is required'),
  user: z.string().min(1, 'Username is required'),
  password: z.string().min(1, 'Password is required'),
  host: z.string().min(1, 'Host is required'),
  port: z.number().min(1).max(65535).default(8443),
  useSSL: z.boolean().default(true),
  tableName: z.string().min(1, 'Table name is required'),
  createTableIfNotExists: z.boolean().default(true),
  batchSize: z.number().min(100).max(100000).default(1000),
})

type AzureBlobConfig = z.infer<typeof azureBlobConfigSchema>
type FocusTransformerConfig = z.infer<typeof focusTransformerConfigSchema>
type ClickHouseSinkConfig = z.infer<typeof clickhouseSinkConfigSchema>

interface PluginConfigModalProps {
  pluginName: string
  isOpen: boolean
  onClose: () => void
  onSave: (config: any) => void
}

export function PluginConfigModal({ pluginName, isOpen, onClose, onSave }: PluginConfigModalProps) {
  const [showSasToken, setShowSasToken] = useState(false)
  const [testStatus, setTestStatus] = useState<'idle' | 'testing' | 'success' | 'error'>('idle')
  const [testMessage, setTestMessage] = useState('')
  
  // Load existing configuration
  const { data: existingConfig, isLoading: configLoading } = usePluginConfiguration(pluginName)

  // Azure Blob Storage form
  const azureBlobForm = useForm<AzureBlobConfig>({
    resolver: zodResolver(azureBlobConfigSchema),
    defaultValues: {
      storageAccount: '',
      sasToken: '',
      dataContainer: 'focus-data',
      pathPrefix: 'billing/',
    },
  })

  // FOCUS Transformer form
  const focusTransformerForm = useForm<FocusTransformerConfig>({
    resolver: zodResolver(focusTransformerConfigSchema),
    defaultValues: {
      inputFormat: 'parquet',
      outputModel: 'moose',
      focusVersion: '1.2',
      compressionType: 'snappy',
      batchSize: 10000,
      enableValidation: true,
      sinkPlugin: 'ClickHouse Sink',
    },
  })

  // ClickHouse Sink form
  const clickhouseSinkForm = useForm<ClickHouseSinkConfig>({
    resolver: zodResolver(clickhouseSinkConfigSchema),
    defaultValues: {
      dbName: 'finops-odw',
      user: 'finops',
      password: 'cU2f947&9T{6d',
      host: 'ck.mightytech.cn',
      port: 8443,
      useSSL: true,
      tableName: 'focus_billing_data',
      createTableIfNotExists: true,
      batchSize: 1000,
    },
  })

  // Update form values when existing configuration is loaded
  useEffect(() => {
    if (existingConfig && pluginName === 'ClickHouse Sink') {
      clickhouseSinkForm.reset(existingConfig)
    } else if (existingConfig && pluginName === 'Azure Blob Storage Connector') {
      azureBlobForm.reset(existingConfig)
    } else if (existingConfig && pluginName === 'FOCUS 1.2 Transformer') {
      focusTransformerForm.reset(existingConfig)
    }
  }, [existingConfig, pluginName, clickhouseSinkForm, azureBlobForm, focusTransformerForm])

  const handleTestConnection = async () => {
    setTestStatus('testing')
    setTestMessage('')

    let configPayload: any | undefined
    if (pluginName === 'ClickHouse Sink') {
      configPayload = clickhouseSinkForm.getValues()
    } else if (pluginName === 'Azure Blob Storage Connector') {
      configPayload = azureBlobForm.getValues()
    } else if (pluginName === 'FOCUS 1.2 Transformer') {
      configPayload = focusTransformerForm.getValues()
    }
    
    try {
      const result = await pluginsApi.testPlugin(pluginName, configPayload)
      setTestStatus('success')
      
      if (pluginName === 'Azure Blob Storage Connector') {
        const fileCount =
          result?.object_count ??
          result?.test_results?.object_count ??
          result?.fileCount ??
          result?.test_results?.fileCount ??
          0
        const prefix =
          result?.path_prefix ??
          result?.test_results?.path_prefix ??
          configPayload?.pathPrefix ??
          ''
        const scopeMessage = prefix ? ` under '${prefix}'` : ''
        setTestMessage(`Connection successful! Found ${fileCount} parquet file(s)${scopeMessage}.`)
      } else if (pluginName === 'ClickHouse Sink') {
        const databaseName = result?.database ?? result?.test_results?.database ?? configPayload?.dbName ?? 'finops-odw'
        setTestMessage(`Connection successful! Connected to database '${databaseName}'.`)
      } else {
        setTestMessage(result?.message ?? 'Connection test successful!')
      }
    } catch (error) {
      setTestStatus('error')
      let errorMessage = 'Connection failed. Please check your credentials and configuration.'
      if (error instanceof Error) {
        const rawMessage = error.message.replace(/^HTTP \d+:\s*/i, '')
        try {
          const parsed = JSON.parse(rawMessage)
          errorMessage = parsed?.detail ?? errorMessage
        } catch {
          errorMessage = rawMessage || errorMessage
        }
      }
      setTestMessage(errorMessage)
      console.error('Connection test failed:', error)
    }
  }

  const handleSave = (data: any) => {
    onSave(data)
    onClose()
  }

  if (!isOpen) return null

  const renderAzureBlobConfig = () => (
    <form onSubmit={azureBlobForm.handleSubmit(handleSave)} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="storageAccount">Storage Account Name</Label>
        <Input
          id="storageAccount"
          placeholder="mystorageaccount"
          {...azureBlobForm.register('storageAccount')}
        />
        {azureBlobForm.formState.errors.storageAccount && (
          <p className="text-sm text-destructive flex items-center gap-1">
            <AlertCircle className="h-3 w-3" />
            {azureBlobForm.formState.errors.storageAccount.message}
          </p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="sasToken">SAS Token</Label>
        <div className="relative">
          <Input
            id="sasToken"
            type={showSasToken ? 'text' : 'password'}
            placeholder="?sv=2022-11-02&ss=bfqt&srt=..."
            {...azureBlobForm.register('sasToken')}
          />
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="absolute right-0 top-0 h-full px-3"
            onClick={() => setShowSasToken(!showSasToken)}
          >
            {showSasToken ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </Button>
        </div>
        {azureBlobForm.formState.errors.sasToken && (
          <p className="text-sm text-destructive flex items-center gap-1">
            <AlertCircle className="h-3 w-3" />
            {azureBlobForm.formState.errors.sasToken.message}
          </p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="dataContainer">Data Container</Label>
        <Input
          id="dataContainer"
          placeholder="focus-data"
          {...azureBlobForm.register('dataContainer')}
        />
        {azureBlobForm.formState.errors.dataContainer && (
          <p className="text-sm text-destructive flex items-center gap-1">
            <AlertCircle className="h-3 w-3" />
            {azureBlobForm.formState.errors.dataContainer.message}
          </p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="pathPrefix">Path Prefix (Optional)</Label>
        <Input
          id="pathPrefix"
          placeholder="billing/"
          {...azureBlobForm.register('pathPrefix')}
        />
        <p className="text-xs text-muted-foreground">
          Optional path prefix within the container (e.g., "billing/" or "exports/2024/")
        </p>
      </div>

      {/* Test Connection */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between mb-2">
            <h4 className="font-medium">Test Connection</h4>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleTestConnection}
              disabled={testStatus === 'testing'}
            >
              <TestTube className="h-3 w-3 mr-1" />
              {testStatus === 'testing' ? 'Testing...' : 'Test'}
            </Button>
          </div>
          {testStatus !== 'idle' && (
            <div className={`flex items-center gap-2 text-sm ${
              testStatus === 'success' ? 'text-green-600' : 
              testStatus === 'error' ? 'text-destructive' : 
              'text-muted-foreground'
            }`}>
              {testStatus === 'success' && <CheckCircle className="h-3 w-3" />}
              {testStatus === 'error' && <AlertCircle className="h-3 w-3" />}
              {testMessage}
            </div>
          )}
        </CardContent>
      </Card>

      <div className="flex justify-end gap-2 pt-4">
        <Button type="button" variant="outline" onClick={onClose}>
          Cancel
        </Button>
        <Button type="submit">
          <Save className="h-3 w-3 mr-1" />
          Save Configuration
        </Button>
      </div>
    </form>
  )

  const renderFocusTransformerConfig = () => (
    <form onSubmit={focusTransformerForm.handleSubmit(handleSave)} className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="inputFormat">Input Format</Label>
          <select
            id="inputFormat"
            {...focusTransformerForm.register('inputFormat')}
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          >
            <option value="parquet">Parquet</option>
            <option value="csv">CSV</option>
            <option value="json">JSON</option>
          </select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="outputModel">Output Model</Label>
          <select
            id="outputModel"
            {...focusTransformerForm.register('outputModel')}
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          >
            <option value="moose">Moose Model (Recommended)</option>
            <option value="clickhouse">ClickHouse Direct</option>
            <option value="parquet">Parquet Files</option>
          </select>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="focusVersion">FOCUS Version</Label>
          <select
            id="focusVersion"
            {...focusTransformerForm.register('focusVersion')}
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          >
            <option value="1.0">FOCUS 1.0</option>
            <option value="1.1">FOCUS 1.1</option>
            <option value="1.2">FOCUS 1.2 (Latest)</option>
          </select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="compressionType">Compression</Label>
          <select
            id="compressionType"
            {...focusTransformerForm.register('compressionType')}
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          >
            <option value="snappy">Snappy (Recommended)</option>
            <option value="gzip">GZIP</option>
            <option value="lz4">LZ4</option>
            <option value="none">None</option>
          </select>
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="batchSize">Batch Size</Label>
        <Input
          id="batchSize"
          type="number"
          min="1000"
          max="1000000"
          {...focusTransformerForm.register('batchSize', { valueAsNumber: true })}
        />
        <p className="text-xs text-muted-foreground">
          Number of records to process in each batch (1,000 - 1,000,000)
        </p>
      </div>

      <div className="space-y-2">
        <Label htmlFor="sinkPlugin">Data Sink Plugin</Label>
        <select
          id="sinkPlugin"
          {...focusTransformerForm.register('sinkPlugin')}
          className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
        >
          <option value="">No sink (output only)</option>
          <option value="ClickHouse Sink">ClickHouse Sink</option>
          <option value="Azure Blob Storage">Azure Blob Storage</option>
          <option value="S3 Sink">Amazon S3</option>
        </select>
      </div>

      <div className="flex items-center space-x-2">
        <input
          id="enableValidation"
          type="checkbox"
          {...focusTransformerForm.register('enableValidation')}
          className="rounded border-gray-300"
        />
        <Label htmlFor="enableValidation" className="text-sm">
          Enable FOCUS schema validation
        </Label>
      </div>

      {/* Configuration Preview */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Configuration Preview</CardTitle>
        </CardHeader>
        <CardContent className="p-4 pt-0">
          <div className="space-y-2 text-xs">
            <div className="flex justify-between">
              <span>Transform:</span>
              <Badge variant="outline">
                {focusTransformerForm.watch('inputFormat')} → {focusTransformerForm.watch('outputModel')}
              </Badge>
            </div>
            <div className="flex justify-between">
              <span>Target:</span>
              <Badge variant="outline">FOCUS {focusTransformerForm.watch('focusVersion')}</Badge>
            </div>
            <div className="flex justify-between">
              <span>Compression:</span>
              <Badge variant="outline">{focusTransformerForm.watch('compressionType')}</Badge>
            </div>
            <div className="flex justify-between">
              <span>Batch Size:</span>
              <Badge variant="outline">{focusTransformerForm.watch('batchSize')?.toLocaleString()}</Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end gap-2 pt-4">
        <Button type="button" variant="outline" onClick={onClose}>
          Cancel
        </Button>
        <Button type="submit">
          <Save className="h-3 w-3 mr-1" />
          Save Configuration
        </Button>
      </div>
    </form>
  )

  const renderClickHouseSinkConfig = () => (
    <form onSubmit={clickhouseSinkForm.handleSubmit(handleSave)} className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="dbName">Database Name</Label>
          <Input
            id="dbName"
            placeholder="finops-odw"
            {...clickhouseSinkForm.register('dbName')}
          />
          {clickhouseSinkForm.formState.errors.dbName && (
            <p className="text-sm text-destructive flex items-center gap-1">
              <AlertCircle className="h-3 w-3" />
              {clickhouseSinkForm.formState.errors.dbName.message}
            </p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="user">Username</Label>
          <Input
            id="user"
            placeholder="finops"
            {...clickhouseSinkForm.register('user')}
          />
          {clickhouseSinkForm.formState.errors.user && (
            <p className="text-sm text-destructive flex items-center gap-1">
              <AlertCircle className="h-3 w-3" />
              {clickhouseSinkForm.formState.errors.user.message}
            </p>
          )}
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="password">Password</Label>
        <div className="relative">
          <Input
            id="password"
            type={showSasToken ? 'text' : 'password'}
            placeholder="Enter password"
            {...clickhouseSinkForm.register('password')}
          />
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="absolute right-0 top-0 h-full px-3"
            onClick={() => setShowSasToken(!showSasToken)}
          >
            {showSasToken ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </Button>
        </div>
        {clickhouseSinkForm.formState.errors.password && (
          <p className="text-sm text-destructive flex items-center gap-1">
            <AlertCircle className="h-3 w-3" />
            {clickhouseSinkForm.formState.errors.password.message}
          </p>
        )}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="host">Host</Label>
          <Input
            id="host"
            placeholder="ck.mightytech.cn"
            {...clickhouseSinkForm.register('host')}
          />
          {clickhouseSinkForm.formState.errors.host && (
            <p className="text-sm text-destructive flex items-center gap-1">
              <AlertCircle className="h-3 w-3" />
              {clickhouseSinkForm.formState.errors.host.message}
            </p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="port">Port</Label>
          <Input
            id="port"
            type="number"
            min="1"
            max="65535"
            {...clickhouseSinkForm.register('port', { valueAsNumber: true })}
          />
          {clickhouseSinkForm.formState.errors.port && (
            <p className="text-sm text-destructive flex items-center gap-1">
              <AlertCircle className="h-3 w-3" />
              {clickhouseSinkForm.formState.errors.port.message}
            </p>
          )}
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="tableName">Table Name</Label>
          <Input
            id="tableName"
            placeholder="focus_billing_data"
            {...clickhouseSinkForm.register('tableName')}
          />
          {clickhouseSinkForm.formState.errors.tableName && (
            <p className="text-sm text-destructive flex items-center gap-1">
              <AlertCircle className="h-3 w-3" />
              {clickhouseSinkForm.formState.errors.tableName.message}
            </p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="batchSize">Batch Size</Label>
          <Input
            id="batchSize"
            type="number"
            min="100"
            max="100000"
            {...clickhouseSinkForm.register('batchSize', { valueAsNumber: true })}
          />
          <p className="text-xs text-muted-foreground">
            Records per batch (100 - 100,000)
          </p>
        </div>
      </div>

      <div className="space-y-3">
        <div className="flex items-center space-x-2">
          <input
            id="useSSL"
            type="checkbox"
            {...clickhouseSinkForm.register('useSSL')}
            className="rounded border-gray-300"
          />
          <Label htmlFor="useSSL" className="text-sm">
            Use SSL/TLS encryption
          </Label>
        </div>

        <div className="flex items-center space-x-2">
          <input
            id="createTableIfNotExists"
            type="checkbox"
            {...clickhouseSinkForm.register('createTableIfNotExists')}
            className="rounded border-gray-300"
          />
          <Label htmlFor="createTableIfNotExists" className="text-sm">
            Create table if it doesn't exist
          </Label>
        </div>
      </div>

      {/* Connection Test */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between mb-2">
            <h4 className="font-medium">Test Connection</h4>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleTestConnection}
              disabled={testStatus === 'testing'}
            >
              <TestTube className="h-3 w-3 mr-1" />
              {testStatus === 'testing' ? 'Testing...' : 'Test'}
            </Button>
          </div>
          {testStatus !== 'idle' && (
            <div className={`flex items-center gap-2 text-sm ${
              testStatus === 'success' ? 'text-green-600' : 
              testStatus === 'error' ? 'text-destructive' : 
              'text-muted-foreground'
            }`}>
              {testStatus === 'success' && <CheckCircle className="h-3 w-3" />}
              {testStatus === 'error' && <AlertCircle className="h-3 w-3" />}
              {testMessage}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Configuration Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Connection Summary</CardTitle>
        </CardHeader>
        <CardContent className="p-4 pt-0">
          <div className="space-y-2 text-xs">
            <div className="flex justify-between">
              <span>Database:</span>
              <Badge variant="outline">{clickhouseSinkForm.watch('dbName')}</Badge>
            </div>
            <div className="flex justify-between">
              <span>Host:</span>
              <Badge variant="outline">
                {clickhouseSinkForm.watch('host')}:{clickhouseSinkForm.watch('port')}
              </Badge>
            </div>
            <div className="flex justify-between">
              <span>SSL:</span>
              <Badge variant={clickhouseSinkForm.watch('useSSL') ? 'success' : 'secondary'}>
                {clickhouseSinkForm.watch('useSSL') ? 'Enabled' : 'Disabled'}
              </Badge>
            </div>
            <div className="flex justify-between">
              <span>Table:</span>
              <Badge variant="outline">{clickhouseSinkForm.watch('tableName')}</Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end gap-2 pt-4">
        <Button type="button" variant="outline" onClick={onClose}>
          Cancel
        </Button>
        <Button type="submit">
          <Save className="h-3 w-3 mr-1" />
          Save Configuration
        </Button>
      </div>
    </form>
  )

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-background rounded-lg shadow-lg max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b">
          <div>
            <h2 className="text-xl font-semibold">Configure {pluginName}</h2>
            <p className="text-sm text-muted-foreground">
              Set up connection and processing parameters
            </p>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>
        
        <div className="p-6">
          {configLoading ? (
            <div className="flex items-center justify-center p-8">
              <div className="text-muted-foreground">Loading configuration...</div>
            </div>
          ) : (
            <>
              {pluginName === 'Azure Blob Storage Connector' && renderAzureBlobConfig()}
              {pluginName === 'FOCUS 1.2 Transformer' && renderFocusTransformerConfig()}
              {pluginName === 'ClickHouse Sink' && renderClickHouseSinkConfig()}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
