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

@dp.callback_query_handler(lambda c: c.data == 'admin:broadcast')
@dp.message_handler(admin_only, commands=['broadcast'])
async def admin_broadcast_stage0(message: types.Message, state: FSMContext) -> None:
    await message.answer(f"Введите текст для рассылки\n\n{replies.cancel_action()}")
    await state.set_state(AdminBroadcast.message.state)

@dp.message_handler(admin_only, state=AdminBroadcast.message.state)
async def admin_broadcast_stage1(message: types.Message, state: FSMContext) -> None:
    await state.update_data(message=message.text)
    await message.answer(f"Выберите ширину рассылки\n\n{replies.cancel_action()}", reply_markup=nav.adminBroadcastScopeMenu)
    await state.set_state(AdminBroadcast.scope.state)

@dp.message_handler(admin_only, state=AdminBroadcast.scope.state)
async def admin_broadcast_stage2(message: types.Message, state: FSMContext) -> None:
    await state.update_data(scope=message.text)
    state_data = await state.get_data()
    await message.answer(f"Подтвердите рассылку\nТекст рассылки:\n\"\"\"{state_data['message']}\"\"\"\n\n{replies.cancel_action()}", reply_markup=nav.confirmMenu)
    await state.set_state(AdminBroadcast.confirm.state)

@dp.message_handler(admin_only, state=AdminBroadcast.confirm.state)
async def admin_broadcast_stage3(message: types.Message, state: FSMContext) -> None:
    # Check if user confirmed the broadcast
    if message.text != btntext.CONFIRM:
        message.answer("Рассылка отменена")
        await state.finish()
    state_data = await state.get_data()
    if state_data['scope'] == btntext.EVERYONE:
        scope = 'all'
    elif state_data['scope'] == btntext.USERS:
        scope = 'users'
    elif state_data['scope'] == btntext.ADMINS:
        scope = 'admins'
    else:
        await bot.send_message(message.from_user.id, "Неверный тип рассылки")
        await state.finish()
        return
    # Send broadcast
    asyncio.get_event_loop().create_task(bot_broadcast.broadcast(state_data['message'], scope))
    log.info(f"Admin {message.from_user.id} broadcasted message to scope {scope}\nMessage:\n\"\"\"\n{state_data['message']}\n\"\"\"")
    await message.answer(replies.broadcast_successful(),
                         reply_markup=bot_generic.get_main_keyboard(message))
    await state.finish()


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
