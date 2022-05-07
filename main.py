import re
from threading import Event
import time
from os import environ
import ast
import sys
from types import SimpleNamespace
from deepl import Translator
import urllib.error


from loguru import logger
import yaml
import feedparser
import requests

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


if not (TELEGRAM_TOKEN := environ.get("TOKEN")):

    print("TELEGRAM_TOKEN is not specified!")
    exit(1)

if not (CHAT_ID := environ.get("CHAT_ID", "")):

    print("CHAT_ID is not specified!")
    exit(1)

if not (DEEPL_TOKEN := environ.get("DEEPL_TOKEN", "")):

    print("DEEPL_TOKEN is not specified!")
    exit(1)


BG_BRIGHT_YELLOW = "\u001b[33;1m\u001b[7m"
COLOR_RESET = "\u001b[0m"
FG_BRIGHT_YELLOW = "\u001b[33;1m"

DEBUG = environ.get("DEBUG", False) == "True"
LOGGING_LEVEL = "DEBUG" if DEBUG else environ.get("LOGGING_LEVEL", "INFO")

CONFIG_FILE = environ.get("CONFIG_FILE", "config.yml")
HEADERS = ast.literal_eval(
    environ.get(
        "HEADERS",
        '{"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"}',
    )
)

CHAR_TO_ESCAPE: dict[int, str] = {
    i: "\\" + chr(i)
    for i in bytes(
        "".join(
            (
                "_",
                "*",
                "[",
                "]",
                "(",
                ")",
                "~",
                "`",
                ">",
                "#",
                "+",
                "-",
                "–",
                "=",
                "|",
                "{",
                "}",
                ".",
                "!",
            )
        ).encode("utf8")
    )
}
TELEGRAM_LINK = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
EXIT = Event()
TRANSLATOR = Translator(DEEPL_TOKEN)


def print_message(site_name: str, url: str, text: str) -> None:

    logger.debug(
        f"\n\t{site_name=}  \
                   \n\t{url=}        \
                   \n\t{text=}"
    )


def send_mes(text: str) -> None:

    params: dict[str, str | int] = {}
    params["chat_id"] = CHAT_ID
    params["parse_mode"] = "MarkdownV2"
    params["disable_web_page_preview"] = True
    params["disable_notification"] = False
    params["text"] = text
    logger.debug(params)

    response = requests.post(TELEGRAM_LINK, params=params).json()

    if not response["ok"]:

        logger.error("TELEGRAM ERROR: " + str(response))
        logger.error(text)


def make_request(url: str, url_desc: str) -> list[dict] | list:

    feed: dict = feedparser.parse(url, agent=HEADERS["user-agent"])

    match (feed.get("bozo_exception"), feed["entries"]):

        case feedparser.CharacterEncodingOverride() | None | urllib.error.URLError(gaierror(-3, "Temporary failure in name resolution")), [*articles] if articles:  # type: ignore # NOTE: urlerror might not work

            if feed["status"] != 200:

                feed["entries"].clear()
                logger.warning(f"{url_desc}: {feed}")

            return articles

        case _, [*articles] if articles:  # type: ignore

            feed["entries"].clear()
            logger.warning(f"{url_desc}: {feed}")

            return articles

        case _:

            feed["entries"].clear()
            logger.error(f"{url_desc}: {feed}")
            return []


def remove_p_from_text(text: str) -> str:
    return re.sub(r"</?p>", "", text)


def parse_text(text: str, url_desc: str) -> str:

    match text, url_desc.split("_")[0]:

        case text, _ if len(text) < 3 or not text:
            return ""

        case text, "meduza":
            text = t if len(t := text.split("<p>")[3]) > 3 else ""

        case _:
            pass

    if len(text) < 2000:
        return text.translate(CHAR_TO_ESCAPE)

    return (text[:2000] + "...").translate(CHAR_TO_ESCAPE)


def parse_title(title: str, url_desc: str) -> str:
    match url_desc:

        case "novayagazeta_eu":
            return (
                remove_p_from_text(title)
                .replace("&nbsp;", "")
                .translate(CHAR_TO_ESCAPE)
            )

        case _:
            return title.translate(CHAR_TO_ESCAPE)


