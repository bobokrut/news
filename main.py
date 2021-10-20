import logging
from threading import Event

from requests.exceptions import ConnectionError

from config import TOKEN
from mybot import Bot
from mybot.messages import SendMessage
from mylogs import log_setup
from news.dtp_ptz import DtpPtz
from news.stolicaonego import StolicaOnego
from news.yle import Yle

log_setup()

logger = logging.getLogger("main")

exit = Event()

sites: tuple[StolicaOnego, Yle, DtpPtz] = (StolicaOnego(), Yle(), DtpPtz())


def main():
    while not exit.is_set():
        try:
            for site in sites:
                for url, text in site.get_new().items():
                    with Bot(TOKEN) as bot:
                        bot.send_mes(SendMessage(text=f"{text}\n{url}", chat_id=387387555, disable_notification=True, disable_web_page_preview=True, parse_mode="MarkdownV2"))
        except (KeyboardInterrupt, ConnectionError):
            pass
        except Exception as e:
            logger.exception(e)

        exit.wait(60 * 5)

    logger.info("All done!")


def quit(signo, _frame):
    logger.info("Interrupted by %d, shutting down" % signo)
    exit.set()


if __name__ == "__main__":

    import signal

    for sig in ("TERM", "HUP", "INT"):
        signal.signal(getattr(signal, "SIG" + sig), quit)

    main()
