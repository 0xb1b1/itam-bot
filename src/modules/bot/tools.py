# import asyncio
# from datetime import datetime
from typing import Optional, Union
from aiogram import executor, types
# from aiogram.types.message import ParseMode
# from aiogram.dispatcher.filters.builtin import CommandStart
# from aiogram.dispatcher.filters import ChatTypeFilter
# from aiogram.contrib.fsm_storage.memory import MemoryStorage
# from aiogram.dispatcher import FSMContext
# from aiogram.dispatcher.filters.state import State, StatesGroup
# from aiogram.types import KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
# from aiogram.utils import exceptions

async def is_group_admin(message: types.Message) -> bool:
    # Check if chat is a group
    if not (message.chat.type == 'group' or message.chat.type == 'supergroup'):
        return True
    # Check if the user is a group admin
    administrators = await message.chat.get_administrators()
    administrators = [adm['user']['id'] for adm in administrators]
    if not message.from_user.id in administrators:
        return False
    return True

def conv_call_to_msg(cmessage: Union[types.CallbackQuery, types.Message]) -> types.Message:
    if isinstance(cmessage, types.Message):
        return cmessage
    return cmessage.message
