# region Regular dependencies
import os
import logging                               # Logging events
import asyncio                               # Asynchronous sleep()
from datetime import datetime
from typing import Optional, Union, List
from aiogram import Bot, Dispatcher          # Telegram bot API
from aiogram import executor, types          # Telegram API
from aiogram.types.message import ParseMode  # Send Markdown-formatted messages
from aiogram.dispatcher.filters.builtin import CommandStart
from aiogram.dispatcher.filters import ChatTypeFilter
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.utils.exceptions import MessageNotModified
from aiogram.utils import exceptions
from sqlalchemy.exc import DataError
from logging import Logger

# endregion
# region Local dependencies
import modules.bot.tools as bot_tools           # Bot tools
from modules import markup as nav           # Bot menus
from modules import btntext                 # Telegram bot button text
from modules import replies                 # Telegram bot information output
from modules.coworking import Manager as CoworkingManager  # Coworking space information
from modules import replies                 # Telegram bot information output
from modules.db import DBManager            # Operations with sqlite db
from modules.models import CoworkingStatus, Skill
from modules.bot.coworking import BotCoworkingFunctions  # Bot coworking-related functions
from modules.bot.scheduled import BotScheduledFunctions  # Bot scheduled functions (recurring)
from modules.bot.broadcast import BotBroadcastFunctions  # Bot broadcast functions
from modules.bot.generic import BotGenericFunctions      # Bot generic functions
from modules.bot.states import *
#from modules.buttons import coworking as cwbtn  # Coworking action buttons (admin)
from modules.bot import decorators as dp  # Bot decorators
from modules.markup import get_skill_inl_kb, get_profile_edit_fields_kb
# endregion

# region Passed by setup()
db: DBManager = None  # type: ignore
bot: Bot = None  # type: ignore
log: Logger = None  # type: ignore
bot_generic: BotGenericFunctions = None  # type: ignore
# endregion

# region Lambda functions
debug_dec = lambda message: log.debug(f'User {message.from_user.id} from \
chat {message.chat.id} called command `{message.text}`') or True
admin_only = lambda message: db.is_admin(message.from_user.id)
groups_only = lambda message: message.chat.type in ['group', 'supergroup']
# endregion


@dp.message_handler(commands=['profile'])
@dp.message_handler(lambda message: message.text == btntext.PROFILE_INFO)
async def profile_info(message: types.Message) -> None:
    """Send user profile info and edit buttons."""
    if message.chat.type == 'group':
        await message.answer(replies.profile_info_only_in_pm())
        return
    try:
        await bot.send_message(message.from_user.id,
                               replies.profile_info(db.get_user_data(message.from_user.id)),
                               reply_markup=nav.inlProfileMenu)
    except TypeError:
        await bot.send_message(message.from_user.id,
                               replies.please_start_bot())


@dp.message_handler(commands=['bio'])
async def user_data_get_bio(message: types.Message) -> None:
    """Get user bio."""
    await message.answer(db.get_user_data_bio(message.from_user.id))


@dp.message_handler(commands=['resume'])
async def user_data_get_resume(message: types.Message) -> None:
    """Get user resume."""
    await message.answer(db.get_user_data_resume(message.from_user.id))


@dp.callback_query_handler(lambda c: c.data == 'profile:edit')
async def edit_profile(call: types.CallbackQuery, secondary_run: bool = False) -> None:
    """Edit user profile."""
    keyboard = get_profile_edit_fields_kb()
    if not secondary_run:
        await call.answer()
        await call.message.edit_text(replies.profile_info(db.get_user_data(call.from_user.id)),
                                     reply_markup=keyboard)
    else:
        await bot.send_message(call.from_user.id,
                               replies.profile_info(db.get_user_data(call.from_user.id)),
                               reply_markup=keyboard)
    mkb_remove = await call.message.answer("Убираю основную клавиатуру...", reply_markup=ReplyKeyboardRemove())
    await mkb_remove.delete()


@dp.callback_query_handler(lambda c: c.data.startswith('profile:edit:') and
                           not c.data.startswith('profile:edit:skill:') and
                           not c.data == 'profile:edit:done')
