#!/usr/bin/env python3

"""MISIS Entrance Guide module."""
# region Regular dependencies
from typing import Union
from aiogram import Bot, Dispatcher
from aiogram import types
from aiogram.types.message import ParseMode
from logging import Logger
# endregion

# region Local dependencies
from modules import markup as nav
from modules.db import DBManager
from modules.bot.broadcast import BotBroadcastFunctions
from modules.bot.generic import BotGenericFunctions
# from modules.bot.states import *
from modules.bot import decorators as dp  # Bot decorators
from .replies import navigation as dir_replies
from .skills import bot_skills_menu
from .keyboards import navigation as dir_keyboards

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

# region Menus
# endregion


@dp.callback_query_handler(lambda c: c.data == 'skill:navigation')
async def welcome(call: Union[types.CallbackQuery, types.Message]):
    await call.answer()
    await call.message.edit_text(dir_replies.welcome(),
                                 parse_mode=ParseMode.HTML,
                                 reply_markup=dir_keyboards.main_menu())


@dp.callback_query_handler(lambda c: c.data == 'navigation:back')
async def back(call: types.CallbackQuery):
    """Go back to the skills menu."""
    await call.answer()
    await bot_skills_menu(call.message)
    await call.message.delete()


# noinspection PyProtectedMember
def setup(dispatcher: Dispatcher,
          bot_obj: Bot,
          database: DBManager,
          logger: Logger,
          generic: BotGenericFunctions):
    global bot
    global db
    global log
    global bot_generic
    bot = bot_obj
    bot_generic = generic
    log = logger
    db = database
    for func in globals().values():
        if hasattr(func, '_handlers'):
            for handler_type, args, kwargs in func._handlers:
                if handler_type == 'message':
                    dispatcher.register_message_handler(func, *args, **kwargs)
                elif handler_type == 'callback_query':
                    dispatcher.register_callback_query_handler(func, *args, **kwargs)
