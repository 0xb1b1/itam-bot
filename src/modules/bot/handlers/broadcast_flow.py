#!/usr/bin/env python3

"""Bot broadcast flow handlers."""
# region Regular dependencies
# import os
import logging                               # Logging events
import asyncio                               # Asynchronous sleep()
# from datetime import datetime
from typing import Union
from aiogram import Bot, Dispatcher          # Telegram bot API
from aiogram import types          # Telegram API
# from aiogram.types.message import ParseMode
# from aiogram.dispatcher.filters import ChatTypeFilter
from aiogram.dispatcher import FSMContext
# from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, \
    ReplyKeyboardRemove, ContentType
# from aiogram.utils import exceptions
# from sqlalchemy.exc import DataError
from logging import Logger

# endregion
# region Local dependencies
# import modules.bot.tools as bot_tools           # Bot tools
from modules import markup as nav
from modules import btntext
from modules import replies
from modules.coworking import Manager as CoworkingManager
from modules.db import DBManager
# from modules.models import CoworkingStatus
from modules.bot.broadcast import BotBroadcastFunctions
from modules.bot.generic import BotGenericFunctions
from modules.bot.states import AdminBroadcast
# from modules.buttons import coworking as cwbtn
from modules.bot import decorators as dp
# endregion

# region Passed by setup()
db: DBManager = None  # type: ignore
bot: Bot = None  # type: ignore
log: Logger = None  # type: ignore
bot_broadcast: BotBroadcastFunctions = None  # type: ignore
bot_generic: BotGenericFunctions = None  # type: ignore
coworking: CoworkingManager = None  # type: ignore
# endregion

# region Lambda functions
debug_dec = lambda message: log.debug(f'User {message.from_user.id} \
from chat {message.chat.id} called command `{message.text}`') or True
admin_only = lambda message: db.is_admin(message.from_user.id)
groups_only = lambda message: message.chat.type in ['group', 'supergroup']
# endregion

# Message types
TYPE_TEXT = 'Текст'
TYPE_PIC = 'Картинка'
TYPE_VIDEO = 'Видео'
TYPE_VIDEO_NOTE = 'Видеосообщение'

media_types = {
    TYPE_TEXT: ContentType.TEXT,
    TYPE_PIC: ContentType.PHOTO,
    TYPE_VIDEO: ContentType.VIDEO,
    TYPE_VIDEO_NOTE: ContentType.VIDEO_NOTE
}

msgTypeBroadcastBtn = KeyboardButton(TYPE_TEXT)
picTypeBroadcastBtn = KeyboardButton(TYPE_PIC)
videoTypeBroadcastBtn = KeyboardButton(TYPE_VIDEO)
videoNoteTypeBroadcastBtn = KeyboardButton(TYPE_VIDEO_NOTE)

typeBroadcastMenu = (ReplyKeyboardMarkup(resize_keyboard=True)
                     .add(msgTypeBroadcastBtn,
                          picTypeBroadcastBtn,
                          videoTypeBroadcastBtn,
                          videoNoteTypeBroadcastBtn))


@dp.callback_query_handler(lambda c: c.data == 'admin:broadcast')
@dp.message_handler(admin_only, commands=['broadcast'])
async def admin_broadcast_stage0(message: Union[types.Message,
                                                types.CallbackQuery],
                                 state: FSMContext) -> None:
    """Broadcast message to all users (admin, stage 0)."""
    message = (message.message
               if isinstance(message, types.CallbackQuery)
               else message)
    await message.answer("Выбери тип рассылки", reply_markup=typeBroadcastMenu)
    await state.set_state(AdminBroadcast.msg_type)  # type: ignore


@dp.message_handler(admin_only, state=AdminBroadcast.msg_type)
async def admin_broadcast_stage1(message: types.Message,
                                 state: FSMContext) -> None:
    """Broadcast message to all users (admin, stage 1)."""
    await state.update_data(msg_type=media_types[message.text])
    if message.text == TYPE_TEXT:
        await message.answer(f"Введи текст для рассылки\
\n\n{replies.cancel_action()}")
        await state.set_state(AdminBroadcast.message)  # type: ignore
    else:
        await message.answer(f"Отправь медиа-файл для рассылки\
\n\n{replies.cancel_action()}",
                             reply_markup=ReplyKeyboardRemove())
        await state.set_state(AdminBroadcast.media)  # type: ignore


