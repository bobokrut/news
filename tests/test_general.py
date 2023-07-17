def test_all_env_var_are_correct():
    from os import environ

    from dotenv import load_dotenv

    load_dotenv()

    assert environ.get("TOKEN") is not None
    assert environ.get("CHAT_ID") is not None
    assert environ.get("DEEPL_TOKEN") is not None
    assert environ.get("OPENAI_API_KEY") is not None


def test_tag_remover():
    from main import Text

    assert Text("<p>Hello <b>World</b></p>") == "Hello World"

    assert (
        Text("<p>Hello <b>World</b> <a href='https://google.com'>Google</a></p>")
        == "Hello World [Google](https://google.com)"
    )

    assert (
        Text("<p>Hello <b>World</b> <a href='https://google.com'>Google</a></p>")
        == "Hello World [Google](https://google.com)"
    )

    assert (
        Text(
            "<p>Hello <b>World</b> <a href='https://google.com'>Google</a> <i>Italic</i></p>"
        )
        == "Hello World [Google](https://google.com) Italic"
    )

    assert (
        Text(
            "<p>Hello <b>World</b> <a href='https://google.com'>Google</a> <i>Italic</i> <code>Code</code></p>"
        )
        == "Hello World [Google](https://google.com) Italic Code"
    )


def test_get_openai_usage():
    from main import get_openai_usage

    usage_1, usage_2 = get_openai_usage()

    assert usage_1 is not None
    assert isinstance(usage_1, float)

    assert usage_2 is not None
    assert isinstance(usage_2, float)


def test_general():
    from unittest.mock import patch

    from main import Text, format_news, load_urls, parse, send_mes

    with patch.object(Text, "summarize", side_effect=lambda x: x):
        sites = load_urls()

        for site in sites:
            new, time = parse(site.url_desc, site.url, site.time)

            assert new is not None
            assert time is not None
            assert len(new) == 2

            for article in new:
                text = format_news(site.sitename, article)
                assert send_mes(text) is True


def test_validate_markdownV2_formatting():
    from main import Text, send_mes

    text = """
    <p>This is an example message with <strong class="bold">bold</strong>, <em class="italic">italic</em>,
        <u class="underline">underline</u>, <s class="strikethrough">strikethrough</s>, <span class="spoiler">spoiler</span>,
        <code class="inline-code">inline fixed-width code</code>, and <pre class="pre-code">pre-formatted fixed-width code block</pre>.</p>
    <p>Here is a link: <a href="http://www.example.com/">Inline URL</a></p>
    """
    assert send_mes(Text(text)) is True
