#!/usr/bin/env python3


"""Bot department handlers."""
# region Regular dependencies
import logging
from aiogram import Bot, Dispatcher
from aiogram import types
from aiogram.types.message import ParseMode
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
# endregion

# region Local dependencies
from config import log, db
from modules import btntext
from modules.coworking import Manager as CoworkingManager
from modules import replies
from modules.db import DBManager
from modules.models import CoworkingStatus
from modules.bot.coworking import BotCoworkingFunctions
from modules.bot.broadcast import BotBroadcastFunctions
from modules.bot.generic import BotGenericFunctions
from modules.buttons import coworking as cwbtn  # Coworking mutation buttons
from modules.bot import decorators as dp
# endregion

# region Passed by setup()
bot: Bot = None  # type: ignore
bot_broadcast: BotBroadcastFunctions = None  # type: ignore
bot_generic: BotGenericFunctions = None  # type: ignore
bot_cw: BotCoworkingFunctions = None  # type: ignore
coworking: CoworkingManager = None  # type: ignore
# endregion

# region Lambda functions
debug_dec = lambda message: log.debug(f'User {message.from_user.id} from \
chat {message.chat.id} called command `{message.text}`') or True  # noqa: E731
admin_only = lambda message: db.is_admin(message.from_user.id)  # noqa: E731
groups_only = lambda message: message.chat.type in ['group', 'supergroup']  # noqa: E731
# endregion


@dp.message_handler(lambda message: message.text == btntext.COWORKING_STATUS)
@dp.message_handler(commands=['coworking_status', 'cw_status'])
async def coworking_status_reply(message: types.Message) -> None:
    # Deny access to group chats
    if bot_generic.chat_is_group(message):
        await message.answer(replies.coworking_status_only_in_pm())
        return
    if db.is_admin(message.from_user.id):
        inl_coworking_control_menu = bot_cw.get_admin_markup_full(message)
    else:
        inl_coworking_control_menu = InlineKeyboardMarkup()
        are_notifications_on = db.get_coworking_notifications(message.chat.id)
        inl_coworking_control_menu.add(cwbtn.inl_location_short)
        (inl_coworking_control_menu
         .add(InlineKeyboardButton(replies.toggle_coworking_notifications(are_notifications_on),
                                   callback_data='coworking:toggle_notifications')))
        inl_coworking_control_menu.add(InlineKeyboardButton(btntext.INL_COWORKING_STATUS_EXPLAIN,
                                                            callback_data='coworking:status:explain'))
    try:
        status = coworking.get_status()
        if status == CoworkingStatus.temp_closed:
            await message.answer(replies.coworking_status_reply(status,
                                                                responsible_uname=db.get_coworking_responsible_uname(),
                                                                delta_mins=coworking.get_delta()),
                                 reply_markup=inl_coworking_control_menu)
        else:
            await message.answer(replies.coworking_status_reply(status,
                                                                responsible_uname=db.get_coworking_responsible_uname()),
                                 reply_markup=inl_coworking_control_menu)
    except Exception as exc:
        log.error(f"Error while getting coworking status: {exc}")


@dp.callback_query_handler(lambda c: c.data == 'coworking:status:explain')
async def coworking_status_explain(call: types.CallbackQuery) -> None:
    await call.message.edit_text(replies.coworking_status_explain(coworking.get_responsible_uname()),
                                 parse_mode=ParseMode.MARKDOWN)


# noinspection PyProtectedMember
def setup(dispatcher: Dispatcher,
          bot_obj: Bot,
          broadcast: BotBroadcastFunctions,
          generic: BotGenericFunctions,
          cw: BotCoworkingFunctions):
    global bot
    global bot_broadcast
    global bot_generic
    global coworking
    global bot_cw
    bot = bot_obj
    bot_broadcast = broadcast
    bot_generic = generic
    bot_cw = cw
    coworking = CoworkingManager(db)
    for func in globals().values():
        if hasattr(func, '_handlers'):
            for handler_type, args, kwargs in func._handlers:
                if handler_type == 'message':
                    dispatcher.register_message_handler(func, *args, **kwargs)
                elif handler_type == 'callback_query':
                    dispatcher.register_callback_query_handler(func, *args, **kwargs)
