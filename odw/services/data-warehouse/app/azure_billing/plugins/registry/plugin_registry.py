"""
Plugin Registry

PostgreSQL-based plugin registry with metadata storage, installation tracking,
and configuration management for the ABI plugin marketplace.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from uuid import UUID, uuid4
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import json
import logging
import asyncio

import asyncpg
from asyncpg.exceptions import (
    DuplicateDatabaseError,
    InvalidCatalogNameError,
    InvalidSchemaNameError,
)
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


class PluginType(Enum):
    """Plugin type enumeration"""
    DATA_SOURCE = "data_source"
    TRANSFORMATION = "transformation"
    OUTPUT = "output"
    UTILITY = "utility"


class PluginStatus(Enum):
    """Plugin status enumeration"""
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    DISABLED = "disabled"


class InstallationStatus(Enum):
    """Installation status enumeration"""
    INSTALLED = "installed"
    ACTIVE = "active"
    DISABLED = "disabled"
    FAILED = "failed"
    UNINSTALLED = "uninstalled"


class HealthStatus(Enum):
    """Plugin health status enumeration"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class PluginMetadata:
    """Plugin metadata structure"""
    id: Optional[UUID]
    name: str
    display_name: str
    description: str
    version: str
    author: str
    category: str
    tags: List[str]
    plugin_type: PluginType
    entry_point: str
    requirements: List[str]
    icon_url: Optional[str] = None
    documentation_url: Optional[str] = None
    repository_url: Optional[str] = None
    license: Optional[str] = None
    config_schema: Optional[Dict[str, Any]] = None
    default_config: Optional[Dict[str, Any]] = None
    status: PluginStatus = PluginStatus.ACTIVE
    is_official: bool = False
    is_verified: bool = False
    download_count: int = 0
    rating: float = 0.0
    review_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None


@dataclass
class PluginVersion:
    """Plugin version information"""
    id: Optional[UUID]
    plugin_id: UUID
    version: str
    changelog: Optional[str] = None
    breaking_changes: Optional[str] = None
    migration_notes: Optional[str] = None
    min_abi_version: Optional[str] = None
    max_abi_version: Optional[str] = None
    python_version: Optional[str] = None
    package_url: Optional[str] = None
    package_hash: Optional[str] = None
    package_size: Optional[int] = None
    is_stable: bool = True
    is_prerelease: bool = False
    is_deprecated: bool = False
    created_at: Optional[datetime] = None
    published_at: Optional[datetime] = None


@dataclass
class PluginInstallation:
    """Plugin installation record"""
    id: Optional[UUID]
    plugin_id: UUID
    version_id: Optional[UUID]
    installation_id: str
    instance_id: str
    config: Optional[Dict[str, Any]] = None
    environment_variables: Optional[Dict[str, Any]] = None
    status: InstallationStatus = InstallationStatus.INSTALLED
    health_status: HealthStatus = HealthStatus.UNKNOWN
    last_health_check: Optional[datetime] = None
    installed_by: Optional[str] = None
    installation_method: str = "manual"
    last_used: Optional[datetime] = None
    usage_count: int = 0
    installed_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class PluginConfigurationRecord:
    """Stored plugin configuration entry"""
    id: Optional[UUID]
    plugin_name: str
    configuration: Dict[str, Any]
    description: Optional[str]
    version: Optional[str]
    created_by: Optional[str]
    updated_by: Optional[str]
    is_active: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class PluginRegistryConfig(BaseModel):
    """Plugin registry configuration"""
    host: str
    port: int = 5432
    database: str
    user: str
    password: str
    db_schema: str = "plugin_registry"  # Renamed from 'schema' to avoid shadowing BaseModel.schema
    pool_min_size: int = 5
    pool_max_size: int = 20
    command_timeout: int = 60
    maintenance_database: str = "postgres"
    auto_create_database: bool = True
    auto_run_schema: bool = True
    schema_sql_path: Optional[str] = None

    @classmethod
    def from_dict(cls, config_dict: dict) -> "PluginRegistryConfig":
        """
        Create PluginRegistryConfig from dictionary, handling field name mapping.

        Maps 'schema' to 'db_schema' to avoid Pydantic warning.
        """
        # Create a copy to avoid modifying the original
        config = config_dict.copy()

        # Map 'schema' to 'db_schema' if present
        if "schema" in config:
            config["db_schema"] = config.pop("schema")

        return cls(**config)


