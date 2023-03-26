#!/usr/bin/env python3

"""Opens aiogram listener, ..."""

# region Regular dependencies
import os
# import re                                    # Graceful shutdown
# import signal                                # Graceful shutdown
import logging                               # Logging events
import asyncio                               # Asynchronous sleep()
from datetime import datetime
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
import modules.bot.tools as bot_tools           # Bot tools
from modules import markup as nav           # Bot menus
from modules import btntext                 # Telegram bot button text
from modules import replies                 # Telegram bot information output
from modules import coworking               # Coworking space information
from modules import replies                 # Telegram bot information output
from modules.db import DBManager            # Operations with sqlite db
from modules.models import CoworkingStatus  # Coworking status model
from modules.bot.help import BotHelpFunctions  # Bot help menu functions
from modules.bot.coworking import BotCoworkingFunctions  # Bot coworking-related functions
from modules.bot.scheduled import BotScheduledFunctions  # Bot scheduled functions (recurring)
from modules.bot.broadcast import BotBroadcastFunctions  # Bot broadcast functions
from modules.buttons import coworking as cwbtn  # Coworking action buttons (admin)
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

# Database
db = DBManager(log)

# region Modules
# Coworking status
coworking = coworking.Manager(db)
# endregion

# region Bot initialization
# Get Telegram API token
TELEGRAM_API_TOKEN = os.getenv('TELEGRAM_API_TOKEN')

