-- Plugin Registry Database Schema
-- PostgreSQL schema for managing plugin metadata, installations, and configurations

-- Create schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS plugin_registry;

-- Set search path
SET search_path TO plugin_registry;

-- Plugin metadata table
CREATE TABLE IF NOT EXISTS plugins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    version VARCHAR(50) NOT NULL,
    author VARCHAR(255),
    category VARCHAR(100) NOT NULL,
    tags TEXT[], -- Array of tags for categorization
    
    -- Plugin technical details
    plugin_type VARCHAR(50) NOT NULL, -- 'data_source', 'transformation', 'output', 'utility'
    entry_point VARCHAR(500) NOT NULL, -- Python module path or file path
    requirements TEXT[], -- Array of Python package requirements
    
    -- Plugin metadata
    icon_url TEXT,
    documentation_url TEXT,
    repository_url TEXT,
    license VARCHAR(100),
    
    -- Configuration schema (JSON Schema)
    config_schema JSONB,
    default_config JSONB,
    
    -- Plugin status and lifecycle
    status VARCHAR(50) DEFAULT 'active', -- 'active', 'deprecated', 'disabled'
    is_official BOOLEAN DEFAULT false,
    is_verified BOOLEAN DEFAULT false,
    
    -- Metrics and usage
    download_count INTEGER DEFAULT 0,
    rating DECIMAL(3,2) DEFAULT 0.0,
    review_count INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    published_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT valid_plugin_type CHECK (plugin_type IN ('data_source', 'transformation', 'output', 'utility')),
    CONSTRAINT valid_status CHECK (status IN ('active', 'deprecated', 'disabled')),
    CONSTRAINT valid_rating CHECK (rating >= 0.0 AND rating <= 5.0)
);

-- Plugin versions table for version management
CREATE TABLE IF NOT EXISTS plugin_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plugin_id UUID NOT NULL REFERENCES plugins(id) ON DELETE CASCADE,
    version VARCHAR(50) NOT NULL,
    
    -- Version-specific metadata
    changelog TEXT,
    breaking_changes TEXT,
    migration_notes TEXT,
    
    -- Compatibility information
    min_abi_version VARCHAR(50),
    max_abi_version VARCHAR(50),
    python_version VARCHAR(50),
    
    -- Version artifacts
    package_url TEXT,
    package_hash VARCHAR(128),
    package_size BIGINT,
    
    -- Version status
    is_stable BOOLEAN DEFAULT true,
    is_prerelease BOOLEAN DEFAULT false,
    is_deprecated BOOLEAN DEFAULT false,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    published_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    UNIQUE(plugin_id, version)
);

-- Plugin installations table
CREATE TABLE IF NOT EXISTS plugin_installations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plugin_id UUID NOT NULL REFERENCES plugins(id) ON DELETE CASCADE,
    version_id UUID REFERENCES plugin_versions(id) ON DELETE SET NULL,
    
    -- Installation details
    installation_id VARCHAR(255) NOT NULL UNIQUE, -- Unique per bia instance
    instance_id VARCHAR(255) NOT NULL, -- bia instance identifier
    
    -- Installation configuration
    config JSONB,
    environment_variables JSONB,
    
    -- Installation status
    status VARCHAR(50) DEFAULT 'installed', -- 'installed', 'active', 'disabled', 'failed', 'uninstalled'
    health_status VARCHAR(50) DEFAULT 'unknown', -- 'healthy', 'unhealthy', 'unknown'
    last_health_check TIMESTAMP WITH TIME ZONE,
    
    -- Installation metadata
    installed_by VARCHAR(255),
    installation_method VARCHAR(50) DEFAULT 'manual', -- 'manual', 'auto', 'marketplace'
    
    -- Usage tracking
    last_used TIMESTAMP WITH TIME ZONE,
    usage_count INTEGER DEFAULT 0,
    
    -- Timestamps
    installed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT valid_installation_status CHECK (status IN ('installed', 'active', 'disabled', 'failed', 'uninstalled')),
    CONSTRAINT valid_health_status CHECK (health_status IN ('healthy', 'unhealthy', 'unknown'))
);

-- Plugin configuration table
CREATE TABLE IF NOT EXISTS plugin_configurations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plugin_name VARCHAR(255) NOT NULL,
    configuration JSONB NOT NULL,
    description TEXT,
    version VARCHAR(50),
    created_by VARCHAR(255) DEFAULT 'system',
    updated_by VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Plugin dependencies table
CREATE TABLE IF NOT EXISTS plugin_dependencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plugin_id UUID NOT NULL REFERENCES plugins(id) ON DELETE CASCADE,
    dependency_plugin_id UUID NOT NULL REFERENCES plugins(id) ON DELETE CASCADE,
    
    -- Dependency constraints
    min_version VARCHAR(50),
    max_version VARCHAR(50),
    is_optional BOOLEAN DEFAULT false,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    UNIQUE(plugin_id, dependency_plugin_id),
    CHECK (plugin_id != dependency_plugin_id) -- Prevent self-dependency
);

-- Plugin reviews and ratings table
CREATE TABLE IF NOT EXISTS plugin_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plugin_id UUID NOT NULL REFERENCES plugins(id) ON DELETE CASCADE,
    
    -- Review details
    reviewer_id VARCHAR(255) NOT NULL, -- User identifier
    rating INTEGER NOT NULL,
    title VARCHAR(255),
    review_text TEXT,
    
    -- Review metadata
    version_reviewed VARCHAR(50),
    is_verified_purchase BOOLEAN DEFAULT false,
    
    -- Moderation
    is_approved BOOLEAN DEFAULT true,
    moderation_notes TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT valid_rating CHECK (rating >= 1 AND rating <= 5),
    UNIQUE(plugin_id, reviewer_id) -- One review per user per plugin
);

