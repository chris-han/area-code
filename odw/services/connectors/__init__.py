from __future__ import annotations

from pathlib import Path

package_root = Path(__file__).resolve().parent
src_path = package_root / "src"

if src_path.exists() and str(src_path) not in __path__:  # type: ignore[name-defined]
    # Ensure package submodules can be imported directly when using the source tree.
    __path__.append(str(src_path))  # type: ignore[name-defined]
