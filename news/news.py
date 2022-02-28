from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from time import strftime, strptime, struct_time
from loguru import logger

import requests
from config import HEADERS
from lxml import html
from lxml.html import HtmlElement
import aiohttp

from . import news_typing as nt


class ParseException(Exception):
    pass


class News(ABC):
    """Base class for news parsing

    Abstract methods:

        - ``_parse(self, xml: HtmlElement, ulr: str) -> dict[str, str]``

    Abstract variables:
        - ``self.URLS: Iterable[]``
    """

    def __init__(self) -> None:
        self.logger = logger.bind(name="main")
        self.site_name: nt.sitename = self.__class__.__name__.lower()  # type: ignore
        self.parse_error_occurred = False
        self.URLS: tuple[str] | dict[str, struct_time] = ...

    def get_urls(self) -> dict[str, struct_time] | tuple[str]:

        return self.URLS

    @abstractmethod
    def parse(self, xml: HtmlElement, ulr: str) -> list[nt.news_item] | list:

        """
        Method which should contain parse logic.

        Args:
            xml (HtmlElement): object from ``get_xml()`` method which calls ``lxml.html.fromstring()`` function
            ulr (str): url of the website

        Returns:
            list of found new articles or empty list if nothing was found
        """
        pass

    async def get_new(self, url: str, session: aiohttp.ClientSession) -> list[nt.news_item] | list:
        """
        Entry method for this class which looks for new news and returns them.

        Args:
            url: url of the site
            session: main session

        Returns:
            list of found items or empty list

        """
        result = []
        async with session.get(url) as resp:
            xml: HtmlElement = html.fromstring(await resp.text())
            if xml is not None:
                result.extend(self.parse(xml, url))
        return result

    def get_xml(self, url: str) -> html.HtmlElement | None:

        """
        Makes request to the website, gets html string and converts it to the parsable object.

        Args:
            url: url of the website to request

        Returns:
            html.HtmlElement: returns object which can parse given html string
        """

        news = requests.get(url, headers=HEADERS)
        if news.status_code == 200:
            return html.fromstring(news.text)

        else:
            self.logger.warning(f"Page {url} requested with code: {news.status_code}")
            return None

    def filter_out(self, words_to_filter: tuple[str, ...], text: str) -> bool:
        """
        Indicates if string contains any word from filter list

        Args:
            words_to_filter (list[str]): list with words to filter
            text (str): text where to look for

        Returns:
            bool: True if any word was found in the text else False
        """
        result = any(word in text for word in words_to_filter)
        if result:
            self.logger.info(f"Filtered: {text}")
        return any(word in text for word in words_to_filter)


class NewsWithId(News):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def get_last_news_id(self) -> int:
        """
        Method used to dynamically update last article id on startup. Is called once from ``__int__`` method

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
        """
        super().__init__()

    def get_urls(self):
        return self.URLS.keys()

    def construct_dict_urls(self, urls: tuple[str, ...], timezone_offset: int = +3) -> dict[str, struct_time]:
        """
        Creates dictionary of site url and timetuple (time in a tuple format) for further updates
        Is used for self.URLS in `__init__()`
        """
        return {url: self.get_time(timezone_offset) for url in urls}

    def get_time(self, timezone_offset: int) -> struct_time:

        time = (datetime.now(timezone(timedelta(hours=timezone_offset)))).timetuple()
        self.logger.debug(f"{self.__class__.__name__} started time: {strftime('%Y-%m-%dT%H:%M:%SZ', time)}")

        return time

    def check_time_date(self, time_to_check: str, date_time_format: str, current_time: struct_time) -> struct_time | None:
        """
        checks if given datetime of article is bigger than previous one. if yes returns new `struct_time` else `none`

        Args:
            time_to_check (str): datetime of article
            date_time_format (str): format of time_to_check. must have correct syntax according to the default python time formatting
            current_time (struct_time): of last sent article from certain url. should be located in ``self.urls[url]``

        Returns:
            union[struct_time, none]: none if all articles from webpage are old else returns time of new article
        """

        date_time_struct: struct_time = strptime(time_to_check, date_time_format)
        if date_time_struct > current_time:
            return date_time_struct

        return None
