# 🐍 Virtual Environment Setup Guide

This document explains the service-level virtual environment strategy for the ODW project.

## 📋 Overview

We use **service-level virtual environments** for clean dependency isolation:

- **Backend Services (Shared)**: `services/.venv/` (data-warehouse + connectors)
- **DW Frontend App**: `apps/dw-frontend/.venv/`

## 🚀 Quick Setup

```bash
# Setup all service venvs
./scripts/setup-venvs.sh

# Open VSCode workspace
code .vscode/odw.code-workspace
```

## 🎯 VSCode Integration

### Multi-Service Workspace
- **File**: `.vscode/odw.code-workspace`
- **Features**: 
  - Automatic Python interpreter switching per service
  - Service-specific settings and linting
  - Integrated terminal with correct venv activation

### Service-Specific Settings
Each service has its own `.vscode/settings.json`:

- **Data Warehouse**: `services/data-warehouse/.vscode/settings.json`
- **Connectors**: `services/connectors/.vscode/settings.json` 
- **Frontend**: `apps/dw-frontend/.vscode/settings.json`

### Available Tasks (Ctrl+Shift+P → "Tasks: Run Task")
- Setup All Venvs
- Clean All Venvs
- Data Warehouse: Start Dev
- Frontend: Start Streamlit
- Connectors: Run Tests
- Start All Services

### Debug Configurations (F5)
- Data Warehouse: Moose CLI Dev
- Frontend: Streamlit App
- Connectors: Run Tests

## 🛠️ Manual Commands

### Backend Services (Data Warehouse + Connectors)
```bash
cd services
source .venv/bin/activate
cd data-warehouse && moose-cli dev
```

### Frontend App
```bash
cd apps/dw-frontend  
source .venv/bin/activate
streamlit run main.py
```

### Connectors Development
```bash
cd services
source .venv/bin/activate  # Shared backend venv
cd connectors && python -m pytest tests/
```

## 📦 Dependencies

### Backend Services .venv contains:
- `moose-cli` and `moose-lib`
- `connectors` package (editable install)
- ClickHouse, Kafka, and workflow dependencies

### Frontend .venv contains:
- `streamlit` and dashboard libraries
- Plotting and visualization dependencies
- No backend/database dependencies

### Connectors package:
- Installed as editable dependency in shared backend .venv
- Provides data source connectors and factory patterns
- No standalone venv (uses data-warehouse venv)

## 🧹 Maintenance

### Clean and Recreate
```bash
./scripts/clean-venvs.sh
./scripts/setup-venvs.sh
```

### Update Dependencies
```bash
# Backend Services
cd services
source .venv/bin/activate
uv pip install -e connectors --upgrade
cd data-warehouse && uv pip install -r requirements.txt --upgrade

# Frontend  
cd apps/dw-frontend
source .venv/bin/activate
uv pip install -r requirements.txt --upgrade
```

## 🔍 Troubleshooting

### VSCode Not Using Correct Python
1. Open Command Palette (Ctrl+Shift+P)
2. "Python: Select Interpreter"
3. Choose the service-specific venv path

### Import Errors in Connectors
- Ensure you're using the shared backend .venv
- Connectors package should be installed as editable dependency

### Terminal Not Activating venv
- Check `.vscode/settings.json` in service folder
- Ensure `python.terminal.activateEnvironment: true`

## 🎉 Benefits

✅ **Clean Isolation**: No dependency conflicts between services  
✅ **Fast Development**: Only install what you need per service  
✅ **VSCode Integration**: Automatic venv switching and IntelliSense  
✅ **Production Ready**: Each service can be containerized independently  
✅ **Team Friendly**: Frontend devs don't need backend dependencies  
✅ **CI/CD Optimized**: Faster builds with service-specific dependencies  

This setup follows modern Python mono-repo best practices and provides an excellent developer experience!