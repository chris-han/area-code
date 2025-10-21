#!/bin/bash

# Plugin Configuration Setup Script
# This script sets up the plugin registry database and default configurations

set -e  # Exit on any error

echo "🚀 Azure Billing Intelligence - Plugin Configuration Setup"
echo "=========================================================="

# Check if we're in the right directory
if [ ! -f "services/data-warehouse/moose.config.toml" ]; then
    echo "❌ Error: moose.config.toml not found. Please run this script from the ODW root directory."
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is required but not installed."
    exit 1
fi

# Check if required Python packages are available
echo "📦 Checking Python dependencies..."

# Check if uv is available
if command -v uv &> /dev/null; then
    echo "📦 Using uv for Python package management..."
    # Install required packages if not available
    uv pip install --system --quiet psycopg2-binary toml 2>/dev/null || {
        echo "📦 Installing required Python packages with uv..."
        uv pip install --system psycopg2-binary toml
    }
else
    # Fallback to pip with system packages override
    pip3 install --quiet psycopg2-binary toml 2>/dev/null || {
        echo "📦 Installing required Python packages..."
        pip3 install --break-system-packages psycopg2-binary toml
    }
fi

echo "✅ Python dependencies ready"

# Run the setup script
echo "🔧 Running plugin configuration setup..."
python3 scripts/setup-plugin-config.py

echo ""
echo "✅ Setup completed successfully!"
echo ""
echo "📋 What was configured:"
echo "   • Plugin registry database schema"
echo "   • Azure Blob Storage Connector (default config)"
echo "   • FOCUS 1.2 Transformer (with Moose model output)"
echo "   • ClickHouse Sink (using moose.config.toml settings)"
echo "   • Azure EA Connector (default config)"
echo "   • GCP Billing Export (default config)"
echo ""
echo "🌐 Next steps:"
echo "   1. Start the ABI frontend: cd apps/abi-frontend && bun run dev"
echo "   2. Open http://localhost:3003/admin/plugins"
echo "   3. Configure your Azure storage credentials"
echo "   4. Test plugin connections"
echo ""
echo "🔗 Plugin configurations are stored in the plugin_registry_db:"
echo "   Database: bia_config"
echo "   Schema: plugin_registry"
echo "   Table: plugin_configurations"