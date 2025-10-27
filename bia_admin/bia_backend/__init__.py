"""BIA Backend FastAPI application package."""

try:
    from .app import (  # type: ignore
        abi_app,
        abi_fastapi_app,
        bia_fastapi_app,
        create_abi_fastapi_app,
    )

    bia_app = abi_app  # Backwards compatibility for existing imports

    __all__ = [
        "bia_app",
        "abi_app",
        "abi_fastapi_app",
        "bia_fastapi_app",
        "create_abi_fastapi_app",
    ]
except ModuleNotFoundError:  # pragma: no cover - optional runtime dependency
    __all__ = []
