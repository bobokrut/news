from typing import Iterator, Tuple, Union

import requests

from . import messages as m
from .keyboard import Keyboard

try:
    from loguru import logger

except ModuleNotFoundError:

    import logging
    logger: logging.Logger = logging.getLogger(__name__)

    logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(name)s - %(message)s')
    ch.setFormatter(formatter)

    logger.addHandler(ch)


class BotException(Exception):

    pass


class BotTypeError(TypeError):
    pass


class Bot(Keyboard):

    def __init__(self, token: str, escape_chars: Union[list, str, set, None] = None):

        super().__init__()

        self._update_id: Union[int, None] = None
        self._message: Union[m.TextMessage, m.CallbackMessage, m.PollMessage] = None
        self._update: dict = None
        self._base_url: str = f"https://api.telegram.org/bot{token}/"
        self.escape_chars = self._escape_chars_setup(escape_chars) if escape_chars else None

    def _escape_chars_setup(self, escape_chars: Union[list, str, set]):
        if isinstance(escape_chars, (list, set)):

            return {i: '\\' + chr(i) for i in bytes(''.join(escape_chars).encode('utf8'))}
        else:

            return {i: '\\' + chr(i) for i in bytes(escape_chars.encode('utf8'))}

    def _parse_update(self) -> None:

        if 'message' in self._update['result'][-1].keys():

            self._update_id = self._update['result'][-1]['update_id']

            text: str = self._update['result'][-1]['message']['text']
            chat_id: int = self._update['result'][-1]['message']['chat']['id']
            message_id: int = self._update['result'][-1]['message']['message_id']
            username: str = self._update['result'][-1]['message']['from']['username']

            self._message = m.TextMessage(message_id, username, chat_id, text)

        elif 'callback_query' in self._update['result'][-1].keys():

            self._update_id = self._update['result'][-1]['update_id']
            chat_id: int = self._update['result'][-1]['callback_query']['message']['chat']['id']
            callback_data: str = self._update['result'][-1]['callback_query']['data']

            self._message = m.CallbackMessage(chat_id, callback_data)

        elif 'poll' in self._update['result'][-1].keys():

            self._update_id = self._update['result'][-1]['update_id']

            polls = [poll['text'] for poll in self._update['result'][-1]['poll']['options'] if
                     poll['voter_count'] > 0 and poll['text'] != 'Nothing']

            poll_id: str = self._update['result'][-1]['poll']['id']

            self._message = m.PollMessage(poll_id, polls)
        logger.debug(repr(self._message))

    def get_updates(self) -> Iterator[Union[m.TextMessage, m.PollMessage, m.CallbackMessage, None]]:

        url = self._base_url + "getUpdates"

        if self._update_id:

            data = {
                'offset': self._update_id + 1
            }

            self._update = requests.post(url, params=data).json()

        else:

            self._update = requests.post(url).json()
        if not self._update['ok']:

            logger.exception(BotException(self._update))

        if self._update['result']:

            self._parse_update()

            yield self._message
        else:
            yield None

    def send_mes(self, mess: m.SendMessage) -> None:

        mess.text = self.escape_char(mess.text)
        url: str = self._base_url + "sendMessage"
        params = mess.values()
        logger.debug(params)
        response = requests.post(url, params=params).json()

        if not response['ok']:
            logger.exception(BotException(response))

    def edit_mes(self, mess: m.EditMessageText) -> None:

        mess.text = self.escape_char(mess.text)
        url: str = self._base_url + "editMessageText"
        params = mess.values()
        logger.debug(params)
        response = requests.post(url, params).json()
        if not response['ok']:
            logger.exception(BotException(response))

    def delete_mes(self, mess: m.DeleteMessage) -> None:

        url: str = self._base_url + "deleteMessage"
        params = mess.values()
        logger.debug(params)
        response = requests.post(url, params=params).json()

        if not response['ok']:
            logger.exception(BotException(response))

    def send_poll(self, poll: m.SendPoll) -> Tuple[int, int]:
        url: str = self._base_url + "sendPoll"
        params = poll.values()
        logger.debug(params)
        response = requests.post(url, params=params).json()
        if not response['ok']:
            logger.exception(BotException(response))

        return response['result']['poll']['id'], response['result']['message_id']

    def escape_char(self, text: str) -> str:

        if self.escape_chars:

            return text.translate(self.escape_chars)
        return text

    def __exit__(self, type, value, traceback):
        # Exception handling here
        pass

    def __enter__(self):
        return self
