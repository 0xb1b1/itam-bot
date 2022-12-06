#!/usr/bin/env python3

"""Opens aiogram listener, ..."""

# region Regular dependencies
import os
import re                                    # Graceful shutdown
import signal                                # Graceful shutdown
import logging                               # Logging events
import asyncio                               # Asynchronous sleep()
from datetime import datetime
from xmlrpc.client import Boolean            # Subscription checks
from typing import Optional, Union
from aiogram import Bot, Dispatcher          # Telegram bot API
from aiogram import executor, types          # Telegram API
from aiogram.types.message import ParseMode  # Send Markdown-formatted messages
from dotenv import load_dotenv               # Load .env file
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
from modules import markup as nav           # Bot menus
from modules import btntext                 # Telegram bot button text
from modules import replies                 # Telegram bot information output
from modules import coworking               # Coworking space information
from modules import replies                 # Telegram bot information output
from modules.db import DBManager            # Operations with sqlite db
from modules.models import CoworkingStatus  # Coworking status model
# endregion
# region Modules
#from modules.admin.main import Admin
# endregion

# region Logging
# Create a logger instance
log = logging.getLogger('main.py-aiogram')

# Create log formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Сreate console logging handler and set its level
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
log.addHandler(ch)

# Create file logging handler and set its level
fh = logging.FileHandler(r'/data/logs/telegram_bot.log')
fh.setFormatter(formatter)
log.addHandler(fh)

# region Set logging level
logging_level_lower = os.getenv('LOGGING_LEVEL').lower()
if logging_level_lower == 'debug':
    log.setLevel(logging.DEBUG)
    log.critical("Log level set to debug")
elif logging_level_lower == 'info':
    log.setLevel(logging.INFO)
    log.critical("Log level set to info")
elif logging_level_lower == 'warning':
    log.setLevel(logging.WARNING)
    log.critical("Log level set to warning")
elif logging_level_lower == 'error':
    log.setLevel(logging.ERROR)
    log.critical("Log level set to error")
elif logging_level_lower == 'critical':
    log.setLevel(logging.CRITICAL)
    log.critical("Log level set to critical")
# endregion

# region Debug lambda functions
debug_dec = lambda message: log.debug(f'User {message.from_user.id} from chat {message.chat.id} called command `{message.text}`') or True
admin_only = lambda message: db.is_admin(message.from_user.id)
groups_only = lambda message: message.chat.type in ['group', 'supergroup']
# endregion
# endregion

# region Database
db = DBManager(log)

# region Modules
# Coworking status
coworking = coworking.Manager(db)
# endregion

# Get Telegram API token
TELEGRAM_API_TOKEN = os.getenv('TELEGRAM_API_TOKEN')

