import logging
import logging.config
from json import load
from logging import INFO, Filter, LogRecord

from config import DEBUG


class InfoFilter(Filter):
    def filter(self, record: LogRecord) -> bool:
        return record.levelno == INFO


def log_setup():
    with open("./logging_config.json", "r") as f:
        config = load(f)
        if not DEBUG:
            config["root"]["handlers"] = []
        logging.config.dictConfig(config)
    main_logger = logging.getLogger("main")
    for handler in main_logger.handlers:
        if handler.level == INFO:
            handler.addFilter(InfoFilter())
