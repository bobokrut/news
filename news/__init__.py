import inspect as _inspect
import json as _json
import sys as _sys

import news.mysites as _sites

from .news import News as _News

with open("urls_conf.json", "r") as _f:
    _j_urls = _json.load(_f)

_base_classes = tuple(cls for _, cls in _inspect.getmembers(_sys.modules["news.news"], _inspect.isclass) if cls.__module__ == "news.news")

sites: tuple[_News, ...] = tuple(site(tuple(_j_urls[site.__name__]["urls"])) for cls in _base_classes for site in cls.__subclasses__() if site not in _base_classes)

del _j_urls
