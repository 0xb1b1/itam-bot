#!/usr/bin/env python3

"""Bot skill reply handlers."""
# region Regular dependencies
import logging
from aiogram import Bot, Dispatcher
from aiogram import types
# from aiogram.types.message import ParseMode
from logging import Logger

# endregion
# region Local dependencies
# import modules.bot.tools as bot_tools
from modules import markup as nav
from modules import btntext
from modules.db import DBManager
from modules.bot.generic import BotGenericFunctions
from modules.bot import decorators as dp
from .replies import skills as sk_replies
# endregion

# region Passed by setup()
db: DBManager = None  # type: ignore
bot: Bot = None  # type: ignore
log: Logger = None  # type: ignore
bot_generic: BotGenericFunctions = None  # type: ignore
# endregion

# region Lambda functions
debug_dec = lambda message: log.debug(f'User {message.from_user.id} from chat \
{message.chat.id} called command `{message.text}`') or True
admin_only = lambda message: db.is_admin(message.from_user.id)
groups_only = lambda message: message.chat.type in ['group', 'supergroup']
# endregion


@dp.message_handler(lambda message: message.text == btntext.BOT_SKILLS_BTN)
async def bot_skills_menu(message: types.Message):
    if not db.user_exists(message.from_user.id):
        db.add_regular_user(message.from_user.id,
                            message.from_user.username,
                            message.from_user.first_name,
                            message.from_user.last_name)
    await message.answer(sk_replies.bot_skills_menu(), reply_markup=nav.botSkillsMenu)


# noinspection PyProtectedMember
def setup(dispatcher: Dispatcher,
          bot_obj: Bot,
          database: DBManager,
          logger: logging.Logger,
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
