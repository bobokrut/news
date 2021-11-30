from logging import getLogger
from typing import Iterator, Tuple, Union

import requests

from . import messages as m
from .keyboard import Keyboard

logger = getLogger("bot")


class BotException(Exception):

    pass


class BotTypeError(TypeError):
    pass


class Bot(Keyboard):
    def __init__(self, token: str):

        super().__init__()

        self._update_id: int = 0
        self._message: Union[m.TextMessage, m.CallbackMessage, m.PollMessage] = None
        self._update: dict = {}
        self._base_url: str = f"https://api.telegram.org/bot{token}/"
        self.escape_chars_MarkdownV2 = self._escape_chars_setup(("_", "*", "[", "]", "(", ")", "~", "`", ">", "#", "+", "-", "=", "|", "{", "}", ".", "!"))
        self.escape_chars_Markdown = self._escape_chars_setup(("_", "*", "`", "["))

    def _escape_chars_setup(self, escape_chars: Union[list, str, tuple]):
        if isinstance(escape_chars, (list, tuple)):

            return {i: "\\" + chr(i) for i in bytes("".join(escape_chars).encode("utf8"))}
        else:

            return {i: "\\" + chr(i) for i in bytes(escape_chars.encode("utf8"))}

    def _parse_update(self) -> None:

        if "message" in self._update["result"][-1].keys():

            self._update_id = self._update["result"][-1]["update_id"]

            text: str = self._update["result"][-1]["message"]["text"]
            chat_id: int = self._update["result"][-1]["message"]["chat"]["id"]
            message_id: int = self._update["result"][-1]["message"]["message_id"]
            username: str = self._update["result"][-1]["message"]["from"]["username"]

            self._message = m.TextMessage(message_id, username, chat_id, text)

        elif "callback_query" in self._update["result"][-1].keys():

            self._update_id = self._update["result"][-1]["update_id"]
            chat_id: int = self._update["result"][-1]["callback_query"]["message"]["chat"]["id"]
            callback_data: str = self._update["result"][-1]["callback_query"]["data"]

            self._message = m.CallbackMessage(chat_id, callback_data)

        elif "poll" in self._update["result"][-1].keys():

            self._update_id = self._update["result"][-1]["update_id"]

            polls = [poll["text"] for poll in self._update["result"][-1]["poll"]["options"] if poll["voter_count"] > 0 and poll["text"] != "Nothing"]

            poll_id: str = self._update["result"][-1]["poll"]["id"]

            self._message = m.PollMessage(poll_id, polls)
        logger.debug(repr(self._message))

    def get_updates(self) -> Iterator[Union[m.TextMessage, m.PollMessage, m.CallbackMessage, None]]:

        url = self._base_url + "getUpdates"

        if self._update_id:

            data = {"offset": self._update_id + 1}

            self._update = requests.post(url, params=data).json()

        else:

            self._update = requests.post(url).json()
        if not self._update["ok"]:

            logger.exception(BotException(self._update))

        if self._update["result"]:

            self._parse_update()

            yield self._message
        else:
            yield None

    def send_mes(self, mess: m.SendMessage) -> None:

        url: str = self._base_url + "sendMessage"

        params = self.construct_mess(mess=mess)
        logger.debug(params)
        response = requests.post(url, params=params).json()

        if not response["ok"]:
            logger.exception(BotException(response))

    def edit_mes(self, mess: m.EditMessageText) -> None:

        if mess and mess.parse_mode != "HTML":
            mess.text = self.escape_char(mess.text, mess.parse_mode)
        params = mess.values()
        url: str = self._base_url + "editMessageText"
        logger.debug(params)
        response = requests.post(url, params).json()
        if not response["ok"]:
            logger.exception(BotException(response))

    def delete_mes(self, mess: m.DeleteMessage) -> None:

        url: str = self._base_url + "deleteMessage"
        params = mess.values()
        logger.debug(params)
        response = requests.post(url, params=params).json()

        if not response["ok"]:
            logger.exception(BotException(response))

    def send_poll(self, poll: m.SendPoll) -> Tuple[int, int]:
        url: str = self._base_url + "sendPoll"
        params = poll.values()
        logger.debug(params)
        response = requests.post(url, params=params).json()
        if not response["ok"]:
            logger.exception(BotException(response))

        return response["result"]["poll"]["id"], response["result"]["message_id"]

    def escape_char(self, text: str, pars_mode: str) -> str:
        if pars_mode == "MarkdownV2":
            return text.translate(self.escape_chars_MarkdownV2)
        return text.translate(self.escape_chars_Markdown)

    def __exit__(self, type, value, traceback):
        # Exception handling here
        pass

    def __enter__(self):
        return self

    def construct_mess(self, mess: m.SendMessage):

        if mess and mess.parse_mode != "HTML":
            mess.text = self.escape_char(mess.text, mess.parse_mode)
        params = mess.values()
        params["url"] = params["url"].replace("\\", "\\\\")
        params["text"] = f"[{self.escape_char(params['url_description'], mess.parse_mode)}]({params['url']}): {params['text']}"
        del params["url"]
        del params["url_description"]
        return params
