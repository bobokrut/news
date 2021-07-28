from urllib.parse import urljoin

import requests
from lxml import html
from .news import News
from config import HEADERS

from loguru import logger


class DtpPtz(News):

    def __init__(self) -> None:
        super().__init__(+3)

        self._URLS = ('https://dtpptz.ru/', )
        self._last_id = 12484
        self._xml = None

    @property
    def hashtag(self):
        return "#ptz"

    def _get_xml(self, u):

        dtp_ptz = requests.get(u, headers=HEADERS)
        logger.info(f"Page {u} requested with code: {dtp_ptz.status_code}")
        self._xml = html.fromstring(dtp_ptz.content)

    def _parse(self, u):

        new = {}
        for acc in reversed(self._xml.xpath("//li[contains(@id, 'acc-') and position() < 20]/h2[1]/a[1]")):
            url = acc.xpath("./@href")[0]
            text = acc.xpath("./text()")[0]
            id = int(url.split('/')[2])

            if id > self._last_id:
                new[urljoin(u, url)] = text
                self._last_id = id

        return new

    def get_new(self):

        for u in self._URLS:

            self._get_xml(u)

            yield self._parse(u)
