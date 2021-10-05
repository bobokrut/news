from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
import requests
from lxml import html

from loguru import logger
from config import HEADERS


class News(ABC):

    def __init__(self, td: int) -> None:
        super().__init__()
        self.time = (datetime.now(timezone(timedelta(hours=td))) - timedelta(minutes=30)).timetuple()
        logger.info(f'Started time: {self.time}')

    def get_xml(self, url):

        news = requests.get(url, headers=HEADERS)
        logger.info(f"Page {url} requested with code: {news.status_code}")
        xml = html.fromstring(news.text)
        return xml

    def filter_out(self, filter: list[str], text: str) -> bool:
        return any(word in text for word in filter)

    @property
    @abstractmethod
    def hashtag(self):
        raise NotImplementedError

    @abstractmethod
    def get_new(self):
        raise NotImplementedError
