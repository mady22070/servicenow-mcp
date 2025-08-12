
import pkgutil, importlib, pathlib
__all__ = []
_pkg_path = pathlib.Path(__file__).parent
for mod in pkgutil.iter_modules([str(_pkg_path)]):
    name = mod.name
    if name.endswith("_pack"):
        try:
            m = importlib.import_module(f"{__name__}.{name}")
            globals()[name] = m
            __all__.append(name)
        except Exception:
            pass