async def edit_profile_action(call: types.CallbackQuery, state: FSMContext) -> None:
    """Edit user profile - select action."""
    await call.answer()
    user_data = db.get_user_data(call.from_user.id)
    await state.update_data(profile_call=call)
    fn = lambda x: f'profile:edit:{x}'
    if call.data == fn('first_name'):
        await call.message.edit_text(replies.profile_edit_first_name(user_data['first_name'],
                                                               user_data['last_name']))
        await state.set_state(UserEditProfile.first_name)
    elif call.data == fn('last_name'):
        await call.message.edit_text(replies.profile_edit_last_name(user_data['first_name'],
                                                            user_data['last_name']))
        await state.set_state(UserEditProfile.last_name)
    elif call.data == fn('birthday'):
        await call.message.edit_text(replies.profile_edit_birthday(user_data['birthday']))
        await state.set_state(UserEditProfile.birthday)
    elif call.data == fn('email'):
        await call.message.edit_text(replies.profile_edit_email(user_data['email']))
        await state.set_state(UserEditProfile.email)
    elif call.data == fn('phone'):
        await call.message.edit_text(replies.profile_edit_phone(user_data['phone']))
        await state.set_state(UserEditProfile.phone)
    elif call.data == fn('skills'):
        await edit_profile_skills(call, state, manual_run=True)
    else:
        await bot.send_message(call.from_user.id, f"Field is not editable yet: {call.data}")


@dp.callback_query_handler(lambda c: c.data == 'profile:edit:done')
async def edit_profile_done(call: types.CallbackQuery, state: FSMContext) -> None:
    """Edit user profile (Original state)."""
    await state.finish()
    await call.answer()
    await call.message.edit_text(replies.profile_info(db.get_user_data(call.from_user.id)),
                                 reply_markup=nav.inlProfileMenu)
    await call.message.answer("Восстанавливаю основную клавиатуру...", reply_markup=bot_generic.get_main_keyboard(call.from_user.id))


@dp.callback_query_handler(lambda c: c.data.startswith('profile:edit:skill:'))
@dp.callback_query_handler(state=UserEditProfile.skills)
async def edit_profile_skills(call: types.CallbackQuery,
                              state: FSMContext,
                              manual_run: bool = False,
                              message_to_be_edited: types.Message = None) -> None:
    """Edit user profile skills (loops)."""
    if isinstance(call, types.CallbackQuery):
        await call.answer()
    """Edit user profile skills"""
    await state.finish()
    await state.set_state(UserEditProfile.skills)
    if not manual_run and call.data == 'profile:edit:skill:done':
        await call.answer()
        await call.message.edit_text(replies.profile_info(db.get_user_data(call.from_user.id)),
                                     reply_markup=get_profile_edit_fields_kb())
        await state.finish()
        return
    if not manual_run:
        split = call.data.split(':')
        action = split[3]
        skill = Skill[split[4]]
        if action == 'add':
            db.add_user_skills(call.from_user.id, skill)
        elif action == 'remove':
            db.remove_user_skill(call.from_user.id, skill)
    user_data = db.get_user_data(call.from_user.id)
    keyboard = get_skill_inl_kb(user_data['skills'])
    cmessage = call.message if isinstance(call, types.CallbackQuery) else call
    if not message_to_be_edited:
        await cmessage.edit_text(replies.profile_edit_skills(), reply_markup=keyboard)
    else:
        await message_to_be_edited.edit_text(replies.profile_edit_skills(), reply_markup=keyboard)


@dp.message_handler(state=UserEditProfile.first_name)
async def edit_profile_first_name(message: types.Message, state: FSMContext):
    """Edit user profile first name."""
    profile_call = (await state.get_data())['profile_call']
    await state.update_data(first_name=message.text)
    db.set_user_first_name(message.from_user.id, message.text)
    await profile_call.message.edit_text(replies.profile_info(db.get_user_data(profile_call.from_user.id)),
                                         reply_markup=get_profile_edit_fields_kb())
    await message.delete()
    await state.finish()


@dp.message_handler(state=UserEditProfile.last_name)
async def edit_profile_last_name(message: types.Message, state: FSMContext):
    """Edit user profile last name."""
    profile_call = (await state.get_data())['profile_call']
    await state.update_data(last_name=message.text)
    db.set_user_last_name(message.from_user.id, message.text)
    await profile_call.message.edit_text(replies.profile_info(db.get_user_data(profile_call.from_user.id)),
                                         reply_markup=get_profile_edit_fields_kb())
    await message.delete()
    await state.finish()


@dp.message_handler(state=UserEditProfile.birthday)
async def edit_profile_birthday(message: types.Message, state: FSMContext):
    """Edit user profile date of birth."""
    profile_call = (await state.get_data())['profile_call']
    try:
        birthday = datetime.strptime(message.text, "%d.%m.%Y")
    except ValueError:
        await message.delete()
        try:
            await profile_call.message.edit_text(replies.invalid_date_try_again())
        except MessageNotModified:
            pass
        return
    await state.update_data(birthday=birthday)
    db.set_user_birthday(message.from_user.id, birthday)
    await profile_call.message.edit_text(replies.profile_info(db.get_user_data(profile_call.from_user.id)),
                                         reply_markup=get_profile_edit_fields_kb())
    await message.delete()
    await state.finish()


