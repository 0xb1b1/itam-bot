#!/usr/bin/env python3

import logging
from logging import Logger
from os import getenv

from modules.db import DBManager

# region Logging setup
# Create a logger instance
log = logging.getLogger("itam-bot")

# AIOGram logging
# logging.basicConfig(level=logging.DEBUG)

# Create log formatter
_formatter = logging.Formatter("%(asctime)s \
- %(levelname)s - %(message)s")

# Сreate console logging handler and set its level
_ch = logging.StreamHandler()
_ch.setLevel(logging.DEBUG)
_ch.setFormatter(_formatter)
log.addHandler(_ch)

# Create file logging handler and set its level
_fh = logging.FileHandler(r'/data/logs/telegram_bot.log')
_fh.setFormatter(_formatter)
log.addHandler(_fh)
# endregion

# region Set logging level
LOGGING_LEVEL = getenv("LOGGING_LEVEL", "debug").upper()
if LOGGING_LEVEL == "DEBUG":
    log.setLevel(logging.DEBUG)
elif LOGGING_LEVEL == "INFO":
    log.setLevel(logging.INFO)
elif LOGGING_LEVEL == "WARNING":
    log.setLevel(logging.WARNING)
elif LOGGING_LEVEL == "ERROR":
    log.setLevel(logging.ERROR)
elif LOGGING_LEVEL == "CRITICAL":
    log.setLevel(logging.CRITICAL)
# endregion

# region Database setup
db = DBManager(log)
# endregion

# Region Telegram Bot setup
TELEGRAM_API_TOKEN = getenv('TELEGRAM_API_TOKEN')
if TELEGRAM_API_TOKEN is None:
    log.error("config.TELEGRAM_API_TOKEN: no Telegram API token found")
# endregion

# region Log environment variables
log.critical("*** BEGIN Deployment configuration ***")
log.critical(f"config.LOGGING_LEVEL: {LOGGING_LEVEL}")
log.debug(f"config.TELEGRAM_API_TOKEN: {TELEGRAM_API_TOKEN}")
log.critical("*** END Deployment configuration ***")
# endregion
