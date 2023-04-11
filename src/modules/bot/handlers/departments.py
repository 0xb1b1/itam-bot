#!/usr/bin/env python3


"""Departments module."""
# region Regular dependencies
import logging
from typing import Union
from aiogram import Bot, Dispatcher
from aiogram import types
from aiogram.types.message import ParseMode
from logging import Logger
# endregion

# region Local dependencies
from modules import markup as nav
from modules.coworking import Manager as CoworkingManager
from modules.db import DBManager            # Operations with sqlite db
from modules.bot.broadcast import BotBroadcastFunctions  # Bot broadcast functions
from modules.bot.generic import BotGenericFunctions      # Bot generic functions
from modules.bot.states import *
# from modules.buttons import coworking as cwbtn  # Coworking action buttons (admin)
from modules.bot import decorators as dp  # Bot decorators
from .replies import departments as dept_replies
from modules import stickers
# endregion

# region Passed by setup()
db: DBManager = None  # type: ignore
bot: Bot = None  # type: ignore
log: Logger = None  # type: ignore
bot_broadcast: BotBroadcastFunctions = None  # type: ignore
bot_generic: BotGenericFunctions = None  # type: ignore
# endregion

# region Lambda functions
debug_dec = lambda message: log.debug(f'User {message.from_user.id} from \
chat {message.chat.id} called command `{message.text}`') or True
admin_only = lambda message: db.is_admin(message.from_user.id)
groups_only = lambda message: message.chat.type in ['group', 'supergroup']
# endregion

# region Menues
# endregion


@dp.callback_query_handler(lambda c: c.data == 'skill:departments')
async def welcome(call: Union[types.CallbackQuery, types.Message]):
    await call.answer()
    await call.message.edit_text(dept_replies.welcome(),
                                 parse_mode=ParseMode.MARKDOWN,
                                 reply_markup=nav.skill_departments())


# noinspection PyProtectedMember
def setup(dispatcher: Dispatcher,
          bot_obj: Bot,
          database: DBManager,
          logger: logging.Logger,
          broadcast: BotBroadcastFunctions,
          generic: BotGenericFunctions):
    global bot
    global db
    global log
    global bot_broadcast
    global bot_generic
    global coworking
    bot = bot_obj
    bot_broadcast = broadcast
    bot_generic = generic
    log = logger
    db = database
    coworking = CoworkingManager(db)
    for func in globals().values():
        if hasattr(func, '_handlers'):
            for handler_type, args, kwargs in func._handlers:
                if handler_type == 'message':
                    dispatcher.register_message_handler(func, *args, **kwargs)
                elif handler_type == 'callback_query':
                    dispatcher.register_callback_query_handler(func, *args, **kwargs)
