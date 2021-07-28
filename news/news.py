from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone

from loguru import logger


class News(ABC):

    def __init__(self, td: int) -> None:
        super().__init__()
        self.time = (datetime.now(timezone(timedelta(hours=td))) - timedelta(minutes=30)).timetuple()
        logger.info(f'Started time: {self.time}')

    @property
    @abstractmethod
    def hashtag(self):
        raise NotImplementedError

    @abstractmethod
    def get_new(self):
        raise NotImplementedError
