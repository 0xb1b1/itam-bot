"""Bot coworking-related functions."""
# CYCLE NOTICE: Used in . scheduled.py; . coworking.py

from typing import List, Any
# from typing import Union
# from aiogram import types
# from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types.message import ParseMode
from aiogram.types import ContentType
from aiogram import Bot

# from modules import btntext, replies
from modules.db import CoworkingStatus, DBManager
from modules.coworking import Manager as CoworkingManager
# from modules.buttons import coworking as cwbtn  # Coworking action buttons
from modules import replies


class BotBroadcastFunctions:
    """Bot broadcast-related methods."""

    def __init__(self, bot, db, log):
        """Initialize bot broadcast-related methods."""
        self.db: DBManager = db
        self.bot: Bot = bot
        self.cwman = CoworkingManager(db)
        self.log = log

    async def broadcast(self, content: str, scope: str,  # noqa: C901
                        media_type: str,
                        custom_scope: list | None = None,
                        is_markdown: bool | None = None,
                        media: str | None = None) -> None:
        """Broadcast message to all chats (handles multiple media types)."""
        if media is not None and media_type is None:
            raise ValueError("Media type is not specified")
        if (media is None
                and media_type is not None
                and media_type != ContentType.TEXT):
            raise ValueError("Media is not specified")
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
        self.log.debug(f"Broadcasting message to \
{len(chat_ids)} chats: {chat_ids}")
        if media is None and media_type != ContentType.TEXT:
            raise ValueError("Media is not specified")
        if media is None:
            await self._send_text_broadcast(content,
                                            chat_ids,
                                            is_markdown=is_markdown)
            return
        if media_type in [ContentType.PHOTO, ContentType.VIDEO,
                          ContentType.VIDEO_NOTE]:
            await self._send_media_broadcast(content,
                                             media,
                                             media_type,
                                             chat_ids,
                                             is_markdown=is_markdown)
            return
        raise ValueError("Invalid media type")

    async def _send_text_broadcast(self, content: str,
                                   chat_ids: List[int],
                                   is_markdown: bool | None = None):
        for cid in chat_ids:
            try:
                await self.bot.send_message(cid, content,
                                            parse_mode=(ParseMode.MARKDOWN
                                                        if is_markdown
                                                        else None))
            except Exception as exc:
                self.log.debug(f"Failed to send broadcast message to chat \
{cid}: {exc}; user probably blocked the bot")

    async def _send_media_broadcast(self, caption: str,
                                    media: str,
                                    media_type: str,
                                    chat_ids: List[int],
                                    is_markdown: bool | None = None):
        send_func: Any | None = None
        _ = send_func  # Linter error: unused variable
        match media_type:
            case ContentType.PHOTO:
                send_func = self._send_photo
            case ContentType.VIDEO:
                send_func = self._send_video
            case ContentType.VIDEO_NOTE:
                send_func = self._send_video_note
            case _:
                raise ValueError("Invalid media type")
        for cid in chat_ids:
            await send_func(cid, media, caption=caption,
                            is_markdown=is_markdown)

    async def _send_photo(self, cid: int,
                          photo: str,
                          caption: str | None = None,
                          is_markdown: bool | None = None):
        try:
            await self.bot.send_photo(cid,
                                      photo,
                                      caption=caption,
                                      parse_mode=(ParseMode.MARKDOWN
                                                  if is_markdown
                                                  else None))
        except Exception as exc:
            self.log.debug(f"Failed to send broadcast message to chat {cid}: \
{exc}; user probably blocked the bot")

    async def _send_video(self,
                          cid: int,
                          video: str,
                          caption: str | None = None,
                          is_markdown: bool | None = None):
        try:
            await self.bot.send_video(cid,
                                      video,
                                      caption=caption,
                                      parse_mode=(ParseMode.MARKDOWN
                                                  if is_markdown
                                                  else None))
        except Exception as exc:
            self.log.debug(f"Failed to send broadcast message to chat {cid}: \
{exc}; user probably blocked the bot")

    async def _send_video_note(self, cid: int,
                               video_note: str,
                               caption: str | None = None,
                               is_markdown: bool | None = None):
        _ = caption
        _ = is_markdown
        try:
            await self.bot.send_video_note(cid, video_note)
        except Exception as exc:
            self.log.debug(f"Failed to send broadcast message to chat {cid}: \
{exc}; user probably blocked the bot")

    async def coworking(self,
                        status: CoworkingStatus,
                        delta_mins: int = 0):
        """Broadcast coworking status change to all users."""
        cids = self.db.get_coworking_notification_chats()
        responsible_uname = self.db.get_coworking_responsible_uname()
        reply = (replies
                 .coworking_status_changed(status,
                                           responsible_uname=responsible_uname,
                                           delta_mins=delta_mins))
        for cid in cids:
            try:
                await self.bot.send_message(cid, reply)
            except Exception as exc:
                self.log.debug(f'{cid}: Failed to send message with \
error {exc}; user probably blocked the bot')
