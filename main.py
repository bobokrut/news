from threading import Event

from loguru import logger
from requests.exceptions import ConnectionError

from config import INFO, TOKEN
from mybot import Bot
from mybot.messages import SendMessage
from news.dtp_ptz import DtpPtz
from news.stolicaonego import StolicaOnego
from news.yle import Yle

logger.remove()
logger.add("logs/log_{time:YYYY-MM-DD}.log", rotation='1 week', compression='zip', diagnose=True, level=INFO)

exit = Event()

sites: tuple[StolicaOnego, Yle, DtpPtz] = (StolicaOnego(), Yle(), DtpPtz())


def main():
    while not exit.is_set():
        try:
            news = [n for n in map(lambda x: x.get_new(), sites) if n]
            if news:
                for site in news:
                    logger.info(f'Found {len(site)} articles')
                    logger.debug(site)
                    for url, text in site.items():
                        with Bot(TOKEN) as bot:
                            bot.send_mes(
                                SendMessage(
                                    text=f'{text}\n{url}',
                                    chat_id=387387555,
                                    disable_notification=True,
                                    disable_web_page_preview=True,
                                    parse_mode='MarkdownV2'
                                )
                            )
            else:
                logger.info("Nothing new...")
        except (KeyboardInterrupt, ConnectionError):
            pass
        except Exception as e:
            logger.exception(e)

        exit.wait(60 * 5)

    logger.info("All done!")


def quit(signo, _frame):
    logger.info("Interrupted by %d, shutting down" % signo)
    exit.set()


if __name__ == '__main__':

    import signal
    for sig in ('TERM', 'HUP', 'INT'):
        signal.signal(getattr(signal, 'SIG' + sig), quit)

    main()
