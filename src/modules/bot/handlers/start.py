#!/usr/bin/env python3


"""Bot Start handlers."""
# region Regular dependencies
import logging
import asyncio
from typing import Union
from aiogram import Bot, Dispatcher
from aiogram import types
# from aiogram.types.message import ParseMode
from aiogram.dispatcher.filters.builtin import CommandStart
from aiogram.types import ReplyKeyboardRemove
from aiogram.types.chat import ChatActions
# endregion

# region Local dependencies
from config import log
from modules import replies
from modules.db import DBManager
from modules.bot.generic import BotGenericFunctions
from modules.bot import decorators as dp
from modules.media import stickers
# endregion

# region Passed by setup()
db: DBManager = None  # type: ignore
bot: Bot = None  # type: ignore
bot_generic: BotGenericFunctions = None  # type: ignore
# endregion

# region Lambda functions
debug_dec = lambda message: log.debug(f'User {message.from_user.id} from \
chat {message.chat.id} called command `{message.text}`') or True  # noqa: E731
admin_only = lambda message: db.is_admin(message.from_user.id)  # noqa: E731
groups_only = lambda message: message.chat.type in ['group', 'supergroup']  # noqa: E731
# endregion


@dp.callback_query_handler(lambda query: query.data == 'start')
@dp.message_handler(CommandStart())
async def bot_send_welcome(message: Union[types.Message, types.CallbackQuery], user_first_name: str = None) -> None:
    """Send welcome message and init user's record in DB"""
    if isinstance(message, types.CallbackQuery):
        message = message.message
        args = ['']
    else:
        args = message.get_args().split(',')
        user_first_name = message.from_user.first_name
    args_empty = args[0] == ''
    db.add_regular_user(message.from_user.id,
                        message.from_user.username,
                        message.from_user.first_name,
                        message.from_user.last_name)
    if args_empty:
        await message.answer(replies.welcome_message(user_first_name),
                             reply_markup=ReplyKeyboardRemove())
        await bot.send_chat_action(message.chat.id, ChatActions.TYPING)
        await asyncio.sleep(1.3)
        await message.answer(replies.welcome_message_instructions())
        await bot.send_chat_action(message.chat.id, ChatActions.CHOOSE_STICKER)
        await asyncio.sleep(0.7)
        await bot.send_sticker(message.chat.id, stickers.WELCOME)
        await bot.send_message(message.chat.id, replies.welcome_message_go(),
                               reply_markup=bot_generic.get_main_keyboard(message))
    if not args_empty:
        await message.answer(replies.start_command_found_calling_skill(),
                             reply_markup=ReplyKeyboardRemove())
        await bot.send_chat_action(message.chat.id, ChatActions.TYPING)
        await asyncio.sleep(0.5)
        # if args[0] == 'ya_int':
        #     await yandex_internship_start(message, deeplink=True)
        if False:
            pass
        else:
            await message.answer(replies.start_command_not_found())


# noinspection PyProtectedMember
def setup(dispatcher: Dispatcher,
          bot_obj: Bot,
          database: DBManager,
          generic: BotGenericFunctions):
    global bot
    global db
    global bot_generic
    bot = bot_obj
    bot_generic = generic
    db = database
    for func in globals().values():
        if hasattr(func, '_handlers'):
            for handler_type, args, kwargs in func._handlers:
                if handler_type == 'message':
                    dispatcher.register_message_handler(func, *args, **kwargs)
                elif handler_type == 'callback_query':
                    dispatcher.register_callback_query_handler(func, *args, **kwargs)
