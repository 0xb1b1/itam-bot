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
from aiogram.types.chat import ChatActions
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
from modules import stickers
# endregion

# region Passed by setup()
db: DBManager = None
bot: Bot = None
log = None
bot_generic = None
# endregion

# region Lambda functions
debug_dec = lambda message: log.debug(f'User {message.from_user.id} from chat {message.chat.id} called command `{message.text}`') or True
admin_only = lambda message: db.is_admin(message.from_user.id)
groups_only = lambda message: message.chat.type in ['group', 'supergroup']
# endregion

# region Start routines
from modules.bot.handlers.yandex_internship import yandex_internship_start
# endregion

@dp.callback_query_handler(lambda query: query.data == 'start')
@dp.message_handler(CommandStart())
async def bot_send_welcome(message: Union[types.Message, types.CallbackQuery], user_first_name: str = None) -> None:
    """Send welcome message and init user's record in DB"""
    if isinstance(message, types.CallbackQuery):
        message = message.message
        args = ['']
    else:
        args = message.get_args().split(',')
        user_first_name = message.from_user.first_name
    args_empty = args[0] == ''
    await message.answer(replies.welcome_message(user_first_name),
                        reply_markup=ReplyKeyboardRemove())
    if args_empty:
        await bot.send_chat_action(message.chat.id, ChatActions.TYPING)
        await asyncio.sleep(1.3)
        await message.answer(replies.welcome_message_instructions())
    await bot.send_chat_action(message.chat.id, ChatActions.CHOOSE_STICKER)
    await asyncio.sleep(0.7)
    await bot.send_sticker(message.chat.id, stickers.WELCOME)
    db.add_regular_user(message.from_user.id,
                        message.from_user.username,
                        message.from_user.first_name,
                        message.from_user.last_name)
    if args_empty:
        await bot.send_message(message.chat.id, replies.welcome_message_go(),
                         reply_markup=bot_generic.get_main_keyboard(message))
    if not args_empty:
        await bot.send_chat_action(message.chat.id, ChatActions.TYPING)
        await asyncio.sleep(0.5)
        if args[0] == 'ya_int':
            await yandex_internship_start(message)
        else:
            await message.answer(replies.start_command_not_found())


def setup(dispatcher: Dispatcher,
          bot_obj: Bot,
          database: DBManager,
          logger: logging.Logger,
          generic: BotGenericFunctions):
    global bot
    global db
    global log
    global bot_generic
    global coworking
    bot = bot_obj
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