@dp.message_handler(admin_only,
                    state=AdminBroadcast.media,
                    content_types=[ContentType.PHOTO,
                                   ContentType.VIDEO,
                                   ContentType.VIDEO_NOTE])
async def admin_broadcast_stage2(message: types.Message,
                                 state: FSMContext) -> None:
    """Broadcast message to all users (admin, stage 2)."""
    # Get media type from message
    content_type = message.content_type
    # Get media file ID from message
    media_id = (message.photo[-1].file_id
                if content_type == ContentType.PHOTO
                else message.video.file_id
                if content_type == ContentType.VIDEO
                else message.video_note.file_id)
    await state.update_data(media_id=media_id)
    if content_type in [ContentType.PHOTO, ContentType.VIDEO]:
        await message.answer(f"Введи текст для рассылки\
\n\n{replies.cancel_action()}")
        await state.set_state(AdminBroadcast.message)  # type: ignore
    else:
        await state.update_data(message='')
        await message.answer(f"Выбери ширину рассылки\
\n\n{replies.cancel_action()}",
                             reply_markup=nav.adminBroadcastScopeMenu)
        await state.set_state(AdminBroadcast.scope)  # type: ignore


@dp.message_handler(admin_only, state=AdminBroadcast.message)
async def admin_broadcast_stage3(message: types.Message,
                                 state: FSMContext) -> None:
    """Broadcast message to all users (admin, stage 3)."""
    await state.update_data(message=message.text)
    await message.answer(f"Выбери ширину рассылки\
\n\n{replies.cancel_action()}",
                         reply_markup=nav.adminBroadcastScopeMenu)
    await state.set_state(AdminBroadcast.scope)  # type: ignore


@dp.message_handler(admin_only, state=AdminBroadcast.scope)
async def admin_broadcast_stage4(message: types.Message,
                                 state: FSMContext) -> None:
    """Broadcast message to all users (admin, stage 4)."""
    await state.update_data(scope=message.text)
    state_data = await state.get_data()
    caption_applicable = state_data['msg_type'] in [ContentType.TEXT,
                                                    ContentType.PHOTO,
                                                    ContentType.VIDEO]
    await message.answer(f"""Подтверди рассылку\nТип рассылки: \
{state_data['msg_type']}\nТекст рассылки\n\"\"\"{(state_data['message']
                                                   if caption_applicable
                                                   else 'ПУСТО')}\
\"\"\"\n\n{replies.cancel_action()}""", reply_markup=nav.confirmMenu)
    await state.set_state(AdminBroadcast.confirm)  # type: ignore


@dp.message_handler(admin_only, state=AdminBroadcast.confirm)
async def admin_broadcast_stage5(message: types.Message,
                                 state: FSMContext) -> None:
    """Broadcast message to all users (admin, stage 5)."""
    # Check if user confirmed the broadcast
    if message.text != btntext.CONFIRM:
        await message.answer("Рассылка отменена")
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
    media_type = state_data['msg_type']
    # Send broadcast
    if media_type == ContentType.TEXT:
        asyncio.get_event_loop().create_task(bot_broadcast
                                             .broadcast(state_data['message'],
                                                        scope))
    else:
        (asyncio.get_event_loop()
         .create_task(bot_broadcast.broadcast(state_data['message'],
                                              scope,
                                              media=state_data['media_id'],
                                              media_type=media_type)))
    log.info(f"Admin {message.from_user.id} broadcasted message to scope \
{scope}\nMessage:\n\"\"\"\n{state_data['message']}\n\"\"\"")
    await message.answer(replies.broadcast_successful(),
                         reply_markup=bot_generic.get_main_keyboard(message))
    await state.finish()


def setup(dispatcher: Dispatcher,
          bot_obj: Bot,
          database: DBManager,
          logger: logging.Logger,
          broadcast: BotBroadcastFunctions,
          generic: BotGenericFunctions):
    """Set up handlers for admin broadcast flow."""
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
                    dispatcher.register_callback_query_handler(func,
                                                               *args,
                                                               **kwargs)
