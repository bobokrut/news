from threading import Event
import time
from os import environ
import ast

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

if not (CHAT_ID := environ.get("CHAT_ID")):

    print("CHAT_ID is not specified!")
    exit(1)

DEBUG = (environ.get("DEBUG", False) == 'True')
LOGGING_LEVEL = "DEBUG" if DEBUG else environ.get("LOGGING_LEVEL", "INFO")
CONFIG_FILE = environ.get("CONFIG_FILE", "config.yml")
HEADERS = ast.literal_eval(environ.get("HEADERS", '{"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"}'))

CHAR_TO_ESCAPE: dict[int, str] = {i: "\\" + chr(i) for i in bytes("".join(('_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!')).encode("utf8"))}
TELEGRAM_LINK = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
EXIT = Event()

logger.level(LOGGING_LEVEL)


def print_message(site_name: str, url: str, text: str) -> None:

    logger.debug(f"\n\t{site_name=}\n\t{url=}\n\t{text=}")


def send_mes(site_name: str, url: str, text: str) -> None:
    
    params: dict[str, str | int] = {}
    params["chat_id"] = CHAT_ID
    params["parse_mode"] = "MarkdownV2"
    params["disable_web_page_preview"] = True
    params["disable_notification"] = True

    text = text.translate(CHAR_TO_ESCAPE)
    params["text"] = f"[{site_name}]({url}): {text}"
    logger.debug(params)

    response = requests.post(TELEGRAM_LINK, params=params).json()

    if not response["ok"]:
        logger.exception("TELEGRAM ERROR: " + str(response))


def parse(site_name: str, url: str, previous_time: time.struct_time) -> tuple[list[tuple[str, str, str]], time.struct_time | None]:
    # returns (site_name, url, text), time
    to_return = []
    feed = feedparser.parse(url, agent=HEADERS["user-agent"])
    articles = feed['entries']

    for article in reversed(articles):
        if (time := article['published_parsed']) > previous_time:
            title = article['title']
            link = article['link'].split('?')[0] if site_name == 'yle' else article['link']
            text = article['summary'].split('<p>')[3] if site_name == "meduza" else article['summary']
            to_return.append((site_name, link, f"{title}\n\n{text}"))
            previous_time = time

    return to_return, previous_time 


def get_time_of_last_article(url: str) -> time.struct_time:

        feed = feedparser.parse(url, agent=HEADERS["user-agent"])
        return feed['entries'][0]["published_parsed"]


def load_urls() -> dict:

    with open (CONFIG_FILE, "r") as f:

        sites: dict[str, dict] = yaml.safe_load(f)["sites"]

    for k in sites.copy().keys():

        if not sites[k]["active"]:
            del sites[k]

    for site in sites.values():

        for i in range(len(site["urls"])):

            site["urls"][i]["time"] = get_time_of_last_article(site["urls"][i]["url"])

    return sites


def main():

    logger.info("START....")
    sites = load_urls()
    while not EXIT.is_set():
        try:
            for site_name, site_data in sites.items():
                for d_url in site_data["urls"]:
                    new, time = parse(site_name, d_url["url"], d_url["time"])
                    if new:
                        for article in new:
                            site, url, text = article
                            if DEBUG:
                                print_message(url=url, site_name=site_name, text=text)
                            else:
                                send_mes(url=url, site_name=site, text=text)
                        d_url["time"] = time

        except Exception as e:
            logger.exception(e)

        EXIT.wait(60 * 10)
    logger.info("All done!")


def quit(signo, _frame):
    logger.info("Interrupted by %d, shutting down" % signo)
    EXIT.set()


if __name__ == "__main__":

    import signal

    for sig in ("TERM", "HUP", "INT"):
        signal.signal(getattr(signal, "SIG" + sig), quit)

    main()

