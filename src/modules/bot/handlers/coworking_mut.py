#!/usr/bin/env python3


"""Bot coworking status mutation handlers."""
# region Regular dependencies
import logging
import asyncio
from aiogram import Bot, Dispatcher
from aiogram import types
# from aiogram.types.message import ParseMode
# from aiogram.dispatcher.filters import ChatTypeFilter
# from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
# from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ChatType
# endregion

# region Local dependencies
from config import log, db
from modules import markup as nav
from modules import btntext
from modules.coworking import Manager as CoworkingManager
from modules import replies
from modules.db import DBManager
from modules.models import CoworkingStatus
from modules.bot.coworking import BotCoworkingFunctions
from modules.bot.broadcast import BotBroadcastFunctions
from modules.bot.generic import BotGenericFunctions
from modules.bot.states import AdminCoworkingTempCloseFlow
from modules.bot import decorators as dp
# endregion

# region Passed by setup()
bot: Bot = None  # type: ignore
bot_broadcast: BotBroadcastFunctions = None  # type: ignore
bot_generic: BotGenericFunctions = None  # type: ignore
bot_cw: BotCoworkingFunctions = None  # type: ignore
coworking: CoworkingManager = None  # type: ignore
# endregion

# region Lambda functions
debug_dec = lambda message: log.debug(f'User {message.from_user.id} from \
chat {message.chat.id} called command `{message.text}`') or True  # noqa: E731
admin_only = lambda message: db.is_admin(message.from_user.id)  # noqa: E731
groups_only = lambda message: message.chat.type in ['group', 'supergroup']  # noqa: E731
# endregion


@dp.callback_query_handler(lambda c: c.data == 'coworking:take_responsibility')
async def coworking_take_responsibility(call: types.CallbackQuery) -> None:
    """Take responsibility for coworking status."""
    if coworking.is_responsible(call.from_user.id):
        await call.answer(replies.coworking_status_already_responsible())
        return
    db.coworking_status_set_uid_responsible(call.from_user.id)
    # Update inline keyboard in the call message
    await call.message.edit_reply_markup(reply_markup=bot_cw.get_admin_markup_full(call))
    await call.answer(replies.coworking_status_now_responsible())


@dp.callback_query_handler(lambda c: c.data == 'coworking:open',
                           chat_type=ChatType.PRIVATE)
async def coworking_open(call: types.CallbackQuery) -> None:
    """Set coworking status to open."""
    # Check if the user is permitted to mutate coworking status
    if not coworking.is_trusted(call.from_user.id):
        await call.answer(replies.permission_denied())
        return
    if coworking.get_status() == CoworkingStatus.open:
        await call.answer("Коворкинг уже открыт")
        return
    coworking.open(call.from_user.id)
    asyncio.get_event_loop().create_task(bot_broadcast.coworking(CoworkingStatus.open))
    await call.answer("Коворкинг теперь открыт")
    # Update inline keyboard in the call message
    await call.message.edit_reply_markup(reply_markup=bot_cw.get_admin_markup_full(call))
    log.info(f"Coworking opened by {call.from_user.id}")


@dp.callback_query_handler(lambda c: c.data == 'coworking:close',
                           chat_type=ChatType.PRIVATE)
async def coworking_close(call: types.CallbackQuery) -> None:
    """Set coworking status to closed."""
    # Check if the user is permitted to mutate coworking status
    if not coworking.is_trusted(call.from_user.id):
        await call.answer(replies.permission_denied())
        return
    if coworking.get_status() == CoworkingStatus.closed:
        await call.answer("Коворкинг уже закрыт")
        return
    coworking.close(call.from_user.id)
    asyncio.get_event_loop().create_task(bot_broadcast.coworking(CoworkingStatus.closed))
    await call.answer("Коворкинг теперь закрыт")
    # Update inline keyboard in the call message
    await call.message.edit_reply_markup(reply_markup=bot_cw.get_admin_markup_full(call))
    log.info(f"Coworking closed by {call.from_user.id}")


@dp.callback_query_handler(lambda c: c.data == 'coworking:temp_close',
                           chat_type=ChatType.PRIVATE)
async def coworking_temp_close_stage0(call: types.CallbackQuery, state: FSMContext) -> None:
    """Set coworking status to temporarily closed."""
    # Check if the user is permitted to mutate coworking status
    if not coworking.is_trusted(call.from_user.id):
        await call.answer(replies.permission_denied())
        return
    if coworking.get_status() == CoworkingStatus.temp_closed:
        await call.answer(f"Коворкинг уже временно закрыт\n\n{replies.cancel_action()}")
        return
    # Set AdminCoworkingTempCloseFlow state
    await state.set_state(AdminCoworkingTempCloseFlow.delta.state)
    # Store call id in state
    await state.update_data(status_msg_id=call.message.message_id)
    await bot.send_message(call.from_user.id,
                           f"На какое время закрыть коворкинг? (в минутах; можно ввести любое целое число)\
\n\n{replies.cancel_action()}",
                           reply_markup=nav.coworkingTempCloseDeltaMenu)


