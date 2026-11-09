"""Load the models package without importing Home Assistant."""

import importlib.util
import sys
from pathlib import Path

_PATH = (
    Path(__file__).parents[1]
    / "custom_components"
    / "egge_cloud_lorawan"
    / "models"
)
_spec = importlib.util.spec_from_file_location(
    "egge_models", _PATH / "__init__.py", submodule_search_locations=[str(_PATH)]
)
assert _spec and _spec.loader
_module = importlib.util.module_from_spec(_spec)
sys.modules["egge_models"] = _module
_spec.loader.exec_module(_module)