class PluginRegistry:
    """
    PostgreSQL-based plugin registry for managing plugin metadata,
    installations, and configurations.
    """
    
    def __init__(self, config: PluginRegistryConfig):
        self.config = config
        self.pool: Optional[asyncpg.Pool] = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize the plugin registry connection pool"""
        if self._initialized:
            return
        
        try:
            try:
                await self._create_pool()
            except InvalidCatalogNameError as exc:
                if not self.config.auto_create_database:
                    logger.error(
                        "Plugin registry database %s is missing and auto creation is disabled.",
                        self.config.database,
                    )
                    raise

                logger.warning(
                    "Plugin registry database %s not found. Attempting to create it.",
                    self.config.database,
                )
                await self._ensure_database_exists()
                await self._create_pool()

            await self._set_search_path(ignore_missing_schema=True)

            if self.config.auto_run_schema:
                await self._apply_schema()
                await self._set_search_path()

            self._initialized = True
            logger.info("Plugin registry initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize plugin registry: {e}")
            raise
    
    async def close(self):
        """Close the connection pool"""
        if self.pool:
            await self.pool.close()
            self._initialized = False

    async def _create_pool(self):
        """Create asyncpg connection pool"""
        self.pool = await asyncpg.create_pool(
            host=self.config.host,
            port=self.config.port,
            database=self.config.database,
            user=self.config.user,
            password=self.config.password,
            min_size=self.config.pool_min_size,
            max_size=self.config.pool_max_size,
            command_timeout=self.config.command_timeout,
        )

    async def _set_search_path(self, ignore_missing_schema: bool = False):
        """Ensure all connections use the configured schema"""
        if not self.pool:
            return

        async with self.pool.acquire() as conn:
            try:
                await conn.execute(f"SET search_path TO {self.config.db_schema}")
            except InvalidSchemaNameError:
                if ignore_missing_schema:
                    logger.info(
                        "Plugin registry schema %s not found yet; continuing without search_path update",
                        self.config.db_schema,
                    )
                    return
                raise

    async def _ensure_database_exists(self):
        """Create the plugin registry database if it does not exist"""
        connection = await asyncpg.connect(
            host=self.config.host,
            port=self.config.port,
            database=self.config.maintenance_database,
            user=self.config.user,
            password=self.config.password,
            command_timeout=self.config.command_timeout,
        )

        try:
            await connection.execute(f'CREATE DATABASE "{self.config.database}"')
            logger.info("Created plugin registry database %s", self.config.database)
        except DuplicateDatabaseError:
            logger.info("Plugin registry database %s already exists", self.config.database)
        except Exception as exc:
            logger.error(
                "Unable to create plugin registry database %s: %s",
                self.config.database,
                exc,
            )
            raise
        finally:
            await connection.close()

    async def _apply_schema(self):
        """Run schema SQL to ensure required tables exist"""
        if not self.pool:
            return

        schema_path = (
            Path(self.config.schema_sql_path).resolve()
            if self.config.schema_sql_path
            else Path(__file__).resolve().with_name("schema.sql")
        )

        if not schema_path.exists():
            logger.warning("Schema file not found at %s; skipping schema initialization", schema_path)
            return

        sql_statements = self._load_schema_statements(schema_path)
        if not sql_statements:
            return

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                for statement in sql_statements:
                    await conn.execute(statement)

        logger.info("Plugin registry schema ensured at %s", schema_path)

    def _load_schema_statements(self, schema_path: Path) -> List[str]:
        """Load and split schema SQL into executable statements"""
        try:
            content = schema_path.read_text(encoding="utf-8")
        except Exception as exc:
            logger.error("Unable to read schema file %s: %s", schema_path, exc)
            return []

        statements: List[str] = []
        buffer: List[str] = []

        in_dollar_quote = False

        for line in content.splitlines():
            stripped = line.strip()

            # Skip empty lines and comments
            if not stripped or stripped.startswith("--"):
                continue

            buffer.append(line)

            line_no_comment = line.split("--", 1)[0]
            if line_no_comment.count("$$") % 2 == 1:
                in_dollar_quote = not in_dollar_quote

            if not in_dollar_quote and line_no_comment.rstrip().endswith(";"):
                statement = "\n".join(buffer).strip()
                statements.append(statement)
                buffer = []

        # Add any remaining statement without trailing semicolon
        if buffer:
            statement = "\n".join(buffer).strip()
            statements.append(statement)

        return statements

    def _table(self, name: str) -> str:
        """Return fully-qualified table reference for the configured schema."""
        if self.config.db_schema:
            return f"{self.config.db_schema}.{name}"
        return name
    
    async def register_plugin(self, plugin: PluginMetadata) -> UUID:
        """
        Register a new plugin in the registry.
        
        Args:
            plugin: Plugin metadata
            
        Returns:
            Plugin UUID
        """
        if not self._initialized:
            await self.initialize()
        
        plugin_id = uuid4()
        
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO plugins (
                    id, name, display_name, description, version, author, category, tags,
                    plugin_type, entry_point, requirements, icon_url, documentation_url,
                    repository_url, license, config_schema, default_config, status,
                    is_official, is_verified, published_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21
                )
            """, 
                plugin_id, plugin.name, plugin.display_name, plugin.description,
                plugin.version, plugin.author, plugin.category, plugin.tags,
                plugin.plugin_type.value, plugin.entry_point, plugin.requirements,
                plugin.icon_url, plugin.documentation_url, plugin.repository_url,
                plugin.license, json.dumps(plugin.config_schema) if plugin.config_schema else None,
                json.dumps(plugin.default_config) if plugin.default_config else None,
                plugin.status.value, plugin.is_official, plugin.is_verified,
                plugin.published_at or datetime.utcnow()
            )
        
        logger.info(f"Registered plugin: {plugin.name} ({plugin_id})")
        return plugin_id
    
    async def get_plugin(self, plugin_id: UUID) -> Optional[PluginMetadata]:
        """
        Get plugin metadata by ID.
        
        Args:
            plugin_id: Plugin UUID
            
        Returns:
            Plugin metadata or None if not found
        """
        if not self._initialized:
            await self.initialize()
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM plugins WHERE id = $1
            """, plugin_id)
            
            if not row:
                return None
            
            return self._row_to_plugin_metadata(row)
    
    async def get_plugin_by_name(self, name: str) -> Optional[PluginMetadata]:
        """
        Get plugin metadata by name.
        
        Args:
            name: Plugin name
            
        Returns:
            Plugin metadata or None if not found
        """
        if not self._initialized:
            await self.initialize()
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM plugins WHERE name = $1
            """, name)
            
            if not row:
                return None
            
            return self._row_to_plugin_metadata(row)
    
    async def list_plugins(self, 
                          category: Optional[str] = None,
                          plugin_type: Optional[PluginType] = None,
                          status: Optional[PluginStatus] = None,
                          tags: Optional[List[str]] = None,
                          search_query: Optional[str] = None,
                          limit: int = 50,
                          offset: int = 0) -> List[PluginMetadata]:
        """
        List plugins with optional filtering.
        
        Args:
            category: Filter by category
            plugin_type: Filter by plugin type
            status: Filter by status
            tags: Filter by tags (any match)
            search_query: Search in name and description
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of plugin metadata
        """
        if not self._initialized:
            await self.initialize()
        
        # Build dynamic query
        conditions = []
        params = []
        param_count = 0
        
        if category:
            param_count += 1
            conditions.append(f"category = ${param_count}")
            params.append(category)
        
        if plugin_type:
            param_count += 1
            conditions.append(f"plugin_type = ${param_count}")
            params.append(plugin_type.value)
        
        if status:
            param_count += 1
            conditions.append(f"status = ${param_count}")
            params.append(status.value)
        
        if tags:
            param_count += 1
            conditions.append(f"tags && ${param_count}")
            params.append(tags)
        
        if search_query:
            param_count += 1
            conditions.append(f"(name ILIKE ${param_count} OR description ILIKE ${param_count})")
            params.append(f"%{search_query}%")
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        param_count += 1
        limit_param = f"${param_count}"
        params.append(limit)
        
        param_count += 1
        offset_param = f"${param_count}"
        params.append(offset)
        
        query = f"""
            SELECT * FROM plugins 
            {where_clause}
            ORDER BY rating DESC, download_count DESC, created_at DESC
            LIMIT {limit_param} OFFSET {offset_param}
        """
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [self._row_to_plugin_metadata(row) for row in rows]
    
    async def update_plugin(self, plugin_id: UUID, updates: Dict[str, Any]) -> bool:
        """
        Update plugin metadata.
        
        Args:
            plugin_id: Plugin UUID
            updates: Dictionary of fields to update
            
        Returns:
            True if update successful
        """
        if not self._initialized:
            await self.initialize()
        
        if not updates:
            return True
        
        # Build dynamic update query
        set_clauses = []
        params = []
        param_count = 0
        
        for field, value in updates.items():
            param_count += 1
            set_clauses.append(f"{field} = ${param_count}")
            
            # Handle JSON fields
            if field in ['config_schema', 'default_config'] and value is not None:
                params.append(json.dumps(value))
            else:
                params.append(value)
        
        param_count += 1
        params.append(plugin_id)
        
        query = f"""
            UPDATE plugins 
            SET {', '.join(set_clauses)}, updated_at = CURRENT_TIMESTAMP
            WHERE id = ${param_count}
        """
        
        async with self.pool.acquire() as conn:
            result = await conn.execute(query, *params)
            return result.split()[-1] == "1"  # Check if one row was updated
    
    async def delete_plugin(self, plugin_id: UUID) -> bool:
        """
        Delete a plugin from the registry.
        
        Args:
            plugin_id: Plugin UUID
            
        Returns:
            True if deletion successful
        """
        if not self._initialized:
            await self.initialize()
        
        async with self.pool.acquire() as conn:
            result = await conn.execute("""
                DELETE FROM plugins WHERE id = $1
            """, plugin_id)
            
            return result.split()[-1] == "1"
    
    async def create_installation(self, installation: PluginInstallation) -> UUID:
        """
        Create a new plugin installation record.
        
        Args:
            installation: Installation details
            
        Returns:
            Installation UUID
        """
        if not self._initialized:
            await self.initialize()
        
        installation_uuid = uuid4()
        
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO plugin_installations (
                    id, plugin_id, version_id, installation_id, instance_id,
                    config, environment_variables, status, health_status,
                    installed_by, installation_method
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11
                )
            """,
                installation_uuid, installation.plugin_id, installation.version_id,
                installation.installation_id, installation.instance_id,
                json.dumps(installation.config) if installation.config else None,
                json.dumps(installation.environment_variables) if installation.environment_variables else None,
                installation.status.value, installation.health_status.value,
                installation.installed_by, installation.installation_method
            )
        
        logger.info(f"Created installation: {installation.installation_id}")
        return installation_uuid
    
    async def get_installation(self, installation_id: str) -> Optional[PluginInstallation]:
        """
        Get installation by installation ID.
        
        Args:
            installation_id: Installation identifier
            
        Returns:
            Installation details or None if not found
        """
        if not self._initialized:
            await self.initialize()
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM plugin_installations WHERE installation_id = $1
            """, installation_id)
            
            if not row:
                return None
            
            return self._row_to_plugin_installation(row)
    
    async def list_installations(self, 
                               instance_id: Optional[str] = None,
                               plugin_id: Optional[UUID] = None,
                               status: Optional[InstallationStatus] = None) -> List[PluginInstallation]:
        """
        List plugin installations with optional filtering.
        
        Args:
            instance_id: Filter by instance ID
            plugin_id: Filter by plugin ID
            status: Filter by installation status
            
        Returns:
            List of installations
        """
        if not self._initialized:
            await self.initialize()
        
        conditions = []
        params = []
        param_count = 0
        
        if instance_id:
            param_count += 1
            conditions.append(f"instance_id = ${param_count}")
            params.append(instance_id)
        
        if plugin_id:
            param_count += 1
            conditions.append(f"plugin_id = ${param_count}")
            params.append(plugin_id)
        
        if status:
            param_count += 1
            conditions.append(f"status = ${param_count}")
            params.append(status.value)
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        query = f"""
            SELECT * FROM plugin_installations 
            {where_clause}
            ORDER BY installed_at DESC
        """
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [self._row_to_plugin_installation(row) for row in rows]
    
    async def update_installation_status(self, 
                                       installation_id: str, 
                                       status: InstallationStatus,
                                       health_status: Optional[HealthStatus] = None) -> bool:
        """
        Update installation status.
        
        Args:
            installation_id: Installation identifier
            status: New installation status
            health_status: Optional health status
            
        Returns:
            True if update successful
        """
        if not self._initialized:
            await self.initialize()
        
        async with self.pool.acquire() as conn:
            if health_status:
                result = await conn.execute("""
                    UPDATE plugin_installations 
                    SET status = $1, health_status = $2, last_health_check = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                    WHERE installation_id = $3
                """, status.value, health_status.value, installation_id)
            else:
                result = await conn.execute("""
                    UPDATE plugin_installations 
                    SET status = $1, updated_at = CURRENT_TIMESTAMP
                    WHERE installation_id = $2
                """, status.value, installation_id)
            
            return result.split()[-1] == "1"
    
    async def record_plugin_usage(self, installation_id: str) -> bool:
        """
        Record plugin usage.
        
        Args:
            installation_id: Installation identifier
            
        Returns:
            True if recording successful
        """
        if not self._initialized:
            await self.initialize()
        
        async with self.pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE plugin_installations 
                SET usage_count = usage_count + 1, last_used = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE installation_id = $1
            """, installation_id)
            
            return result.split()[-1] == "1"
    
    async def get_plugin_statistics(self) -> Dict[str, Any]:
        """
        Get plugin registry statistics.
        
        Returns:
            Dictionary with various statistics
        """
        if not self._initialized:
            await self.initialize()
        
        async with self.pool.acquire() as conn:
            # Plugin counts by category and type
            plugin_stats = await conn.fetch("""
                SELECT 
                    category,
                    plugin_type,
                    status,
                    COUNT(*) as count
                FROM plugins 
                GROUP BY category, plugin_type, status
            """)
            
            # Installation stats
            installation_stats = await conn.fetch("""
                SELECT 
                    status,
                    health_status,
                    COUNT(*) as count
                FROM plugin_installations 
                GROUP BY status, health_status
            """)
            
            # Top plugins by downloads and rating
            top_plugins = await conn.fetch("""
                SELECT name, download_count, rating, review_count
                FROM plugins 
                WHERE status = 'active'
                ORDER BY download_count DESC, rating DESC
                LIMIT 10
            """)
            
            return {
                "plugin_stats": [dict(row) for row in plugin_stats],
                "installation_stats": [dict(row) for row in installation_stats],
                "top_plugins": [dict(row) for row in top_plugins],
                "total_plugins": len(await self.list_plugins(limit=1000)),
                "active_installations": len(await self.list_installations(status=InstallationStatus.ACTIVE))
            }
    
    async def get_plugin_configuration(self, plugin_name: str) -> Optional[PluginConfigurationRecord]:
        """
        Retrieve stored configuration for a plugin.
        """
        if not self._initialized:
            await self.initialize()

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                f"""
                SELECT id, plugin_name, configuration, description, version,
                       created_by, updated_by, is_active, created_at, updated_at
                FROM {self._table('plugin_configurations')}
                WHERE plugin_name = $1 AND is_active = TRUE
                ORDER BY updated_at DESC
                LIMIT 1
                """,
                plugin_name,
            )

        if not row:
            return None

        return self._row_to_plugin_configuration(row)

    async def list_plugin_configurations(self) -> List[PluginConfigurationRecord]:
        """
        List all plugin configurations.
        """
        if not self._initialized:
            await self.initialize()

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                f"""
                SELECT id, plugin_name, configuration, description, version,
                       created_by, updated_by, is_active, created_at, updated_at
                FROM {self._table('plugin_configurations')}
                ORDER BY plugin_name, updated_at DESC
                """
            )

        return [self._row_to_plugin_configuration(row) for row in rows]

    async def upsert_plugin_configuration(
        self,
        plugin_name: str,
        configuration: Dict[str, Any],
        description: Optional[str] = None,
        version: Optional[str] = None,
        updated_by: Optional[str] = None,
    ) -> PluginConfigurationRecord:
        """
        Create or update a plugin configuration entry.
        """
        if not self._initialized:
            await self.initialize()

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    f"""
                    UPDATE {self._table('plugin_configurations')}
                    SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
                    WHERE plugin_name = $1 AND is_active = TRUE
                    """,
                    plugin_name,
                )

                actor = updated_by or "frontend"

                row = await conn.fetchrow(
                    f"""
                    INSERT INTO {self._table('plugin_configurations')} (
                        plugin_name,
                        configuration,
                        description,
                        version,
                        created_by,
                        updated_by,
                        is_active
                    ) VALUES ($1, CAST($2 AS jsonb), $3, $4, $5, $6, TRUE)
                    RETURNING id, plugin_name, configuration, description, version,
                              created_by, updated_by, is_active, created_at, updated_at
                    """,
                    plugin_name,
                    json.dumps(configuration) if configuration is not None else None,
                    description,
                    version,
                    actor,
                    actor,
                )

        return self._row_to_plugin_configuration(row)
    
    def _row_to_plugin_metadata(self, row) -> PluginMetadata:
        """Convert database row to PluginMetadata"""
        return PluginMetadata(
            id=row['id'],
            name=row['name'],
            display_name=row['display_name'],
            description=row['description'],
            version=row['version'],
            author=row['author'],
            category=row['category'],
            tags=row['tags'] or [],
            plugin_type=PluginType(row['plugin_type']),
            entry_point=row['entry_point'],
            requirements=row['requirements'] or [],
            icon_url=row['icon_url'],
            documentation_url=row['documentation_url'],
            repository_url=row['repository_url'],
            license=row['license'],
            config_schema=json.loads(row['config_schema']) if row['config_schema'] else None,
            default_config=json.loads(row['default_config']) if row['default_config'] else None,
            status=PluginStatus(row['status']),
            is_official=row['is_official'],
            is_verified=row['is_verified'],
            download_count=row['download_count'],
            rating=float(row['rating']),
            review_count=row['review_count'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            published_at=row['published_at']
        )
    
    def _row_to_plugin_installation(self, row) -> PluginInstallation:
        """Convert database row to PluginInstallation"""
        return PluginInstallation(
            id=row['id'],
            plugin_id=row['plugin_id'],
            version_id=row['version_id'],
            installation_id=row['installation_id'],
            instance_id=row['instance_id'],
            config=json.loads(row['config']) if row['config'] else None,
            environment_variables=json.loads(row['environment_variables']) if row['environment_variables'] else None,
            status=InstallationStatus(row['status']),
            health_status=HealthStatus(row['health_status']),
            last_health_check=row['last_health_check'],
            installed_by=row['installed_by'],
            installation_method=row['installation_method'],
            last_used=row['last_used'],
            usage_count=row['usage_count'],
            installed_at=row['installed_at'],
            updated_at=row['updated_at']
        )

    def _row_to_plugin_configuration(self, row) -> PluginConfigurationRecord:
        """Convert database row to PluginConfigurationRecord"""
        configuration = row["configuration"]
        if isinstance(configuration, str):
            try:
                configuration = json.loads(configuration)
            except json.JSONDecodeError:
                logger.warning("Stored configuration for %s is not valid JSON", row["plugin_name"])
        return PluginConfigurationRecord(
            id=row["id"],
            plugin_name=row["plugin_name"],
            configuration=configuration or {},
            description=row["description"],
            version=row["version"],
            created_by=row.get("created_by"),
            updated_by=row["updated_by"],
            is_active=row.get("is_active", True),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
