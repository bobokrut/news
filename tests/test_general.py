from os import environ
from unittest.mock import patch

from dotenv import load_dotenv

from main import Text, format_news, get_openai_usage, load_urls, parse, send_mes


def test_all_env_var_are_correct():
    load_dotenv()

    assert environ.get("TOKEN") is not None
    assert environ.get("CHAT_ID") is not None
    assert environ.get("DEEPL_TOKEN") is not None
    assert environ.get("OPENAI_API_KEY") is not None


def test_tag_remover():
    """Shoudl remove all html tags except <b>, <strong>, <i>, <em>, <u>, <ins>, <s>, <strike>, <del>, <a> but keep the text. Any atts except href should be removed."""

    text = """
    <p>This is an example message with <strong class="bold">bold</strong>, <em class="italic">italic</em>,
        <u class="underline">underline</u>, <s class="strikethrough">strikethrough</s>, <span class="spoiler">spoiler</span>,
        <code class="inline-code">inline fixed-width code</code>, and <pre class="pre-code">pre-formatted fixed-width code block</pre>.</p>
    <p>Here is a link: <a href="http://www.example.com/">Inline URL</a></p>
    """

    text = Text(text)

    assert (
        text.text
        == """This is an example message with <strong>bold</strong>, <em>italic</em>,
        <u>underline</u>, <s>strikethrough</s>, spoiler,
        inline fixed-width code, and pre-formatted fixed-width code block.
    Here is a link: <a href='http://www.example.com/'>Inline URL</a>"""
    )


def test_get_openai_usage():
    usage_1, usage_2 = get_openai_usage()

    assert usage_1 is not None
    assert isinstance(usage_1, float)

    assert usage_2 is not None
    assert isinstance(usage_2, float)


def test_general():
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


def test_validate_formatting():
    text = """
    <p>This is an example message with <strong class="bold">bold</strong>, <em class="italic">italic</em>,
        <u class="underline">underline</u>, <s class="strikethrough">strikethrough</s>, <span class="spoiler">spoiler</span>,
        <code class="inline-code">inline fixed-width code</code>, and <pre class="pre-code">pre-formatted fixed-width code block</pre>.</p>
    <p>Here is a link: <a href="http://www.example.com/">Inline URL</a></p>
    """
    assert send_mes(Text(text)) is True
