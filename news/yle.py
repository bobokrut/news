from urllib.parse import urljoin

from lxml.html import HtmlElement

from news.news import NewsWithTime


class Yle(NewsWithTime):
    def __init__(self) -> None:
        super().__init__()

        self.URLS = {"https://yle.fi/uutiset/osasto/novosti/": self.time}
        self.time_format = "%Y-%m-%dT%H:%M:%S%z"

    def get_new(self) -> dict[str, str]:
        new = {}
        for u in self.URLS:
            xml = self.get_xml(u)
            new.update(self._parse(xml, u))
        return new

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
