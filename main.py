import calendar
import datetime
import re
import sys
import time
import urllib.error
from html.parser import HTMLParser
from os import environ
from threading import Event, Thread
from types import SimpleNamespace

import feedparser
import openai
import requests
import yaml
from deepl import Translator
from loguru import logger

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


if not (TELEGRAM_TOKEN := environ.get("TOKEN")):
    logger.error("TELEGRAM_TOKEN is not specified!")
    exit(1)

if not (CHAT_ID := environ.get("CHAT_ID", "")):
    logger.error("CHAT_ID is not specified!")
    exit(1)

if not (DEEPL_TOKEN := environ.get("DEEPL_TOKEN", "")):
    logger.error("DEEPL_TOKEN is not specified!")
    exit(1)

if not (OPENAI_API_KEY := environ.get("OPENAI_API_KEY", "")):
    logger.error("OPENAI_API_KEY is not specified!")
    exit(1)

openai.api_key = OPENAI_API_KEY

BG_BRIGHT_YELLOW = "\u001b[33;1m\u001b[7m"
COLOR_RESET = "\u001b[0m"
FG_BRIGHT_YELLOW = "\u001b[33;1m"

DEBUG = environ.get("DEBUG", "False") == "True"
LOGGING_LEVEL = "DEBUG" if DEBUG else environ.get("LOGGING_LEVEL", "INFO")

CONFIG_FILE = environ.get("CONFIG_FILE", "config.yml")

HEADERS = {
    "user-agent": environ.get(
        "USER_AGENT",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    )
}


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
if DEBUG:
    token = environ.get("DEBUG_TOKEN")
    TELEGRAM_LINK = f"https://api.telegram.org/bot{token}/sendMessage"
else:
    TELEGRAM_LINK = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

exit = Event()
translator = Translator(DEEPL_TOKEN)


class Text(HTMLParser):
    def __init__(self, text) -> None:
        super().__init__()

        self.html_text: list[str] = []
        self.allowed_tags = [
            "b",
            "strong",
            "i",
            "em",
            "u",
            "ins",
            "s",
            "strike",
            "del",
            "a",
        ]
        self.text: str = ""
        self.url: str | None = None
        self.long_text: bool = False

        if "\xa0" in text:
            text = text.replace("\xa0", " ")

        if self.check_if_html(text):
            self.feed(text)
            text = "".join(self.html_text).strip()
        else:
            text = text.strip()

        if len(t := self.remove_html_tags(text)) > 1000:
            text = self.summarize(t)

        self.text = text

        logger.debug(f"{self.text=}")

    def __eq__(self, o: object) -> bool:
        if isinstance(o, Text):
            return self.text == o.text

        if isinstance(o, str):
            return self.text == o

        return False

    def __str__(self) -> str:
        return self.text

    def check_if_html(self, text: str) -> bool:
        return bool(re.search(r"<[^>]*>", text))

    def handle_data(self, data: str) -> None:
        self.html_text.append(data)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag not in self.allowed_tags:
            return
        logger.debug(f"{tag=}")

        if tag == "a":
            url = dict(attrs).get("href")
            self.html_text.append(f"<a href='{url}'>")
            return

        self.html_text.append(f"<{tag.strip()}>")

    def handle_endtag(self, tag: str) -> None:
        if tag not in self.allowed_tags:
            return

        self.html_text.append(f"</{tag.strip()}>")

    def summarize(self, text: str) -> str:
        if len(text) > 2000:
            text = text[:2000]

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "user",
                    "content": "Can you provide a comprehensive and short summary of the given news article? The summary should cover all the key points and main ideas presented in the original article, while also condensing the information into a concise and easy-to-understand format. Please ensure that the summary includes relevant details and examples that support the main ideas, while avoiding any unnecessary information or repetition. The length of the summary should be appropriate for the length and complexity of the original text, providing a clear and accurate overview without omitting any important information. This article is in russian and provide the summary in russian",
                },
                {
                    "role": "user",
                    "content": text,
                },
            ],
            temperature=1,
            max_tokens=800,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )
        return response["choices"][0]["message"]["content"] + "\n\nAI summary"

    def remove_html_tags(self, text: str) -> str:
        """Remove html tags from a string but keep the text"""
        return re.sub(r"<[^>]*>", "", text)


def print_message(site_name: str, url: str, text: str) -> None:
    logger.debug(
        f"\n\t{site_name=} \
          \n\t{url=}       \
          \n\t{text=}"
    )


