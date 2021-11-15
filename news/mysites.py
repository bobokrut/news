from typing import Iterator, Optional
from urllib.parse import urljoin

from lxml.html import HtmlElement

from . import news_typing as nt
from .news import NewsWithId, NewsWithTime


class DtpPtz(NewsWithId):
    def __init__(self, urls: tuple) -> None:

        super().__init__()
        self.URLS = urls
        self.last_id = self.get_last_news_id()

    def get_last_news_id(self) -> int:

        xml = self.get_xml(self.URLS[0])
        url: str = xml.xpath("/html/body/main/div[2]/div/div[1]/ul/li[position()=2]/h2/a/@href")[0]
        id = int(url.split("/")[-1])
        self.logger.debug(f"{id=}")

        return id

    def parse(self, xml: HtmlElement, u) -> Optional[Iterator[nt.news_item]]:

        for acc in reversed(xml.xpath("/html/body/main/div[2]/div/div[1]/ul/li[position()<=8]/h2/a")):

            url = acc.xpath("./@href")[0]
            text = acc.xpath("./text()")[0]
            id = int(url.split("/")[2])

            if id > self.last_id:
                self.last_id = id
                yield (urljoin(u, url), text)


class StolicaOnego(NewsWithTime):
    def __init__(self, urls: tuple) -> None:
        super().__init__()

        self.URLS = self.construct_dict_urls(urls)

        self.FILTER: tuple[str, ...] = ("коронавирус", "пропал", "пропавший", "пропавшая")
        self.time_format = "%d.%m.%Y, %H:%M"

    def parse(self, xml: HtmlElement, url) -> Optional[Iterator[nt.news_item]]:

        elements: list[HtmlElement] = xml.xpath("/html/body/div[5]/div/div[1]/div[2]/div/div[position() < 7]/div[2]")

        for article in reversed(elements):
            try:

                news_url = article.xpath("./div[1]/a[1]/@href")[0]
                text = article.xpath("./div[2]/text()")[0]
                time = article.xpath("./div[3]/text()")[0]
            except Exception:
                continue

            if self.filter_out(filter=self.FILTER, text=text):
                continue

            if time := self.check_time_date(time, self.time_format, self.URLS[url]):
                self.URLS[url] = time
                yield (self.sitename, urljoin(url, news_url), text)


class Yle(NewsWithTime):
    def __init__(self, urls: tuple) -> None:

        super().__init__()

        self.URLS = self.construct_dict_urls(urls)

        self.time_format = "%Y-%m-%dT%H:%M:%S%z"

    def parse(self, xml: HtmlElement, url) -> Optional[Iterator[nt.news_item]]:

        elements: list[HtmlElement] = xml.xpath("/html/body/div[@id='container']/div[@id='oikea_palsta']/section/article[position() < 4]")

        for article in elements:

            news_url: str = article.xpath("./h1/a[1]/@href")[0]
            text: str = article.xpath("./h1/a/text()")[0][1:-1]  # cutting off \n at the begging and at the end
            time = article.xpath("./time/@datetime")[0]

            if time := self.check_time_date(time, self.time_format, self.URLS[url]):

                self.URLS[url] = time
                yield (self.sitename, urljoin(url, news_url), text)