# Initialize bot and dispatcher
bot = Bot(token=TELEGRAM_API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
# endregion

# region Post-bot-init modules
bot_help = BotHelpFunctions(bot, db, log)
bot_cw = BotCoworkingFunctions(bot, db, log)
bot_scheduled = BotScheduledFunctions(bot, db, log)
bot_broadcast = BotBroadcastFunctions(bot, db, log)
# endregion

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

class UserEditProfile(StatesGroup):
    selector = State()
    first_name = State()
    last_name = State()
    birthday = State()
    email = State()
    phone = State()
# endregion


# region Reusable functions
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
    btnHelp = KeyboardButton(btntext.HELP_MAIN)
    mainMenu = ReplyKeyboardMarkup(row_width=2).add(btnClubs,
                                                             btnCoworkingStatus,
                                                             btnProfileInfo,
                                                             btnHelp)
    if db.is_admin(message.from_user.id):
        mainMenu.add(KeyboardButton(btntext.ADMIN_BTN))
    return ReplyKeyboardRemove() if chat_is_group(message) else mainMenu
# endregion

# region Bot replies
@dp.message_handler(debug_dec, CommandStart())
async def bot_send_welcome(message: types.Message) -> None:
    """Send welcome message and init user's record in DB"""
    await message.answer(replies.welcome_message(message.from_user.first_name),
                        reply_markup=get_main_keyboard(message))
    db.add_regular_user(message.from_user.id,
                        message.from_user.username,
                        message.from_user.first_name,
                        message.from_user.last_name)

# region Cancel all states
@dp.callback_query_handler(lambda c: c.data == 'cancel', state='*')
@dp.message_handler(state='*', commands=['cancel'])
@dp.message_handler(lambda message: message.text.lower() == 'cancel' or message.text.lower() == btntext.CANCEL.lower(), state='*')
async def bot_cancel_handler(cmessage: Union[types.Message, types.CallbackQuery], state: FSMContext):
    """Allow user to cancel any action"""
    log.debug(f"User {cmessage.from_user.id} canceled an action")
    # Cancel state and inform user about it
    await state.finish()
    # Check if the type of cmessage is CallbackQuery
    if isinstance(cmessage, types.CallbackQuery):
        await bot.send_message(cmessage.message.chat.id,
                               'Действие отменено',
                               reply_markup=get_main_keyboard(cmessage))
        return
    await bot.send_message(cmessage.chat.id,
                           'Действие отменено',
                           reply_markup=get_main_keyboard(cmessage))
# endregion

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

# region Coworking notifications (user control)
@dp.callback_query_handler(lambda c: c.data == 'coworking:toggle_notifications', state='*')
@dp.message_handler(commands=['notify'])
async def bot_notify(message: Union[types.Message, types.CallbackQuery]) -> None:
    """Turn on notifications for a given chat ID"""
    message = bot_tools.conv_call_to_msg(message)
    is_grp_admin = await bot_tools.is_group_admin(message)
    if not is_grp_admin:
        await message.answer(replies.permission_denied())
        return
    current_status = db.toggle_coworking_notifications(message.chat.id)
    await message.answer(replies.coworking_notifications_on() if current_status else replies.coworking_notifications_off())

@dp.message_handler(commands=['notify_status'])
async def bot_notify_status(message: types.Message) -> None:
    """Get notification status for a given chat ID"""
    if db.get_coworking_notifications(message.chat.id):
        await message.answer(replies.coworking_notifications_on())
        return
    await message.answer(replies.coworking_notifications_off())
# endregion

# region Administration
@dp.message_handler(admin_only, lambda message: message.text == btntext.ADMIN_BTN)
@dp.message_handler(admin_only, commands=['admin'])
async def bot_admin_panel(message: types.Message) -> None:
    """Send admin panel"""
    inlAdminChangeGroupBtn = InlineKeyboardButton(btntext.INL_ADMIN_EDIT_GROUP, callback_data='change_user_group')
    inlAdminBroadcastBtn = InlineKeyboardButton(btntext.INL_ADMIN_BROADCAST, callback_data='admin:broadcast')
    markup = InlineKeyboardMarkup().add(inlAdminChangeGroupBtn,
                                        inlAdminBroadcastBtn)
    await message.answer(replies.admin_panel(coworking.get_status()), reply_markup=markup)
    log.info(f"User {message.from_user.id} opened the admin panel")

# region Coworking administration
@dp.callback_query_handler(lambda c: c.data == 'coworking:trim_log')
async def bot_trim_coworking_status_log(call: types.CallbackQuery) -> None:
    """Trim coworking log"""
    limit = 10 # TODO: make this configurable
    coworking.trim_log(limit=limit)
    await call.answer(f"Лог статуса коворкинга урезан; последние {limit} записей сохранены")

@dp.callback_query_handler(lambda c: c.data == 'coworking:take_responsibility')
async def bot_coworking_take_responsibility(call: types.CallbackQuery) -> None:
    """Take responsibility for coworking status"""
    if coworking.is_responsible(call.from_user.id):
        await call.answer(replies.coworking_status_already_responsible())
        return
    db.coworking_status_set_uid_responsible(call.from_user.id)
    await call.answer(replies.coworking_status_now_responsible())

@dp.callback_query_handler(lambda c: c.data == 'coworking:open')
async def bot_coworking_open(call: types.CallbackQuery) -> None:
    """Set coworking status to open"""
    # If the call is not from a private conversation, deny access
    if call.message.chat.type != 'private':
        await call.answer(replies.permission_denied())
        return
    # Check if the user is permitted to mutate coworking status
    if not coworking.is_trusted(call.from_user.id):
        await call.answer(replies.permission_denied())
        return
    if coworking.get_status() == CoworkingStatus.open:
        await call.answer("Коворкинг уже открыт")
        return
    coworking.open(call.from_user.id)
    asyncio.get_event_loop().create_task(bot_broadcast.coworking(CoworkingStatus.open))
    await call.answer("Коворкинг теперь открыт")
    log.info(f"Coworking opened by {call.from_user.id}")

@dp.callback_query_handler(lambda c: c.data == 'coworking:close')
async def bot_coworking_close(call: types.CallbackQuery) -> None:
    """Set coworking status to closed"""
    # If the call is not from a private conversation, deny access
    if call.message.chat.type != 'private':
        await call.answer(replies.permission_denied())
        return
    # Check if the user is permitted to mutate coworking status
    if not coworking.is_trusted(call.from_user.id):
        await call.answer(replies.permission_denied())
        return
    if coworking.get_status() == CoworkingStatus.closed:
        await call.answer("Коворкинг уже закрыт")
        return
    coworking.close(call.from_user.id)
    asyncio.get_event_loop().create_task(bot_broadcast.coworking(CoworkingStatus.closed))
    await call.answer("Коворкинг теперь закрыт")
    log.info(f"Coworking closed by {call.from_user.id}")

@dp.callback_query_handler(lambda c: c.data == 'coworking:temp_close')
async def bot_coworking_temp_close_stage0(call: types.CallbackQuery, state: FSMContext) -> None:
    """Set coworking status to temporarily closed"""
    # If the call is not from a private conversation, deny access
    if call.message.chat.type != 'private':
        await call.answer(replies.permission_denied())
        return
    # Check if the user is permitted to mutate coworking status
    if not coworking.is_trusted(call.from_user.id):
        await call.answer(replies.permission_denied())
        return
    if coworking.get_status() == CoworkingStatus.temp_closed:
        await call.answer(f"Коворкинг уже временно закрыт\n\n{replies.cancel_action()}")
        return
    # Set AdminCoworkingTempCloseFlow state
    await state.set_state(AdminCoworkingTempCloseFlow.delta.state)
    await bot.send_message(call.from_user.id,
                           f"На какое время закрыть коворкинг? (в минутах; можно ввести любое целое число)\n\n{replies.cancel_action()}",
                           reply_markup=nav.coworkingTempCloseDeltaMenu)

@dp.message_handler(admin_only, state=AdminCoworkingTempCloseFlow.delta.state)
async def bot_coworking_temp_close_stage1(message: types.Message, state: FSMContext) -> None:
    """Set coworking status to temporarily closed"""
    if coworking.get_status() == CoworkingStatus.temp_closed:
        await message.answer(f"Коворкинг уже временно закрыт\n\n{replies.cancel_action()}")
        return
    # Get delta
    try:
        delta = int(message.text)
    except ValueError:
        await message.answer(f"Неверный формат! Попробуй еще раз\n\n{replies.cancel_action()}")
        return
    # Validate delta value
    if delta > 60:
        await message.answer(f"Коворкинг будет закрыт слишком долго! Введи значение от 5 до 60 минут или закрой его\n\n{replies.cancel_action()}")
        return
    elif delta < 5:
        await message.answer(f"Слишком маленький перерыв! Введи значение от 5 до 60 минут или закрой коворкинг\n\n{replies.cancel_action()}")
        return
    # Save delta
    await state.update_data(delta=delta)
    # Set AdminCoworkingTempCloseFlow state
    await state.set_state(AdminCoworkingTempCloseFlow.confirm.state)
    # Send message
    await message.answer("Подтвердите введенные данные", reply_markup=nav.confirmMenu)

@dp.message_handler(admin_only, state=AdminCoworkingTempCloseFlow.confirm.state)
async def bot_coworking_temp_close_stage2(message: types.Message, state: FSMContext) -> None:
    """Set coworking status to temporarily closed"""
    if coworking.get_status() == CoworkingStatus.temp_closed:
        await message.answer(f"Коворкинг уже временно закрыт\n\n{replies.cancel_action()}")
        return
    # Check confirmation
    if message.text != btntext.CONFIRM:
        await message.answer("Действие отменено")
        await state.finish()
        return
    # Get delta
    data = await state.get_data()
    delta: int = data['delta']
    # Temporarily close coworking
    coworking.temp_close(message.from_user.id, delta_mins=delta)
    asyncio.get_event_loop().create_task(bot_broadcast.coworking(CoworkingStatus.temp_closed, delta_mins=delta))
    await message.answer("Коворкинг теперь временно закрыт",
                        reply_markup=get_main_keyboard(message))
    log.info(f"Coworking temporarily closed by {message.from_user.id} for {delta} minutes")
    await state.finish()

@dp.callback_query_handler(lambda c: c.data == 'coworking:event_open')
async def bot_coworking_event_open(call: types.CallbackQuery) -> None:
    """Set coworking status to opened for an event"""
    # If the call is not from a private conversation, deny access
    if call.message.chat.type != 'private':
        await call.answer(replies.permission_denied())
        return
    # Check if the user is permitted to mutate coworking status
    if not coworking.is_trusted(call.from_user.id):
        await call.answer(replies.permission_denied())
        return
    if coworking.get_status() == CoworkingStatus.event_open:
        await call.answer("Коворкинг уже открыт (с предупреждением о проведении мероприятия)")
        return
    coworking.event_open(call.from_user.id)
    asyncio.get_event_loop().create_task(bot_broadcast.coworking(CoworkingStatus.event_open))
    await call.answer("Коворкинг теперь открыт (с предупреждением о проведении мероприятия)")
    log.info(f"Coworking opened for an event by {call.from_user.id}")

@dp.callback_query_handler(lambda c: c.data == 'coworking:event_close')
async def bot_coworking_event_close(call: types.CallbackQuery) -> None:
    """Set coworking status to closed for an event"""
    # If the call is not from a private conversation, deny access
    if call.message.chat.type != 'private':
        await call.answer(replies.permission_denied())
        return
    # Check if the user is permitted to mutate coworking status
    if not coworking.is_trusted(call.from_user.id):
        await call.answer(replies.permission_denied())
        return
    if coworking.get_status() == CoworkingStatus.event_closed:
        await call.answer("Коворкинг уже закрыт на мероприятие")
        return
    coworking.event_close(call.from_user.id)
    asyncio.get_event_loop().create_task(bot_broadcast.coworking(CoworkingStatus.event_closed))
    await call.answer("Коворкинг теперь закрыт на мероприятие")
    log.info(f"Coworking closed for an event by {call.from_user.id}")

@dp.message_handler(admin_only, commands=['get_coworking_status_log'])
async def bot_get_coworking_status_log(message: types.Message) -> None:
    """Get coworking status log"""
    await message.answer(coworking.get_log_str())

@dp.message_handler(admin_only, commands=['update_admin_kb'])
async def bot_update_admin_kb(message: types.Message) -> None:
    """Update admin menu"""
    admins = db.get_admin_chats()
    for admin in admins:
        bot.send_message(admin, "Клавиатура администратора обновлена", reply_markup=get_main_keyboard(message))
        log.debug(f"Admin keyboard updated for {admin} by {message.from_user.id}")
    log.info(f"Admin keyboard updated by {message.from_user.id} for {len(admins)} administrators")
    await message.answer(replies.menu_updated_reply(len(admins), admins_only=True))
# endregion

# region Broadcast
@dp.callback_query_handler(lambda c: c.data == 'admin:broadcast')
@dp.message_handler(admin_only, commands=['broadcast'])
async def bot_admin_broadcast_stage0(message: types.Message, state: FSMContext) -> None:
    await message.answer(f"Введите текст для рассылки\n\n{replies.cancel_action()}")
    await state.set_state(AdminBroadcast.message.state)

@dp.message_handler(admin_only, state=AdminBroadcast.message.state)
async def bot_admin_broadcast_stage1(message: types.Message, state: FSMContext) -> None:
    await state.update_data(message=message.text)
    await message.answer(f"Выберите ширину рассылки\n\n{replies.cancel_action()}", reply_markup=nav.adminBroadcastScopeMenu)
    await state.set_state(AdminBroadcast.scope.state)

@dp.message_handler(admin_only, state=AdminBroadcast.scope.state)
async def bot_admin_broadcast_stage2(message: types.Message, state: FSMContext) -> None:
    await state.update_data(scope=message.text)
    state_data = await state.get_data()
    await message.answer(f"Подтвердите рассылку\nТекст рассылки:\n\"\"\"{state_data['message']}\"\"\"\n\n{replies.cancel_action()}", reply_markup=nav.confirmMenu)
    await state.set_state(AdminBroadcast.confirm.state)

@dp.message_handler(admin_only, state=AdminBroadcast.confirm.state)
async def bot_admin_broadcast_stage3(message: types.Message, state: FSMContext) -> None:
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
                         reply_markup=get_main_keyboard(message))
    await state.finish()
