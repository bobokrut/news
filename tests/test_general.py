def test_all_env_var_are_correct():
    from os import environ

    from dotenv import load_dotenv

    load_dotenv()

    assert environ.get("TOKEN") is not None
    assert environ.get("CHAT_ID") is not None
    assert environ.get("DEEPL_TOKEN") is not None
    assert environ.get("OPENAI_API_KEY") is not None


def test_tag_remover():
    from main import TagsRemover

    tr = TagsRemover()

    tr.feed("<p>Hello <b>World</b></p>")
    assert tr.get_text() == "Hello World"

    tr.feed("<p>Hello <b>World</b> <a href='https://google.com'>Google</a></p>")
    assert tr.get_text() == "Hello World Google"

    tr.feed("<p>Hello <b>World</b> <a href='https://google.com'>Google</a></p>")
    assert tr.get_text() == "Hello World Google"

    tr.feed(
        "<p>Hello <b>World</b> <a href='https://google.com'>Google</a> <i>Italic</i></p>"
    )
    assert tr.get_text() == "Hello World Google Italic"

    tr.feed(
        "<p>Hello <b>World</b> <a href='https://google.com'>Google</a> <i>Italic</i> <code>Code</code></p>"
    )
    assert tr.get_text() == "Hello World Google Italic Code"

    tr.feed(
        "<p>Hello <b>World</b> <a href='https://google.com'>Google</a> <i>Italic</i> <code>Code</code> <code>Code</code></p>"
    )
    assert tr.get_text() == "Hello World Google Italic Code Code"

    tr.feed(
        "<p>Hello <b>World</b> <a href='https://google.com'>Google</a> <i>Italic</i> <code>Code</code> <code>Code</code> <code>Code</code></p>"
    )
    assert tr.get_text() == "Hello World Google Italic Code Code Code"

    tr.feed(
        "<p>Hello <b>World</b> <a href='https://google.com'>Google</a> <i>Italic</i> <code>Code</code> <code>Code</code> <code>Code</code> <code>Code</code></p>"
    )
    assert tr.get_text() == "Hello World Google Italic Code Code Code Code"

    tr.feed(
        "<p>Hello <b>World</b> <a href='https://google.com'>Google</a> <i>Italic</i> <code>Code</code> <code>Code</code> <code>Code</code> <code>Code</code> <code>Code</code></p>"
    )
    assert tr.get_text() == "Hello World Google Italic Code Code Code Code Code"


def test_get_openai_usage():
    from main import get_openai_usage

    usage_1, usage_2 = get_openai_usage()

    assert usage_1 is not None
    assert isinstance(usage_1, float)

    assert usage_2 is not None
    assert isinstance(usage_2, float)


def test_summarize():
    from unittest.mock import patch

    import main
    from main import load_urls, parse

    main.DEBUG = True

    with patch("main.summarize") as mock_summarize:
        mock_summarize.side_effect = lambda text: text

        sites = load_urls()

        for site in sites:
            new, time = parse(site.url_desc, site.url, site.time)

            assert new is not None
            assert time is not None
            assert len(new) == 2