def get_openai_usage() -> tuple[float, float]:
    today = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1)
    start_of_month = today.replace(day=calendar.monthrange(today.year, today.month)[0])
    end_of_month = today.replace(day=calendar.monthrange(today.year, today.month)[1])

    r = openai.api_requestor.APIRequestor()
    resp = r.request(
        "GET", f"/dashboard/billing/usage?start_date={today}&end_date={tomorrow}"
    )
    usage_today = resp[0].data["total_usage"] / 100
    usage_today = round(usage_today, 4)

    resp = r.request(
        "GET",
        f"/dashboard/billing/usage?start_date={start_of_month}&end_date={end_of_month}",
    )
    usage_this_month = resp[0].data["total_usage"] / 100
    usage_this_month = round(usage_this_month, 4)

    return usage_today, usage_this_month


def send_mes(text: Text | str) -> bool:
    params: dict[str, str | int] = {}
    params["chat_id"] = CHAT_ID
    params["parse_mode"] = "HTML"
    params["disable_web_page_preview"] = True
    params["disable_notification"] = False
    params["text"] = text
    logger.debug(params)

    response = requests.post(TELEGRAM_LINK, params=params).json()

    if not response["ok"]:
        logger.error("TELEGRAM ERROR: " + str(response))
        logger.error(text)
        return False

    return True


def format_news(site_name: str, article: SimpleNamespace) -> str:
    return f"<a href='{article.url}'>{site_name}</a>: <b>{article.title}</b>\n\n{article.text}"


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


def parse_text(text: str, url_desc: str) -> str | Text:
    match text, url_desc.split("_")[0]:
        case text, _ if not text or len(text) < 3:
            return ""

        case text, "meduza":
            text_return = Text(t if len(t := text.split("<p>")[3]) > 3 else "")

        case _:
            text_return = Text(text)

    return text_return


def parse_title(title: str) -> Text:
    return Text(title)


def parse(
    url_desc: str, url: str, previous_time: time.struct_time
) -> tuple[list[SimpleNamespace] | list, time.struct_time]:
    """returns SimpleNamespace(link, title, text), time"""

    if articles := make_request(url, url_desc):
        logger.success(url_desc)
        to_return: list[SimpleNamespace] = []

        for article in reversed(articles[: len(articles) // 3]):
            if (time := article["published_parsed"]) > previous_time:
                title = parse_title(article["title"])
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

    exit.set()
    return None


def translate_text(text: str, from_lang: str, to_lang: str) -> str:
    return translator.translate_text(text, source_lang=from_lang, target_lang=to_lang).text  # type: ignore


def check_translator_usage() -> None:
    usage = translator.get_usage()

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


def load_urls() -> tuple[SimpleNamespace, ...]:
    news_items: list[SimpleNamespace] = []

    with open(CONFIG_FILE, "r") as f:
        sites: dict[str, dict] = yaml.safe_load(f)

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

    while not exit.is_set():
        try:
            for site in sites:
                new, time = parse(site.url_desc, site.url, site.time)

                if new:
                    site.time = time

                    for article in new:
                        if site.translate:
                            article.text = translate_text(
                                article.text,
                                site.translate["from"],
                                site.translate["to"],
                            )

                            article.title = translate_text(
                                article.title,
                                site.translate["from"],
                                site.translate["to"],
                            )

                        text = format_news(site.sitename, article)
                        send_mes(text)

        except Exception as e:
            logger.exception(e)

        exit.wait(60 * 10)

    logger.info("All done!")


def quit(signo, _frame):  # type: ignore
    logger.info("Interrupted by %d, shutting down" % signo)
    exit.set()


def run_get_openai_usage() -> None:
    date = None
    while not exit.is_set():
        now = datetime.datetime.now().time()
        if (
            now.hour == 23
            and now.minute == 50
            and date != datetime.datetime.now().date()
        ):
            date = datetime.datetime.now().date()
            usage_today, usage_this_month = [
                str(usage).replace(".", "\\.") for usage in get_openai_usage()
            ]
            message = f"*Open AI Usage*\n_Today_: {usage_today}$\n_This month_: {usage_this_month}$"
            send_mes(message)
            exit.wait(50)


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

    main_thread = Thread(target=main)
    usage_thread = Thread(target=run_get_openai_usage)

    main_thread.start()
    usage_thread.start()

    main_thread.join()
    usage_thread.join()
