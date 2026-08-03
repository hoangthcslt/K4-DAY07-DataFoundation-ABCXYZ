import importlib
import sys

_PACKAGE = "src.2A202601436_NguyenDinhHoang"
_m = importlib.import_module(_PACKAGE)

# Export all attributes from the student package to top-level src
for attr in dir(_m):
    if not attr.startswith("__"):
        globals()[attr] = getattr(_m, attr)

# Also register src.<submodule> (e.g. src.chunking) so that direct submodule
# imports elsewhere in the repo (ingest.py, main.py) keep working even though
# the real files only live under the student package above.
for _name in ("agent", "chunking", "embeddings", "models", "store"):
    sys.modules[f"src.{_name}"] = importlib.import_module(f"{_PACKAGE}.{_name}")
