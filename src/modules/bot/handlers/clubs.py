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

# message text that should be handled sis btntext.CLUBS_BTN
@dp.message_handler(lambda message: message.text == btntext.CLUBS_BTN)
async def clubs_menu(message: types.Message):
        await message.answer(replies.club_info_general(),
                             reply_markup=nav.inlClubsMenu)

@dp.callback_query_handler(lambda c: c.data in [i+'_club_info' for i in ['ctf', 'hackathon', 'design', 'gamedev', 'robotics']])
async def club_info(call: types.CallbackQuery) -> None:
    """Club info"""
    await call.answer()
    club = call.data.split('_')[0]
    # Edit previous bot message
    try:
        if club == 'ctf':
            await call.message.edit_text(replies.ctf_club_info(),
                                        reply_markup=nav.inlClubsMenu,
                                        parse_mode=ParseMode.MARKDOWN)
        elif club == 'hackathon':
            await call.message.edit_text(replies.hackathon_club_info(),
                                        reply_markup=nav.inlClubsMenu,
                                        parse_mode=ParseMode.MARKDOWN)
        elif club == 'design':
            await call.message.edit_text(replies.design_club_info(),
                                        reply_markup=nav.inlClubsMenu,
                                        parse_mode=ParseMode.MARKDOWN)
        elif club == 'gamedev':
            await call.message.edit_text(replies.gamedev_club_info(),
                                        reply_markup=nav.inlClubsMenu,
                                        parse_mode=ParseMode.MARKDOWN)
        elif club == 'robotics':
            await call.message.edit_text(replies.robotics_club_info(),
                                        reply_markup=nav.inlClubsMenu,
                                        parse_mode=ParseMode.MARKDOWN)
        # elif club == 'ml':
        #     await call.message.edit_text(replies.ml_club_info(),
        #                                 reply_markup=nav.inlClubsMenu,
        #                                 parse_mode=ParseMode.MARKDOWN)
    except exceptions.MessageNotModified:
        log.debug(f"User {call.from_user.id} tried to request the same club info ({club})")


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