# endregion

@dp.callback_query_handler(lambda c: c.data == 'change_user_group')
async def bot_change_user_group_stage0(call: types.CallbackQuery, state: FSMContext) -> None:
    """Change user group, stage 0"""
    await state.set_state(AdminChangeUserGroup.user_id.state)
    await call.message.edit_text(f"Введите ID пользователя\n\n{replies.cancel_action()}")

@dp.message_handler(state=AdminChangeUserGroup.user_id)
async def bot_change_user_group_stage1(message: types.Message, state: FSMContext) -> None:
    """Change user group, stage 1"""
    user_id = message.text
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for group_name in db.get_groups_and_ids_as_dict_namekey():
        keyboard.add(types.KeyboardButton(group_name))
    await message.answer(f"Выберите группу\n\n{replies.cancel_action()}", reply_markup=keyboard)
    await state.update_data(user_id=user_id)
    await state.set_state(AdminChangeUserGroup.group_id.state)  # Also accepted: await AdminChangeUserGroup.next()

@dp.message_handler(state=AdminChangeUserGroup.group_id)
async def bot_change_user_group_stage2(message: types.Message, state: FSMContext) -> None:
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
                             reply_markup=get_main_keyboard(message))
        await state.finish()
        return
    try:
        db.set_user_group(user_id, group_id)
    except (DataError, AttributeError) as exc:
        await message.answer(f"Invalid data sent to DB. Please try again.\n\nFull error:\n{exc}")
        await state.finish()
        return
    await message.answer(replies.user_group_changed(), reply_markup=get_main_keyboard(message))
    log.info(f"User {message.from_user.id} changed user {user_id} group to {group_id}")
    await state.finish()

