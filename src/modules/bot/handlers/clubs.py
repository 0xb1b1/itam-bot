#!/usr/bin/env python3


"""Bot club handlers."""
# region Regular dependencies
from aiogram import Bot, Dispatcher
from aiogram import types
from aiogram.types.message import ParseMode
from aiogram.utils import exceptions
from logging import Logger
# endregion

# region Local dependencies
from modules import markup as nav
from modules import btntext
from modules import replies
from modules.db import DBManager
from modules.bot.broadcast import BotBroadcastFunctions
from modules.bot.generic import BotGenericFunctions
from modules.bot.states import *
from modules.bot import decorators as dp
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


@dp.message_handler(lambda message: message.text == btntext.CLUBS_BTN)
async def clubs_menu(message: types.Message):
    """Send club menu."""
    await message.answer(replies.club_info_general(),
                         reply_markup=nav.inlClubsMenu)


@dp.callback_query_handler(lambda c: c.data in [i+'_club_info' for i in ['ctf',
                                                                         'hackathon',
                                                                         'design',
                                                                         'gamedev',
                                                                         'robotics']])
async def club_info(call: types.CallbackQuery) -> None:
    """Answer with requested club info."""
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
            keyboard = nav.inlClubsMenu
            # ( keyboard.add(  # url button
            #     [InlineKeyboardButton(  # Delimiter button, no action
            #         text=" ",
            #         callback_data="sinkhole")],
            #     [InlineKeyboardButton(
            #         text="YouTube",
            #         url="https://www.youtube.com/@design_now"
            #     )]
            # ))
            await call.message.edit_text(replies.design_club_info(),
                                         reply_markup=keyboard,
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


# noinspection PyProtectedMember
def setup(dispatcher: Dispatcher,
          bot_obj: Bot,
          database: DBManager,
          logger: Logger,
          broadcast: BotBroadcastFunctions,
          generic: BotGenericFunctions):
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
                    dispatcher.register_callback_query_handler(func, *args, **kwargs)
