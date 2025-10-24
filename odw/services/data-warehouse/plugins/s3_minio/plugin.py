"""
S3/MinIO Plugin

Data source plugin for S3-compatible object storage integration
with CSV billing data extraction and FOCUS transformation.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime
import csv
import io
from pathlib import Path

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import pandas as pd

from ...app.azure_billing.plugins.manager import BasePlugin

logger = logging.getLogger(__name__)


class S3MinIOPlugin(BasePlugin):
    """
    S3/MinIO plugin for CSV billing data extraction.
    
    This plugin provides integration with S3-compatible storage services
    to extract CSV billing data for FOCUS transformation.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # S3/MinIO configuration
        self.endpoint_url = config.get("endpoint_url")  # None for AWS S3, URL for MinIO
        self.access_key_id = config.get("access_key_id")
        self.secret_access_key = config.get("secret_access_key")
        self.region_name = config.get("region_name", "us-east-1")
        self.bucket_name = config.get("bucket_name")
        self.use_ssl = config.get("use_ssl", True)
        
        # Processing configuration
        self.file_pattern = config.get("file_pattern", "*.csv")
        self.batch_size = config.get("batch_size", 1000)
        self.max_file_size_mb = config.get("max_file_size_mb", 100)
        self.encoding = config.get("encoding", "utf-8")
        
        # S3 client
        self.s3_client = None
        self.s3_resource = None
    
    async def initialize(self) -> bool:
        """Initialize the S3/MinIO plugin"""
        try:
            # Validate required configuration
            if not self.access_key_id or not self.secret_access_key or not self.bucket_name:
                logger.error("Missing required configuration: access_key_id, secret_access_key, or bucket_name")
                return False
            
            # Initialize S3 client
            self._init_s3_client()
            
            # Test connection
            connection_test = await self.test_connection()
            if not connection_test:
                logger.error("S3/MinIO connection test failed")
                return False
            
            self._initialized = True
            logger.info("S3/MinIO plugin initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize S3/MinIO plugin: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on S3/MinIO connection"""
        health_result = {
            "healthy": False,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {}
        }
        
        try:
            # Check client initialization
            if not self.s3_client:
                health_result["checks"]["client"] = {"status": "failed", "message": "S3 client not initialized"}
                return health_result
            
            health_result["checks"]["client"] = {"status": "ok", "message": "S3 client initialized"}
            
            # Test bucket access
            start_time = datetime.utcnow()
            try:
                response = self.s3_client.head_bucket(Bucket=self.bucket_name)
                response_time = (datetime.utcnow() - start_time).total_seconds()
                
                health_result["checks"]["bucket_access"] = {
                    "status": "ok",
                    "response_time_seconds": response_time,
                    "message": f"Bucket '{self.bucket_name}' accessible"
                }
                health_result["healthy"] = True
                
            except ClientError as e:
                error_code = e.response['Error']['Code']
                health_result["checks"]["bucket_access"] = {
                    "status": "failed",
                    "error_code": error_code,
                    "message": f"Bucket access failed: {error_code}"
                }
            
            # Test list objects permission
            try:
                response = self.s3_client.list_objects_v2(
                    Bucket=self.bucket_name,
                    MaxKeys=1
                )
                health_result["checks"]["list_permission"] = {
                    "status": "ok",
                    "message": "List objects permission available"
                }
            except ClientError as e:
                health_result["checks"]["list_permission"] = {
                    "status": "warning",
                    "message": f"List objects permission issue: {e.response['Error']['Code']}"
                }
            
        except Exception as e:
            health_result["checks"]["general"] = {
                "status": "failed",
                "message": f"Health check failed: {str(e)}"
            }
        
        return health_result
    
    async def cleanup(self):
        """Clean up plugin resources"""
        # S3 client doesn't need explicit cleanup
        logger.info("S3/MinIO plugin cleanup completed")
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """Return plugin metadata"""
        return {
            "name": "s3-minio-csv",
            "version": "1.0.0",
            "description": "S3/MinIO CSV data source plugin for billing data extraction",
            "author": "bia Team",
            "category": "data_source",
            "plugin_type": "data_source",
            "tags": ["s3", "minio", "csv", "billing", "storage"],
            "requirements": ["boto3>=1.26.0", "pandas>=1.5.0"],
            "config_schema": {
                "type": "object",
                "properties": {
                    "endpoint_url": {
                        "type": ["string", "null"],
                        "description": "S3 endpoint URL (null for AWS S3, URL for MinIO)",
                        "examples": ["http://localhost:9000", "https://s3.amazonaws.com"]
                    },
                    "access_key_id": {
                        "type": "string",
                        "description": "S3 access key ID"
                    },
                    "secret_access_key": {
                        "type": "string",
                        "description": "S3 secret access key",
                        "format": "password"
                    },
                    "region_name": {
                        "type": "string",
                        "default": "us-east-1",
                        "description": "S3 region name"
                    },
                    "bucket_name": {
                        "type": "string",
                        "description": "S3 bucket name containing CSV files"
                    },
                    "use_ssl": {
                        "type": "boolean",
                        "default": true,
                        "description": "Use SSL for connections"
                    },
                    "file_pattern": {
                        "type": "string",
                        "default": "*.csv",
                        "description": "File pattern to match CSV files"
                    },
                    "batch_size": {
                        "type": "integer",
                        "default": 1000,
                        "minimum": 100,
                        "maximum": 10000,
                        "description": "Number of records to process in each batch"
                    },
                    "max_file_size_mb": {
                        "type": "integer",
                        "default": 100,
                        "minimum": 1,
                        "maximum": 1000,
                        "description": "Maximum file size to process (MB)"
                    },
                    "encoding": {
                        "type": "string",
                        "default": "utf-8",
                        "description": "File encoding"
                    }
                },
                "required": ["access_key_id", "secret_access_key", "bucket_name"]
            },
            "icon_url": "https://aws.amazon.com/favicon.ico",
            "documentation_url": "https://boto3.amazonaws.com/v1/documentation/api/latest/index.html"
        }
    
    async def test_connection(self) -> bool:
        """Test connection to S3/MinIO"""
        try:
            if not self.s3_client:
                self._init_s3_client()
            
            # Test bucket access
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info("S3/MinIO connection test successful")
            return True
            
        except NoCredentialsError:
            logger.error("S3/MinIO credentials not found")
            return False
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                logger.error(f"Bucket '{self.bucket_name}' not found")
            elif error_code == '403':
                logger.error(f"Access denied to bucket '{self.bucket_name}'")
            else:
                logger.error(f"S3/MinIO connection test failed: {error_code}")
            return False
        except Exception as e:
            logger.error(f"S3/MinIO connection test failed: {e}")
            return False
    
    async def list_files(self, prefix: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List CSV files in the bucket.
        
        Args:
            prefix: Optional prefix to filter files
            
        Returns:
            List of file metadata
        """
        try:
            files = []
            
            # List objects in bucket
            paginator = self.s3_client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(
                Bucket=self.bucket_name,
                Prefix=prefix or ""
            )
            
            for page in page_iterator:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        # Filter CSV files
                        if obj['Key'].lower().endswith('.csv'):
                            # Check file size
                            size_mb = obj['Size'] / (1024 * 1024)
                            if size_mb <= self.max_file_size_mb:
                                files.append({
                                    "key": obj['Key'],
                                    "size_bytes": obj['Size'],
                                    "size_mb": round(size_mb, 2),
                                    "last_modified": obj['LastModified'],
                                    "etag": obj['ETag'].strip('"')
                                })
                            else:
                                logger.warning(f"Skipping large file {obj['Key']} ({size_mb:.2f} MB)")
            
            logger.info(f"Found {len(files)} CSV files in bucket")
            return files
            
        except Exception as e:
            logger.error(f"Failed to list files: {e}")
            return []
    
    async def extract_data(self, 
                          file_key: str,
                          start_row: int = 0,
                          max_rows: Optional[int] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Extract data from a CSV file.
        
        Args:
            file_key: S3 object key
            start_row: Starting row number
            max_rows: Maximum number of rows to read
            
        Yields:
            CSV records as dictionaries
        """
        try:
            # Get object
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=file_key)
            
            # Read CSV content
            content = response['Body'].read()
            
            # Decode content
            try:
                text_content = content.decode(self.encoding)
            except UnicodeDecodeError:
                # Try alternative encodings
                for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                    try:
                        text_content = content.decode(encoding)
                        logger.warning(f"Used {encoding} encoding for {file_key}")
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    raise ValueError(f"Could not decode file {file_key} with any encoding")
            
            # Parse CSV
            csv_reader = csv.DictReader(io.StringIO(text_content))
            
            # Skip to start row
            for _ in range(start_row):
                try:
                    next(csv_reader)
                except StopIteration:
                    return
            
            # Yield records
            row_count = 0
            for row_number, row in enumerate(csv_reader, start=start_row + 1):
                if max_rows and row_count >= max_rows:
                    break
                
                # Add metadata to row
                enriched_row = {
                    **row,
                    "_metadata": {
                        "source_file": file_key,
                        "row_number": row_number,
                        "extraction_timestamp": datetime.utcnow().isoformat()
                    }
                }
                
                yield enriched_row
                row_count += 1
                
                # Batch processing pause
                if row_count % self.batch_size == 0:
                    await asyncio.sleep(0.01)  # Small pause for other tasks
            
            logger.info(f"Extracted {row_count} records from {file_key}")
            
        except Exception as e:
            logger.error(f"Failed to extract data from {file_key}: {e}")
            raise
    
    async def get_file_schema(self, file_key: str) -> Dict[str, Any]:
        """
        Analyze CSV file schema.
        
        Args:
            file_key: S3 object key
            
        Returns:
            Schema information
        """
        try:
            # Get a sample of the file
            sample_records = []
            async for record in self.extract_data(file_key, max_rows=100):
                sample_records.append(record)
            
            if not sample_records:
                return {"error": "No data found in file"}
            
            # Analyze schema
            headers = list(sample_records[0].keys())
            if "_metadata" in headers:
                headers.remove("_metadata")
            
            schema = {
                "file_key": file_key,
                "headers": headers,
                "total_columns": len(headers),
                "sample_size": len(sample_records),
                "column_analysis": {}
            }
            
            # Analyze each column
            for header in headers:
                values = [record.get(header) for record in sample_records if record.get(header) is not None]
                
                if values:
                    schema["column_analysis"][header] = {
                        "non_null_count": len(values),
                        "null_percentage": ((len(sample_records) - len(values)) / len(sample_records)) * 100,
                        "sample_values": values[:5],
                        "detected_type": self._detect_column_type(values)
                    }
                else:
                    schema["column_analysis"][header] = {
                        "non_null_count": 0,
                        "null_percentage": 100.0,
                        "sample_values": [],
                        "detected_type": "unknown"
                    }
            
            return schema
            
        except Exception as e:
            logger.error(f"Failed to analyze schema for {file_key}: {e}")
            return {"error": str(e)}
    
    def _init_s3_client(self):
        """Initialize S3 client and resource"""
        try:
            # Configure S3 client
            client_config = {
                'aws_access_key_id': self.access_key_id,
                'aws_secret_access_key': self.secret_access_key,
                'region_name': self.region_name,
                'use_ssl': self.use_ssl
            }
            
            # Add endpoint URL for MinIO
            if self.endpoint_url:
                client_config['endpoint_url'] = self.endpoint_url
            
            self.s3_client = boto3.client('s3', **client_config)
            self.s3_resource = boto3.resource('s3', **client_config)
            
            logger.info("S3 client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            raise
    
    def _detect_column_type(self, values: List[Any]) -> str:
        """Detect column data type from sample values"""
        if not values:
            return "unknown"
        
        # Count type occurrences
        type_counts = {"numeric": 0, "date": 0, "boolean": 0, "string": 0}
        
        for value in values[:20]:  # Sample first 20 values
            str_value = str(value).strip().lower()
            
            # Check numeric
            try:
                float(str_value.replace(',', ''))
                type_counts["numeric"] += 1
                continue
            except ValueError:
                pass
            
            # Check boolean
            if str_value in ['true', 'false', 'yes', 'no', '1', '0']:
                type_counts["boolean"] += 1
                continue
            
            # Check date-like
            if any(char in str_value for char in ['-', '/', ':']):
                type_counts["date"] += 1
                continue
            
            # Default to string
            type_counts["string"] += 1
        
        # Return most common type
        return max(type_counts, key=type_counts.get)


# Plugin factory function
def create_plugin(config: Dict[str, Any]) -> S3MinIOPlugin:
    """Create and return plugin instance"""
    return S3MinIOPlugin(config)

# Plugin class for direct instantiation
Plugin = S3MinIOPlugin