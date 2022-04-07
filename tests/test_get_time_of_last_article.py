import main
import pytest
import time

@pytest.mark.parametrize("url,url_desc", [("https://feeds.yle.fi/uutiset/v1/recent.rss?publisherIds=YLE_NEWS", "yle_en"),
                                           ("https://feeds.yle.fi/uutiset/v1/recent.rss?publisherIds=YLE_NOVOSTI", "yle_rus"),
                                           ("https://meduza.io/rss/news", "meduza"),
                                           ("https://novayagazeta.ru/feed/rss", "novayagazeta_rus"),
                                           ("https://news.radio-t.com/rss", "radio-t")])
def test_get_time_of_last_article_is_not_none(url, url_desc):

    result = main.get_time_of_last_article(url=url, url_desc=url_desc)
    assert result is not None
    assert isinstance(result, time.struct_time)


