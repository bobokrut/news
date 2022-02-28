from urllib.parse import urljoin

from lxml.html import HtmlElement

from .news import NewsWithId, NewsWithTime, ParseException


class DtpPtz(NewsWithId):

    def __init__(self, urls: tuple) -> None:

        super().__init__()

        self.URLS = urls
        self.last_id = self.get_last_news_id()

    def get_last_news_id(self):

        xml: HtmlElement = super().get_xml(self.URLS[0])  # type: ignore
        url: str = xml.xpath("/html/body/main/div[2]/div/div[1]/ul/li[position()=2]/h2/a/@href")[0]
        id = int(url.split("/")[-1])
        self.logger.debug(f"{id=}")

        return id

    def parse(self, xml: HtmlElement, u):

        result = []

        elements = xml.xpath("/html/body/main/div[2]/div/div[1]/ul/li[position()<=8]/h2/a")

        if not elements and not self.parse_error_occurred:
            self.parse_error_occurred = True
            raise ParseException("Parsing exception in DtpPtz")

        for acc in reversed(elements):

            url = acc.xpath("./@href")[0]
            text = acc.xpath("./text()")[0]
            id = int(url.split("/")[2])

            if id > self.last_id:
                self.last_id = id
                result.append((self.site_name, urljoin(u, url), text))

        return result


class StolicaOnego(NewsWithTime):

    def __init__(self, urls: tuple) -> None:

        super().__init__()

        self.URLS = self.construct_dict_urls(urls)
        self.FILTER: tuple[str, ...] = ("коронавирус", "пропал", "пропавший", "пропавшая", "Коронавирус", "Ковид", "ковид", "COVID")
        self.time_format = "%d.%m.%Y, %H:%M"

    def parse(self, xml: HtmlElement, url):

        result = []
        elements: list[HtmlElement] = xml.xpath("/html/body/div[5]/div/div[1]/div[2]/div/div[position() < 7]/div[2]")

        if not elements and not self.parse_error_occurred:
            self.parse_error_occurred = True
            raise ParseException("Parsing exception in StolicaOnego")

        for article in reversed(elements):

            try:
                news_url = article.xpath("./div[1]/a[1]/@href")[0]
                text1 = article.xpath("./div[1]/a[1]/text()")[0]
                text2 = article.xpath("./div[2]/text()")[0]
                text = ". ".join((text1, text2))
                time = article.xpath("./div[3]/text()")[0]

                if time := self.check_time_date(time, self.time_format, self.URLS[url]):
                    self.URLS[url] = time

                    if not super().filter_out(words_to_filter=self.FILTER, text=text):
                        result.append((self.site_name, urljoin(url, news_url), text))

            except Exception:
                if not self.parse_error_occurred:
                    self.parse_error_occurred = True
                    raise ParseException("Parsing exception in StolicaOnego")

        return result


class Yle(NewsWithTime):

    def __init__(self, urls: tuple) -> None:

        super().__init__()

        self.URLS = self.construct_dict_urls(urls, timezone_offset=+2)
        self.time_format = "%Y-%m-%dT%H:%M:%S%z"

    def parse(self, xml: HtmlElement, url):

        result = []
        elements: list[HtmlElement] = xml.get_element_by_id("yle__contentAnchor").xpath("./div/main/div/div[2]/ol/li[position() < 6]/div/div[1]")

        if not elements and not self.parse_error_occurred:
            self.parse_error_occurred = True
            raise ParseException("Parsing exception in Yle")

        for article in reversed(elements):

            try:

                news_url: str = article.xpath("./h3/a/@href")[0]
                text: str = article.xpath("./h3[1]/a[1]/text()")[0]
                time = article.xpath("./div[1]/time[1]/@datetime")[0]

                if time := self.check_time_date(time, self.time_format, self.URLS[url]):
                    self.URLS[url] = time
                    result.append((self.site_name, urljoin(url, news_url), text))

            except Exception:

                if not self.parse_error_occurred:
                    self.parse_error_occurred = True
                    raise ParseException("Parsing exception in StolicaOnego")

        return result

    # def check_time_date(self, time_to_check: str, date_time_format: str, current_time: struct_time) -> struct_time | None:
    # """yle time patch, hope temporary"""

    # date_time_struct = (datetime.strptime(time_to_check, date_time_format) - timedelta(hours=1)).timetuple()
    # if date_time_struct > current_time:
    # return date_time_struct

    # return None
