from urllib.parse import urljoin

from loguru import logger

from .news import News


class DtpPtz(News):

    def __init__(self) -> None:
        super().__init__(+3)

        self._URLS = ('https://dtpptz.ru/', )
        self._last_id = self._get_last_news_id()

    def _get_last_news_id(self):

        xml = self.get_xml(self._URLS[0])
        url: str = xml.xpath("//li[contains(@id, 'acc-') and position() = 2]/h2[1]/a[1]/@href")[0]
        id = int(url.split('/')[-1])
        logger.debug(f'{id=}')
        return id

    @property
    def hashtag(self):
        return "#ptz"

    def _parse(self, xml, u):

        new = {}

        for acc in reversed(xml.xpath("//li[contains(@id, 'acc-') and position() < 20]/h2[1]/a[1]")):

            url = acc.xpath("./@href")[0]
            text = acc.xpath("./text()")[0]
            id = int(url.split('/')[2])

            if id > self._last_id:
                new[urljoin(u, url)] = text
                self._last_id = id

        return new

    def get_new(self):

        new = {}

        for u in self._URLS:

            xml = self.get_xml(u)

            new.update(self._parse(xml, u))

        return new