# Initialize bot and dispatcher
bot = Bot(token=TELEGRAM_API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# region Bot state classes
class AdminChangeUserGroup(StatesGroup):
    user_id = State()
    group_id = State()

class AdminBroadcast(StatesGroup):
    message = State()
    scope = State()
    confirm = State()

class AdminCoworkingTempCloseFlow(StatesGroup):
    delta = State()
    notification = State()
    confirm = State()
# endregion

# region Multiuse functions
def chat_is_group(message: types.Message) -> bool:
    """Check if message is sent from group or private chat"""
    # Check if the type of cmessage is CallbackQuery
    if isinstance(message, types.CallbackQuery):
        message = message.message
    if message.chat.type == 'group' or message.chat.type == 'supergroup':
        return True
    return False

def get_main_keyboard(message: types.Message) -> InlineKeyboardMarkup:
    btnClubs = KeyboardButton(btntext.CLUBS_BTN)
    btnCoworkingStatus = KeyboardButton(btntext.COWORKING_STATUS)
    btnProfileInfo = KeyboardButton(btntext.PROFILE_INFO)
    btnHelp = KeyboardButton(btntext.HELP_ME)
    mainMenu = ReplyKeyboardMarkup(resize_keyboard=True).add(btnClubs,
                                                             btnCoworkingStatus,
                                                             btnProfileInfo,
                                                             btnHelp)
    if db.is_admin(message.from_user.id):
        mainMenu.add(KeyboardButton(btntext.ADMIN_BTN))
    return ReplyKeyboardRemove() if chat_is_group(message) else mainMenu

async def send_coworking_notifications(is_open: bool, delta_mins: int = 0) -> None:
    cids = db.get_coworking_notification_chats()
    for cid in cids:
        if not cids[cid]["notifications_enabled"]:
            continue
        await bot.send_message(cid, replies.coworking_status_changed(is_open,
                                                                     responsible_uname=db.get_coworking_responsible_uname(),
                                                                     delta_mins=delta_mins))

async def broadcast(message: str, scope: str, custom_scope: list = None) -> None:
    if custom_scope:
        cids = custom_scope
    elif scope == 'all':
        cids = db.get_all_chats()
    elif scope == 'admins':
        cids = db.get_admin_chats()
    elif scope == 'users':
        cids = db.get_user_chats()
    else:
        raise ValueError("Invalid scope")
    log.debug(f"Broadcasting message to {len(cids)} chats: {cids}")
    for cid in cids:
        try:
            await bot.send_message(cid, message)
        except Exception as exc:
            log.debug(f"Failed to send broadcast message to chat {cid}: {exc}")

async def is_group_admin(message: types.Message) -> bool:
    # Check if chat is a group
    if not (message.chat.type == 'group' or message.chat.type == 'supergroup'):
        return True
    # Check if the user is a group admin
    administrators = await message.chat.get_administrators()
    administrators = [adm['user']['id'] for adm in administrators]
    if not message.from_user.id in administrators:
        return False
    return True

def conv_call_to_msg(call: Union[types.CallbackQuery, types.Message]) -> types.Message:
    if isinstance(call, types.Message):
        return call
    return call.message
# endregion

# region Scheduled tasks
async def coworking_status_checker(open_time: datetime, close_time: datetime, sleep: int = 20, dry_run: bool = False):
    """Check if the coworking space is closed after open_time and open after close_time"""
    try:
        # Set open_time and close_time to current date
        current_time = datetime.now()
        open_time = open_time.replace(year=current_time.year, month=current_time.month, day=current_time.day)
        close_time = close_time.replace(year=current_time.year, month=current_time.month, day=current_time.day)
        if not dry_run:
            admins = db.get_admin_chats()
        else:
            admins = [os.getenv("DEFAULT_ADMIN_UID")]
        # Check if the coworking space is closed after open_time
        if not current_time > open_time and coworking.get_status() == CoworkingStatus.closed:
            if not coworking.opened_today() and not coworking.notified_closed_during_hours_today():
                # Send broadcast to admins
                log.debug("Sending broadcast to admins about coworking space being closed during hours")
                await broadcast(replies.coworking_closed_during_hours(), custom_scope=admins)
            else:
                # Create debug log message
                # TODO: Remove when debug is done
                log.debug(f"NOT sending broadcast to admins (closed after open time); {coworking.opened_today()=}, {coworking.notified_closed_during_hours_today()=}")
        elif current_time > close_time and coworking.get_status() == CoworkingStatus.open:
            if not coworking.notified_open_after_hours_today():
                # Send broadcast to admins
                log.debug("Sending broadcast to admins about coworking space being open after hours")
                await broadcast(replies.coworking_open_after_hours(), custom_scope=admins)
            else:
                log.debug(f"NOT sending broadcast to admins (closed after open time); {coworking.notified_closed_during_hours_today()=}")
        else:
            # Create debug log message
            # TODO: Remove when debug is done
            log.debug(f"NOT sending broadcast to admins (not closed after open time or not open after close time); closed after open time ({coworking.get_status() == CoworkingStatus.closed}, {current_time > open_time}), open after closed time ({coworking.get_status() == CoworkingStatus.open}, {current_time > close_time})")
        # Log the datetime variables
        log.debug(f"[coworking_status_checker] open_time: {open_time}, close_time: {close_time}, current_time: {current_time}, closed_after_open_time: {datetime.now() > open_time}, open_after_close_time: {datetime.now() > close_time}")
        # Send all variables to debug
        log.debug(f"[coworking_status_checker] {open_time=}, {close_time=}, {current_time=}, {coworking.get_status()=}, {coworking.opened_today()=}, {coworking.notified_closed_during_hours_today()=}, {coworking.notified_open_after_hours_today()=}")
        # Sleep for the specified amount of time before running again
        await asyncio.sleep(sleep)
    except Exception as exc:
        log.error(f"Error in coworking_status_checker: {exc}")
# endregion

# region Bot replies
# Command message handling
@dp.message_handler(debug_dec, CommandStart())
async def send_welcome(message: types.Message) -> None:
    """Send welcome message and init user's record in DB"""
    await message.reply(replies.welcome_message(message.from_user.first_name),
                        reply_markup=get_main_keyboard(message))
    db.add_regular_user(message.from_user.id, message.from_user.username, message.from_user.first_name, message.from_user.last_name)

# region Cancel all states
@dp.callback_query_handler(lambda c: c.data == 'cancel', state='*')
@dp.message_handler(state='*', commands=['cancel'])
@dp.message_handler(lambda message: message.text.lower() == 'cancel' or message.text.lower() == btntext.CANCEL.lower(), state='*')
async def cancel_handler(cmessage: Union[types.Message, types.CallbackQuery], state: FSMContext):
    """Allow user to cancel any action"""
    log.debug(f"User {cmessage.from_user.id} canceled an action")
    # Cancel state and inform user about it
    await state.finish()
    # Check if the type of cmessage is CallbackQuery
    if isinstance(cmessage, types.CallbackQuery):
        await bot.send_message(cmessage.message.chat.id,
                               'Действие отменено', reply_markup=get_main_keyboard(cmessage))
        return
    await bot.send_message(cmessage.chat.id,
                           'Действие отменено', reply_markup=get_main_keyboard(cmessage))
# endregion

@dp.message_handler(debug_dec, commands=['amiadmin'])
async def check_admin(message: types.Message) -> None:
    """Check if user is admin"""
    if db.is_admin(message.from_user.id):
        await message.reply("Admin OK")
    else:
        await message.reply(replies.permission_denied())

@dp.message_handler(debug_dec, commands=['get_groups'])
async def get_groups(message: types.Message) -> None:
    """Get groups"""
    await message.reply(str(db.get_groups()))

@dp.message_handler(debug_dec, commands=['get_users'])
async def get_users(message: types.Message) -> None:
    """Get user info"""
    await message.reply(str(db.get_users_str()))

@dp.message_handler(debug_dec, commands=['get_users_verbose'])
async def get_users_verbose(message: types.Message) -> None:
    """Get verbose user info"""
    await message.reply(str(db.get_users_verbose_str()))

# region Coworking notifications
# region User interaction
@dp.callback_query_handler(lambda c: c.data == 'toggle_coworking_notifications', state='*')
@dp.message_handler(debug_dec, commands=['notify'])
async def notify(message: types.Message) -> None:
    """Turn on notifications for a given chat ID"""
    message = conv_call_to_msg(message)
    is_grp_admin = await is_group_admin(message)
    if not is_grp_admin:
        await message.reply(replies.permission_denied())
        return
    current_status = db.toggle_coworking_notifications(message.chat.id)
    message = conv_call_to_msg(message)
    await message.reply(replies.coworking_notifications_on() if current_status else replies.coworking_notifications_off())

@dp.message_handler(debug_dec, commands=['notify_status'])
async def notify_status(message: types.Message) -> None:
    """Get notification status for a given chat ID"""
    if db.get_coworking_notifications(message.chat.id):
        await message.reply(replies.coworking_notifications_on())
    else:
        await message.reply(replies.coworking_notifications_off())
# endregion
# endregion

# region Administration
@dp.message_handler(admin_only, debug_dec, lambda message: message.text == btntext.ADMIN_BTN)
@dp.message_handler(admin_only, debug_dec, commands=['admin'])
async def admin_panel(message: types.Message) -> None:
    """Send admin panel"""
    inlAdminChangeGroupBtn = InlineKeyboardButton(btntext.INL_ADMIN_EDIT_GROUP, callback_data='change_user_group')
    inlCoworkingControlBtn = InlineKeyboardButton(btntext.COWORKING_CONTROL, callback_data='coworking_control')
    markup = InlineKeyboardMarkup().add(inlAdminChangeGroupBtn,
                                        inlCoworkingControlBtn)
    await message.reply(replies.admin_panel(coworking.get_status()), reply_markup=markup)
    log.info(f"User {message.from_user.id} opened the admin panel")

@dp.callback_query_handler(admin_only, lambda c: c.data == 'coworking_control')
@dp.message_handler(admin_only, debug_dec, commands=['cwcontrol'])
async def coworking_control(cmessage: types.Message) -> None:
    """Send coworking control panel"""
    cw_status: CoworkingStatus = coworking.get_status()
    is_cw_open: bool = coworking.get_status() == CoworkingStatus.open
    cw_binary_status: bool = cw_status in [CoworkingStatus.open, CoworkingStatus.closed]
    markup: InlineKeyboardMarkup = InlineKeyboardMarkup()
    if cw_binary_status:
        if cw_status == CoworkingStatus.open:
            markup.add(InlineKeyboardButton(btntext.CLOSE_COWORKING, callback_data='coworking_close'))
        else:
            markup.add(InlineKeyboardButton(btntext.OPEN_COWORKING, callback_data='coworking_open'))
        markup.add(InlineKeyboardButton(btntext.EVENT_OPEN_COWORKING, callback_data='coworking_event_open'))
        markup.add(InlineKeyboardButton(btntext.TEMP_CLOSE_COWORKING, callback_data='coworking_temp_close'))
    else:
        markup.add(InlineKeyboardButton(btntext.OPEN_COWORKING, callback_data='coworking_open'))
        markup.add(InlineKeyboardButton(btntext.CLOSE_COWORKING, callback_data='coworking_close'))
        if cw_status == CoworkingStatus.temp_closed:
            markup.add(InlineKeyboardButton(btntext.EVENT_OPEN_COWORKING, callback_data='coworking_event_open'))
        elif cw_status == CoworkingStatus.event_open:
            markup.add(InlineKeyboardButton(btntext.TEMP_CLOSE_COWORKING, callback_data='coworking_temp_close'))
    if not coworking.is_responsible(cmessage.from_user.id):
        markup.add(InlineKeyboardButton(btntext.COWORKING_TAKE_RESPONSIBILITY, callback_data='coworking_take_responsibility'))
    await conv_call_to_msg(cmessage).reply(replies.coworking_control(cw_status, coworking.get_responsible_uname()), reply_markup=markup)

# region Coworking administration
@dp.callback_query_handler(lambda c: c.data == 'trim_coworking_status_log')
@dp.message_handler(debug_dec, admin_only, commands=['trim_coworking_status_log'])
async def trim_coworking_status_log(message: Union[types.CallbackQuery, types.Message]) -> None:
    """Trim coworking log"""
    limit = 10 # TODO: make this configurable
    coworking.trim_log(limit=limit)
    await conv_call_to_msg(message).reply(f"Лог статуса коворкинга урезан; последние {limit} записей сохранены")

@dp.callback_query_handler(lambda c: c.data == 'coworking_take_responsibility')
async def coworking_take_responsibility(cmessage: Union[types.CallbackQuery, types.Message]) -> None:
    """Take responsibility for coworking status"""
    message = conv_call_to_msg(cmessage)
    if coworking.is_responsible(cmessage.from_user.id):
        await message.reply(replies.coworking_status_already_responsible())
        return
    db.coworking_status_set_uid_responsible(cmessage.from_user.id)
    await message.reply(replies.coworking_status_now_responsible())

@dp.callback_query_handler(lambda c: c.data == 'coworking_open')
@dp.message_handler(debug_dec, admin_only, commands=['coworking_open'])
async def coworking_open(message: types.Message) -> None:
    """Set coworking status to open"""
    if coworking.get_status() == CoworkingStatus.open:
        await conv_call_to_msg(message).reply("Коворкинг уже открыт")
        return
    coworking.open(message.from_user.id)
    await send_coworking_notifications(CoworkingStatus.open)
    await conv_call_to_msg(message).reply("Коворкинг теперь открыт")
    log.info(f"Coworking opened by {message.from_user.id}")

@dp.callback_query_handler(lambda c: c.data == 'coworking_close')
@dp.message_handler(debug_dec, admin_only, commands=['coworking_close'])
async def coworking_close(message: types.Message) -> None:
    """Set coworking status to closed"""
    if coworking.get_status() == CoworkingStatus.closed:
        await conv_call_to_msg(message).reply("Коворкинг уже закрыт")
        return
    coworking.close(message.from_user.id)
    await send_coworking_notifications(CoworkingStatus.closed)
    await conv_call_to_msg(message).reply("Коворкинг теперь закрыт")
    log.info(f"Coworking closed by {message.from_user.id}")

@dp.callback_query_handler(lambda c: c.data == 'coworking_temp_close')
@dp.message_handler(debug_dec, admin_only, commands=['coworking_temp_close'])
async def coworking_temp_close_stage0(message: types.Message, state: FSMContext) -> None:
    """Set coworking status to temporarily closed"""
    if coworking.get_status() == CoworkingStatus.temp_closed:
        await conv_call_to_msg(message).reply(f"Коворкинг уже временно закрыт\n\n{replies.cancel_action()}")
        return
    # Set AdminCoworkingTempCloseFlow state
    await state.set_state(AdminCoworkingTempCloseFlow.delta.state)
    # coworking.temp_close(message.from_user.id)
    # await send_coworking_notifications(CoworkingStatus.closed)
    # await message.reply("Коворкинг теперь временно закрыт")
    # log.info(f"Coworking temporarily closed by {message.from_user.id}")
    await conv_call_to_msg(message).reply(f"На какое время закрыть коворкинг? (в минутах; можно ввести любое целое число)\n\n{replies.cancel_action()}",
                        reply_markup=nav.coworkingTempCloseDeltaMenu)

@dp.message_handler(debug_dec, admin_only, state=AdminCoworkingTempCloseFlow.delta.state)
async def coworking_temp_close_stage1(message: types.Message, state: FSMContext) -> None:
    """Set coworking status to temporarily closed"""
    if coworking.get_status() == CoworkingStatus.temp_closed:
        await message.reply(f"Коворкинг уже временно закрыт\n\n{replies.cancel_action()}")
        return
    # Get delta
    try:
        delta = int(message.text)
    except ValueError:
        await message.reply(f"Неверный формат! Попробуй еще раз\n\n{replies.cancel_action()}")
        return
    # Validate delta value
    if delta > 60:
        await message.reply(f"Коворкинг будет закрыт слишком долго! Введи значение от 5 до 60 минут или закрой его\n\n{replies.cancel_action()}")
        return
    elif delta < 5:
        await message.reply(f"Слишком маленький перерыв! Введи значение от 5 до 60 минут или закрой коворкинг\n\n{replies.cancel_action()}")
        return
    # Save delta
    await state.update_data(delta=delta)
    # Set AdminCoworkingTempCloseFlow state
    await state.set_state(AdminCoworkingTempCloseFlow.confirm.state)
    # Send message
    await message.reply("Подтвердите введенные данные", reply_markup=nav.confirmMenu)

@dp.message_handler(debug_dec, admin_only, state=AdminCoworkingTempCloseFlow.confirm.state)
async def coworking_temp_close_stage2(message: types.Message, state: FSMContext) -> None:
    """Set coworking status to temporarily closed"""
    if coworking.get_status() == CoworkingStatus.temp_closed:
        await message.reply(f"Коворкинг уже временно закрыт\n\n{replies.cancel_action()}")
        return
    # Check confirmation
    if message.text != btntext.CONFIRM:
        await message.reply("Действие отменено")
        await state.finish()
        return
    # Get delta
    data = await state.get_data()
    delta: int = data['delta']
    # Temporarily close coworking
    coworking.temp_close(message.from_user.id, delta_mins=delta)
    await send_coworking_notifications(CoworkingStatus.temp_closed, delta_mins=delta)
    await message.reply("Коворкинг теперь временно закрыт",
                        reply_markup=get_main_keyboard(message))
    log.info(f"Coworking temporarily closed by {message.from_user.id} for {delta} minutes")
    await state.finish()

@dp.callback_query_handler(lambda c: c.data == 'coworking_event_open')
@dp.message_handler(debug_dec, admin_only, commands=['coworking_event_open'])
async def coworking_event_open(message: types.Message) -> None:
    """Set coworking status to opened for an event"""
    if coworking.get_status() == CoworkingStatus.event_open:
        await conv_call_to_msg(message).reply("Коворкинг уже открыт (с предупреждением о проведении мероприятия)")
        return
    coworking.close(message.from_user.id)
    await send_coworking_notifications(CoworkingStatus.closed)
    await conv_call_to_msg(message).reply("Коворкинг теперь открыт (с предупреждением о проведении мероприятия)")
    log.info(f"Coworking opened for an event by {message.from_user.id}")

@dp.message_handler(debug_dec, admin_only, commands=['get_coworking_status_log'])
async def get_coworking_status_log(message: types.Message) -> None:
    """Get coworking status log"""
    await message.reply(coworking.get_log_str())

@dp.message_handler(debug_dec, admin_only, commands=['update_admin_kb'])
async def update_admin_kb(message: types.Message) -> None:
    """Update admin menu"""
    admins = db.get_admin_chats()
    for admin in admins:
        bot.send_message(admin, "Клавиатура администратора обновлена", reply_markup=get_main_keyboard(message))
        log.debug(f"Admin keyboard updated for {admin} by {message.from_user.id}")
    log.info(f"Admin keyboard updated by {message.from_user.id} for {len(admins)} administrators")
    await message.reply(replies.menu_updated_reply(len(admins), admins_only=True))
# endregion

# region Broadcast
@dp.message_handler(debug_dec, admin_only, commands=['broadcast'])
async def admin_broadcast_stage0(message: types.Message, state: FSMContext) -> None:
    await message.reply(f"Введите текст для рассылки\n\n{replies.cancel_action()}")
    await state.set_state(AdminBroadcast.message.state)

@dp.message_handler(debug_dec, admin_only, state=AdminBroadcast.message.state)
async def admin_broadcast_stage1(message: types.Message, state: FSMContext) -> None:
    await state.update_data(message=message.text)
    await message.reply(f"Выберите ширину рассылки\n\n{replies.cancel_action()}", reply_markup=nav.adminBroadcastScopeMenu)
    await state.set_state(AdminBroadcast.scope.state)

@dp.message_handler(debug_dec, admin_only, state=AdminBroadcast.scope.state)
async def admin_broadcast_stage2(message: types.Message, state: FSMContext) -> None:
    await state.update_data(scope=message.text)
    state_data = await state.get_data()
    await message.reply(f"Подтвердите рассылку\nТекст рассылки:\n\"\"\"{state_data['message']}\"\"\"\n\n{replies.cancel_action()}", reply_markup=nav.confirmMenu)
    await state.set_state(AdminBroadcast.confirm.state)

@dp.message_handler(debug_dec, admin_only, state=AdminBroadcast.confirm.state)
async def admin_broadcast_stage3(message: types.Message, state: FSMContext) -> None:
    # Check if user confirmed the broadcast
    if message.text != btntext.CONFIRM:
        message.reply("Рассылка отменена")
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
    await broadcast(state_data['message'], scope)
    log.info(f"Admin {message.from_user.id} broadcasted message to scope {scope}\nMessage:\n\"\"\"\n{state_data['message']}\n\"\"\"")
    await state.finish()
# endregion
# endregion

# region Administration
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
    await message.reply(f"Выберите группу\n\n{replies.cancel_action()}", reply_markup=keyboard)
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
        await message.reply("I encountered an exception! Details below:\n\n" + str(exc))
        return
    if not db.is_superadmin(message.from_user.id):
        await message.reply(replies.permission_denied(),
                            reply_markup=get_main_keyboard(message))
        await state.finish()
        return
    try:
        db.set_user_group(user_id, group_id)
    except (DataError, AttributeError) as exc:
        await message.reply(f"Invalid data sent to DB. Please try again.\n\nFull error:\n{exc}")
        await state.finish()
        return
    await message.reply(replies.user_group_changed(), reply_markup=get_main_keyboard(message))
    log.info(f"User {message.from_user.id} changed user {user_id} group to {group_id}")
    await state.finish()

@dp.message_handler(debug_dec, admin_only, commands=['get_notif_db'])
async def get_notif_db(message: types.Message) -> None:
    """Get notification database"""
    await message.reply(db.get_coworking_notification_chats_str())

@dp.message_handler(debug_dec, admin_only, commands=['stats'])
async def get_stats(message: types.Message) -> None:
    """Get stats"""
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text=btntext.TRIM_COWORKING_LOG, callback_data="trim_coworking_status_log"))
    await message.reply(replies.stats(db.get_stats()), reply_markup=markup)
