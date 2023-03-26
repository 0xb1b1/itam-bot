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
#bot_broadcast = None
#bot_generic = None
# endregion

# region Lambda functions
debug_dec = lambda message: log.debug(f'User {message.from_user.id} from chat {message.chat.id} called command `{message.text}`') or True
admin_only = lambda message: db.is_admin(message.from_user.id)
groups_only = lambda message: message.chat.type in ['group', 'supergroup']
# endregion

@dp.message_handler(commands=['profile'])
@dp.message_handler(lambda message: message.text == btntext.PROFILE_INFO)
async def profile_info(message: types.Message) -> None:
    if message.chat.type == 'group':
        await message.answer(replies.profile_info_only_in_pm())
        return
    await bot.send_message(message.from_user.id,
                            replies.profile_info(db.get_user_data_short(message.from_user.id)),
                            reply_markup=nav.inlProfileMenu)

@dp.message_handler(commands=['bio'])
async def user_data_get_bio(message: types.Message) -> None:
    """Get user bio"""
    await message.answer(db.get_user_data_bio(message.from_user.id))

@dp.message_handler(commands=['resume'])
async def user_data_get_resume(message: types.Message) -> None:
    """Get user resume"""
    await message.answer(db.get_user_data_resume(message.from_user.id))

@dp.callback_query_handler(lambda c: c.data == 'edit_profile')
async def edit_profile(call: types.CallbackQuery, state: FSMContext, secondary_run: bool = False) -> None:
    """Edit user profile"""
    short_user_data = db.get_user_data_short(call.from_user.id)
    fields = list(short_user_data.keys())
    field_names = replies.profile_fields()
    keyboard = types.InlineKeyboardMarkup(resize_keyboard=True)
    for key in fields:
        if key in ['uid', 'gname']:
            continue
        keyboard.add(types.InlineKeyboardButton(field_names[key], callback_data=f'edit_profile_{key}'))
    if not secondary_run:
        await call.answer()
        await call.message.edit_text(replies.profile_info(db.get_user_data_short(call.from_user.id)),
                                    reply_markup=keyboard)
    else:
        await bot.send_message(call.from_user.id,
                               replies.profile_info(db.get_user_data_short(call.from_user.id)),
                               reply_markup=keyboard)
    await state.set_state(UserEditProfile.selector)
    await state.update_data(first_name=short_user_data['first_name'],
                            last_name=short_user_data['last_name'],
                            birthday=short_user_data['birthday'],
                            email=short_user_data['email'],
                            phone=short_user_data['phone'])

    await call.message.answer("Что изменим?", reply_markup=nav.inlCancelMenu)

@dp.callback_query_handler(state=UserEditProfile.selector)
async def edit_profile_action(call: types.CallbackQuery, state: FSMContext) -> None:
    """Edit user profile - select action"""
    await call.answer()
    state_data = await state.get_data()
    fn = lambda x: f'edit_profile_{x}'
    if call.data == fn('first_name'):
        await bot.send_message(call.from_user.id,
                               replies.profile_edit_first_name(state_data['first_name'],
                                                               state_data['last_name']))
        await state.set_state(UserEditProfile.first_name)
    elif call.data == fn('last_name'):
        await bot.send_message(call.from_user.id,
                               replies.profile_edit_last_name(state_data['first_name'],
                                                              state_data['last_name']))
        await state.set_state(UserEditProfile.last_name)
    elif call.data == fn('birthday'):
        await bot.send_message(call.from_user.id,
                               replies.profile_edit_birthday(state_data['birthday']))
        await state.set_state(UserEditProfile.birthday)
    elif call.data == fn('email'):
        await bot.send_message(call.from_user.id,
                               replies.profile_edit_email(state_data['email']))
        await state.set_state(UserEditProfile.email)
    elif call.data == fn('phone'):
        await bot.send_message(call.from_user.id,
                               replies.profile_edit_phone(state_data['phone']))
        await state.set_state(UserEditProfile.phone)
    else:
        await bot.send_message(call.from_user.id, f"Field is not editable yet: {call.data}")

@dp.message_handler(state=UserEditProfile.first_name)
async def edit_profile_first_name(message: types.Message, state: FSMContext):
    """Edit user profile first name"""
    #state_data = await state.get_data()
    await state.update_data(first_name=message.text)
    db.set_user_first_name(message.from_user.id, message.text)
    await message.answer(replies.profile_edit_success())
    await state.finish()

@dp.message_handler(state=UserEditProfile.last_name)
async def edit_profile_last_name(message: types.Message, state: FSMContext):
    """Edit user profile last name"""
    #state_data = await state.get_data()
    await state.update_data(last_name=message.text)
    db.set_user_last_name(message.from_user.id, message.text)
    await message.answer(replies.profile_edit_success())
    await state.finish()

@dp.message_handler(state=UserEditProfile.birthday)
async def edit_profile_birthday(message: types.Message, state: FSMContext):
    """Edit user profile date of birth"""
    #state_data = await state.get_data()
    try:
        birthday = datetime.strptime(message.text, "%d.%m.%Y")
    except ValueError:
        await message.answer(replies.invalid_date_try_again())
        return
    await state.update_data(birthday=birthday)
    db.set_user_birthday(message.from_user.id, birthday)
    await message.answer(replies.profile_edit_success())
    await state.finish()

@dp.message_handler(state=UserEditProfile.email)
async def edit_profile_email(message: types.Message, state: FSMContext):
    """Edit user profile email"""
    #state_data = await state.get_data()
    try:
        db.set_user_email(message.from_user.id, message.text)
    except ValueError:
        await message.answer(replies.invalid_email_try_again())
        return
    await message.answer(replies.profile_edit_success())
    await state.finish()

@dp.message_handler(state=UserEditProfile.phone)
async def edit_profile_phone(message: types.Message, state: FSMContext):
    """Edit user profile phone"""
    #state_data = await state.get_data()
    try:
        db.set_user_phone(message.from_user.id, message.text)
    except ValueError:
        await message.answer(replies.invalid_phone_try_again())
        return
    await message.answer(replies.profile_edit_success())
    await state.finish()

# region Profile setup flow (full profile info)
#@dp.message_handler()
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
    #global bot_broadcast
    #global bot_generic
    global coworking
    bot = bot_obj
    #bot_broadcast = broadcast
    #bot_generic = generic
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
