from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from time import struct_time, strptime
from typing import Union
import requests
from lxml import html

from loguru import logger
from config import HEADERS


class News(ABC):

    @property
    @abstractmethod
    def hashtag(self):
        pass

    @abstractmethod
    def get_new(self):
        pass

    @abstractmethod
    def _parse(self, xml, ulr: str):
        pass

    def get_xml(self, url) -> html.HtmlElement:

        news = requests.get(url, headers=HEADERS)
        logger.info(f"Page {url} requested with code: {news.status_code}")
        xml = html.fromstring(news.text)

        return xml

    def filter_out(self, filter: list[str], text: str) -> bool:

        return any(word in text for word in filter)


class NewsWithTime(News):

    def __init__(self, td: Union[int, None]) -> None:
        super().__init__()
        self.time = (datetime.now(timezone(timedelta(hours=td)))).timetuple() if td else None
        logger.info(f'Started time: {self.time}')

    def _check_time_date(self, time_to_check: str, date_time_format: str, current_time: struct_time) -> Union[struct_time, None]:

        date_time_struct: struct_time = strptime(time_to_check, date_time_format)

        if date_time_struct > current_time:
            return date_time_struct

        return None
