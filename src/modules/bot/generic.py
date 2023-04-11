
from typing import Union
from aiogram import types
from aiogram.types import KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

from modules import btntext

class BotGenericFunctions:
    def __init__(self, bot, db, log):
        self.db = db
        self.bot = bot
        self.log = log

    def chat_is_group(self, message: types.Message) -> bool:
        """Check if message is sent from group or private chat"""
        # Check if the type of cmessage is CallbackQuery
        if isinstance(message, types.CallbackQuery):
            message = message.message
        if message.chat.type == 'group' or message.chat.type == 'supergroup':
            return True
        return False

    def get_main_keyboard(self, message: Union[types.Message, int]) -> InlineKeyboardMarkup:
        user_id = message.from_user.id if isinstance(message, types.Message) else message
        btnClubs = KeyboardButton(btntext.CLUBS_BTN)
        btnCoworkingStatus = KeyboardButton(btntext.COWORKING_STATUS)
        btnProfileInfo = KeyboardButton(btntext.PROFILE_INFO)
        btnHelp = KeyboardButton(btntext.HELP_MAIN)
        btnBotSkills = KeyboardButton(btntext.BOT_SKILLS_BTN)
        mainMenu = ReplyKeyboardMarkup(row_width=2).add(btnClubs,
                                                        btnCoworkingStatus,
                                                        btnProfileInfo,
                                                        btnHelp,
                                                        btnBotSkills)
        if self.db.is_admin(user_id):
            mainMenu.add(KeyboardButton(btntext.ADMIN_BTN))
        if isinstance(message, types.Message):
            return ReplyKeyboardRemove() if self.chat_is_group(message) else mainMenu
        return mainMenu
