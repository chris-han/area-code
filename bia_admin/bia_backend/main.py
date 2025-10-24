"""Entry point for the Billing Intelligence API (BIA) FastAPI application."""

from bia_backend.app import create_abi_fastapi_app

app = create_abi_fastapi_app()

__all__ = ["app"]
