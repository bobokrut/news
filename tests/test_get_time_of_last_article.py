import main
import pytest
import time

@pytest.mark.parametrize("url,site_name", [("https://feeds.yle.fi/uutiset/v1/recent.rss?publisherIds=YLE_NEWS", "yle"),
                                           ("https://feeds.yle.fi/uutiset/v1/recent.rss?publisherIds=YLE_NOVOSTI", "yle"),
                                           ("https://meduza.io/rss/news", "meduza"),
                                           ("https://novayagazeta.ru/feed/rss", "novayagazeta"),
                                           ("https://news.radio-t.com/rss", "radiot")])
def test_get_time_of_last_article_is_not_none(url, site_name):

    result = main.get_time_of_last_article(url=url, site_name=site_name)
    assert result is not None
    assert isinstance(result, time.struct_time)


