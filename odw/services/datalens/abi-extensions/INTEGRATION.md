# ABI Extensions Integration Guide

This directory contains the ABI (Application Binary Interface) extensions for DataLens, providing custom components and functionality specific to the ODW (Operational Data Warehouse) implementation.

## Integration with DataLens UI

The ABI extensions are now properly integrated within the DataLens UI project structure:

### Directory Structure
```
abi-extensions/
├── src/                    # Extension source code
│   ├── components/         # Custom React components
│   ├── connectors/         # Data source connectors
│   ├── charts/            # Custom chart types
│   └── utils/             # Utility functions
├── package.json           # Extension dependencies
└── README.md             # Extension documentation
```

### Build Integration

The extensions are automatically included during the Docker build process:

1. **Frontend Dockerfile** (`frontend-abi.Dockerfile`):
   ```dockerfile
   # Copy ABI extensions (integrated within datalens-ui)
   COPY datalens-ui/abi-extensions /app/src/abi-extensions
   ```

2. **Volume Mounts** (for development):
   ```yaml
   volumes:
     # Production mount
     - ./datalens-ui/abi-extensions:/app/abi-extensions:ro
     # Development hot reload
     - ./datalens-ui/abi-extensions/src:/app/src/abi-extensions:ro
   ```

### Environment Configuration

ABI extensions are enabled through environment variables:

```yaml
environment:
  - ENABLE_ABI_EXTENSIONS=true
  - FOCUS_SPECIFICATION_VERSION=1.0
  - REACT_APP_ENABLE_ABI_EXTENSIONS=true  # For development
```

## Development Workflow

### 1. Local Development
When developing ABI extensions locally:

```bash
cd odw/services/datalens/datalens-ui
npm install  # Install main dependencies

cd abi-extensions
npm install  # Install extension dependencies

# Make changes to extension files
# Hot reload will automatically pick up changes via volume mount
```

### 2. Building Extensions
Extensions are built as part of the main DataLens build process:

```bash
cd odw/services/datalens
docker-compose build datalens-frontend
```

### 3. Testing Integration
Test the integration using the development environment:

```bash
./scripts/dev.sh  # Starts integrated DataLens with Moose
```

## Extension Types

### Custom Components
- Location: `src/components/`
- Purpose: Reusable UI components specific to ODW needs
- Integration: Imported into main DataLens component library

### Data Connectors
- Location: `src/connectors/`
- Purpose: Custom data source connections (ClickHouse, Moose-specific)
- Integration: Registered with DataLens connection manager

### Chart Types
- Location: `src/charts/`
- Purpose: Custom visualization types for ODW data
- Integration: Added to DataLens chart registry

### Utilities
- Location: `src/utils/`
- Purpose: Helper functions and shared logic
- Integration: Available throughout the application

## Configuration Files

The ABI extensions use configuration files from the main config directory:

- `config/connections.yaml` - Data source configurations
- `config/dashboards.yaml` - Dashboard templates and layouts

These are copied into the container during build and mounted for development.

## Troubleshooting

### Common Issues

1. **Extensions not loading**: Check `ENABLE_ABI_EXTENSIONS=true` in environment
2. **Build failures**: Ensure all dependencies are installed in both main and extension package.json
3. **Hot reload not working**: Verify volume mounts are correct in docker-compose.override.yml

### Verification

Check that extensions are properly integrated:

```bash
# Check if extensions directory is mounted
docker exec datalens_datalens-frontend_1 ls -la /app/src/abi-extensions

# Check environment variables
docker exec datalens_datalens-frontend_1 env | grep ABI

# Check build logs
docker-compose logs datalens-frontend
```

## Best Practices

1. **Modular Design**: Keep extensions modular and loosely coupled
2. **Configuration**: Use configuration files for customizable behavior
3. **Documentation**: Document all custom components and their usage
4. **Testing**: Include tests for extension functionality
5. **Version Control**: Keep extensions in sync with DataLens UI versions

## Integration with Moose

The ABI extensions are designed to work seamlessly with the Moose data warehouse:

- **Data Sources**: Direct integration with Moose ClickHouse instance
- **Event Streaming**: Can publish/consume from Moose Redpanda topics
- **Caching**: Uses shared Redis instance (database 1)
- **Workflows**: Can trigger Moose Temporal workflows

This ensures that DataLens extensions can leverage the full Moose ecosystem while maintaining proper isolation and resource sharing.