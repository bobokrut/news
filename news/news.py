from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from logging import getLogger as _getLogger
from time import strptime, struct_time
from typing import Union

import requests
from config import HEADERS
from lxml import html
from lxml.html import HtmlElement


class News(ABC):
    """Base class for news parsing

    Abstract methods:

        - ``_parse(self, xml: HtmlElement, ulr: str) -> dict[str, str]``
        - ``get_new(self) -> dict[str, str]``
    """

    def __init__(self) -> None:
        self.logger = _getLogger("main")

    @abstractmethod
    def get_new(self) -> dict[str, str]:
        """
        Entry method for this class which looks for new news and returns them.

        Returns:
            dict[str, str]: returns dict {url: text} with all new founded news or is empty if nothing was found
        """
        pass

    @abstractmethod
    def _parse(self, xml: HtmlElement, ulr: str) -> dict[str, str]:
        """
        Method which should contain parse logic.

        Args:
            xml (HtmlElement): object from ``get_xml()`` method which calls ``lxml.html.fromstring()`` function
            ulr (str): url of the website

        Returns:
            dict[str, str]: returns dict {url: text} with all new founded news or is empty if nothing was found
        """
        pass

    def get_xml(self, url: str) -> html.HtmlElement:
        """
        Makes request to the website, gets html string and converts it to the parsible object.

        Args:
            url (str): url of the website to request

        Returns:
            html.HtmlElement: returts object which can parse given html string
        """

        news = requests.get(url, headers=HEADERS)
        self.logger.info(f"Page {url} requested with code: {news.status_code}")
        xml = html.fromstring(news.text)

        return xml

    def filter_out(self, filter: list[str], text: str) -> bool:
        """
        Endicates if string conains any word from filter list

        Args:
            filter (list[str]): list with words to filter
            text (str): text where to look for

        Returns:
            bool: True if any word was found in the text else False
        """

        return any(word in text for word in filter)


class NewsWithTime(News):
    """
    Extended News class which supports parsing articles with time stamp

    Abstract methods:

        - ``_parse(self, xml: HtmlElement, ulr: str) -> dict[str, str]``
        - ``get_new(self) -> dict[str, str]``
    """

    def __init__(self, td: int = +3) -> None:
        """
        Creates self.time with correct time_struct considering given timezone

        Args:
            td (int): timezone as `+3` or `-2`
        """
        super().__init__()
        self.time = (datetime.now(timezone(timedelta(hours=td)))).timetuple() if td else None
        self.logger.info(f'Started time: {self.time}')

    def _check_time_date(self, time_to_check: str, date_time_format: str, current_time: struct_time) -> Union[struct_time, None]:
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
