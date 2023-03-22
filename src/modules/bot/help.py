"Bot help functions"

from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types.message import ParseMode

from modules import btntext, replies
from modules.coworking import Manager as CoworkingManager

class BotHelpFunctions:
    def __init__(self, bot, db, log):
        self.db = db
        self.bot = bot
        self.cwman = CoworkingManager(db)
        self.log = log

    async def main(self, message: types.Message) -> None:
        if message.chat.id != message.from_user.id:  # Avoid sending the help menu in groups
            return
        inlHelpMenu = InlineKeyboardMarkup(resize_keyboard=True)
        inlHelpMenu.add(InlineKeyboardButton(btntext.CREDITS,
                                            callback_data='credits'))
        inlHelpMenu.add(InlineKeyboardButton(btntext.COWORKING_LOCATION,
                                            callback_data='coworking:location'))
        await message.answer(replies.help_message(),
                            parse_mode=ParseMode.MARKDOWN,
                            reply_markup=inlHelpMenu)

    async def location(self, call: types.CallbackQuery) -> None:
        await call.answer()
        await self.bot.send_location(call.from_user.id,
                                     self.cwman.location['lat'],
                                     self.cwman.location['lon'],
                                     reply_markup=InlineKeyboardMarkup())
        await call.message.edit_text(replies.coworking_location_info(),
                                     reply_markup=InlineKeyboardMarkup())