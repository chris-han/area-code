# Plugin Frontend Integration

## React Components

### Plugin Configuration Modal

Interactive modal for configuring plugin settings with form validation.

**Location**: `src/components/plugin-config-modal.tsx`

**Features:**
- Dynamic form generation based on plugin type
- Zod schema validation
- Password masking for sensitive fields
- Connection testing
- Real-time configuration preview

**Usage:**
```tsx
<PluginConfigModal
  pluginName="ClickHouse Sink"
  isOpen={configModalOpen}
  onClose={() => setConfigModalOpen(false)}
  onSave={handleSaveConfig}
/>
```

### Plugin Marketplace

Plugin discovery and management interface.

**Location**: `src/app/admin/plugins/page.tsx`

**Features:**
- Plugin grid with ratings and metadata
- Installation status indicators
- Search and filtering
- Category-based organization
- Configuration access

## React Hooks

### usePluginConfiguration

Load existing plugin configuration from database.

```tsx
const { data: config, isLoading } = usePluginConfiguration('ClickHouse Sink')
```

### usePlugins

Get all available plugins from marketplace.

```tsx
const { data: plugins, isLoading, error } = usePlugins()
```

### useConfigurePlugin

Save plugin configuration with optimistic updates.

```tsx
const configurePlugin = useConfigurePlugin()

const handleSave = async (config) => {
  await configurePlugin.mutateAsync({ pluginName, config })
}
```

### useTestPlugin

Test plugin connection and configuration.

```tsx
const testPlugin = useTestPlugin()

const handleTest = async () => {
  const result = await testPlugin.mutateAsync(pluginName)
}
```

## API Client

### Plugin API Wrapper

**Location**: `src/api/plugins.ts`

**Methods:**
- `getPlugins()` - Get marketplace plugins
- `configurePlugin(name, config)` - Save configuration
- `getPluginConfiguration(name)` - Load configuration
- `testPlugin(name)` - Test plugin connection
- `installPlugin(name, config)` - Install plugin

## State Management

### Zustand Store

Global state for plugin management.

**Location**: `src/lib/store.ts`

**State:**
- Active plugins list
- Configuration cache
- Installation status
- Error handling

## Form Validation

### Zod Schemas

Type-safe validation for plugin configurations.

**Location**: `src/lib/schemas.ts`

**Schemas:**
- `azureBlobConfigSchema` - Azure Blob Storage validation
- `focusTransformerConfigSchema` - FOCUS Transformer validation
- `clickhouseSinkConfigSchema` - ClickHouse Sink validation

## UI Components

### ShadCN Integration

- **Cards** - Plugin display containers
- **Forms** - Configuration input forms
- **Badges** - Status and category indicators
- **Buttons** - Actions and navigation
- **Modals** - Configuration dialogs

### Navigation

Plugin management accessible via:
- Main navigation: `/admin/plugins`
- Plugin details: `/admin/plugins/[slug]`
- Configuration modals: Overlay interface

## Error Handling

- Form validation errors with inline display
- API error handling with user-friendly messages
- Connection test results with success/failure indicators
- Loading states during async operations