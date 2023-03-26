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

@dp.message_handler(admin_only, lambda message: message.text == btntext.ADMIN_BTN)
@dp.message_handler(admin_only, commands=['admin'])
async def admin_panel(message: types.Message) -> None:
    """Send admin panel"""
    inlAdminChangeGroupBtn = InlineKeyboardButton(btntext.INL_ADMIN_EDIT_GROUP, callback_data='change_user_group')
    inlAdminBroadcastBtn = InlineKeyboardButton(btntext.INL_ADMIN_BROADCAST, callback_data='admin:broadcast')
    markup = InlineKeyboardMarkup().add(inlAdminChangeGroupBtn,
                                        inlAdminBroadcastBtn)
    await message.answer(replies.admin_panel(coworking.get_status()), reply_markup=markup)
    log.info(f"User {message.from_user.id} opened the admin panel")

@dp.message_handler(admin_only, commands=['get_notif_db'])
async def get_notif_db(message: types.Message) -> None:
    """Get notification database"""
    await message.answer(db.get_coworking_notification_chats_str())

@dp.message_handler(admin_only, commands=['stats'])
async def get_stats(message: types.Message) -> None:
    """Get stats"""
    mkup = InlineKeyboardMarkup().add(types.InlineKeyboardButton(text=btntext.TRIM_COWORKING_LOG, callback_data="coworking:trim_log"))
    await message.answer(replies.stats(db.get_stats()), reply_markup=mkup)

@dp.callback_query_handler(lambda c: c.data == 'change_user_group')
async def change_user_group_stage0(call: types.CallbackQuery, state: FSMContext) -> None:
    """Change user group, stage 0"""
    await state.set_state(AdminChangeUserGroup.user_id.state)
    await call.message.edit_text(f"Введите ID пользователя\n\n{replies.cancel_action()}")

@dp.message_handler(state=AdminChangeUserGroup.user_id)
async def change_user_group_stage1(message: types.Message, state: FSMContext) -> None:
    """Change user group, stage 1"""
    user_id = message.text
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for group_name in db.get_groups_and_ids_as_dict_namekey():
        keyboard.add(types.KeyboardButton(group_name))
    await message.answer(f"Выберите группу\n\n{replies.cancel_action()}", reply_markup=keyboard)
    await state.update_data(user_id=user_id)
    await state.set_state(AdminChangeUserGroup.group_id.state)  # Also accepted: await AdminChangeUserGroup.next()

@dp.message_handler(state=AdminChangeUserGroup.group_id)
async def change_user_group_stage2(message: types.Message, state: FSMContext) -> None:
    """Change user group, stage 2"""
    state_data = await state.get_data()
    user_id = state_data['user_id']
    try:
        group_id = db.get_groups_and_ids_as_dict_namekey()[message.text]["gid"]
    except Exception as exc:
        await message.answer("I encountered an exception! Details below:\n\n" + str(exc))
        return
    if not db.is_superadmin(message.from_user.id):
        await message.answer(replies.permission_denied(),
                             reply_markup=bot_generic.get_main_keyboard(message))
        await state.finish()
        return
    try:
        db.set_user_group(user_id, group_id)
    except (DataError, AttributeError) as exc:
        await message.answer(f"Invalid data sent to DB. Please try again.\n\nFull error:\n{exc}")
        await state.finish()
        return
    await message.answer(replies.user_group_changed(),
                         reply_markup=bot_generic.get_main_keyboard(message))
    log.info(f"User {message.from_user.id} changed user {user_id} group to {group_id}")
    await state.finish()

@dp.message_handler(admin_only, commands=['update_admin_kb'])
async def update_admin_kb(message: types.Message) -> None:
    """Update admin menu"""
    admins = db.get_admin_chats()
    for admin in admins:
        bot.send_message(admin, "Клавиатура администратора обновлена",
                         reply_markup=bot_generic.get_main_keyboard(message))
        log.debug(f"Admin keyboard updated for {admin} by {message.from_user.id}")
    log.info(f"Admin keyboard updated by {message.from_user.id} for {len(admins)} administrators")
    await message.answer(replies.menu_updated_reply(len(admins), admins_only=True))

# region Debug commands
@dp.message_handler(commands=['amiadmin'])
async def check_admin(message: types.Message) -> None:
    """Check if user is admin"""
    if db.is_admin(message.from_user.id):
        await message.answer("Admin OK")
    else:
        await message.answer(replies.permission_denied())

@dp.message_handler(commands=['get_groups'])
async def get_groups(message: types.Message) -> None:
    """Get groups"""
    await message.answer(str(db.get_groups()))

@dp.message_handler(commands=['get_users'])
async def get_users(message: types.Message) -> None:
    """Get user info"""
    await message.answer(str(db.get_users_str()))

@dp.message_handler(commands=['get_users_verbose'])
async def get_users_verbose(message: types.Message) -> None:
    """Get verbose user info"""
    await message.answer(str(db.get_users_verbose_str()))
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