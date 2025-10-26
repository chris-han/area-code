"""
Dependency Injection for BIA FastAPI Application

Provides FastAPI dependency functions for shared resources like
ClickHouse, Temporal, and Redis clients. Imported by routers to avoid
circular import issues with app.py.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bia_backend.app import ABIApplication

# Global reference to the application instance (set by app.py)
_abi_app: "ABIApplication" = None  # type: ignore


def set_abi_app(app: "ABIApplication"):
    """Set the global ABI application instance (called by app.py during initialization)"""
    global _abi_app
    _abi_app = app


def get_clickhouse_client():
    """FastAPI dependency for ClickHouse client"""
    return _abi_app.get_clickhouse_client()


def get_temporal_client():
    """FastAPI dependency for Temporal client"""
    return _abi_app.get_temporal_client()


def get_redis_client():
    """FastAPI dependency for Redis client"""
    return _abi_app.get_redis_client()
