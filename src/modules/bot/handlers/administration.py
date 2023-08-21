#!/usr/bin/env python3


"""Bot administration handlers."""
# region Regular dependencies
import io
import csv
from typing import Union
from aiogram import Bot, Dispatcher
from aiogram import types
from aiogram.types.message import ParseMode
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ContentType
from aiogram.utils.exceptions import MessageNotModified, BotKicked
from sqlalchemy.exc import DataError
# endregion

# region Local dependencies
from config import log
from modules import btntext
from modules.coworking import Manager as CoworkingManager
from modules import replies
from modules.db import DBManager
from modules.bot.broadcast import BotBroadcastFunctions
from modules.bot.generic import BotGenericFunctions
from modules.bot.states import AdminChangeUserGroup, AdminGetObjectId
from modules.bot import decorators as dp  # Bot decorators
from modules import markup as nav
from modules import constants
# endregion

# region Passed by setup()
db: DBManager = None  # type: ignore
bot: Bot = None  # type: ignore
bot_broadcast: BotBroadcastFunctions = None  # type: ignore
bot_generic: BotGenericFunctions = None  # type: ignore
coworking: CoworkingManager = None  # type: ignore
# endregion

# region Lambda functions
debug_dec = lambda message: log.debug(f'User {message.from_user.id} from chat \
{message.chat.id} called command `{message.text}`') or True  # noqa: E731
admin_only = lambda message: db.is_admin(message.from_user.id)  # noqa: E731
groups_only = lambda message: message.chat.type in ['group', 'supergroup']  # noqa: E731
# endregion


@dp.message_handler(admin_only, lambda message: message.text == btntext.ADMIN_BTN)
@dp.message_handler(admin_only, commands=['admin'])
@dp.callback_query_handler(admin_only, lambda c: c.data in ['admin:panel', 'admin:panel:override'])
async def admin_panel(msg: Union[types.Message, types.CallbackQuery]):
    """Send admin panel."""
    user_id = msg.from_user.id
    if user_id not in [1989957381, 232200895, 201667444]:  # TODO: REMOVE NIPPEL
        await msg.answer(replies.admin_panel_access_denied())
        log.info(f"User {user_id} tried to open the admin panel; denied access")
        return
    if isinstance(msg, types.CallbackQuery):
        await msg.answer()
        override_msg = msg.data == 'admin:panel:override'
        msg = msg.message
    else:
        override_msg = False
    inl_admin_change_group_btn = InlineKeyboardButton(btntext.INL_ADMIN_EDIT_GROUP,
                                                      callback_data='change_user_group')
    inl_admin_broadcast_btn = InlineKeyboardButton(btntext.INL_ADMIN_BROADCAST,
                                                   callback_data='admin:broadcast')
    inl_admin_stats_btn = InlineKeyboardButton(btntext.INL_ADMIN_STATS,
                                               callback_data='admin:stats')
    markup = InlineKeyboardMarkup().add(inl_admin_change_group_btn,
                                        inl_admin_broadcast_btn,
                                        inl_admin_stats_btn)
    if override_msg:
        await msg.edit_text(replies.admin_panel(), reply_markup=markup)
        log.info(f"User {user_id} re-opened the admin panel from another menu")
    else:
        await msg.answer(replies.admin_panel(), reply_markup=markup)
        log.info(f"User {user_id} opened the admin panel")


@dp.message_handler(admin_only, commands=['get_notif_db'])
async def get_notif_db(message: types.Message):
    """Get notification database."""
    await message.answer(db.get_coworking_notification_chats_str())


