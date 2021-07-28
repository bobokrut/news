import time as tm
from urllib.parse import urljoin

import requests
from config import HEADERS
from loguru import logger
from lxml import html
from lxml.html import HtmlElement


from news.news import News


class Yle(News):

    def __init__(self) -> None:
        super().__init__(+3)

        self.URL = {
            "https://yle.fi/uutiset/osasto/news/": self.time
        }

    @property
    def hashtag(self):
        return "#finland"

    def get_new(self):

        for u in self.URL:
            xml = self._get_xml(u)
            yield self._parse(xml, u)

    def _get_xml(self, url):

        news = requests.get(url, headers=HEADERS)
        logger.info(f"Page {url} requested with code: {news.status_code}")
        return html.fromstring(news.content)

    def _check_time_date(self, date_time: str, url) -> bool:
        date_time_struct = tm.strptime(date_time, '%Y-%m-%dT%H:%M:%S%z')
        if date_time_struct > self.URL[url]:
            self.URL[url] = date_time_struct
            return True

        return False

    def _parse(self, xml, url):
        new = {}
        elements: list[HtmlElement] = xml.xpath("/html/body/div[@id='container']/div[@id='oikea_palsta']/section/article[position() < 4]")
        logger.debug(f"Found {len(elements)} articles")
        for article in elements:
            news_url: str = article.xpath("./h1/a[1]")[0].get('href')
            text: str = article.xpath("./h1/a/text()")[0].replace("\n", '')
            time = article.xpath("./time/@datetime")[0]

            logger.debug(f"Time: {time}")
            logger.debug(f"Url: {news_url}")
            logger.debug(f"Text: {text[:10]}")

            if self._check_time_date(time, url):
                logger.debug("New article to the dict 'new' added!")
                new[urljoin(url, news_url)] = text

        return new