@dp.message_handler(admin_only, state=AdminCoworkingTempCloseFlow.delta.state)
async def coworking_temp_close_stage1(message: types.Message, state: FSMContext) -> None:
    """Set coworking status to temporarily closed."""
    if coworking.get_status() == CoworkingStatus.temp_closed:
        await message.answer(f"Коворкинг уже временно закрыт\n\n{replies.cancel_action()}")
        return
    # Get delta
    try:
        delta = int(message.text)
    except ValueError:
        await message.answer(f"Неверный формат! Попробуй еще раз\n\n{replies.cancel_action()}")
        return
    # Validate delta value
    if delta > 60:
        await message.answer(f"Коворкинг будет закрыт слишком долго! Введи значение от 5 до 60 минут \
или закрой его\n\n{replies.cancel_action()}")
        return
    elif delta < 5:
        await message.answer(f"Слишком маленький перерыв! Введи значение от 5 до 60 минут \
или закрой коворкинг\n\n{replies.cancel_action()}")
        return
    # Save delta
    await state.update_data(delta=delta)
    # Set AdminCoworkingTempCloseFlow state
    await state.set_state(AdminCoworkingTempCloseFlow.confirm.state)
    # Send message
    await message.answer("Подтвердите введенные данные", reply_markup=nav.confirmMenu)


@dp.message_handler(admin_only, state=AdminCoworkingTempCloseFlow.confirm.state)
async def coworking_temp_close_stage2(message: types.Message, state: FSMContext) -> None:
    """Set coworking status to temporarily closed."""
    if coworking.get_status() == CoworkingStatus.temp_closed:
        await message.answer(f"Коворкинг уже временно закрыт\n\n{replies.cancel_action()}")
        return
    # Check confirmation
    if message.text != btntext.CONFIRM:
        await message.answer("Действие отменено")
        await state.finish()
        return
    # Get delta
    data = await state.get_data()
    delta: int = data['delta']
    # Temporarily close coworking
    coworking.temp_close(message.from_user.id, delta_mins=delta)
    asyncio.get_event_loop().create_task(bot_broadcast.coworking(CoworkingStatus.temp_closed, delta_mins=delta))
    await message.answer("Коворкинг теперь временно закрыт",
                         reply_markup=bot_generic.get_main_keyboard(message))
    # Update inline keyboard in the call message (from state)
    await bot.edit_message_reply_markup(message.from_user.id, data['status_msg_id'],
                                        reply_markup=bot_cw.get_admin_markup_full(message))
    log.info(f"Coworking temporarily closed by {message.from_user.id} for {delta} minutes")
    await state.finish()


@dp.callback_query_handler(lambda c: c.data == 'coworking:event_open',
                           chat_type=ChatType.PRIVATE)
async def coworking_event_open(call: types.CallbackQuery) -> None:
    """Set coworking status to opened for an event."""
    # Check if the user is permitted to mutate coworking status
    if not coworking.is_trusted(call.from_user.id):
        await call.answer(replies.permission_denied())
        return
    if coworking.get_status() == CoworkingStatus.event_open:
        await call.answer("Коворкинг уже открыт (с предупреждением о проведении мероприятия)")
        return
    coworking.event_open(call.from_user.id)
    asyncio.get_event_loop().create_task(bot_broadcast.coworking(CoworkingStatus.event_open))
    await call.answer("Коворкинг теперь открыт (с предупреждением о проведении мероприятия)")
    # Update inline keyboard in the call message
    await call.message.edit_reply_markup(reply_markup=bot_cw.get_admin_markup_full(call))
    log.info(f"Coworking opened for an event by {call.from_user.id}")


@dp.callback_query_handler(lambda c: c.data == 'coworking:event_close',
                           chat_type=ChatType.PRIVATE)
async def coworking_event_close(call: types.CallbackQuery) -> None:
    """Set coworking status to closed for an event."""
    # If the call is not from a private conversation, deny access
    if call.message.chat.type != 'private':
        await call.answer(replies.permission_denied())
        return
    # Check if the user is permitted to mutate coworking status
    if not coworking.is_trusted(call.from_user.id):
        await call.answer(replies.permission_denied())
        return
    if coworking.get_status() == CoworkingStatus.event_closed:
        await call.answer("Коворкинг уже закрыт на мероприятие")
        return
    coworking.event_close(call.from_user.id)
    asyncio.get_event_loop().create_task(bot_broadcast.coworking(CoworkingStatus.event_closed))
    await call.answer("Коворкинг теперь закрыт на мероприятие")
    # Update inline keyboard in the call message
    await call.message.edit_reply_markup(reply_markup=bot_cw.get_admin_markup_full(call))
    log.info(f"Coworking closed for an event by {call.from_user.id}")


@dp.callback_query_handler(admin_only, lambda c: c.data == 'coworking:trim_log',
                           chat_type=ChatType.PRIVATE)
async def trim_coworking_status_log(call: types.CallbackQuery) -> None:
    """Trim coworking log."""
    limit = 10  # TODO: make this configurable
    coworking.trim_log(limit=limit)
    await call.answer(f"Лог статуса коворкинг пространства урезан; последние {limit} записей сохранены")


@dp.message_handler(admin_only, commands=['get_coworking_status_log'],
                    chat_type=ChatType.PRIVATE)
async def get_coworking_status_log(message: types.Message) -> None:
    """Get coworking status log."""
    await message.answer(coworking.get_log_str())


# noinspection PyProtectedMember
def setup(dispatcher: Dispatcher,
          bot_obj: Bot,
          broadcast: BotBroadcastFunctions,
          generic: BotGenericFunctions,
          cw: BotCoworkingFunctions):
    global bot
    global bot_broadcast
    global bot_generic
    global coworking
    global bot_cw
    bot = bot_obj
    bot_broadcast = broadcast
    bot_generic = generic
    bot_cw = cw
    coworking = CoworkingManager(db)
    for func in globals().values():
        if hasattr(func, '_handlers'):
            for handler_type, args, kwargs in func._handlers:
                if handler_type == 'message':
                    dispatcher.register_message_handler(func, *args, **kwargs)
                elif handler_type == 'callback_query':
                    dispatcher.register_callback_query_handler(func, *args, **kwargs)
