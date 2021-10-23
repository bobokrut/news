from urllib.parse import urljoin

from lxml.html import HtmlElement

from news.news import NewsWithTime


class StolicaOnego(NewsWithTime):
    def __init__(self) -> None:
        super().__init__()

        self.URLS = {
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
                self.logger.info(f"Filtered: {url}")
                continue

            if time := self._check_time_date(time, self.time_format, self.URLS[url]):
                self.URLS[url] = time
                new[urljoin(url, news_url)] = text

        return new
