#!/usr/bin/env python3

"""Generic bot functions."""
from typing import Union
from aiogram import types
from aiogram.types import KeyboardButton, InlineKeyboardMarkup, \
    ReplyKeyboardMarkup, ReplyKeyboardRemove

from modules import btntext


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