# endregion

# region User Data
@dp.message_handler(debug_dec, commands=['bio'])
async def user_data_get_bio(message: types.Message) -> None:
    """Get user bio"""
    await message.reply(db.get_user_data_bio(message.from_user.id))

@dp.message_handler(debug_dec, commands=['resume'])
async def user_data_get_resume(message: types.Message) -> None:
    """Get user resume"""
    await message.reply(db.get_user_data_resume(message.from_user.id))

@dp.callback_query_handler(lambda c: c.data == 'edit_profile')
async def edit_profile(call: types.CallbackQuery) -> None:
    """Edit user profile"""
    fields = list(db.get_user_data_short(call.from_user.id).keys())
    field_names = replies.profile_fields()
    keyboard = types.InlineKeyboardMarkup(resize_keyboard=True)
    for key in fields:
        if key == 'uid':
            continue
        keyboard.add(types.InlineKeyboardButton(field_names[key], callback_data=f'edit_profile_{key}'))
    await call.message.edit_text(replies.profile_info(db.get_user_data_short(call.from_user.id)),
                                 reply_markup=keyboard)
    await call.message.reply("Что изменим?", reply_markup=nav.inlCancelMenu)
# endregion

# region Plaintext answers in groups (chats/superchats)
@dp.message_handler(groups_only, debug_dec, commands=['plaintext'])
async def plaintext_answers_toggle(message: types.Message):
    """Toggle plaintext answers boolean in database"""
    is_grp_admin = await is_group_admin(message)
    if not is_grp_admin:
        await message.reply(replies.permission_denied())
        return
    status = db.toggle_message_answers_status(message.chat.id)
    await message.reply(replies.plaintext_answers_reply(status, toggled=True))

