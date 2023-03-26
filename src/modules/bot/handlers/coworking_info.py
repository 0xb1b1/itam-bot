# region Regular dependencies
import os
import logging                               # Logging events
import asyncio                               # Asynchronous sleep()
from datetime import datetime
from typing import Optional, Union
from aiogram import Bot, Dispatcher          # Telegram bot API
from aiogram import executor, types          # Telegram API
from aiogram.types.message import ParseMode  # Send Markdown-formatted messages
from aiogram.dispatcher.filters.builtin import CommandStart
from aiogram.dispatcher.filters import ChatTypeFilter
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.utils import exceptions
from sqlalchemy.exc import DataError

# endregion
# region Local dependencies
import modules.bot.tools as bot_tools           # Bot tools
from modules import markup as nav           # Bot menus
from modules import btntext                 # Telegram bot button text
from modules import replies                 # Telegram bot information output
from modules.coworking import Manager as CoworkingManager  # Coworking space information
from modules import replies                 # Telegram bot information output
from modules.db import DBManager            # Operations with sqlite db
from modules.models import CoworkingStatus  # Coworking status model
from modules.bot.coworking import BotCoworkingFunctions  # Bot coworking-related functions
from modules.bot.scheduled import BotScheduledFunctions  # Bot scheduled functions (recurring)
from modules.bot.broadcast import BotBroadcastFunctions  # Bot broadcast functions
from modules.bot.generic import BotGenericFunctions      # Bot generic functions
from modules.bot.states import *
from modules.buttons import coworking as cwbtn  # Coworking action buttons (admin)
from modules.bot import decorators as dp  # Bot decorators
# endregion

# region Passed by setup()
db = None
bot = None
log = None
bot_broadcast = None
bot_generic = None
bot_cw = None
# endregion

# region Lambda functions
debug_dec = lambda message: log.debug(f'User {message.from_user.id} from chat {message.chat.id} called command `{message.text}`') or True
admin_only = lambda message: db.is_admin(message.from_user.id)
groups_only = lambda message: message.chat.type in ['group', 'supergroup']
# endregion

@dp.message_handler(lambda message: message.text == btntext.COWORKING_STATUS)
@dp.message_handler(commands=['coworking_status', 'cw_status'])
async def coworking_status_reply(message: types.Message) -> None:
    # Deny access to group chats
    if bot_generic.chat_is_group(message):
        await message.answer(replies.coworking_status_only_in_pm())
        return
    if db.is_admin(message.from_user.id):
        inlCoworkingControlMenu = bot_cw.get_admin_markup(message)
    else:
        inlCoworkingControlMenu = InlineKeyboardMarkup()
    are_notifications_on = db.get_coworking_notifications(message.chat.id)
    inlCoworkingControlMenu.add(cwbtn.inl_location_short)
    inlCoworkingControlMenu.add(InlineKeyboardButton(replies.toggle_coworking_notifications(are_notifications_on),
                                                     callback_data='coworking:toggle_notifications'))
    inlCoworkingControlMenu.add(InlineKeyboardButton(btntext.INL_COWORKING_STATUS_EXPLAIN,
                                                     callback_data='coworking:status:explain'))
    try:
        status = coworking.get_status()
        if status == CoworkingStatus.temp_closed:
            await message.answer(replies.coworking_status_reply(status,
                                                                responsible_uname=db.get_coworking_responsible_uname(),
                                                                delta_mins=coworking.get_delta()),
                                reply_markup=inlCoworkingControlMenu)
        else:
            await message.answer(replies.coworking_status_reply(status,
                                                                responsible_uname=db.get_coworking_responsible_uname()),
                                 reply_markup=inlCoworkingControlMenu)
    except Exception as exc:
        log.error(f"Error while getting coworking status: {exc}")

@dp.callback_query_handler(lambda c: c.data == 'coworking:status:explain')
async def coworking_status_explain(call: types.CallbackQuery) -> None:
    await call.message.edit_text(replies.coworking_status_explain(coworking.get_responsible_uname()),
                                 parse_mode=ParseMode.MARKDOWN)


def setup(dispatcher: Dispatcher,
          bot_obj: Bot,
          database: DBManager,
          logger: logging.Logger,
          broadcast: BotBroadcastFunctions,
          generic: BotGenericFunctions,
          cw: BotCoworkingFunctions):
    global bot
    global db
    global log
    global bot_broadcast
    global bot_generic
    global coworking
    global bot_cw
    bot = bot_obj
    bot_broadcast = broadcast
    bot_generic = generic
    log = logger
    db = database
    bot_cw = cw
    coworking = CoworkingManager(db)
    for func in globals().values():
        if hasattr(func, '_handlers'):
            for handler_type, args, kwargs in func._handlers:
                if handler_type == 'message':
                    dispatcher.register_message_handler(func, *args, **kwargs)
                elif handler_type == 'callback_query':
                    dispatcher.register_callback_query_handler(func, *args, **kwargs)