@dp.message_handler(admin_only, commands=['get_notif_db'])
async def bot_get_notif_db(message: types.Message) -> None:
    """Get notification database"""
    await message.answer(db.get_coworking_notification_chats_str())

@dp.message_handler(admin_only, commands=['stats'])
async def bot_get_stats(message: types.Message) -> None:
    """Get stats"""
    mkup = InlineKeyboardMarkup().add(types.InlineKeyboardButton(text=btntext.TRIM_COWORKING_LOG, callback_data="coworking:trim_log"))
    await message.answer(replies.stats(db.get_stats()), reply_markup=mkup)
# endregion

# region User Data
@dp.message_handler(commands=['bio'])
async def bot_user_data_get_bio(message: types.Message) -> None:
    """Get user bio"""
    await message.answer(db.get_user_data_bio(message.from_user.id))

@dp.message_handler(commands=['resume'])
async def bot_user_data_get_resume(message: types.Message) -> None:
    """Get user resume"""
    await message.answer(db.get_user_data_resume(message.from_user.id))

@dp.callback_query_handler(lambda c: c.data == 'edit_profile')
async def bot_edit_profile(call: types.CallbackQuery, state: FSMContext, secondary_run: bool = False) -> None:
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
async def bot_edit_profile_action(call: types.CallbackQuery, state: FSMContext) -> None:
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
async def bot_edit_profile_first_name(message: types.Message, state: FSMContext):
    """Edit user profile first name"""
    #state_data = await state.get_data()
    await state.update_data(first_name=message.text)
    db.set_user_first_name(message.from_user.id, message.text)
    await message.answer(replies.profile_edit_success())
    await state.finish()

