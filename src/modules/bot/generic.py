#!/usr/bin/env python3

"""Generic bot functions."""
from typing import Union
from aiogram import types
from aiogram.types import KeyboardButton, InlineKeyboardMarkup, \
    ReplyKeyboardMarkup, ReplyKeyboardRemove

from modules import btntext
from modules import constants


class BotGenericFunctions:
    """Generic bot functions."""

    def __init__(self, bot, db, log):
        """Initialize generic bot functions."""
        self.db = db
        self.bot = bot
        self.log = log

    @staticmethod
    def chat_is_group(message: types.Message) -> bool:
        """Check if message is sent from group or private chat"""
        # Check if the type of cmessage is CallbackQuery
        if isinstance(message, types.CallbackQuery):
            message = message.message
        if message.chat.type == 'group' or message.chat.type == 'supergroup':
            return True
        return False

    @staticmethod
    def chat_is_private(message: types.Message) -> bool:
        """Check if message is sent from group or private chat"""
        # Check if the type of cmessage is CallbackQuery
        if isinstance(message, types.CallbackQuery):
            message = message.message
        if message.chat.type == 'private':
            return True
        return False

    def get_main_keyboard(self, message: Union[types.Message, int]) -> InlineKeyboardMarkup:
        user_id = message.from_user.id if isinstance(message, types.Message) else message
        btn_clubs = KeyboardButton(btntext.CLUBS_BTN)
        btn_coworking_status = KeyboardButton(btntext.COWORKING_STATUS)
        btn_profile_info = KeyboardButton(btntext.PROFILE_INFO)
        btn_help = KeyboardButton(btntext.HELP_MAIN)
        btn_bot_skills = KeyboardButton(btntext.BOT_SKILLS_BTN)
        main_menu = ReplyKeyboardMarkup(row_width=2).add(btn_clubs,
                                                         btn_coworking_status,
                                                         btn_profile_info,
                                                         btn_help,
                                                         btn_bot_skills)
        if self.db.is_admin(user_id):
            main_menu.add(KeyboardButton(btntext.ADMIN_BTN))
        if isinstance(message, types.Message):
            return ReplyKeyboardRemove() if self.chat_is_group(message) else main_menu
        return main_menu

    async def send_long_message(self, chat_id, message_text):
        # check if the message length is greater than the maximum allowed by Telegram
        if len(message_text) > constants.MAX_MESSAGE_LENGTH:
            # split the message into parts
            message_parts = [message_text[i:i + constants.MAX_MESSAGE_LENGTH] for i in
                             range(0, len(message_text), constants.MAX_MESSAGE_LENGTH)]

            # send each part of the message
            for part in message_parts:
                await self.bot.send_message(chat_id, part)
        else:
            # send the message if it doesn't exceed the maximum length
            await self.bot.send_message(chat_id, message_text)
