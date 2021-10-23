import time
from logging import INFO
from unittest.mock import patch

import pytest
from lxml.html import HtmlElement
from mylogs import log_setup
from news import mysites
from news.news import News
from requests.exceptions import ConnectionError
from requests_mock.mocker import Mocker

log_setup()


@pytest.fixture
def news_class():
    with patch.multiple("news.news.News", __abstractmethods__=set()):
        return News()


@pytest.fixture
def stolica_onego_class():

    return mysites.StolicaOnego()


@pytest.fixture
def yle_class():
    return mysites.Yle()


def test_news_filtering(news_class: News, caplog: pytest.LogCaptureFixture):

    text = ("Коронавирус наступает!", "Начались поиски пропавшей девушки", "Summer vocations are close! Get ready")
    filters = ("ready", "Корона", "пропавшей")

    for t in text:
        result = news_class.filter_out(filters, t)

        assert result is True

        with caplog.at_level(INFO):
            assert caplog.records[-1].message == f"Filtered: {t}"


def test_stolica_onego_start_time(stolica_onego_class: mysites.StolicaOnego):

    excpected = time.localtime().tm_hour

    actual = stolica_onego_class.time.tm_hour

    assert excpected == actual


def test_yle_start_time(yle_class: mysites.Yle):

    excpected = time.localtime().tm_hour

    actual = yle_class.time.tm_hour

    assert excpected == actual
