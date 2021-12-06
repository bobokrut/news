from typing import Iterator, Optional
from urllib.parse import urljoin

from lxml.html import HtmlElement

from . import news_typing as nt
from .news import NewsWithId, NewsWithTime


class DtpPtz(NewsWithId):
    def __init__(self, urls: tuple) -> None:

        super().__init__()
        self.URLS = urls
        self.last_id = self.get_last_news_id() - 3

    def get_last_news_id(self) -> int:

        xml = self.get_xml(self.URLS[0])
        url: str = xml.xpath("/html/body/main/div[2]/div/div[1]/ul/li[position()=2]/h2/a/@href")[0]
        id = int(url.split("/")[-1])
        self.logger.debug(f"{id=}")

        return id

    async def parse(self, xml: HtmlElement, u) -> Optional[Iterator[nt.news_item]]:
        result = []
        for acc in reversed(xml.xpath("/html/body/main/div[2]/div/div[1]/ul/li[position()<=8]/h2/a")):

            url = acc.xpath("./@href")[0]
            text = acc.xpath("./text()")[0]
            id = int(url.split("/")[2])

            if id > self.last_id:
                self.last_id = id
                result.append((self.sitename, urljoin(u, url), text))
        return result


class StolicaOnego(NewsWithTime):
    def __init__(self, urls: tuple) -> None:
        super().__init__()

        self.URLS = self.construct_dict_urls(urls, 0)

        self.FILTER: tuple[str, ...] = ("коронавирус", "пропал", "пропавший", "пропавшая", "Коронавирус", "Ковид", "ковид", "COVID")
        self.time_format = "%d.%m.%Y, %H:%M"

    async def parse(self, xml: HtmlElement, url) -> Optional[Iterator[nt.news_item]]:
        result = []
        elements: list[HtmlElement] = xml.xpath("/html/body/div[5]/div/div[1]/div[2]/div/div[position() < 7]/div[2]")

        for article in reversed(elements):
            try:

                news_url = article.xpath("./div[1]/a[1]/@href")[0]
                text1 = article.xpath("./div[1]/a[1]/text()")[0]
                text2 = article.xpath("./div[2]/text()")[0]
                text = ". ".join((text1, text2))
                time = article.xpath("./div[3]/text()")[0]
            except Exception:
                continue

            if time := self.check_time_date(time, self.time_format, self.URLS[url]):
                self.URLS[url] = time
                if not self.filter_out(filter=self.FILTER, text=text):
                    result.append((self.sitename, urljoin(url, news_url), text))
        return result


class Yle(NewsWithTime):
    def __init__(self, urls: tuple) -> None:

        super().__init__()

        self.URLS = self.construct_dict_urls(urls, 0)

        self.time_format = "%Y-%m-%dT%H:%M:%S%z"

    async def parse(self, xml: HtmlElement, url) -> Optional[Iterator[nt.news_item]]:
        result = []
        elements: list[HtmlElement] = xml.xpath("/html/body/div[@id='container']/div[@id='oikea_palsta']/section/article[position() < 4]")

        for article in elements:

            news_url: str = article.xpath("./h1/a[1]/@href")[0]
            text: str = article.xpath("./h1/a/text()")[0][1:-1]  # cutting off \n at the begging and at the end
            time = article.xpath("./time/@datetime")[0]

            if time := self.check_time_date(time, self.time_format, self.URLS[url]):

                self.URLS[url] = time
                result.append((self.sitename, urljoin(url, news_url), text))
        return result
