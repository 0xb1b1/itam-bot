# import asyncio
from typing import Union
from aiogram import types


async def is_group_admin(message: types.Message) -> bool:
    # Check if chat is a group
    if not (message.chat.type == 'group' or message.chat.type == 'supergroup'):
        return True
    # Check if the user is a group admin
    administrators = await message.chat.get_administrators()
    administrators = [adm['user']['id'] for adm in administrators]
    if message.from_user.id not in administrators:
        return False
    return True


def conv_call_to_msg(cmessage: Union[types.CallbackQuery, types.Message]) -> types.Message:
    if isinstance(cmessage, types.Message):
        return cmessage
    return cmessage.message
