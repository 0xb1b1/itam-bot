"Bot coworking-related functions"
#! CYCLE NOTICE: Used in . scheduled.py; . coworking.py

from typing import List
#from typing import Union
#from aiogram import types
#from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types.message import ParseMode

#from modules import btntext, replies
from modules.db import CoworkingStatus
from modules.coworking import Manager as CoworkingManager
#from modules.buttons import coworking as cwbtn  # Coworking action buttons (admin)
from modules import replies

class BotBroadcastFunctions:
    def __init__(self, bot, db, log):
        self.db = db
        self.bot = bot
        self.cwman = CoworkingManager(db)
        self.log = log

    async def broadcast(self, content: str, scope: str,
                        custom_scope: list = None,
                        is_markdown: bool = None) -> None:
        if custom_scope:
            chat_ids = custom_scope
        elif scope == 'all':
            chat_ids = self.db.get_all_chats()
        elif scope == 'admins':
            chat_ids = self.db.get_admin_chats()
        elif scope == 'users':
            chat_ids = self.db.get_user_chats()
        else:
            raise ValueError("Invalid scope")
        self.log.debug(f"Broadcasting message to {len(chat_ids)} chats: {chat_ids}")
        await self._send_broadcast(content, chat_ids, is_markdown=is_markdown)

    async def _send_broadcast(self, content: str,
                              chat_ids: List[int],
                              is_markdown: bool = None):
        for cid in chat_ids:
            try:
                await self.bot.send_message(cid, content,
                                            parse_mode=ParseMode.MARKDOWN if is_markdown else None)
            except Exception as exc:
                self.log.debug(f"Failed to send broadcast message to chat {cid}: {exc}; user probably blocked the bot")

    async def coworking(self, status: CoworkingStatus, delta_mins: int = 0):  # Prev. send_coworking_notifications
        cids = self.db.get_coworking_notification_chats()
        responsible_uname = self.db.get_coworking_responsible_uname()
        for cid in cids:
            try:
                await self.bot.send_message(cid, replies.coworking_status_changed(status,
                                                                                  responsible_uname=responsible_uname,
                                                                                  delta_mins=delta_mins))
            except Exception as exc:
                self.log.debug(f'{cid}: Failed to send message with error {exc}; user probably blocked the bot')
