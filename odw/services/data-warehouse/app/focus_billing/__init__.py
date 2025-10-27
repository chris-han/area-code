"""
Compatibility shim for the relocated FOCUS billing implementation.

Re-exports everything from ``bia_admin.bia_backend.workflows.focus_billing`` so
existing imports under ``app.focus_billing`` continue to function.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path


def _ensure_repo_on_path() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    repo_str = str(repo_root)
    if repo_str not in sys.path:
        sys.path.insert(0, repo_str)


_ensure_repo_on_path()

_TARGET_MODULE = "bia_admin.bia_backend.workflows.focus_billing"
_module = importlib.import_module(_TARGET_MODULE)

__all__ = getattr(_module, "__all__", [])

globals().update(
    {
        name: getattr(_module, name)
        for name in dir(_module)
        if not name.startswith("_")
    }
)

__path__ = getattr(_module, "__path__", [])


def __getattr__(name: str):
    return getattr(_module, name)
