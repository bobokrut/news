import main

def test_url_load_not_empty():

    result = main.load_urls()
    assert result != {}

def test_yle_load_urls_only_active():

    result = main.load_urls()
    assert bool(s["active"] for s in result.values()) == True
    assert bool(s.get("time") for s in result.values()) == True