@dp.message_handler(debug_dec, groups_only, commands=['plaintext_status'])
async def plaintext_answers_status(message: types.Message):
    """Get plaintext answers boolean status"""
    status = db.get_message_answers_status(message.chat.id)
    await message.reply(replies.plaintext_answers_reply(status, toggled=False))
# endregion

# region Fix keyboard !TODO: FIX
@dp.message_handler(commands=['fix'])
async def fix_keyboard(message: types.Message) -> None:
    """Fix keyboard"""
    msg = await bot.send_message(message.from_user.id, "Чиним клавиатуру...", reply_markup=ReplyKeyboardRemove())
    await asyncio.sleep(0.5)
    await msg.edit_reply_markup(get_main_keyboard(message))
    await msg.edit_text("Починили клавиатуру!")

# endregion

# region Debug
@dp.message_handler(admin_only, debug_dec, commands=['debug_cw'])
async def debug_cw(message: types.Message) -> None:
    """Debug coworking"""
    await message.reply(db.get_coworking_notification_chats())
# endregion

# region Club information
@dp.callback_query_handler(lambda c: c.data in [i+'_club_info' for i in ['ctf', 'hackathon', 'design', 'gamedev', 'robotics']])
async def club_info(call: types.CallbackQuery) -> None:
    """Club info"""
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
    except exceptions.MessageNotModified:
        log.debug(f"User {call.from_user.id} tried to request the same club info ({club})")
