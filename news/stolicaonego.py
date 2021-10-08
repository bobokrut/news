from urllib.parse import urljoin

from lxml.html import HtmlElement

from news.news import NewsWithTime


class StolicaOnego(NewsWithTime):

    def __init__(self) -> None:
        super().__init__(+3)

        self.URLS = {
            "https://stolicaonego.ru/news/society/": self.time,
            "https://stolicaonego.ru/news/crime/": self.time,
            "https://stolicaonego.ru/news/incident/": self.time,
            "https://stolicaonego.ru/news/personal/": self.time
        }

        self.FILTER: list[str] = ['коронавирус', 'пропал', 'пропавший', 'пропавшая']
        self.time_format = "%d.%m.%Y, %H:%M"

    @property
    def hashtag(self):
        return "#ptz"

    def get_new(self):
        new = {}
        for u in self.URLS:
            xml = self.get_xml(u)
            new.update(self._parse(xml, u))
        return new

    def _parse(self, xml: HtmlElement, url):

        new = {}
        elements: list[HtmlElement] = xml.xpath("//div[@class='content_news' and position() < 6]/div[@class='content_news_list_text']")

        for article in reversed(elements):

            news_url = article.xpath("./div[@class='content_news_list_text_title']/a[1]/@href")[0]
            text = article.xpath("./div[@class='content_news_list_text_title']/a[1]/text()")[0]
            time = article.xpath("./div[@class='content_news_list_text_date']/text()")[0]

            if self.filter_out(filter=self.FILTER, text=text):
                continue

            if time := self._check_time_date(time, self.time_format, self.URLS[url]):
                self.URLS[url] = time
                new[urljoin(url, news_url)] = text

        return new