@dp.message_handler(state=UserEditProfile.email)
async def edit_profile_email(message: types.Message, state: FSMContext):
    """Edit user profile email."""
    profile_call = (await state.get_data())['profile_call']
    try:
        db.set_user_email(message.from_user.id, message.text)
    except ValueError:
        await message.delete()
        try:
            await profile_call.message.edit_text(replies.invalid_email_try_again())
        except MessageNotModified:
            pass
        return
    await profile_call.message.edit_text(replies.profile_info(db.get_user_data(profile_call.from_user.id)),
                                         reply_markup=get_profile_edit_fields_kb())
    await message.delete()
    await state.finish()


@dp.message_handler(state=UserEditProfile.phone)
async def edit_profile_phone(message: types.Message, state: FSMContext):
    """Edit user profile phone."""
    profile_call = (await state.get_data())['profile_call']
    try:
        db.set_user_phone(message.from_user.id, message.text)
    except ValueError:
        await message.delete()
        try:
            await profile_call.message.edit_text(replies.invalid_phone_try_again())
        except MessageNotModified:
            pass
        return
    await profile_call.message.edit_text(replies.profile_info(db.get_user_data(profile_call.from_user.id)),
                                         reply_markup=get_profile_edit_fields_kb())
    await message.delete()
    await state.finish()


# region Profile setup flow (full profile info)
@dp.callback_query_handler(lambda call: call.data == 'profile:setup')
async def profile_setup(call: types.CallbackQuery):
    """Profile setup."""
    await call.answer()
    await call.message.answer(replies.profile_setup_first_name(),
                              reply_markup=nav.inlCancelMenu)
    mkb_remove = await call.message.answer("Убираю основную клавиатуру...", reply_markup=ReplyKeyboardRemove())
    await mkb_remove.delete()
    await UserProfileSetup.first_name.set()


@dp.message_handler(state=UserProfileSetup.first_name)
async def profile_setup_first_name(message: types.Message, state: FSMContext):
    """Profile setup first name."""
    await state.update_data(first_name=message.text)
    db.set_user_first_name(message.from_user.id, message.text)
    await message.answer(replies.profile_setup_last_name(message.text),
                         reply_markup=nav.inlCancelMenu)
    await state.set_state(UserProfileSetup.last_name)


@dp.message_handler(state=UserProfileSetup.last_name)
async def profile_setup_last_name(message: types.Message, state: FSMContext):
    """Profile setup last name."""
    await state.update_data(last_name=message.text)
    db.set_user_last_name(message.from_user.id, message.text)
    await message.answer(replies.profile_setup_birthday(message.text),
                         reply_markup=nav.inlCancelMenu)
    await state.set_state(UserProfileSetup.birthday)


@dp.message_handler(state=UserProfileSetup.birthday)
async def profile_setup_birthday(message: types.Message, state: FSMContext):
    """Profile setup birthday."""
    try:
        birthday = datetime.strptime(message.text, "%d.%m.%Y")
    except ValueError:
        await message.answer(replies.invalid_date_try_again())
        return
    db.set_user_birthday(message.from_user.id, birthday)
    await message.answer(replies.profile_setup_email(birthday),
                         reply_markup=nav.inlCancelMenu)
    await state.set_state(UserProfileSetup.email)


@dp.message_handler(state=UserProfileSetup.email)
async def profile_setup_email(message: types.Message, state: FSMContext):
    """Profile setup email."""
    try:
        db.set_user_email(message.from_user.id, message.text)
    except ValueError:
        await message.answer(replies.invalid_email_try_again())
        return
    await message.answer(replies.profile_setup_phone(message.text),
                         reply_markup=nav.inlCancelMenu)
    await state.set_state(UserProfileSetup.phone)


@dp.message_handler(state=UserProfileSetup.phone)
async def profile_setup_phone(message: types.Message, state: FSMContext):
    """Profile setup phone."""
    try:
        db.set_user_phone(message.from_user.id, message.text)
    except ValueError:
        await message.answer(replies.invalid_phone_try_again())
        return
    message_to_be_edited = await message.answer(replies.profile_setup_skills(message.text))
    await edit_profile_skills(message, state, manual_run=True,
                              message_to_be_edited=message_to_be_edited)
# endregion


def setup(dispatcher: Dispatcher,
          bot_obj: Bot,
          database: DBManager,
          logger: logging.Logger,
          broadcast: BotBroadcastFunctions,
          generic: BotGenericFunctions):
    """Setup handlers for bot."""
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
                    dispatcher.register_callback_query_handler(func,
                                                               *args,
                                                               **kwargs)