-- Plugin categories table
CREATE TABLE IF NOT EXISTS plugin_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    icon VARCHAR(100),
    sort_order INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Plugin tags table
CREATE TABLE IF NOT EXISTS plugin_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    display_name VARCHAR(255) NOT NULL,
    color VARCHAR(7), -- Hex color code
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Plugin usage analytics table
CREATE TABLE IF NOT EXISTS plugin_usage_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    installation_id UUID NOT NULL REFERENCES plugin_installations(id) ON DELETE CASCADE,
    
    -- Usage metrics
    event_type VARCHAR(100) NOT NULL, -- 'activation', 'execution', 'error', 'configuration_change'
    event_data JSONB,
    
    -- Performance metrics
    execution_time_ms INTEGER,
    memory_usage_mb INTEGER,
    cpu_usage_percent DECIMAL(5,2),
    
    -- Error tracking
    error_message TEXT,
    error_stack_trace TEXT,
    
    -- Timestamps
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_plugins_name ON plugins(name);
CREATE INDEX IF NOT EXISTS idx_plugins_category ON plugins(category);
CREATE INDEX IF NOT EXISTS idx_plugins_status ON plugins(status);
CREATE INDEX IF NOT EXISTS idx_plugins_created_at ON plugins(created_at);

CREATE INDEX IF NOT EXISTS idx_plugin_versions_plugin_id ON plugin_versions(plugin_id);
CREATE INDEX IF NOT EXISTS idx_plugin_versions_version ON plugin_versions(version);

CREATE INDEX IF NOT EXISTS idx_plugin_installations_plugin_id ON plugin_installations(plugin_id);
CREATE INDEX IF NOT EXISTS idx_plugin_installations_instance_id ON plugin_installations(instance_id);
CREATE INDEX IF NOT EXISTS idx_plugin_installations_status ON plugin_installations(status);

CREATE INDEX IF NOT EXISTS idx_plugin_reviews_plugin_id ON plugin_reviews(plugin_id);
CREATE INDEX IF NOT EXISTS idx_plugin_reviews_rating ON plugin_reviews(rating);

CREATE UNIQUE INDEX IF NOT EXISTS unique_active_plugin_config 
    ON plugin_configurations(plugin_name)
    WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_plugin_configurations_name 
    ON plugin_configurations(plugin_name);
CREATE INDEX IF NOT EXISTS idx_plugin_configurations_active 
    ON plugin_configurations(is_active);
CREATE INDEX IF NOT EXISTS idx_plugin_configurations_created_at 
    ON plugin_configurations(created_at);

CREATE INDEX IF NOT EXISTS idx_usage_analytics_installation_recorded 
    ON plugin_usage_analytics(installation_id, recorded_at);
CREATE INDEX IF NOT EXISTS idx_usage_analytics_event_type 
    ON plugin_usage_analytics(event_type);
CREATE INDEX IF NOT EXISTS idx_usage_analytics_recorded_at 
    ON plugin_usage_analytics(recorded_at);

CREATE INDEX IF NOT EXISTS idx_plugin_configurations_name 
    ON plugin_configurations(plugin_name);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at columns
DROP TRIGGER IF EXISTS update_plugins_updated_at ON plugins;
CREATE TRIGGER update_plugins_updated_at 
    BEFORE UPDATE ON plugins 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_plugin_installations_updated_at ON plugin_installations;
CREATE TRIGGER update_plugin_installations_updated_at 
    BEFORE UPDATE ON plugin_installations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_plugin_reviews_updated_at ON plugin_reviews;
CREATE TRIGGER update_plugin_reviews_updated_at 
    BEFORE UPDATE ON plugin_reviews 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_plugin_configurations_updated_at ON plugin_configurations;
CREATE TRIGGER update_plugin_configurations_updated_at 
    BEFORE UPDATE ON plugin_configurations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default categories
INSERT INTO plugin_categories (name, display_name, description, sort_order) VALUES
('data_source', 'Data Sources', 'Plugins for extracting data from various sources', 1),
('transformation', 'Transformations', 'Plugins for data transformation and processing', 2),
('output', 'Output Connectors', 'Plugins for sending data to external systems', 3),
('utility', 'Utilities', 'Helper plugins and tools', 4),
('analytics', 'Analytics', 'Plugins for data analysis and reporting', 5),
('security', 'Security', 'Plugins for security and compliance', 6)
ON CONFLICT (name) DO NOTHING;

-- Insert default tags
INSERT INTO plugin_tags (name, display_name, color) VALUES
('azure', 'Azure', '#0078d4'),
('aws', 'AWS', '#ff9900'),
('gcp', 'Google Cloud', '#4285f4'),
('billing', 'Billing', '#28a745'),
('focus', 'FOCUS', '#6f42c1'),
('api', 'API', '#17a2b8'),
('csv', 'CSV', '#ffc107'),
('json', 'JSON', '#fd7e14'),
('sql', 'SQL', '#20c997'),
('real-time', 'Real-time', '#dc3545'),
('batch', 'Batch Processing', '#6c757d'),
('official', 'Official', '#007bff')
ON CONFLICT (name) DO NOTHING;
