import asyncio
from threading import Event

from requests.exceptions import ConnectionError
import aiohttp
from loguru import logger as _logger

import mylogs
from config import TOKEN
from mybot import Bot
from mybot.messages import SendMessage
from news import sites
from news.news import ParseException


exit = Event()
logger = _logger.bind(name="main")


async def main():

    logger.info("START....")
    session = aiohttp.ClientSession(raise_for_status=True)

    while not exit.is_set():

        try:
            results = await asyncio.gather(*[site.get_new(url, session) for site in sites for url in site.get_urls()])

            for result in results:
                for r in result:
                    site, url, text = r
                    with Bot(TOKEN) as bot:
                        bot.send_mes(SendMessage(url=url, url_description=site, text=text, chat_id=387387555, disable_notification=True, disable_web_page_preview=True, parse_mode="MarkdownV2"))

        except (KeyboardInterrupt, ConnectionError):
            pass

        except ParseException as e:

            with Bot(TOKEN) as bot:
                bot.send_mes(SendMessage(text=f"❗Error❗:\n{str(e)}", chat_id=387387555, disable_notification=True, disable_web_page_preview=True, parse_mode="MarkdownV2"))
                logger.error(e)

        except Exception as e:
            logger.exception(e)

        exit.wait(60 * 60)
    await session.close()
    logger.info("All done!")


def quit(signo, _frame):
    logger.info("Interrupted by %d, shutting down" % signo)
    exit.set()


if __name__ == "__main__":

    import signal

    for sig in ("TERM", "HUP", "INT"):
        signal.signal(getattr(signal, "SIG" + sig), quit)

    asyncio.run(main())
