from urllib.parse import urljoin

from lxml import html

from .news import News


class DtpPtz(News):
    def __init__(self) -> None:
        super().__init__()

        self._URLS = ("https://dtpptz.ru/",)
        self._last_id = self._get_last_news_id()

    def get_new(self):

        new = {}

        for u in self._URLS:

            xml = self.get_xml(u)

            new.update(self._parse(xml, u))

        return new

    def _get_last_news_id(self) -> int:
        """
        Method used to dynamicly update last article id on startup. Is called once from ``__int__`` method

        Returns:
            [int]: last article id
        """

        xml = self.get_xml(self._URLS[0])
        url: str = xml.xpath("/html/body/main/div[2]/div/div[1]/ul/li[position()=2]/h2/a/@href")[0]
        id = int(url.split("/")[-1])
        self.logger.debug(f"{id=}")

        return id

    def _parse(self, xml: html.HtmlElement, u):

        new = {}

        for acc in reversed(xml.xpath("/html/body/main/div[2]/div/div[1]/ul/li[position()<=8]/h2/a")):

            url = acc.xpath("./@href")[0]
            text = acc.xpath("./text()")[0]
            id = int(url.split("/")[2])

            if id > self._last_id:
                new[urljoin(u, url)] = text
                self._last_id = id

        return new
