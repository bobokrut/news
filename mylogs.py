from loguru import logger
import sys

logger.remove(0)
logger.add(sys.stderr, level="INFO", backtrace=True, filter=lambda record: record["extra"].get("name") == "bot")
logger.add(sys.stderr, level="INFO", backtrace=True, filter=lambda record: record["extra"].get("name") == "main")
