from urllib.parse import urljoin

from .news import News


class DtpPtz(News):

    def __init__(self) -> None:
        super().__init__(+3)

        self._URLS = ('https://dtpptz.ru/', )
        self._last_id = 12635
        self._xml = None

    @property
    def hashtag(self):
        return "#ptz"

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

            self.get_xml(u)

            yield self._parse(u)
