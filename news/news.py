from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from functools import wraps
from logging import getLogger as _getLogger
from time import strftime, strptime, struct_time
from typing import Iterator, Optional, Union

import requests
from config import HEADERS
from lxml import html
from lxml.html import HtmlElement

from . import news_typing as nt

# def _log_articles(fn):
#     @wraps(fn)
#     def wrapped(*args, **kwargs):

#         result: Generator[tuple[str, None, None]] = fn(*args, **kwargs)
#         if result:
#             args[0].logger.info(f"Found some article(s) on {args[0].__class__.__name__}")
#         else:
#             args[0].logger.info(f"Nothing was found on {args[0].__class__.__name__} ...")
#         return result

#     return wrapped


class News(ABC):
    """Base class for news parsing

    Abstract methods:

        - ``_parse(self, xml: HtmlElement, ulr: str) -> dict[str, str]``

    Abstract variables:
        - ``self.URLS: Iterable[]``
    """

    def __init__(self) -> None:
        self.logger = _getLogger("main")
        self.sitename: nt.sitename = self.__class__.__name__.lower()  # type: ignore

    @abstractmethod
    def parse(self, xml: HtmlElement, ulr: str) -> Optional[Iterator[nt.news_item]]:

        """
        Method which should contain parse logic.

        Args:
            xml (HtmlElement): object from ``get_xml()`` method which calls ``lxml.html.fromstring()`` function
            ulr (str): url of the website

        Returns:
            dict[url, article_text]: returns dict {url: text} with all new founded news or is empty if nothing was found
        """
        pass

    # @_log_articles
    def get_new(self) -> Optional[Iterator[nt.news_item]]:
        """
        Entry method for this class which looks for new news and returns them.

        Returns:
            dict[url, article_text]: returns dict {url: text} with all new founded news or is empty if nothing was found
        """
        for u in self.URLS:  # type: ignore
            xml: HtmlElement = self.get_xml(u)
            if xml is not None:
                yield from self.parse(xml, u)

    def get_xml(self, url: str) -> Optional[html.HtmlElement]:
        """
        Makes request to the website, gets html string and converts it to the parsible object.

        Args:
            url (str): url of the website to request

        Returns:
            html.HtmlElement: returts object which can parse given html string
        """

        news = requests.get(url, headers=HEADERS)
        if news.status_code == 200:
            return html.fromstring(news.text)

        else:
            self.logger.warning(f"Page {url} requested with code: {news.status_code}")
            return None

    def filter_out(self, filter: tuple[str, ...], text: str) -> bool:
        """
        Endicates if string conains any word from filter list

        Args:
            filter (list[str]): list with words to filter
            text (str): text where to look for

        Returns:
            bool: True if any word was found in the text else False
        """
        result = any(word in text for word in filter)
        if result:
            self.logger.info(f"Filtered: {text}")
        return any(word in text for word in filter)


class NewsWithId(News):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def get_last_news_id(self) -> int:
        """
        Method used to dynamicly update last article id on startup. Is called once from ``__int__`` method

        Returns:
            [int]: last article id
        """
        pass


class NewsWithTime(News):
    """
    Extended News class which supports parsing articles with time stamp

    Abstract methods:

        - ``_parse(self, xml: HtmlElement, ulr: str) -> dict[str, str]``

    Abstract variables:
        - ``self.URLS: dict[str, time.struct_time]`` = {'http://...', `self.time`}

            `self.time` is from NewsWithTime.__init__()
    """

    def __init__(self) -> None:
        """
        Creates self.time with correct time_struct considering given timezone

        Args:
            td (int): timezone as `+3` or `-2` (default: +3)
        """
        super().__init__()

    def construct_dict_urls(self, urls: tuple[str, ...], tz: int = +3):

        return {url: self.get_time(tz) for url in urls}

    def get_time(self, tz: int) -> struct_time:

        time = (datetime.now(timezone(timedelta(hours=tz)))).timetuple()
        self.logger.debug(f"{self.__class__.__name__} started time: {strftime('%Y-%m-%dT%H:%M:%SZ', time)}")

        return time

    def check_time_date(self, time_to_check: str, date_time_format: str, current_time: struct_time) -> Union[struct_time, None]:
        """
        Checks if given datetime of article is bigger than previous one. If yes returns new `struct_time` else `None`

        Args:
            time_to_check (str): datetime of article
            date_time_format (str): format of time_to_check. must have correct syntax according to the default python time formatting
            current_time (struct_time): of last sent article from certain url. Should be located in ``self.URLS[url]``

        Returns:
            Union[struct_time, None]: None if all articles from webpage are old else returns time of new article
        """

        date_time_struct: struct_time = strptime(time_to_check, date_time_format)

        if date_time_struct > current_time:
            return date_time_struct

        return None