# endregion

# region Credits
@dp.callback_query_handler(lambda c: c.data == 'credits')
async def credits(call: types.CallbackQuery) -> None:
    """Send credits"""
    await call.message.reply(replies.credits(),
                             reply_markup=get_main_keyboard(call),
                             parse_mode=ParseMode.MARKDOWN)
# endregion

# region Moved from Normal messages
@dp.message_handler(debug_dec, commands=['profile'])
@dp.message_handler(debug_dec, lambda message: message.text == btntext.PROFILE_INFO)
async def profile_info(message: types.Message) -> None:
    if message.chat.type == 'group':
        await message.reply(replies.profile_info_only_in_pm())
        return
    await bot.send_message(message.from_user.id,
                            replies.profile_info(db.get_user_data_short(message.from_user.id)),
                            reply_markup=nav.inlProfileMenu)

@dp.message_handler(debug_dec, lambda message: message.text == btntext.COWORKING_STATUS)
async def coworking_status_reply(message: types.Message) -> None:
    try:
        status = coworking.get_status()
        if status == CoworkingStatus.temp_closed:
            await message.reply(replies.coworking_status_reply(status,
                                                               responsible_uname=db.get_coworking_responsible_uname(),
                                                               delta_mins=coworking.get_delta()),
                                reply_markup=get_main_keyboard(message))
        else:
            await message.reply(replies.coworking_status_reply(status,
                                                               responsible_uname=db.get_coworking_responsible_uname()),
                                reply_markup=get_main_keyboard(message))
    except Exception as exc:
        log.error(f"Error while getting coworking status: {exc}")

