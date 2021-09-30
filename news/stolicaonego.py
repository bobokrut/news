import time as tm
from urllib.parse import urljoin

from lxml.html import HtmlElement

from news.news import News


class StolicaOnego(News):

    def __init__(self) -> None:
        super().__init__(+3)

        self._URLS = {
            "https://stolicaonego.ru/news/society/": self.time,
            "https://stolicaonego.ru/news/crime/": self.time,
            "https://stolicaonego.ru/news/incident/": self.time,
            "https://stolicaonego.ru/news/personal/": self.time
        }

        self.FILTER: list[str] = ['коронавирус']

    @property
    def hashtag(self):
        return "#ptz"

    def _check_time_date(self, date_time: str, url) -> bool:

        date_time_struct: tm.struct_time = tm.strptime(date_time, "%d.%m.%Y, %H:%M")

        if date_time_struct > self._URLS[url]:
            self._URLS[url] = date_time_struct
            return True

        return False

    def _parse(self, xml, url):

        new = {}
        elements: list[HtmlElement] = xml.xpath("//div[@class='content_news' and position() < 6]/div[@class='content_news_list_text']")

        for article in reversed(elements):

            news_url = article.xpath("./div[@class='content_news_list_text_title']/a[1]")[0].get("href")
            text = article.xpath("./div[@class='content_news_list_text_title']/a[1]/text()")[0]
            time = article.xpath("./div[@class='content_news_list_text_date']/text()")[0]

            if self.filter_out(filter=self.FILTER, text=text):
                continue

            if self._check_time_date(time, url):
                new[urljoin(url, news_url)] = text

        return new

    def get_new(self):

        for u in self._URLS:
            xml = self.get_xml(u)
            yield self._parse(xml, u)