@dp.message_handler(state=UserEditProfile.last_name)
async def bot_edit_profile_last_name(message: types.Message, state: FSMContext):
    """Edit user profile last name"""
    #state_data = await state.get_data()
    await state.update_data(last_name=message.text)
    db.set_user_last_name(message.from_user.id, message.text)
    await message.answer(replies.profile_edit_success())
    await state.finish()

@dp.message_handler(state=UserEditProfile.birthday)
async def bot_edit_profile_birthday(message: types.Message, state: FSMContext):
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
async def bot_edit_profile_email(message: types.Message, state: FSMContext):
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
async def bot_edit_profile_phone(message: types.Message, state: FSMContext):
    """Edit user profile phone"""
    #state_data = await state.get_data()
    try:
        db.set_user_phone(message.from_user.id, message.text)
    except ValueError:
        await message.answer(replies.invalid_phone_try_again())
        return
    await message.answer(replies.profile_edit_success())
    await state.finish()
# endregion

# region Plaintext answers in groups (chats/superchats)
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
# endregion

# region Fix keyboard !TODO: FIX
@dp.message_handler(commands=['fix'])
async def fix_keyboard(message: types.Message) -> None:
    """Fix keyboard"""
    await bot.send_message(message.from_user.id, "Чиним клавиатуру...", reply_markup=ReplyKeyboardRemove())
    await asyncio.sleep(0.5)
    await message.answer("Починили клавиатуру!", reply_markup=get_main_keyboard(message))