@dp.message_handler(debug_dec, lambda message: message.text == btntext.HELP_ME)
@dp.message_handler(commands=['help'])
async def help_menu_reply(message: types.Message) -> None:
    if message.chat.id != message.from_user.id:  # Avoid sending the help menu in groups
        return
    are_notifications_on = db.get_coworking_notifications(message.chat.id)
    inlHelpMenu = InlineKeyboardMarkup(resize_keyboard=True)
    inlHelpMenu.add(InlineKeyboardButton(f"{'Выключить' if are_notifications_on else 'Включить'} уведомления о статусе коворкинга (сейчас {'включены 🟢' if are_notifications_on else 'выключены 🔴'})",
                                         callback_data='toggle_coworking_notifications'))
    inlHelpMenu.add(InlineKeyboardButton(btntext.CREDITS,
                                         callback_data='credits'))
    await message.reply(replies.help_message(),
                        reply_markup=inlHelpMenu)
# endregion

# Normal messages
@dp.message_handler()
async def answer(message: types.Message) -> None:
    """Answer to random messages and messages from buttons"""
    if not db.is_uname_set(message.from_user.id):  # TODO: Measure performance hit
        if not chat_is_group(message):
            if db.does_user_exist(message.from_user.id):
                db.set_uname(message.from_user.id, message.from_user.username)
            else:
                message.reply(replies.please_click_start())
    # Menus
    text_lower = message.text.lower()

    # Plaintext message answers — checking db value for ChatSettings.message_answers_enabled
    if chat_is_group(message):
        if not db.get_message_answers_status(message.chat.id):
            log.debug(f"Received a message in a group, but plaintext_message_answers is False for {message.chat.id}")
            return

    if any(word in text_lower for word in ['коворк', 'кв']) and any(word in text_lower for word in ['статус', 'открыт', 'закрыт']):
        await message.reply(replies.coworking_status(coworking.get_status()),
                            reply_markup=get_main_keyboard(message))
    elif message.text == btntext.CLUBS_BTN:
        await message.reply(replies.club_info_general(),
                            reply_markup=nav.inlClubsMenu)
# endregion

# region StartUp
def run() -> None:
    loop = asyncio.get_event_loop()
    # loop.create_task(coworking_status_checker(datetime.strptime('2021-09-01 02:00:00', '%Y-%m-%d %H:%M:%S'),
    #                                           datetime.strptime('2021-09-01 17:30:00', '%Y-%m-%d %H:%M:%S'),
    #                                           sleep=10,
    #                                           dry_run=True))
    log.info('Starting AIOgram...')
    executor.start_polling(dp, skip_updates=True)
    log.info('AIOgram stopped successfully')
# endregion
