from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = ROOT / "ire"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if "ire" not in sys.modules and PACKAGE_ROOT.exists():
    spec = importlib.util.spec_from_file_location(
        "ire",
        PACKAGE_ROOT / "__init__.py",
        submodule_search_locations=[str(PACKAGE_ROOT)],
    )
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        sys.modules["ire"] = module
        spec.loader.exec_module(module)