# endregion

# region Admin management of chats
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
# endregion

# region Club information
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
# endregion

# region Credits
@dp.callback_query_handler(lambda c: c.data == 'credits')
async def credits(call: types.CallbackQuery) -> None:
    """Send credits"""
    await call.message.edit_text(replies.credits(),
                                 parse_mode=ParseMode.MARKDOWN)
# endregion

# region Moved from Normal messages
@dp.message_handler(commands=['profile'])
@dp.message_handler(lambda message: message.text == btntext.PROFILE_INFO)
async def bot_profile_info(message: types.Message) -> None:
    if message.chat.type == 'group':
        await message.answer(replies.profile_info_only_in_pm())
        return
    await bot.send_message(message.from_user.id,
                            replies.profile_info(db.get_user_data_short(message.from_user.id)),
                            reply_markup=nav.inlProfileMenu)

@dp.message_handler(lambda message: message.text == btntext.COWORKING_STATUS)
@dp.message_handler(commands=['coworking_status', 'cw_status'])
async def bot_coworking_status_reply(message: types.Message) -> None:
    # Deny access to group chats
    if chat_is_group(message):
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
async def bot_coworking_status_explain(call: types.CallbackQuery) -> None:
    await call.message.edit_text(replies.coworking_status_explain(coworking.get_responsible_uname()),
                                 parse_mode=ParseMode.MARKDOWN)
# endregion

# region Help
@dp.message_handler(lambda message: message.text == btntext.HELP_MAIN)
@dp.message_handler(commands=['help'])
async def bot_help_menu(message: types.Message):
    await bot_help.main(message)

@dp.callback_query_handler(lambda c: c.data == 'coworking:location')
async def bot_coworking_location(call: types.CallbackQuery) -> None:
    await bot_help.location(call)
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
                message.answer(replies.please_click_start())
    # Menus
    text_lower = message.text.lower()

    # Plaintext message answers — checking db value for ChatSettings.message_answers_enabled
    if chat_is_group(message):
        if not db.get_message_answers_status(message.chat.id):
            log.debug(f"Received a message in a group, but plaintext_message_answers is False for {message.chat.id}")
            return

    if any(word in text_lower for word in ['коворк', 'кв']) and any(word in text_lower for word in ['статус', 'открыт', 'закрыт']):
        await message.answer(replies.coworking_status_reply(coworking.get_status(),
                                                            responsible_uname=db.get_coworking_responsible_uname()),
                             reply_markup=get_main_keyboard(message))
    elif message.text == btntext.CLUBS_BTN:
        await message.answer(replies.club_info_general(),
                             reply_markup=nav.inlClubsMenu)
# endregion

# region StartUp
def run() -> None:
    loop = asyncio.get_event_loop()
    loop.create_task(bot_scheduled.coworking_status_checker(datetime.strptime(f'2021-09-01 {os.getenv("COWORKING_OPENING_TIME", "09:00:00")}', '%Y-%m-%d %H:%M:%S'),
                                                            datetime.strptime(f'2021-09-01 {os.getenv("COWORKING_CLOSING_TIME", "19:00:00")}', '%Y-%m-%d %H:%M:%S'),
                                                            timeout=int(os.getenv('COWORKING_STATUS_WORKER_TIMEOUT', '120'))))
    log.info('Starting AIOgram...')
    executor.start_polling(dp, skip_updates=True)
    log.info('AIOgram stopped successfully')
# endregion
