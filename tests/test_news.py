import time
from logging import INFO, WARNING

import config
import pytest
from lxml import html
from mylogs import log_setup
from news import mysites
from news.news import News
from requests_mock.mocker import Mocker

config.DEBUG = True
log_setup()

# Fixtures


@pytest.fixture
def news_cls(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(News, "__abstractmethods__", set())
    return News()  # type: ignore


@pytest.fixture
def stolicaonego():
    cls = mysites.StolicaOnego()
    cls.URLS = {"https://stolicaonego.ru/news/society/": cls.time}
    return mysites.StolicaOnego()


@pytest.fixture
def yle():
    cls = mysites.Yle()
    cls.URLS = {"https://yle.fi/uutiset/osasto/novosti/": cls.time}
    return mysites.Yle()


# News


def test_news_filtering(news_cls: News, caplog: pytest.LogCaptureFixture):

    text = ("Коронавирус наступает!", "Начались поиски пропавшей девушки", "Summer vocations are close! Get ready")
    filters = ("ready", "Корона", "пропавшей")

    for t in text:
        result = news_cls.filter_out(filters, t)

        assert result is True

        with caplog.at_level(INFO):
            assert caplog.records[-1].message == f"Filtered: {t}"


# StolicaOnego


def test_stolicaonego_start_time(stolicaonego: mysites.StolicaOnego):

    excpected = time.localtime().tm_hour

    actual = stolicaonego.time.tm_hour

    assert excpected == actual


def test_stolicaonego_time_format(stolicaonego: mysites.StolicaOnego):

    expected = "04.10.2021, 16:26"

    t = time.strptime("4.10.2021 16:26", "%d.%m.%Y %H:%M")

    actual = time.strftime(stolicaonego.time_format, t)

    assert expected == actual


def test_stolicaonego_get_xml(stolicaonego: mysites.StolicaOnego, requests_mock: Mocker):

    url = "https://stolicaonego.ru/news/society/"

    with open("tests/files/stolicaonego.html", "r") as file:

        text = file.read()

    requests_mock.get(url, text=text, status_code=200)

    result = stolicaonego.get_xml(url)
    expected = html.fromstring(text)

    assert isinstance(result, html.HtmlElement)
    assert result.items() == expected.items()


def test_stolicaonego_get_xml_badcode(stolicaonego: mysites.StolicaOnego, requests_mock: Mocker, caplog: pytest.LogCaptureFixture):

    url = "https://stolicaonego.ru/news/society/"

    with open("tests/files/stolicaonego.html", "r") as file:

        requests_mock.get(url, text=file.read(), status_code=404)

    result = stolicaonego.get_xml(url)

    assert not isinstance(result, html.HtmlElement)

    with caplog.at_level(WARNING):
        assert caplog.records[-1].message == f"Page {url} requested with code: {404}"


def test_stolicaonego_parse(stolicaonego: mysites.StolicaOnego, requests_mock: Mocker):

    url = "https://stolicaonego.ru/news/society/"

    initial_time = time.strptime("24.10.2021 15:00", "%d.%m.%Y %H:%M")

    stolicaonego.URLS[url] = initial_time

    expected = {
        "https://stolicaonego.ru/news/glava-petrozavodska-s-pomoschju-petra-pervogo-zagadal-administratsii-goroda-zagadku-foto/": "Глава Петрозаводска с помощью Петра Первого загадал администрации города загадку (ФОТО)",
        "https://stolicaonego.ru/news/poborovshie-ogon-politsejskie-v-karelii-poluchili-blagodarstvennye-pisma/": "Поборовшие огонь полицейские в Карелии получили благодарственные письма",
    }

    with open("tests/files/stolicaonego.html", "r") as file:

        requests_mock.get(url, text=file.read(), status_code=200)

    xml = stolicaonego.get_xml(url)
    result = stolicaonego._parse(xml, url)

    assert expected == result


# Yle


def test_yle_start_time(yle: mysites.Yle):

    excpected = time.localtime().tm_hour

    actual = yle.time.tm_hour

    assert excpected == actual
