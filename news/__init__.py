import importlib as _importlib
import inspect as _inspect
import os as _os
import sys as _sys

from .news import News as _News

_modules = [file.split(".")[0] for file in _os.listdir("news") if "." in file and file.split(".")[1] == "py" and file != "__init__.py"]

for module in _modules:
    _importlib.import_module(f"news.{module}")

_base_classes = tuple(cls for _, cls in _inspect.getmembers(_sys.modules["news.news"], _inspect.isclass) if cls.__module__ == "news.news")
sites: tuple[_News, ...] = tuple(site() for cls in _base_classes for site in cls.__subclasses__() if site not in _base_classes)
__all__ = ["sites"]
