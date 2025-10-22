"""
Storage management services for S3/MinIO configuration and validation.

These helpers are consumed by the BIA FastAPI routers and do not register
Moose consumption endpoints.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import asyncio

logger = logging.getLogger(__name__)


class S3Configuration(BaseModel):
    """S3/MinIO configuration model"""
    name: str
    endpoint_url: Optional[str] = None  # None for AWS S3, URL for MinIO
    access_key_id: str
    secret_access_key: str
    region_name: str = "us-east-1"
    bucket_name: str
    use_ssl: bool = True
    signature_version: str = "s3v4"
    path_prefix: Optional[str] = Field(default=None, alias="pathPrefix")

    model_config = {"populate_by_name": True}


class S3ConfigurationRequest(BaseModel):
    """S3/MinIO configuration request"""
    configuration: S3Configuration
    test_connection: bool = True


class S3ConfigurationResponse(BaseModel):
    """S3/MinIO configuration response"""
    success: bool
    message: str
    configuration_id: Optional[str] = None
    test_results: Optional[Dict[str, Any]] = None


class S3ConnectionTest(BaseModel):
    """S3/MinIO connection test parameters"""
    configuration: S3Configuration


class S3ConnectionTestResponse(BaseModel):
    """S3/MinIO connection test response"""
    success: bool
    message: str
    test_results: Dict[str, Any]
    response_time_ms: float


class S3BucketInfo(BaseModel):
    """S3 bucket information"""
    name: str
    creation_date: Optional[datetime] = None
    region: Optional[str] = None
    object_count: Optional[int] = None
    total_size_bytes: Optional[int] = None


class S3BucketListQuery(BaseModel):
    """S3 bucket list query parameters"""
    configuration_name: Optional[str] = None


class S3BucketListResponse(BaseModel):
    """S3 bucket list response"""
    buckets: List[S3BucketInfo]
    total_count: int
    configuration_used: str


class S3ObjectInfo(BaseModel):
    """S3 object information"""
    key: str
    size: int
    last_modified: datetime
    etag: str
    storage_class: Optional[str] = None


class S3ObjectListQuery(BaseModel):
    """S3 object list query parameters"""
    configuration_name: str
    bucket_name: Optional[str] = None
    prefix: Optional[str] = None
    max_keys: int = Field(default=100, ge=1, le=1000)


class S3ObjectListResponse(BaseModel):
    """S3 object list response"""
    objects: List[S3ObjectInfo]
    total_count: int
    bucket_name: str
    prefix_used: Optional[str] = None


def create_s3_client(config: S3Configuration):
    """Create S3 client from configuration"""
    try:
        client_config = {
            'aws_access_key_id': config.access_key_id,
            'aws_secret_access_key': config.secret_access_key,
            'region_name': config.region_name
        }
        
        if config.endpoint_url:
            client_config['endpoint_url'] = config.endpoint_url
        
        if config.signature_version:
            client_config['config'] = boto3.session.Config(
                signature_version=config.signature_version
            )
        
        return boto3.client('s3', **client_config)
        
    except Exception as e:
        logger.error(f"Failed to create S3 client: {e}")
        raise


async def configure_s3_storage(client, params: S3ConfigurationRequest) -> S3ConfigurationResponse:
    """
    Configure S3/MinIO storage connection.
    
    Args:
        client: Database client for storing configuration
        params: S3 configuration request
        
    Returns:
        S3ConfigurationResponse with configuration result
    """
    
    try:
        config = params.configuration
        
        # Validate configuration
        if not config.access_key_id or not config.secret_access_key:
            return S3ConfigurationResponse(
                success=False,
                message="Access key ID and secret access key are required"
            )
        
        if not config.bucket_name:
            return S3ConfigurationResponse(
                success=False,
                message="Bucket name is required"
            )
        
        # Test connection if requested
        test_results = None
        if params.test_connection:
            test_response = await test_s3_connection(client, S3ConnectionTest(configuration=config))
            test_results = test_response.test_results
            
            if not test_response.success:
                return S3ConfigurationResponse(
                    success=False,
                    message=f"Configuration test failed: {test_response.message}",
                    test_results=test_results
                )
        
        # Store configuration (in a real implementation, this would be stored in database)
        configuration_id = f"s3_config_{config.name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # In a real implementation, store in database:
        # await store_s3_configuration(client, configuration_id, config)
        
        return S3ConfigurationResponse(
            success=True,
            message=f"S3 configuration '{config.name}' saved successfully",
            configuration_id=configuration_id,
            test_results=test_results
        )
        
    except Exception as e:
        logger.error(f"Error configuring S3 storage: {e}")
        return S3ConfigurationResponse(
            success=False,
            message=f"Failed to configure S3 storage: {str(e)}"
        )


async def test_s3_connection(client, params: S3ConnectionTest) -> S3ConnectionTestResponse:
    """
    Test S3/MinIO connection and permissions.
    
    Args:
        client: Database client (not used for S3 operations)
        params: S3 connection test parameters
        
    Returns:
        S3ConnectionTestResponse with test results
    """
    
    start_time = datetime.utcnow()
    test_results = {
        "connection_test": False,
        "authentication_test": False,
        "bucket_access_test": False,
        "list_objects_test": False,
        "error_details": []
    }
    
    try:
        config = params.configuration
        s3_client = create_s3_client(config)
        
        # Test 1: Basic connection and authentication
        try:
            s3_client.list_buckets()
            test_results["connection_test"] = True
            test_results["authentication_test"] = True
        except NoCredentialsError:
            test_results["error_details"].append("Invalid credentials")
        except ClientError as e:
            if e.response['Error']['Code'] == 'InvalidAccessKeyId':
                test_results["error_details"].append("Invalid access key ID")
            elif e.response['Error']['Code'] == 'SignatureDoesNotMatch':
                test_results["error_details"].append("Invalid secret access key")
            else:
                test_results["error_details"].append(f"Authentication error: {e}")
        except Exception as e:
            test_results["error_details"].append(f"Connection error: {e}")
        
        # Test 2: Bucket access
        if test_results["authentication_test"]:
            try:
                s3_client.head_bucket(Bucket=config.bucket_name)
                test_results["bucket_access_test"] = True
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchBucket':
                    test_results["error_details"].append(f"Bucket '{config.bucket_name}' does not exist")
                elif e.response['Error']['Code'] == 'Forbidden':
                    test_results["error_details"].append(f"Access denied to bucket '{config.bucket_name}'")
                else:
                    test_results["error_details"].append(f"Bucket access error: {e}")
            except Exception as e:
                test_results["error_details"].append(f"Bucket access error: {e}")
        
        # Test 3: List objects permission
        if test_results["bucket_access_test"]:
            try:
                base_kwargs = {
                    "Bucket": config.bucket_name,
                    "MaxKeys": 1000,
                }
                normalized_prefix = None
                if config.path_prefix:
                    normalized_prefix = config.path_prefix.lstrip("/")
                    if normalized_prefix and not normalized_prefix.endswith("/"):
                        normalized_prefix = f"{normalized_prefix}/"
                    if normalized_prefix:
                        base_kwargs["Prefix"] = normalized_prefix

                total_count = 0
                continuation_token = None

                while True:
                    kwargs = dict(base_kwargs)
                    if continuation_token:
                        kwargs["ContinuationToken"] = continuation_token
                    response = s3_client.list_objects_v2(**kwargs)
                    total_count += response.get('KeyCount', 0)
                    if not response.get('IsTruncated'):
                        break
                    continuation_token = response.get('NextContinuationToken')

                test_results["list_objects_test"] = True
                test_results["object_count"] = total_count
                test_results["path_prefix"] = normalized_prefix or ''
            except ClientError as e:
                test_results["error_details"].append(f"List objects error: {e}")
            except Exception as e:
                test_results["error_details"].append(f"List objects error: {e}")
        
        # Calculate response time
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Determine overall success
        success = all([
            test_results["connection_test"],
            test_results["authentication_test"],
            test_results["bucket_access_test"]
        ])
        
        message = "All tests passed" if success else "Some tests failed"
        if test_results["error_details"]:
            message += f": {'; '.join(test_results['error_details'])}"
        
        return S3ConnectionTestResponse(
            success=success,
            message=message,
            test_results=test_results,
            response_time_ms=response_time
        )
        
    except Exception as e:
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.error(f"Error testing S3 connection: {e}")
        
        return S3ConnectionTestResponse(
            success=False,
            message=f"Connection test failed: {str(e)}",
            test_results=test_results,
            response_time_ms=response_time
        )


async def list_s3_buckets(client, params: S3BucketListQuery) -> S3BucketListResponse:
    """
    List S3/MinIO buckets.
    
    Args:
        client: Database client for retrieving configuration
        params: Bucket list query parameters
        
    Returns:
        S3BucketListResponse with bucket information
    """
    
    try:
        # In a real implementation, retrieve configuration from database
        # For now, use mock configuration
        mock_config = S3Configuration(
            name=params.configuration_name or "default",
            endpoint_url="http://localhost:9500",
            access_key_id="minioadmin",
            secret_access_key="minioadmin",
            bucket_name="abi-data"
        )
        
        s3_client = create_s3_client(mock_config)
        
        # List buckets
        response = s3_client.list_buckets()
        
        buckets = []
        for bucket in response.get('Buckets', []):
            bucket_info = S3BucketInfo(
                name=bucket['Name'],
                creation_date=bucket.get('CreationDate'),
                region=None  # Would need separate call to get region
            )
            
            # Get additional bucket information
            try:
                # Get object count and size (simplified)
                objects_response = s3_client.list_objects_v2(
                    Bucket=bucket['Name'],
                    MaxKeys=1000
                )
                
                bucket_info.object_count = objects_response.get('KeyCount', 0)
                
                # Calculate total size (would be more efficient with inventory)
                total_size = 0
                if 'Contents' in objects_response:
                    total_size = sum(obj.get('Size', 0) for obj in objects_response['Contents'])
                
                bucket_info.total_size_bytes = total_size
                
            except Exception as e:
                logger.warning(f"Failed to get bucket details for {bucket['Name']}: {e}")
            
            buckets.append(bucket_info)
        
        return S3BucketListResponse(
            buckets=buckets,
            total_count=len(buckets),
            configuration_used=mock_config.name
        )
        
    except Exception as e:
        logger.error(f"Error listing S3 buckets: {e}")
        return S3BucketListResponse(
            buckets=[],
            total_count=0,
            configuration_used=params.configuration_name or "default"
        )


async def list_s3_objects(client, params: S3ObjectListQuery) -> S3ObjectListResponse:
    """
    List objects in S3/MinIO bucket.
    
    Args:
        client: Database client for retrieving configuration
        params: Object list query parameters
        
    Returns:
        S3ObjectListResponse with object information
    """
    
    try:
        # In a real implementation, retrieve configuration from database
        mock_config = S3Configuration(
            name=params.configuration_name,
            endpoint_url="http://localhost:9500",
            access_key_id="minioadmin",
            secret_access_key="minioadmin",
            bucket_name=params.bucket_name or "abi-data"
        )
        
        s3_client = create_s3_client(mock_config)
        
        # List objects
        list_params = {
            'Bucket': mock_config.bucket_name,
            'MaxKeys': params.max_keys
        }
        
        if params.prefix:
            list_params['Prefix'] = params.prefix
        
        response = s3_client.list_objects_v2(**list_params)
        
        objects = []
        for obj in response.get('Contents', []):
            object_info = S3ObjectInfo(
                key=obj['Key'],
                size=obj['Size'],
                last_modified=obj['LastModified'].replace(tzinfo=None),
                etag=obj['ETag'].strip('"'),
                storage_class=obj.get('StorageClass')
            )
            objects.append(object_info)
        
        return S3ObjectListResponse(
            objects=objects,
            total_count=len(objects),
            bucket_name=mock_config.bucket_name,
            prefix_used=params.prefix
        )
        
    except Exception as e:
        logger.error(f"Error listing S3 objects: {e}")
        return S3ObjectListResponse(
            objects=[],
            total_count=0,
            bucket_name=params.bucket_name or "unknown",
            prefix_used=params.prefix
        )
