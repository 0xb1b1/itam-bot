#!/usr/bin/env python3

import logging
from logging import Logger
from os import getenv

# region Logging setup
# Create a logger instance
log = logging.getLogger("itam-bot")

# AIOGram logging
# logging.basicConfig(level=logging.DEBUG)

# Create log formatter
formatter = logging.Formatter("%(asctime)s \
- %(levelname)s - %(message)s")

# Сreate console logging handler and set its level
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
log.addHandler(ch)

# Create file logging handler and set its level
fh = logging.FileHandler(r'/data/logs/telegram_bot.log')
fh.setFormatter(formatter)
log.addHandler(fh)
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
