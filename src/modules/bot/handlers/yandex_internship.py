#!/usr/bin/env python3

"""Yandex Internship skill."""
# region Regular dependencies
import logging                               # Logging events
import asyncio                               # Asynchronous sleep()
from typing import Union
from aiogram import Bot, Dispatcher          # Telegram bot API
from aiogram import types          # Telegram API
from aiogram.types.message import ParseMode  # Send Markdown-formatted messages
# from aiogram.dispatcher.filters.builtin import CommandStart
# from aiogram.dispatcher.filters import ChatTypeFilter
# from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
# from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, \
    InlineKeyboardButton, KeyboardButton, \
    ReplyKeyboardMarkup, ReplyKeyboardRemove
# from aiogram.utils import exceptions
from aiogram.types.chat import ChatActions
# from sqlalchemy.exc import DataError
from logging import Logger
# endregion

# region Local dependencies
# import modules.bot.tools as bot_tools
from modules import markup as nav
# from modules import btntext
from modules import replies
# from modules.coworking import Manager as CoworkingManager
from modules.db import DBManager            # Operations with sqlite db
from modules.models import Skill
from modules.bot.broadcast import BotBroadcastFunctions
from modules.bot.generic import BotGenericFunctions
from modules.bot.states import YandexInternship
# from modules.buttons import coworking as cwbtn
from modules.bot import decorators as dp
# from modules.markup import get_skill_inl_kb, get_profile_edit_fields_kb
from .replies import yandex_internship as ya_replies
from modules import stickers
# endregion

# region Passed by setup()
db: DBManager = None  # type: ignore
bot: Bot = None  # type: ignore
log: Logger = None  # type: ignore
bot_broadcast: BotBroadcastFunctions = None  # type: ignore
bot_generic: BotGenericFunctions = None  # type: ignore
# endregion

# region Lambda functions
debug_dec = lambda message: log.debug(f'User {message.from_user.id} from \
chat {message.chat.id} called command `{message.text}`') or True
admin_only = lambda message: db.is_admin(message.from_user.id)
groups_only = lambda message: message.chat.type in ['group', 'supergroup']
# endregion

# region Menues
inlStartAgree = InlineKeyboardButton("Да, я в деле",
                                     callback_data="skill:yandex_internship\
:welcome:agree")
inlStartLater = InlineKeyboardButton("Создать анкету",
                                     callback_data="skill:yandex_internship\
:welcome:later")
inlStartDisagree = InlineKeyboardButton("Не сейчас",
                                        callback_data="skill:yandex_internship\
:welcome:disagree")
inlStartMenu = InlineKeyboardMarkup(row_width=2).add(inlStartDisagree,
                                                     inlStartLater,
                                                     inlStartAgree)
# endregion


@dp.callback_query_handler(lambda c: c.data == 'skill:yandex_internship')
async def yandex_internship_start(message: Union[types.Message,
                                                 types.CallbackQuery]):
    """Handle /yandex_internship command or button press."""
    if isinstance(message, types.CallbackQuery):
        await message.answer()
        message = message.message
    # Remove previous message
    await message.delete()
    welcome = ya_replies.welcome()
    await message.answer(ya_replies.start(), reply_markup=ReplyKeyboardRemove())
    await bot.send_chat_action(message.chat.id, ChatActions.CHOOSE_STICKER)
    await asyncio.sleep(0.4)
    await bot.send_sticker(message.chat.id, stickers.YANDEX_INTERNSHIP_START)
    await bot.send_chat_action(message.chat.id, ChatActions.TYPING)
    await asyncio.sleep(0.7)
    await message.answer(welcome[0], parse_mode=ParseMode.MARKDOWN)
    await bot.send_chat_action(message.chat.id, ChatActions.TYPING)
    await asyncio.sleep(1)
    await message.answer(welcome[1], parse_mode=ParseMode.MARKDOWN)
    await bot.send_chat_action(message.chat.id, ChatActions.TYPING)
    await asyncio.sleep(1)
    await message.answer(welcome[2], parse_mode=ParseMode.MARKDOWN,
                         reply_markup=inlStartMenu)


@dp.callback_query_handler(lambda c: c.data == 'skill:yandex_internship:welcome:disagree')
async def welcome_disagree(call: types.CallbackQuery):
    """Handle user disagreement to participate in Yandex Internship."""
    await call.answer()
    # Delete three messages (call.message and two previous)
    for i in range(4):
        await bot.delete_message(call.message.chat.id,
                                 call.message.message_id - i)
        await asyncio.sleep(0.3)
    await bot.send_message(call.from_user.id, ya_replies.welcome_disagree(),
                           reply_markup=(bot_generic
                                         .get_main_keyboard(call.from_user.id)
                                         )
                           )


