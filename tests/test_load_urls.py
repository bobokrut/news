import main
from time import struct_time


def test_url_load_not_empty():

    result = main.load_urls()
    assert result != {}


def test_yle_load_check_attrs_and_types():

    result = main.load_urls()[0]
    assert isinstance(result.sitename, str)
    assert isinstance(result.url, str)
    assert isinstance(result.url_desc, str)
    assert isinstance(result.time, struct_time)
