#!/usr/bin/env python3

"""Opens aiogram listener, ..."""

# region Regular dependencies
import os
import logging                               # Logging events
import asyncio                               # Asynchronous sleep()
from datetime import datetime
from typing import Union
from aiogram import Bot, Dispatcher          # Telegram bot API
from aiogram import executor, types          # Telegram API
from aiogram.types.message import ParseMode  # Send Markdown-formatted messages
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.types.message import ContentType

from fastapi import FastAPI
# endregion

# region Local dependencies
from config import log, db
from config import TELEGRAM_API_TOKEN
# import modules.bot.tools as bot_tools           # Bot tools
# from modules import markup as nav           # Bot menus
from modules import btntext                 # Telegram bot button text
# from modules import replies                 # Telegram bot information output
from modules import coworking               # Coworking space information
from modules import replies                 # Telegram bot information output
# from modules.models import CoworkingStatus  # Coworking status model
from modules.bot.help import BotHelpFunctions  # Bot help menu functions
from modules.bot.coworking import BotCoworkingFunctions  # Bot coworking-related functions
from modules.bot.scheduled import BotScheduledFunctions  # Bot scheduled functions (recurring)
from modules.bot.broadcast import BotBroadcastFunctions  # Bot broadcast functions
from modules.bot.generic import BotGenericFunctions      # Bot generic functions
# from modules.bot.states import *
# from modules.buttons import coworking as cwbtn  # Coworking action buttons (admin)
# from modules import stickers
# endregion

# region Lambda functions
debug_dec = lambda message: log.debug(f'User {message.from_user.id} from chat {message.chat.id} \
called command `{message.text}`') or True  # noqa: E731
admin_only = lambda message: db.is_admin(message.from_user.id)  # noqa: E731
groups_only = lambda message: message.chat.type in ['group', 'supergroup']  # noqa: E731
# endregion
# endregion

# region Modules
# Coworking status
coworking = coworking.Manager(db)
# endregion

