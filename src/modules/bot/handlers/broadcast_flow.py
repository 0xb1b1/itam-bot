#!/usr/bin/env python3

"""Bot broadcast flow handlers."""
# region Regular dependencies
import logging
import asyncio
# from datetime import datetime
from typing import Union
from aiogram import Bot, Dispatcher
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, \
    ReplyKeyboardRemove, ContentType
# endregion

# region Local dependencies
from config import log, db
from modules import markup as nav
from modules import btntext
from modules import replies
from modules.db import DBManager
from modules.bot.broadcast import BotBroadcastFunctions
from modules.bot.generic import BotGenericFunctions
from modules.bot.states import AdminBroadcast
from modules.bot import decorators as dp
# endregion

# region Passed by setup()
bot: Bot = None  # type: ignore
bot_broadcast: BotBroadcastFunctions = None  # type: ignore
bot_generic: BotGenericFunctions = None  # type: ignore
# endregion

# region Lambda functions
debug_dec = lambda message: log.debug(f'User {message.from_user.id} \
from chat {message.chat.id} called command `{message.text}`') or True  # noqa: E731
admin_only = lambda message: db.is_admin(message.from_user.id)  # noqa: E731
groups_only = lambda message: message.chat.type in ['group', 'supergroup']  # noqa: E731
# endregion

# Message types
TYPE_TEXT = 'Текст'
TYPE_PIC = 'Картинка'
TYPE_VIDEO = 'Видео'
TYPE_VIDEO_NOTE = 'Видео-сообщение'

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
    if isinstance(message, types.CallbackQuery):
        await message.answer()
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
        await message.answer(f"Введи текст для рассылки\n\n{replies.cancel_action()}",
                             reply_markup=ReplyKeyboardRemove())
        await state.set_state(AdminBroadcast.message)  # type: ignore
    else:
        await message.answer(f"Отправь медиа-файл для рассылки\n\n{replies.cancel_action()}",
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
        await message.answer(f"Введи текст для рассылки\n\n{replies.cancel_action()}")
        await state.set_state(AdminBroadcast.message)  # type: ignore
    else:
        await state.update_data(message='')
        await message.answer(f"Выбери ширину рассылки\n\n{replies.cancel_action()}",
                             reply_markup=nav.adminBroadcastScopeMenu)
        await state.set_state(AdminBroadcast.scope)  # type: ignore


@dp.message_handler(admin_only, state=AdminBroadcast.message)
async def admin_broadcast_stage3(message: types.Message,
                                 state: FSMContext) -> None:
    """Broadcast message to all users (admin, stage 3)."""
    await state.update_data(message=message.text)
    await message.answer(f"Выбери ширину рассылки\n\n{replies.cancel_action()}",
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
    elif state_data['scope'] == btntext.YANDEX_INTERNSHIP_NOT_SIGNED_UP:
        scope = 'ya_int-not_signed_up'
    elif state_data['scope'] == btntext.YANDEX_INTERNSHIP_SIGNED_UP:
        scope = 'ya_int-signed_up'
    elif state_data['scope'] == btntext.YANDEX_INTERNSHIP_NOT_ENROLLED:
        scope = 'ya_int-not_enrolled'
    elif state_data['scope'] == btntext.YANDEX_INTERNSHIP_ENROLLED:
        scope = 'ya_int-enrolled'
    elif state_data['scope'] == btntext.YANDEX_INTERNSHIP_NOT_FLOW_STARTED:
        scope = 'ya_int-not_flow_started'
    elif state_data['scope'] == btntext.YANDEX_INTERNSHIP_FLOW_STARTED:
        scope = 'ya_int-flow_started'
    else:
        await bot.send_message(message.from_user.id, "Неверный тип рассылки")
        await state.finish()
        return
    media_type = state_data['msg_type']
    # Send broadcast
    if media_type == ContentType.TEXT:
        asyncio.get_event_loop().create_task(bot_broadcast.broadcast(state_data['message'], scope,
                                                                     ContentType.TEXT, is_html=True))
    else:
        (asyncio.get_event_loop()
         .create_task(bot_broadcast.broadcast(state_data['message'],
                                              scope,
                                              media_type,
                                              media=state_data['media_id'])))
    log.info(f"Admin {message.from_user.id} successful broadcast message to scope \
{scope}\nMessage:\n\"\"\"\n{state_data['message']}\n\"\"\"")
    await message.answer(replies.broadcast_successful(),
                         reply_markup=bot_generic.get_main_keyboard(message))
    await state.finish()


# noinspection PyProtectedMember
def setup(dispatcher: Dispatcher,
          bot_obj: Bot,
          broadcast: BotBroadcastFunctions,
          generic: BotGenericFunctions):
    """Set up handlers for admin broadcast flow."""
    global bot
    global bot_broadcast
    global bot_generic
    bot = bot_obj
    bot_broadcast = broadcast
    bot_generic = generic
    for func in globals().values():
        if hasattr(func, '_handlers'):
            for handler_type, args, kwargs in func._handlers:
                if handler_type == 'message':
                    dispatcher.register_message_handler(func, *args, **kwargs)
                elif handler_type == 'callback_query':
                    dispatcher.register_callback_query_handler(func, *args, **kwargs)