@dp.callback_query_handler(lambda c: c.data in ['skill:yandex_internship:welcome:' + i for i in ['agree', 'later']])
async def welcome_positive(call: types.CallbackQuery, state: FSMContext):
    """Handle user agreement to participate in Yandex Internship."""
    await call.answer()
    choice = call.data.split(':')[-1]
    await state.set_state(YandexInternship.first_name)  # type: ignore
    if choice == 'agree':
        await call.message.answer(ya_replies.welcome_agree())
        await state.update_data(agree=True)
    else:
        await call.message.answer(ya_replies.welcome_later())
        await state.update_data(agree=False)
    await bot.send_chat_action(call.message.chat.id, ChatActions.TYPING)
    await asyncio.sleep(0.5)
    await call.message.answer(ya_replies.profile_first_name(),
                              reply_markup=nav.inlCancelMenu)


@dp.message_handler(state=YandexInternship.first_name)
async def first_name(message: types.Message, state: FSMContext):
    """Set user first name."""
    db.set_user_first_name(message.from_user.id, message.text)
    await message.answer(ya_replies.profile_last_name(),
                         reply_markup=nav.inlCancelMenu)
    await state.set_state(YandexInternship.last_name)  # type: ignore


@dp.message_handler(state=YandexInternship.last_name)
async def last_name(message: types.Message, state: FSMContext):
    """Set user last name."""
    db.set_user_last_name(message.from_user.id, message.text)
    share_btn = KeyboardButton(text="Поделиться",
                               request_contact=True)
    share_kb = (ReplyKeyboardMarkup(resize_keyboard=True,
                                    one_time_keyboard=True)
                .add(share_btn))
    await message.answer(ya_replies.profile_phone(),
                         reply_markup=share_kb)
    await state.set_state(YandexInternship.phone)  # type: ignore


@dp.message_handler(state=YandexInternship.phone,
                    content_types=types.ContentType.CONTACT)
async def phone(message: types.Message, state: FSMContext):
    """Set user phone."""
    try:
        db.set_user_phone(message.from_user.id,
                          int(message.contact.phone_number))
    except ValueError:
        await message.answer(replies.invalid_phone_try_again(),
                             reply_markup=nav.inlCancelMenu)
        return
    await message.answer(ya_replies.profile_email(),
                         reply_markup=nav.inlCancelMenu)
    await state.set_state(YandexInternship.email)  # type: ignore


@dp.message_handler(state=YandexInternship.email)
async def email(message: types.Message, state: FSMContext):
    """Set user email."""
    try:
        db.set_user_email(message.from_user.id, message.text)
    except ValueError:
        await message.answer(replies.invalid_email_try_again(),
                             reply_markup=nav.inlCancelMenu)
        return
    await state.finish()
    message_to_be_edited = await message.answer(ya_replies.profile_skills())
    await skills(message, state, manual_run=True,
                 message_to_be_edited=message_to_be_edited)


@dp.callback_query_handler(state=YandexInternship.skills)
async def skills(call: Union[types.CallbackQuery, types.Message],
                 state: FSMContext,
                 manual_run: bool = False,
                 message_to_be_edited: types.Message | None = None) -> None:
    """Edit user profile skills (loops)."""
    if isinstance(call, types.CallbackQuery):
        await call.answer()
    """Edit user profile skills"""
    await state.finish()
    await state.set_state(YandexInternship.skills)  # type: ignore
    if not manual_run and call.data == 'skill:yandex_internship:setup:done':
        await call.answer()
        await bot.send_chat_action(call.message.chat.id, ChatActions.TYPING)
        await asyncio.sleep(0.2)
        await call.message.answer(ya_replies.profile_skills_done())
        await bot.send_chat_action(call.message.chat.id, ChatActions.TYPING)
        await asyncio.sleep(0.3)
        await call.message.edit_text(replies
                                     .profile_info(db.
                                                   get_user_data(call
                                                                 .from_user
                                                                 .id)))
        await bot.send_chat_action(call.message.chat.id, ChatActions.TYPING)
        await asyncio.sleep(0.7)
        await call.message.answer(ya_replies.profile_edit_done())
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
    if user_data is None:
        raise AttributeError('User data is None')
    keyboard = ya_replies.get_skill_inl_kb(user_data['skills'])
    cmessage = call.message if isinstance(call, types.CallbackQuery) else call
    if not message_to_be_edited:
        await cmessage.edit_text(replies.profile_edit_skills(),
                                 reply_markup=keyboard)
    else:
        await message_to_be_edited.edit_text(replies.profile_edit_skills(),
                                             reply_markup=keyboard)


# noinspection PyProtectedMember
def setup(dispatcher: Dispatcher,
          bot_obj: Bot,
          database: DBManager,
          logger: logging.Logger,
          broadcast: BotBroadcastFunctions,
          generic: BotGenericFunctions):
    """Set up handlers for dispatcher."""
    global bot
    global db
    global log
    global bot_broadcast
    global bot_generic
    bot = bot_obj
    bot_broadcast = broadcast
    bot_generic = generic
    log = logger
    db = database
    for func in globals().values():
        if hasattr(func, '_handlers'):
            for handler_type, args, kwargs in func._handlers:
                if handler_type == 'message':
                    dispatcher.register_message_handler(func, *args, **kwargs)
                elif handler_type == 'callback_query':
                    dispatcher.register_callback_query_handler(func,
                                                               *args,
                                                               **kwargs)
