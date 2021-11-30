from dataclasses import dataclass as _dataclass
from typing import List as _List
from typing import Literal as _Literal
from typing import Union as _Union


@_dataclass(init=True, repr=True, eq=False)
class TextMessage:

    message_id: int
    username: str
    chat_id: int
    text: str


@_dataclass(init=True, repr=True, eq=False)
class CallbackMessage:

    chat_id: int
    callback_data: str


@_dataclass(init=True, repr=True, eq=False)
class PollMessage:

    poll_id: str
    polls: _List[str]


@_dataclass(init=True, repr=True, eq=False)
class SendMessage:
    """
    api_params:
        * parse_mode: MarkdownV2, Markdown, HTML (https://core.telegram.org/bots/api#formatting-options)
        * disable_web_page_preview: `True` or  `False`
        * disable_notification: `True` or `False`
        * allow_sending_without_reply: `True` or `False`
    """

    chat_id: int
    text: str
    parse_mode: _Union[_Literal["MarkdownV2", "HTML", "Markdown"], None] = None
    disable_web_page_preview: _Union[bool, None] = None
    disable_notification: _Union[bool, None] = None
    reply_to_message_id: _Union[int, None] = None
    allow_sending_without_reply: _Union[bool, None] = None
    reply_markup: _Union[str, None] = None
    url: str = None
    url_description: str = None

    def values(self):

        return {key: value for key, value in self.__dict__.items() if value}


@_dataclass(init=True, repr=True, eq=False)
class EditMessageText:
    """
    api_params:
        * parse_mode: MarkdownV2, Markdown, HTML (https://core.telegram.org/bots/api#formatting-options)
        * disable_web_page_preview: `True` or `False`
        * disable_notification: `True` or `False`
    """

    chat_id: int
    message_id: int
    text: str
    inline_message_id: _Union[int, None] = None
    disable_web_page_preview: _Union[bool, None] = None
    reply_markup: _Union[str, None] = None
    parse_mode: _Union[_Literal["MarkdownV2", "HTML", "Markdown"], None] = None

    def values(self):

        return {key: value for key, value in self.__dict__.items() if value}


@_dataclass(init=True, repr=True, eq=False)
class SendPoll:
    """
    api_params:
        * parse_mode: MarkdownV2, Markdown, HTML (https://core.telegram.org/bots/api#formatting-options)
        * disable_notification: `True` or `False`
        * allow_sending_without_reply: `True` or `False`
        * is_anonymous (oprional): `True` or `False`. Defaults to `False`
        * type (optional): "quiz", "regular". Defaults to "regular"
        * allows_multiple_answers (optional): `True` or `False`. Defaults to `False`
        * correct_option_id (`int`, optional): 0-based identifier of the correct answer option, required for polls in `quiz` mode
        * explanation (`str`, optional): Text that is shown when a user chooses an incorrect answer or taps on the lamp icon in a `quiz`-style poll, 0-200 characters with at most 2 line feeds after entities parsing
        * explanation_parse_mode (optional): MarkdownV2, Markdown, HTML (https://core.telegram.org/bots/api#formatting-options)
        * open_period (`int`, optional): Amount of time in seconds the poll will be active after creation, 5-600. Can't be used together with close_date
        * close_date (`int`, optional): Point in time (Unix timestamp) when the poll will be automatically closed. Must be at least 5 and no more than 600 seconds in the future. Can't be used together with open_period
        * is_closed (optional): `True` or `False`
        * reply_to_message_id (optional, `int`)

    """

    chat_id: int
    question: str
    options: str
    is_anonymous: _Union[bool, None] = None
    type: _Union[_Literal["quiz", "regular"], None] = None
    allows_multiple_answers: _Union[bool, None] = None
    correct_option_id: _Union[int, None] = None
    explanation: _Union[str, None] = None
    open_period: _Union[int, None] = None
    close_date: _Union[bool, None] = None
    is_closed: _Union[bool, None] = None
    disable_notification: _Union[bool, None] = None
    reply_to_message_id: _Union[int, None] = None
    allow_sending_without_reply: _Union[bool, None] = None
    reply_markup: _Union[str, None] = None
    explanation_parse_mode: _Union[_Literal["MarkdownV2", "HTML", "Markdown"], None] = None

    def values(self):

        return {key: value for key, value in self.__dict__.items() if value}


@_dataclass(init=True, repr=True, eq=False)
class DeleteMessage:

    chat_id: int
    message_id: int

    def values(self):

        return {key: value for key, value in self.__dict__.items() if value}