@dp.callback_query_handler(lambda c: c.data == 'admin:stats')
async def get_stats(call: types.CallbackQuery) -> None:
    """Get bot statistics for administration."""
    await call.answer()
    if call.from_user.id not in [1989957381, 232200895, 201667444]:
        await call.message.answer(replies.admin_panel_access_denied())
        log.info(f"User {call.from_user.id} tried to open the admin panel; denied access")
        return
    trim_coworking_log_btn = InlineKeyboardButton(text=btntext.TRIM_COWORKING_LOG,
                                                  callback_data="coworking:trim_log")
    refresh_btn = InlineKeyboardButton(text=btntext.REFRESH,
                                       callback_data="admin:stats")
    back_btn = InlineKeyboardButton(text=btntext.BACK,
                                    callback_data="admin:panel:override")
    markup = InlineKeyboardMarkup().add(trim_coworking_log_btn, refresh_btn, back_btn)
    try:
        await call.message.edit_text(replies.stats(db.get_stats()), reply_markup=markup)
    except MessageNotModified:
        return


@dp.callback_query_handler(lambda c: c.data == 'change_user_group')
async def change_user_group_stage0(call: types.CallbackQuery, state: FSMContext) -> None:
    """Change user group, stage 0."""
    await call.answer()
    await state.set_state(AdminChangeUserGroup.user_id.state)
    await call.message.edit_text(f"Введите ID пользователя\n\n{replies.cancel_action()}")


@dp.message_handler(state=AdminChangeUserGroup.user_id)
async def change_user_group_stage1(message: types.Message, state: FSMContext) -> None:
    """Change user group, stage 1."""
    user_id = message.text
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for group_name in db.get_groups_and_ids_as_dict_namekey():
        keyboard.add(types.KeyboardButton(group_name))
    await message.answer(f"Выберите группу\n\n{replies.cancel_action()}", reply_markup=keyboard)
    await state.update_data(user_id=user_id)
    await state.set_state(AdminChangeUserGroup.group_id.state)


@dp.message_handler(state=AdminChangeUserGroup.group_id)
async def change_user_group_stage2(message: types.Message, state: FSMContext) -> None:
    """Change user group, stage 2."""
    state_data = await state.get_data()
    user_id = state_data['user_id']
    try:
        group_id = db.get_groups_and_ids_as_dict_namekey()[message.text]["gid"]
    except Exception as exc:
        await message.answer("I encountered an exception! \
Details below:\n\n" + str(exc))
        return
    if not db.is_superadmin(message.from_user.id):
        await message.answer(replies.permission_denied(),
                             reply_markup=(bot_generic
                                           .get_main_keyboard(message)))
        await state.finish()
        return
    try:
        db.set_user_group(user_id, group_id)
    except (DataError, AttributeError) as exc:
        await message.answer(f"Invalid data sent to DB. Please try again.\
\n\nFull error:\n{exc}")
        await state.finish()
        return
    await message.answer(replies.user_group_changed(),
                         reply_markup=bot_generic.get_main_keyboard(message))
    log.info(f"User {message.from_user.id} changed user {user_id} group \
to {group_id}")
    await state.finish()


@dp.message_handler(admin_only, commands=['update_admin_kb'])
async def update_admin_kb(message: types.Message):
    """Update admin menu"""
    admins = db.get_admin_chats()
    for admin in admins:
        await bot.send_message(admin, "Клавиатура администратора обновлена",
                               reply_markup=(bot_generic
                                             .get_main_keyboard(message)))
        log.debug(f"Admin keyboard updated for {admin} \
by {message.from_user.id}")
    log.info(f"Admin keyboard updated by {message.from_user.id} for \
{len(admins)} administrators")
    await message.answer(replies.menu_updated_reply(len(admins), admins_only=True))


# region Debug commands
@dp.message_handler(commands=['amiadmin'])
async def check_admin(message: types.Message):
    """Check if user is admin."""
    if db.is_admin(message.from_user.id):
        await message.answer("Admin OK")
    else:
        await message.answer(replies.permission_denied())


@dp.message_handler(admin_only, commands=['get_groups'])
async def get_groups(msg: types.Message):
    """Get groups."""
    await msg.answer("\n".join([f"{i + 1}. {g.name}" for i, g in enumerate(db.get_groups())]))


