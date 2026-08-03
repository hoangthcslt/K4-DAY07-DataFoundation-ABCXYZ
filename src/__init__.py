import importlib

_m = importlib.import_module("src.2A202601436_NguyenDinhHoang")

# Export all attributes from the student package to top-level src
for attr in dir(_m):
    if not attr.startswith("__"):
        globals()[attr] = getattr(_m, attr)
