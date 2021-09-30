from threading import Event
from traceback import print_exc
from typing import Tuple

from loguru import logger

from config import INFO, TOKEN
from mybot import Bot
from mybot.messages import SendMessage
from news.dtp_ptz import DtpPtz
from news.stolicaonego import StolicaOnego
from news.yle import Yle
from requests.exceptions import ConnectionError

logger.remove()
logger.add("logs/log_{time:YYYY-MM-DD}.log", rotation='1 week', compression='zip', diagnose=True, level=INFO)

exit = Event()

news: Tuple[StolicaOnego, Yle, DtpPtz] = (StolicaOnego(), Yle(), DtpPtz())


def main():
    while not exit.is_set():
        try:
            for n in news:
                for site in n.get_new():
                    if site:
                        logger.info(f'Found {len(site)} articles')
                        logger.debug(site)
                        for url, text in site.items():
                            with Bot(TOKEN) as bot:
                                bot.send_mes(
                                    SendMessage(
                                        text=f'{n.hashtag}\n{text}\n{url}',
                                        chat_id=387387555,
                                        disable_notification=True,
                                        disable_web_page_preview=True,
                                        parse_mode='MarkdownV2'
                                    )
                                )
                    else:
                        logger.info('Nothing new...')
        except KeyboardInterrupt:
            pass
        except ConnectionError:
            pass
        except NotImplementedError as e:
            print_exc(e)
            exit.set()
        except Exception as e:
            logger.exception(e)

        exit.wait(60 * 5)

    logger.info("All done!")
    # perform any cleanup here


def quit(signo, _frame):
    logger.info("Interrupted by %d, shutting down" % signo)
    exit.set()


if __name__ == '__main__':

    import signal
    for sig in ('TERM', 'HUP', 'INT'):
        signal.signal(getattr(signal, 'SIG' + sig), quit)

    main()
