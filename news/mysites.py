from time import struct_time
from urllib.parse import urljoin

from lxml.html import HtmlElement

from .news import News, NewsWithTime


class DtpPtz(News):
    def __init__(self) -> None:
        super().__init__()

        self.URLS: tuple[str, ...] = ("https://dtpptz.ru/",)
        self._last_id = self._get_last_news_id()

    def _get_last_news_id(self) -> int:
        """
        Method used to dynamicly update last article id on startup. Is called once from ``__int__`` method

        Returns:
            [int]: last article id
        """

        xml = self.get_xml(self.URLS[0])
        url: str = xml.xpath("/html/body/main/div[2]/div/div[1]/ul/li[position()=2]/h2/a/@href")[0]
        id = int(url.split("/")[-1])
        self.logger.debug(f"{id=}")

        return id

    def _parse(self, xml: HtmlElement, u):

        new = {}

        for acc in reversed(xml.xpath("/html/body/main/div[2]/div/div[1]/ul/li[position()<=8]/h2/a")):

            url = acc.xpath("./@href")[0]
            text = acc.xpath("./text()")[0]
            id = int(url.split("/")[2])

            if id > self._last_id:
                new[urljoin(u, url)] = text
                self._last_id = id

        return new


class StolicaOnego(NewsWithTime):
    def __init__(self) -> None:
        super().__init__()

        self.URLS: dict[str, struct_time] = {
            "https://stolicaonego.ru/news/society/": self.time,
            #  "https://stolicaonego.ru/news/crime/": self.time,
            "https://stolicaonego.ru/news/incident/": self.time,
            "https://stolicaonego.ru/news/personal/": self.time,
        }

        self.FILTER: tuple[str, ...] = ("коронавирус", "пропал", "пропавший", "пропавшая")
        self.time_format = "%d.%m.%Y, %H:%M"

    def _parse(self, xml: HtmlElement, url):

        new = {}
        elements: list[HtmlElement] = xml.xpath("/html/body/div[5]/div/div[1]/div[2]/div/div[position() < 7]/div[2]")

        for article in reversed(elements):
            try:

                news_url = article.xpath("./div[1]/a[1]/@href")[0]
                text = article.xpath("./div[1]/a[1]/text()")[0]
                time = article.xpath("./div[3]/text()")[0]
            except Exception:
                continue

            if self.filter_out(filter=self.FILTER, text=text):
                continue

            if time := self._check_time_date(time, self.time_format, self.URLS[url]):
                self.URLS[url] = time
                new[urljoin(url, news_url)] = text

        return new


class Yle(NewsWithTime):
    def __init__(self) -> None:
        super().__init__()

        self.URLS: dict[str, struct_time] = {"https://yle.fi/uutiset/osasto/novosti/": self.time}
        self.time_format = "%Y-%m-%dT%H:%M:%S%z"

    def _parse(self, xml: HtmlElement, url):

        new = {}
        elements: list[HtmlElement] = xml.xpath("/html/body/div[@id='container']/div[@id='oikea_palsta']/section/article[position() < 4]")

        for article in elements:

            news_url: str = article.xpath("./h1/a[1]/@href")[0]
            text: str = article.xpath("./h1/a/text()")[0][1:-1]  # cutting off \n at the begging and at the end
            time = article.xpath("./time/@datetime")[0]

            if time := self._check_time_date(time, self.time_format, self.URLS[url]):

                self.URLS[url] = time
                new[urljoin(url, news_url)] = text

        return new
