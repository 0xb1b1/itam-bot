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
#from modules.buttons import coworking as cwbtn  # Coworking action buttons (admin)
from modules.bot import decorators as dp  # Bot decorators
# endregion

# region Passed by setup()
db = None
bot = None
log = None
bot_broadcast = None
bot_generic = None
# endregion

# region Lambda functions
debug_dec = lambda message: log.debug(f'User {message.from_user.id} from chat {message.chat.id} called command `{message.text}`') or True
admin_only = lambda message: db.is_admin(message.from_user.id)
groups_only = lambda message: message.chat.type in ['group', 'supergroup']
# endregion

@dp.message_handler(admin_only, commands=['plaintext_toggle_for_chat'])
async def plaintext_answers_toggle_for_chat(message: types.Message):
    """Toggle plaintext answers boolean in database for a given chat"""
    chat_id = message.get_args()
    if not chat_id:
        await message.answer("Укажите айди чата!")
        return
    status = db.toggle_message_answers_status(chat_id)
    await message.answer(replies.plaintext_answers_reply(status, toggled=True, chat_id=chat_id))
    await bot.send_message(chat_id, replies.plaintext_answers_reply(status, toggled=True,
                                                                    admin_uname=message.from_user.username))

@dp.message_handler(groups_only, commands=['plaintext'])
async def plaintext_answers_toggle(message: types.Message):
    """Toggle plaintext answers boolean in database"""
    is_grp_admin = await bot_tools.is_group_admin(message)
    if not is_grp_admin:
        if not db.is_admin(message.from_user.id):
            await message.answer(replies.permission_denied())
            return
    status = db.toggle_message_answers_status(message.chat.id)
    await message.answer(replies.plaintext_answers_reply(status, toggled=True))

@dp.message_handler(groups_only, commands=['plaintext_status'])
async def plaintext_answers_status(message: types.Message):
    """Get plaintext answers boolean status"""
    status = db.get_message_answers_status(message.chat.id)
    await message.answer(replies.plaintext_answers_reply(status, toggled=False))

# region Coworking notifications (user control)
@dp.callback_query_handler(lambda c: c.data == 'coworking:toggle_notifications', state='*')
@dp.message_handler(commands=['notify'])
async def notify(message: Union[types.Message, types.CallbackQuery]) -> None:
    """Turn on notifications for a given chat ID"""
    message = bot_tools.conv_call_to_msg(message)
    is_grp_admin = await bot_tools.is_group_admin(message)
    if not is_grp_admin:
        await message.answer(replies.permission_denied())
        return
    current_status = db.toggle_coworking_notifications(message.chat.id)
    await message.answer(replies.coworking_notifications_on() if current_status else replies.coworking_notifications_off())

@dp.message_handler(commands=['notify_status'])
async def notify_status(message: types.Message) -> None:
    """Get notification status for a given chat ID"""
    if db.get_coworking_notifications(message.chat.id):
        await message.answer(replies.coworking_notifications_on())
        return
    await message.answer(replies.coworking_notifications_off())
# endregion


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
