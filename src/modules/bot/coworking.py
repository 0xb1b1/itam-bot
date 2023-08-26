#!/usr/bin/env python3

"""Bot coworking-related functions."""

# import asyncio
from typing import Union
from aiogram import types
from aiogram.types import InlineKeyboardMarkup as InlKbMarkup
from aiogram.types import InlineKeyboardButton as InlKbBtn
# from aiogram.types.message import ParseMode

from modules.static import btntext, replies
# from modules import coworking
from modules.db.db.spaces.spaces import SpaceStates
from modules.coworking import Manager as CoworkingManager  #! TODO: redo for mongo
from modules.buttons import coworking as cwbtn  # Coworking action buttons
from modules.bot.broadcast import BotBroadcastFunctions


class BotCoworkingFunctions:
    """Bot coworking-related methods."""

    def __init__(self, bot, db, log):
        """Initialize bot coworking-related methods."""
        self.db = db
        self.bot = bot
        self.cwman = CoworkingManager(db)
        self.log = log
        self.broadcast = BotBroadcastFunctions(bot, db, log)

    def get_admin_markup(self, cmessage: Union[types.CallbackQuery, types.Message]) -> InlKbMarkup:
        """Get admin markup for coworking status buttons."""
        cw_status: CoworkingStatus = self.cwman.get_status()
        markup = InlKbMarkup(row_width=1)
        if cw_status == CoworkingStatus.open:
            markup.add(cwbtn.inl_event_open,
                       cwbtn.inl_event_close,
                       cwbtn.inl_temp_close,
                       cwbtn.inl_close)
        elif cw_status == CoworkingStatus.event_open:
            markup.add(cwbtn.inl_open,
                       cwbtn.inl_event_close,
                       cwbtn.inl_temp_close,
                       cwbtn.inl_close)
        elif cw_status == CoworkingStatus.event_closed:
            markup.add(cwbtn.inl_open,
                       cwbtn.inl_event_open,
                       cwbtn.inl_temp_close,
                       cwbtn.inl_close)
        elif cw_status == CoworkingStatus.temp_closed:
            markup.add(cwbtn.inl_open,
                       cwbtn.inl_event_open,
                       cwbtn.inl_event_close,
                       cwbtn.inl_close)
        elif cw_status == CoworkingStatus.closed:
            markup.add(cwbtn.inl_open,
                       cwbtn.inl_event_open,
                       cwbtn.inl_event_close,
                       cwbtn.inl_temp_close)
        if not self.cwman.is_responsible(cmessage.from_user.id):
            markup.add(cwbtn.inl_take_responsibility)
        return markup

    def get_admin_markup_full(self, cmessage: Union[types.CallbackQuery, types.Message]) -> InlKbMarkup:
        """Get admin markup for coworking status buttons (full version)."""
        # TODO: Document what a full markup is
        if isinstance(cmessage, types.CallbackQuery):
            cmessage = cmessage.message
        markup: InlKbMarkup = self.get_admin_markup(cmessage)
        notifications_on = self.db.get_coworking_notifications(cmessage.chat.id)
        markup.add(cwbtn.inl_location_short)
        markup.add(InlKbBtn(replies.toggle_coworking_notifications(notifications_on),
                            callback_data='coworking:toggle_notifications'))
        markup.add(InlKbBtn(btntext.INL_COWORKING_STATUS_EXPLAIN,
                            callback_data='coworking:status:explain'))
        return markup
