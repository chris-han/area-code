"""Data models for schema migration."""

from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class SchemaDiff:
    """Represents schema differences between source and canonical FOCUS schema."""

    requires_migration: bool
    added_columns: List[str]
    removed_columns: List[str]
    type_changes: Dict[str, Tuple[str, str]]
    new_version: str

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'requires_migration': self.requires_migration,
            'added_columns': self.added_columns,
            'removed_columns': self.removed_columns,
            'type_changes': self.type_changes,
            'new_version': self.new_version
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'SchemaDiff':
        """Create SchemaDiff from dictionary."""
        return cls(
            requires_migration=data['requires_migration'],
            added_columns=data['added_columns'],
            removed_columns=data['removed_columns'],
            type_changes=data['type_changes'],
            new_version=data['new_version']
        )


@dataclass
class MigrationResult:
    """Result of schema migration execution."""

    rows_migrated: int
    old_version: str
    new_version: str
    status: str
    duration_seconds: float

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'rows_migrated': self.rows_migrated,
            'old_version': self.old_version,
            'new_version': self.new_version,
            'status': self.status,
            'duration_seconds': self.duration_seconds
        }