# region Bot initialization
# Initialize bot and dispatcher
bot = Bot(token=TELEGRAM_API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
# endregion

# region Post-bot-init modules
bot_help = BotHelpFunctions(bot, db, log)
bot_cw = BotCoworkingFunctions(bot, db, log)
bot_scheduled = BotScheduledFunctions(bot, db, log)
bot_broadcast = BotBroadcastFunctions(bot, db, log)
bot_generic = BotGenericFunctions(bot, db, log)
# endregion


# region Bot replies
# region Cancel all states
@dp.callback_query_handler(lambda c: c.data == 'cancel', state='*')
@dp.message_handler(state='*', commands=['cancel'])
@dp.message_handler(lambda message: message.text.lower() == 'cancel' or message.text.lower() == btntext.CANCEL.lower(),
                    state='*')
async def bot_cancel_handler(cmessage: Union[types.Message, types.CallbackQuery], state: FSMContext):
    """Allow user to cancel any action"""
    log.debug(f"User {cmessage.from_user.id} canceled an action")
    # Cancel state and inform user about it
    await state.finish()
    # Check if the type of cmessage is CallbackQuery
    if isinstance(cmessage, types.CallbackQuery):
        await bot.send_message(cmessage.message.chat.id,
                               'Действие отменено',
                               reply_markup=bot_generic.get_main_keyboard(cmessage.from_user.id))
        return
    await bot.send_message(cmessage.chat.id,
                           'Действие отменено',
                           reply_markup=bot_generic.get_main_keyboard(cmessage))
# endregion


# region Credits
@dp.callback_query_handler(lambda c: c.data == 'bot:credits')
async def bot_credits(call: types.CallbackQuery) -> None:
    """Send credits"""
    await call.message.edit_text(replies.bot_credits(),
                                 parse_mode=ParseMode.MARKDOWN)
# endregion


# region Help
@dp.message_handler(lambda message: message.text == btntext.HELP_MAIN)
@dp.message_handler(commands=['help'])
async def bot_help_menu(message: types.Message):
    await bot_help.main(message)


@dp.callback_query_handler(lambda c: c.data == 'coworking:location')
async def bot_coworking_location(call: types.CallbackQuery) -> None:
    await bot_help.location(call)
# endregion


# Normal messages
async def answer(message: types.Message) -> None:
    """Answer to random messages and messages from buttons."""
    # If the chat is private, send a message asking if the user is lost and restore their keyboard
    if bot_generic.chat_is_private(message):
        await message.answer(replies.plain_message_pm_answer(),
                             reply_markup=bot_generic.get_main_keyboard(message.from_user.id))
    if not db.is_uname_set(message.from_user.id):  # TODO: Measure performance hit
        if not bot_generic.chat_is_group(message):
            if db.does_user_exist(message.from_user.id):
                db.set_uname(message.from_user.id, message.from_user.username)
            else:
                await message.answer(replies.please_click_start())
    # Menus
    text_lower = message.text.lower()

    # Plaintext message answers — checking db value for ChatSettings.message_answers_enabled
    if bot_generic.chat_is_group(message):
        if not db.get_message_answers_status(message.chat.id):
            log.debug(f"Received a message in a group, but plaintext_message_answers is False for {message.chat.id}")
            return

    if any(word in text_lower for word in ['коворк', 'кв']) and any(word in text_lower for word in ['статус',
                                                                                                    'открыт',
                                                                                                    'закрыт']):
        await message.answer(replies.coworking_status_reply(coworking.get_status(),
                                                            responsible_uname=db.get_coworking_responsible_uname()),
                             reply_markup=bot_generic.get_main_keyboard(message))
# endregion


# region FastAPI endpoints
app = FastAPI()


@app.get("/healthz")
async def health_check():
    return {"status": "ok"}
# endregion


# region Startup functions
async def aiogram_start_polling():
    await dp.start_polling()


async def run_loop():
    await asyncio.gather(
        # Run AIOGram and FastAPI in one event loop
        aiogram_start_polling(),
        app.run_task(host='0.0.0.0', port=8000)
    )


# endregion

# region Startup
def run() -> None:
    loop = asyncio.get_event_loop()
    loop.create_task(bot_scheduled.coworking_status_checker(datetime.strptime(f'2021-09-01 \
{os.getenv("COWORKING_OPENING_TIME", "09:00:00")}', '%Y-%m-%d %H:%M:%S'),
                                                            datetime.strptime(f'2021-09-01 \
{os.getenv("COWORKING_CLOSING_TIME", "19:00:00")}', '%Y-%m-%d %H:%M:%S'),
                                                            timeout=int(os.getenv('COWORKING_STATUS_WORKER_TIMEOUT',
                                                                                  '120'))))
    log.info('Starting AIOGram...')

    # region Message handlers
    from modules.bot.handlers import start, \
        skills, \
        administration, \
        coworking_mut, \
        coworking_info, \
        user_profile, \
        broadcast_flow, \
        chat_mgr, \
        clubs, \
        departments, \
        navigation
    start.setup(dp, bot, bot_generic)
    skills.setup(dp, bot, bot_generic)
    administration.setup(dp, bot, bot_broadcast, bot_generic)
    coworking_mut.setup(dp, bot, bot_broadcast, bot_generic, bot_cw)
    coworking_info.setup(dp, bot, bot_broadcast, bot_generic, bot_cw)
    user_profile.setup(dp, bot, bot_generic)
    broadcast_flow.setup(dp, bot, bot_broadcast, bot_generic)
    chat_mgr.setup(dp, bot, bot_broadcast, bot_generic)
    clubs.setup(dp, bot, bot_broadcast, bot_generic)
    departments.setup(dp, bot, bot_generic)
    navigation.setup(dp, bot, bot_generic)
    # endregion

    # Add plaintext handler
    dp.register_message_handler(answer, content_types=ContentType.TEXT)

    executor.start_polling(dp, skip_updates=True)
    log.info('AIOgram stopped successfully')
# endregion
