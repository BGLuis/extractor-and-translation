import pkgutil
import importlib

__all__ = []

for _, module_name, _ in pkgutil.iter_modules(__path__):
    __all__.append(module_name)
    importlib.import_module(f"{__name__}.{module_name}")
