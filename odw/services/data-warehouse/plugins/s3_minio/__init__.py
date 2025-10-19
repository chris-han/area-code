"""
S3/MinIO CSV Plugin

Data source plugin for S3-compatible object storage integration
with CSV billing data extraction and FOCUS transformation.
"""

from .plugin import S3MinIOPlugin, create_plugin

__all__ = ["S3MinIOPlugin", "create_plugin"]