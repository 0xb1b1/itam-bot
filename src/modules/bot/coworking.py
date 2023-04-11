"""Bot coworking-related functions."""

# import asyncio
from typing import Union
from aiogram import types
from aiogram.types import InlineKeyboardMarkup as InlKbMkup
from aiogram.types import InlineKeyboardButton as InlKbBtn
# from aiogram.types.message import ParseMode

from modules import btntext, replies
# from modules import coworking
from modules.db import CoworkingStatus
from modules.coworking import Manager as CoworkingManager
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

    def get_admin_markup(self, cmessage: Union[types.CallbackQuery,
                                               types.Message]) -> InlKbMkup:
        """Get admin markup for coworking status buttons."""
        cw_status: CoworkingStatus = self.cwman.get_status()
        mkup = InlKbMkup(row_width=1)
        if cw_status == CoworkingStatus.open:
            mkup.add(cwbtn.inl_event_open,
                     cwbtn.inl_event_close,
                     cwbtn.inl_temp_close,
                     cwbtn.inl_close)
        elif cw_status == CoworkingStatus.event_open:
            mkup.add(cwbtn.inl_open,
                     cwbtn.inl_event_close,
                     cwbtn.inl_temp_close,
                     cwbtn.inl_close)
        elif cw_status == CoworkingStatus.event_closed:
            mkup.add(cwbtn.inl_open,
                     cwbtn.inl_event_open,
                     cwbtn.inl_temp_close,
                     cwbtn.inl_close)
        elif cw_status == CoworkingStatus.temp_closed:
            mkup.add(cwbtn.inl_open,
                     cwbtn.inl_event_open,
                     cwbtn.inl_event_close,
                     cwbtn.inl_close)
        elif cw_status == CoworkingStatus.closed:
            mkup.add(cwbtn.inl_open,
                     cwbtn.inl_event_open,
                     cwbtn.inl_event_close,
                     cwbtn.inl_temp_close)
        if not self.cwman.is_responsible(cmessage.from_user.id):
            mkup.add(cwbtn.inl_take_responsibility)
        return mkup

    def get_admin_markup_full(self,
                              cmessage: Union[types.CallbackQuery,
                                              types.Message]) -> InlKbMkup:
        """Get admin markup for coworking status buttons (full version)."""
        # TODO: Document what a full markup is
        if isinstance(cmessage, types.CallbackQuery):
            cmessage = cmessage.message
        mkup: InlKbMkup = self.get_admin_markup(cmessage)
        notifs_on = self.db.get_coworking_notifications(cmessage.chat.id)
        mkup.add(cwbtn.inl_location_short)
        mkup.add(InlKbBtn(replies.toggle_coworking_notifications(notifs_on),
                          callback_data='coworking:toggle_notifications'))
        mkup.add(InlKbBtn(btntext.INL_COWORKING_STATUS_EXPLAIN,
                          callback_data='coworking:status:explain'))
        return mkup
