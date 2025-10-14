import hashlib
import time
import xxhash
from typing import Optional
from clickhouse_connect import get_client
from clickhouse_connect.driver.client import Client
import logging
import sys
import psutil

CLICKHOUSE_HOST = "ck.mightytech.cn"
CLICKHOUSE_PORT = "8443"
CLICKHOUSE_USER = "finops"
CLICKHOUSE_PASS = "cU2f947&9T{6d"
CLICKHOUSE_DB = "dbo"

# Configure logging
def setup_logging() -> logging.Logger:
    """Configure logging for the module"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s | %(levelname)-8s | %(name)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('azure_ea_pipeline.log')
        ]
    )
    logger = logging.getLogger(__name__)
    
    # Log system information
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Total memory: {psutil.virtual_memory().total / (1024 * 1024 * 1024):.2f} GB")
    logger.info(f"Available memory: {psutil.virtual_memory().available / (1024 * 1024 * 1024):.2f} GB")
    
    return logger

def get_clickhouse_client(max_retries: int = 3, retry_delay: int = 5) -> Client:
    """Establishes a connection to the ClickHouse database with retry logic."""
    logger = setup_logging()
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            client = get_client(
                host=CLICKHOUSE_HOST,
                port=CLICKHOUSE_PORT,
                username=CLICKHOUSE_USER,
                password=CLICKHOUSE_PASS,
                database=CLICKHOUSE_DB,
                secure=True,
                compress='lz4',
                settings={'max_memory_usage': 0} # Added max_memory_usage setting
            )
            
            # Test connection with a simple query
            client.command("SELECT 1")
            logger.info("Successfully connected to ClickHouse.")
            return client
        except Exception as e:
            last_error = e
            logger.warning(f"ClickHouse connection attempt {attempt}/{max_retries} failed: {str(e)}")
            if attempt < max_retries:
                time.sleep(retry_delay * attempt)  # Exponential backoff
                
    logger.error(f"Failed to connect to ClickHouse after {max_retries} attempts")
    raise ConnectionError(f"Could not establish ClickHouse connection after {max_retries} attempts. Last error: {str(last_error)}")


def get_hash_str(item) -> Optional[str]:
    """
    Calculates the SHA-256 hash of a string item.

    Args:
        item: The string item to hash.

    Returns:
        The hexadecimal representation of the hash, or None if the item is None.
    """
    if item is None:
        return None
    # Use SHA-256 for hashing
    hash_object = hashlib.sha256(item.encode('utf-8'))
    hex_str = hash_object.hexdigest()
    return hex_str

def get_xxhash64_bytes(item) -> Optional[bytes]:
    """
    Calculates the xxhash64 hash of a string item and returns the raw bytes.

    Args:
        item: The string item to hash.

    Returns:
        The bytes representation of the hash, or None if the item is None.
    """
    if item is None:
        return None
    # Use xxhash64 for hashing and return bytes
    hash_object = xxhash.xxh64()
    hash_object.update(item.encode('utf-8'))
    return hash_object.digest()

def get_xxhash64_str(item) -> Optional[str]:
    """
    Calculates the xxh64 hash of a string item.

    Args:
        item: The string item to hash.

    Returns:
        The hexadecimal representation of the hash, or None if the item is None.
    """
    if item is None:
        return None
    # Use xxh64 for hashing
    hash_object = xxhash.xxh64(item.encode('utf-8'))
    hex_str = hash_object.hexdigest()
    return hex_str

def get_hash_bytes(item) -> Optional[bytes]:
    """
    Calculates the SHA-256 hash of a string item and returns the raw bytes.

    Args:
        item: The string item to hash.

    Returns:
        The bytes representation of the hash, or None if the item is None.
    """
    if item is None:
        return None
    # Use SHA-256 for hashing and return bytes
    hash_object = hashlib.sha256(item.encode('utf-8'))
    return hash_object.digest()

def get_xxhash64_uint64(item) -> Optional[int]:
    """
    Calculates the xxh64 hash of a string item and returns the integer representation (Uint64).

    Args:
        item: The string item to hash.

    Returns:
        The integer representation of the hash, or None if the item is None.
    """
    if item is None:
        return None
    # Use xxh64 for hashing and return integer
    hash_object = xxhash.xxh64(item.encode('utf-8'))
    return hash_object.intdigest()

# def get_hash_hexdigest(item) -> Optional[str]:
#     """
#     Calculates the SHA-256 hash of a string item and returns the hexdigest.

#     Args:
#         item: The string item to hash.

#     Returns:
#         The hexdigest of the hash, or None if the item is None.
#     """
#     if item is None:
#         return None
#     hash_object = hashlib.sha256(item.encode('utf-8'))
#     return hash_object.hexdigest()