def parse(
    url_desc: str, url: str, previous_time: time.struct_time
) -> tuple[list[SimpleNamespace] | list, time.struct_time]:
    """returns SimpleNamespace(link, title, text), time"""

    if articles := make_request(url, url_desc):

        logger.success(url_desc)
        to_return: list[SimpleNamespace] = []

        for article in reversed(articles[: len(articles) // 3]):

            if (time := article["published_parsed"]) > previous_time:

                title = parse_title(article["title"], url_desc)
                link = (
                    article["link"].split("?")[0]
                    if url_desc.startswith("yle")
                    else article["link"]
                )
                text = parse_text(article["summary"], url_desc)
                to_return.append(SimpleNamespace(url=link, title=title, text=text))
                previous_time = time

        return to_return, previous_time

    logger.warning(url_desc)
    return articles, previous_time


def get_time_of_last_article(*, url: str, url_desc: str) -> time.struct_time | None:

    index: int = 2 if DEBUG else 0
    if articles := make_request(url, url_desc):

        p_time: time.struct_time = articles[index]["published_parsed"]

        logger.info(
            f"Starting time for {FG_BRIGHT_YELLOW}{url_desc}{COLOR_RESET} is {time.strftime('%m-%dT%H:%MZ', p_time)}"
        )
        return p_time

    EXIT.set()
    return None


def translate_text(text: str, from_lang: str, to_lang: str) -> str:

    return TRANSLATOR.translate_text(text, source_lang=from_lang, target_lang=to_lang).text  # type: ignore


def check_translator_usage() -> None:
    usage = TRANSLATOR.get_usage()

    if usage.character.limit is None or usage.character.count is None:

        logger.warning(
            f"Failed to count remaining characters for translation: {usage.character.limit=}, {usage.character.count}"
        )

        return

    ch_remaining = usage.character.limit - usage.character.count

    if (ch_remaining) < 5000:

        text = f"🔴WARNING: {ch_remaining} are left for traslation!"
        send_mes(text)

    return


def format_news(site_name: str, article: SimpleNamespace) -> str:
    return f"[{site_name}]({article.url}): *{article.title}*\n\n{article.text}"


def load_urls() -> tuple[SimpleNamespace, ...]:

    news_items: list[SimpleNamespace] = []

    with open(CONFIG_FILE, "r") as f:

        sites: dict[str, dict] = yaml.safe_load(f)["sites"]

    logger.debug(sites)

    for k in sites.copy().keys():

        if not sites[k]["active"]:
            del sites[k]

        else:
            del sites[k]["description"]

    for sitename, urls in sites.items():

        for url in urls["urls"]:

            if not (status := url.get("active", True)) and not status:

                continue

            time = get_time_of_last_article(url=url["url"], url_desc=url["name"])
            news_items.append(
                SimpleNamespace(
                    sitename=sitename,
                    url=url["url"],
                    url_desc=url["name"],
                    time=time,
                    translate=url.get("translate"),
                )
            )

    logger.debug(news_items)
    return tuple(news_items)


def main() -> None:

    logger.info("Start....")
    logger.info("Loading urls....")
    sites = load_urls()
    logger.success("Done!")
    logger.info("Starting main loop....")
    while not EXIT.is_set():
        try:
            for site in sites:
                new, time = parse(site.url_desc, site.url, site.time)
                if new:
                    for article in new:
                        if DEBUG:
                            print_message(
                                url=article.url,
                                site_name=site.sitename,
                                text=article.text,
                            )
                        else:
                            article.text = (
                                translate_text(
                                    article.text,
                                    site.translate["from"],
                                    site.translate["to"],
                                )
                                if site.translate
                                else article.text
                            )
                            article.title = (
                                translate_text(
                                    article.title,
                                    site.translate["from"],
                                    site.translate["to"],
                                )
                                if site.translate
                                else article.title
                            )
                            text = format_news(site.sitename, article)
                            send_mes(text)
                    site.time = time

        except Exception as e:
            logger.exception(e)

        EXIT.wait(60 * 10)
    logger.info("All done!")


def quit(signo, _frame):  # type: ignore
    logger.info("Interrupted by %d, shutting down" % signo)
    EXIT.set()


if __name__ == "__main__":

    import signal

    for sig in ("TERM", "HUP", "INT"):
        signal.signal(getattr(signal, "SIG" + sig), quit)

    logger.info(
        f"Logging level is set to {BG_BRIGHT_YELLOW}{LOGGING_LEVEL}{COLOR_RESET}"
    )
    logger.remove()
    logger.add(sys.stderr, level=LOGGING_LEVEL, backtrace=True, diagnose=True)
    logger.info(f"Debug is set to {BG_BRIGHT_YELLOW}{DEBUG}{COLOR_RESET}")
    logger.info(f"Config file is {BG_BRIGHT_YELLOW}{CONFIG_FILE}{COLOR_RESET}")

    main()
