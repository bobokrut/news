import inspect as _inspect
import sys as _sys

import news.mysites as _sites

from .news import News as _News

_base_classes = tuple(cls for _, cls in _inspect.getmembers(_sys.modules["news.news"], _inspect.isclass) if cls.__module__ == "news.news")
sites: tuple[_News, ...] = tuple(site() for cls in _base_classes for site in cls.__subclasses__() if site not in _base_classes)
