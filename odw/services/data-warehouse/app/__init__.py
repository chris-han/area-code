"""
Application package bootstrap.

Provides compatibility aliases for the legacy `app.focus_billing` package by
redirecting imports to the relocated implementation under
`bia_admin.bia_backend.workflows.focus_billing`.
"""

from __future__ import annotations

import importlib
import pkgutil
import sys
from pathlib import Path


def _ensure_repo_on_path() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    repo_str = str(repo_root)
    if repo_str not in sys.path:
        sys.path.insert(0, repo_str)


def _register_focus_billing_aliases() -> None:
    target_prefix = "bia_admin.bia_backend.workflows.focus_billing"
    alias_prefix = "app.focus_billing"

    try:
        _ensure_repo_on_path()
        target_root = importlib.import_module(target_prefix)
    except ModuleNotFoundError:
        return

    sys.modules.setdefault(alias_prefix, target_root)

    target_path = getattr(target_root, "__path__", None)
    if not target_path:
        return

    for module_info in pkgutil.walk_packages(target_path, target_prefix + "."):
        try:
            module = importlib.import_module(module_info.name)
        except ModuleNotFoundError:
            continue
        alias = alias_prefix + module_info.name[len(target_prefix) :]
        sys.modules[alias] = module


_register_focus_billing_aliases()