@dp.message_handler(admin_only, commands=['fix_group_keyboards'])
async def fix_group_keyboards(msg: types.Message):
    """Fix (remove) keyboards for all groups."""
    for group_id in db.get_group_chats():
        try:
            await bot.send_message(group_id, "Чиню клавиатуру...\nЭтот запрос отправил администратор ITAM Bot",
                                   reply_markup=types.ReplyKeyboardRemove())
        except Exception as exc:
            log.debug(f"Failed to send fix_group_keyboards message to {group_id}: {exc}")
            continue
    await msg.answer("Done")


@dp.message_handler(commands=['get_users'])
async def get_users(msg: types.Message):
    """Get user info."""
    if msg.from_user.id not in [1989957381, 232200895, 201667444]:
        await msg.answer(replies.admin_panel_access_denied())
        log.info(f"User {msg.from_user.id} tried to open the admin panel; denied access")
        return
    await bot_generic.send_long_message(msg.from_user.id, db.get_users_str())


@dp.message_handler(commands=['get_users_verbose'])
async def get_users_verbose(msg: types.Message):
    """Get verbose user info."""
    # await bot_generic.send_long_message(msg.from_user.id, db.get_users_verbose_str())
    # Create a CSV file with the list of users
    if msg.from_user.id not in [1989957381, 232200895, 201667444]:
        await msg.answer(replies.admin_panel_access_denied())
        log.info(f"User {msg.from_user.id} tried to open the admin panel; denied access")
        return
    users = db.get_users_full()
    csv_file = io.StringIO()
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(['User ID', 'Username', 'Phone number', 'Email', 'First name', 'Last name', 'Skills'])
    for user in users:
        csv_writer.writerow([user[0].uid,
                             user[0].uname if user[0].uname is not None else '',
                             f'+{user[1].phone}' if user[1].phone is not None else '',
                             user[1].email if user[1].email is not None else '',
                             user[0].first_name,
                             user[0].last_name if user[0].last_name is not None else '',
                             ', '.join([str(skill.skill) for skill in user[2]])]
                            )
    csv_file.seek(0)
    await bot.send_document(msg.from_user.id, ('user_list.csv', csv_file), caption='User list')
    csv_file.close()


@dp.message_handler(admin_only, commands=['get_id'])
async def get_id(message: types.Message):
    """Get sticker ID."""
    await message.answer("Send me a media object and I'll reply with its ID")
    await AdminGetObjectId.get.set()


@dp.message_handler(state=AdminGetObjectId.get,
                    content_types=[ContentType.STICKER,
                                   ContentType.DOCUMENT,
                                   ContentType.PHOTO,
                                   ContentType.ANIMATION,
                                   ContentType.VIDEO_NOTE])
async def reply_with_id(message: types.Message):
    """Reply with sticker ID."""
    # Get message type
    msg_type = message.content_type
    msg = f"Content type is {msg_type}\n"
    if msg_type == 'sticker':
        msg += f'{message.sticker.file_id}'
    elif msg_type == 'document':
        msg += f'{message.document.file_id}'
    elif msg_type == 'photo':
        msg += f'{message.photo[-1].file_id}'
    elif msg_type == 'animation':
        msg += f'{message.animation.file_id}'
    elif msg_type == 'video_note':
        msg += f'{message.video_note.file_id}'
    else:
        msg = "(I can't get ID from this message)"
    await message.reply(msg + "\n\n" + replies.cancel_action())
# endregion


# noinspection PyProtectedMember
def setup(dispatcher: Dispatcher,
          bot_obj: Bot,
          database: DBManager,
          broadcast: BotBroadcastFunctions,
          generic: BotGenericFunctions):
    global bot
    global db
    global bot_broadcast
    global bot_generic
    global coworking
    bot = bot_obj
    bot_broadcast = broadcast
    bot_generic = generic
    db = database
    coworking = CoworkingManager(db)
    for func in globals().values():
        if hasattr(func, '_handlers'):
            for handler_type, args, kwargs in func._handlers:
                if handler_type == 'message':
                    dispatcher.register_message_handler(func, *args, **kwargs)
                elif handler_type == 'callback_query':
                    dispatcher.register_callback_query_handler(func, *args, **kwargs)
