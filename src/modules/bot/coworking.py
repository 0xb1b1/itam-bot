"Bot coworking-related functions"

import asyncio
from typing import Union
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types.message import ParseMode

from modules import btntext, replies
from modules import coworking
from modules.db import CoworkingStatus
from modules.coworking import Manager as CoworkingManager
from modules.buttons import coworking as cwbtn  # Coworking action buttons (admin)
from modules.bot.broadcast import BotBroadcastFunctions

class BotCoworkingFunctions:
    def __init__(self, bot, db, log):
        self.db = db
        self.bot = bot
        self.cwman = CoworkingManager(db)
        self.log = log
        self.broadcast = BotBroadcastFunctions(bot, db, log)

    def get_admin_markup(self, cmessage: Union[types.CallbackQuery, types.Message]) -> InlineKeyboardMarkup:
        cw_status: CoworkingStatus = self.cwman.get_status()
        mkup: InlineKeyboardMarkup = InlineKeyboardMarkup(row_width=1)
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

    # region Coworking status change

    
    # endregion