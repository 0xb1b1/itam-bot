#!/usr/bin/env python3

"""Bot Yandex Internship skill handlers."""
# region Regular dependencies
import io
from datetime import datetime
from asyncio import sleep as asleep, get_event_loop
from typing import Union
from datetime import timedelta
from aiogram import Bot, Dispatcher
from aiogram import types
from aiogram.types.message import ParseMode
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, \
    InlineKeyboardButton, KeyboardButton, \
    ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.types.chat import ChatActions
from logging import Logger
import csv
# endregion

# region Local dependencies
from modules import markup as nav
from modules import btntext as btns
from modules import replies
from modules.db import DBManager
from modules.models import Skill
from modules.bot.broadcast import BotBroadcastFunctions
from modules.bot.generic import BotGenericFunctions
from modules.bot.states import YandexInternship, YandexInternshipAdminEnrollment
from modules.bot import decorators as dp
from .replies import yandex_internship as ya_replies
from .keyboards import yandex_internship as ya_kbs
from ...media import stickers
from .loops import yandex_internship as ya_loops

# endregion

# region Passed by setup()
db: DBManager = None  # type: ignore
bot: Bot = None  # type: ignore
log: Logger = None  # type: ignore
bot_broadcast: BotBroadcastFunctions = None  # type: ignore
bot_generic: BotGenericFunctions = None  # type: ignore
# endregion

# region Lambda functions
debug_dec = lambda message: log.debug(f'User {message.from_user.id} from \
chat {message.chat.id} called command `{message.text}`') or True
admin_only = lambda message: db.is_admin(message.from_user.id)
groups_only = lambda message: message.chat.type in ['group', 'supergroup']
# endregion

# region Menus
inlStartAgree = InlineKeyboardButton("Да, я в деле", callback_data="skill:yandex_internship:welcome:agree")
inlStartLater = InlineKeyboardButton("Создать анкету", callback_data="skill:yandex_internship:welcome:later")
inlStartDisagree = InlineKeyboardButton("Не сейчас", callback_data="skill:yandex_internship:welcome:disagree")
inlStartMenu = InlineKeyboardMarkup(row_width=2).add(inlStartDisagree,
                                                     inlStartLater,
                                                     inlStartAgree)
# endregion


@dp.callback_query_handler(lambda c: c.data == 'skill:yandex_internship')
async def yandex_internship_start(msg: Union[types.Message,
                                             types.CallbackQuery]):
    """Handle /yandex_internship command or button press."""
    if isinstance(msg, types.CallbackQuery):
        await msg.answer()
        from_user = msg.from_user.id
        msg = msg.message
    else:
        from_user = msg.from_user.id
    if db.is_ya_int_user(from_user):
        await profile_menu(msg)
        return
    # # Remove previous message
    # await msg.delete()
    welcome = ya_replies.welcome()
    await msg.answer(ya_replies.start(), reply_markup=ReplyKeyboardRemove())
    await bot.send_chat_action(msg.chat.id, ChatActions.CHOOSE_STICKER)
    await asleep(0.4)
    await bot.send_sticker(msg.chat.id, stickers.YANDEX_INTERNSHIP_START)
    await bot.send_chat_action(msg.chat.id, ChatActions.TYPING)
    await asleep(0.7)
    await msg.answer(welcome[0], parse_mode=ParseMode.MARKDOWN)
    await bot.send_chat_action(msg.chat.id, ChatActions.TYPING)
    await asleep(1)
    await msg.answer(welcome[1], parse_mode=ParseMode.MARKDOWN)
    await bot.send_chat_action(msg.chat.id, ChatActions.TYPING)
    await asleep(1)
    await msg.answer(welcome[2], parse_mode=ParseMode.MARKDOWN,
                     reply_markup=inlStartMenu)


async def profile_menu(msg: types.Message):
    """Send profile menu to user."""
    await msg.edit_text(ya_replies.profile_menu(),
                        reply_markup=ya_kbs.profile_menu())


@dp.callback_query_handler(lambda c: c.data == 'skill:yandex_internship:enrollment:remove_user')
async def remove_user(call: types.CallbackQuery):
    """Remove user from Yandex Internship."""
    await call.answer()
    await call.message.edit_text(ya_replies.remove_user_ask_confirm(),
                                 reply_markup=ya_kbs.remove_user_confirm())


@dp.callback_query_handler(lambda c: c.data.startswith('skill:yandex_internship:remove_user:'))
async def remove_user_confirmed(call: types.CallbackQuery):
    action = call.data.split(':')[3]
    if action == 'confirm':
        db.del_ya_int_user(call.from_user.id)
        await call.message.answer(ya_replies.remove_user_success(),
                                  reply_markup=bot_generic.get_main_keyboard(call.from_user.id))
    else:
        await call.message.answer(ya_replies.remove_user_cancelled(),
                                  reply_markup=bot_generic.get_main_keyboard(call.from_user.id))
    await call.message.delete()


@dp.callback_query_handler(lambda c: c.data == 'skill:yandex_internship:welcome:disagree')
async def welcome_disagree(call: types.CallbackQuery):
    """Handle user disagreement to participate in Yandex Internship."""
    await call.answer()
    # Delete three messages (call.message and two previous)
    for i in range(4):
        try:
            await bot.delete_message(call.message.chat.id,
                                     call.message.message_id - i)
        except Exception as exc:
            log.debug(f"[Yandex Internship] Failed to delete message {i} in welcome_disagree: {exc}")
        await asleep(0.3)
    await bot.send_message(call.from_user.id, ya_replies.welcome_disagree(),
                           reply_markup=bot_generic.get_main_keyboard(call.from_user.id))


@dp.callback_query_handler(lambda c: c.data in ['skill:yandex_internship:welcome:' + i for i in ['agree', 'later']])
async def welcome_positive(call: types.CallbackQuery, state: FSMContext):
    """Handle user agreement to participate in Yandex Internship."""
    await call.answer()
    choice = call.data.split(':')[-1]
    await state.set_state(YandexInternship.first_name)
    if choice == 'agree':
        await call.message.answer(ya_replies.welcome_agree())
        await state.update_data(agree=True)
    else:
        await call.message.answer(ya_replies.welcome_later())
        await state.update_data(agree=False)
    await bot.send_chat_action(call.message.chat.id, ChatActions.TYPING)
    await asleep(0.5)
    await call.message.answer(ya_replies.profile_first_name(),
                              reply_markup=nav.inlCancelMenu)


@dp.message_handler(state=YandexInternship.first_name)
async def setup_first_name(message: types.Message, state: FSMContext):
    """Set user first name."""
    db.set_user_first_name(message.from_user.id, message.text)
    await message.answer(ya_replies.profile_last_name(), reply_markup=nav.inlCancelMenu)
    await state.set_state(YandexInternship.last_name)


@dp.message_handler(state=YandexInternship.last_name)
async def setup_last_name(message: types.Message, state: FSMContext):
    """Set user last name."""
    data = await state.get_data()
    db.set_user_last_name(message.from_user.id, message.text)
    share_btn = KeyboardButton(text="Поделиться",
                               request_contact=True)
    share_kb = (ReplyKeyboardMarkup(resize_keyboard=True,
                                    one_time_keyboard=True)
                .add(share_btn))
    await message.answer(ya_replies.profile_phone(data.get('agree')),
                         reply_markup=share_kb)
    await state.set_state(YandexInternship.phone)


@dp.message_handler(state=YandexInternship.phone,
                    content_types=types.ContentType.CONTACT)
async def setup_phone(message: types.Message, state: FSMContext):
    """Set user phone."""
    data = await state.get_data()
    try:
        db.set_user_phone(message.from_user.id,
                          int(message.contact.phone_number))
    except ValueError:
        await message.answer(replies.invalid_phone_try_again(),
                             reply_markup=nav.inlCancelMenu)
        return
    await message.answer("Телефон сохранён 🥰",
                         reply_markup=ReplyKeyboardRemove())
    await message.answer(ya_replies.profile_email(data.get('agree')),
                         reply_markup=nav.inlCancelMenu)
    await state.set_state(YandexInternship.email)


@dp.message_handler(state=YandexInternship.email)
async def setup_email(message: types.Message, state: FSMContext):
    """Set user email."""
    try:
        db.set_user_email(message.from_user.id, message.text)
    except ValueError:
        await message.answer(replies.invalid_email_try_again(),
                             reply_markup=nav.inlCancelMenu)
        return
    await message.answer(ya_replies.profile_skills())
    message_to_be_edited = await message.answer("Skill list placeholder")
    await state.set_state(YandexInternship.skills)
    await setup_skills(message, state, manual_run=True,
                       message_to_be_edited=message_to_be_edited)


@dp.callback_query_handler(state=YandexInternship.skills)
async def setup_skills(call: Union[types.CallbackQuery, types.Message],
                       state: FSMContext,
                       manual_run: bool = False,
                       message_to_be_edited: types.Message | None = None) -> None:
    """Edit user profile skills (loops)."""
    if isinstance(call, types.CallbackQuery):
        await call.answer()
        if call.data == 'skill:yandex_internship:setup:done':
            await call.answer()
            await state.set_state(YandexInternship.finalize)
            await setup_finalize(call, state)
            return None
    if not manual_run:
        split = call.data.split(':')
        action = split[4]
        skill = Skill[split[5]]
        if action == 'add':
            db.add_user_skills(call.from_user.id, skill)
        elif action == 'remove':
            db.remove_user_skill(call.from_user.id, skill)
    user_data = db.get_user_data(call.from_user.id)
    if user_data is None:
        raise AttributeError('User data is None')
    keyboard = ya_kbs.get_skill_inl_kb(user_data['skills'])
    cmessage = call.message if isinstance(call, types.CallbackQuery) else call
    if not message_to_be_edited:
        await cmessage.edit_text(replies.profile_edit_skills(),
                                 reply_markup=keyboard)
    else:
        await message_to_be_edited.edit_text(replies.profile_edit_skills(),
                                             reply_markup=keyboard)


async def finalize_enrollment_script(call: types.CallbackQuery):
    await bot.send_chat_action(call.message.chat.id, ChatActions.TYPING)
    await asleep(0.2)
    await call.message.answer(ya_replies.finalize_enrollment_0(),
                              parse_mode=ParseMode.HTML)
    await asleep(0.3)
    await call.message.answer(ya_replies.finalize_enrollment_1(),
                              parse_mode=ParseMode.HTML)
    await asleep(0.5)
    await call.message.answer(ya_replies.finalize_enrollment_2(),
                              parse_mode=ParseMode.HTML)
    await asleep(0.3)
    await call.message.answer(ya_replies.finalize_enrollment_3(),
                              reply_markup=bot_generic.get_main_keyboard(call.from_user.id),
                              parse_mode=ParseMode.HTML)


@dp.callback_query_handler(state=YandexInternship.finalize)
async def setup_finalize(call: types.CallbackQuery, state: FSMContext):
    """Finalize profile setup (for both "agree" and "later" cases)."""
    data = await state.get_data()
    await bot.send_chat_action(call.message.chat.id, ChatActions.TYPING)
    await asleep(0.2)
    await call.message.answer(ya_replies.profile_skills_done())
    await bot.send_chat_action(call.message.chat.id, ChatActions.TYPING)
    await asleep(0.3)
    await call.message.edit_text(replies.profile_info(db.get_user_data(call.from_user.id)))
    await bot.send_chat_action(call.message.chat.id, ChatActions.TYPING)
    await asleep(0.7)
    if data.get('agree'):
        await state.finish()
        db.set_ya_int_user(call.from_user.id, True)
        await finalize_enrollment_script(call)
    else:
        await call.message.answer(ya_replies.profile_edit_done_later(),
                                  reply_markup=ya_kbs.inl_profile_edit_done_later())
        await state.set_state(YandexInternship.finalize_later_upsell)


@dp.callback_query_handler(state=YandexInternship.finalize_later_upsell)
async def finalize_later_upsell(call: types.CallbackQuery, state: FSMContext):
    """Try to upsell the user to agree to the terms."""
    if call.data == 'skill:yandex_internship:setup:finalize:upsell:agree':
        await state.finish()
        db.set_ya_int_user(call.from_user.id, True)
        await finalize_enrollment_script(call)
    elif call.data == 'skill:yandex_internship:setup:finalize:upsell:later':
        await state.finish()
        db.set_ya_int_user(call.from_user.id, False)
        await call.message.answer(ya_replies.profile_edit_done_later_upsell_later(),
                                  reply_markup=bot_generic.get_main_keyboard(call.from_user.id))


@dp.callback_query_handler(lambda c: c.data.startswith('skill:yandex_internship:timer:enroll:'))
async def timer_enroll_handler(call: types.CallbackQuery):
    """Handle timer enroll (dis-)agree."""
    await call.answer()
    if call.data.endswith('agree'):
        await finalize_enrollment_script(call)
        db.set_ya_int_agreed(call.from_user.id, True)
    else:  # Disagree
        await bot.send_chat_action(call.message.chat.id, ChatActions.TYPING)
        await asleep(0.3)
        await call.message.answer(ya_replies.timer_enroll_disagree())
        db.del_ya_int_user(call.from_user.id)


@dp.callback_query_handler(lambda c: c.data == 'skill:yandex_internship:registration:confirm')
async def registration_confirm(call: types.CallbackQuery):
    """Confirm registration."""
    await call.answer()
    await bot.send_chat_action(call.message.chat.id, ChatActions.TYPING)
    await asleep(0.3)
    await call.message.answer(ya_replies.registration_confirmed(),
                              parse_mode=ParseMode.HTML,
                              reply_markup=ya_kbs.inl_registration_confirmed())
    db.set_ya_int_is_registered_confirmed(call.from_user.id, True)


@dp.callback_query_handler(lambda c: c.data == 'skill:yandex_internship:flow:begin')
async def flow_begin(call: types.CallbackQuery):
    """Mark the flow as started."""
    await call.answer()
    await bot.send_chat_action(call.message.chat.id, ChatActions.TYPING)
    await asleep(0.3)
    await call.message.answer(ya_replies.flow_begin())
    db.set_ya_int_is_flow_activated(call.from_user.id, True)


# region Administration
@dp.callback_query_handler(lambda c: c.data == 'admin:yandex_internship')
async def yandex_control_panel(call: Union[types.CallbackQuery, types.Message],
                               send_message: bool = False):
    """Yandex Internship control panel."""
    if isinstance(call, types.CallbackQuery):
        await call.answer()
        from_user = call.from_user.id
        call = call.message
    else:
        from_user = call.from_user.id
    # Get analytics from database
    if send_message:
        await call.answer(replies.yandex_internship_control_panel(db.get_ya_int_all_users_count(),
                                                                  db.get_ya_int_all_enrolled_users_count(),
                                                                  db.get_ya_int_all_is_registered_users_count(),
                                                                  db.get_ya_int_all_is_registered_confirmed_users_count(),  # noqa
                                                                  db.get_ya_int_all_is_flow_activated_users_count()),
                          reply_markup=nav.get_yandex_internship_control_kb())
    else:
        await call.edit_text(replies.yandex_internship_control_panel(db.get_ya_int_all_users_count(),
                                                                  db.get_ya_int_all_enrolled_users_count(),
                                                                  db.get_ya_int_all_is_registered_users_count(),
                                                                  db.get_ya_int_all_is_registered_confirmed_users_count(),  # noqa
                                                                  db.get_ya_int_all_is_flow_activated_users_count()),
                             reply_markup=nav.get_yandex_internship_control_kb())
    log.info(f"User {from_user} opened the Yandex Internship control panel")


@dp.callback_query_handler(admin_only, lambda c: c.data == 'admin:yandex_internship:enrolled_list')
async def admin_get_enrolled_list(call: types.CallbackQuery):
    """Send the list of all enrolled users (agreed or not)."""
    await call.answer()
    users = db.get_ya_int_all_users()
    if not users or len(users) == 0:
        await call.message.answer('No users enrolled.')
        return
    # Create a CSV file with the list of users
    csv_file = io.StringIO()
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(['Phone number', 'Agreed', 'Registered (Yandex end)', 'Registration confirmed by user',
                         'Marathon Activated', 'Registration timestamp', 'User ID', 'Username', 'Email',
                         'First name', 'Last name', 'Skills'])
    for user in users:
        user_profile = db.get_user_data(user.uid)
        csv_writer.writerow([f'+{user_profile["phone"]}',
                             '+' if user.agreed else '',
                             '+' if user.is_registered else '',
                             '+' if user.is_registered_confirmed else '',
                             '+' if user.is_flow_activated else '',
                             datetime.strftime(user.ts, '%Y-%m-%d %H:%M:%S'),
                             user.uid,
                             user_profile['uname'] if user_profile['uname'] else '',
                             user_profile['email'],
                             user_profile['first_name'],
                             user_profile['last_name'],
                             ', '.join([str(skill) for skill in user_profile['skills']])]
                            )
    csv_file.seek(0)
    await bot.send_document(call.from_user.id, ('enrolled_users.csv', csv_file), caption='Enrolled users list')
    csv_file.close()


@dp.callback_query_handler(admin_only, lambda c: c.data == 'admin:yandex_internship:validate_enrollment')
async def admin_validate_enrollment(call: types.CallbackQuery, state: FSMContext):
    """Validate the enrollment of a user."""
    await call.answer()
    await call.message.answer('Please send the phone numbers of the user you wish to validate, separated by newlines.')
    await call.message.delete()
    await state.set_state(YandexInternshipAdminEnrollment.validate)


@dp.message_handler(state=YandexInternshipAdminEnrollment.validate)
async def admin_validate_enrollment_handler(msg: types.Message, state: FSMContext):
    """Handle the validation of a user."""
    await state.finish()
    exceptions = []
    for phone in msg.text.strip().split('\n'):
        phone = phone.strip()
        if phone in ['', '\n']:
            continue
        try:
            db.set_ya_int_is_registered_by_phone(int(phone), True)
        except ValueError:
            exceptions.append(phone)
    if len(exceptions) > 0:
        await msg.answer('The following phone numbers are invalid: ' + ', '.join(exceptions))
    await msg.answer('Done.')
    await yandex_control_panel(msg, send_message=True)


@dp.callback_query_handler(admin_only, lambda c: c.data == 'admin:yandex_internship:remove_user')
async def admin_remove_user(call: types.CallbackQuery, state: FSMContext):
    """Remove a user from the database."""
    await call.answer()
    await call.message.answer('Please send the phone number of the user you wish to remove.')
    await call.message.delete()
    await state.set_state(YandexInternshipAdminEnrollment.del_user)


@dp.message_handler(state=YandexInternshipAdminEnrollment.del_user)
async def admin_remove_user_stage_2(msg: types.message, state: FSMContext):
    """Remove a user from the database."""
    await state.finish()
    db.del_ya_int_user(db.get_uid_by_phone(int(msg.text)))
    await msg.answer('User removed from database.')


@dp.callback_query_handler(admin_only, lambda c: c.data == 'admin:yandex_internship:time_travel')
async def admin_time_travel(call: types.CallbackQuery, state: FSMContext):
    """Make an enrolled user time travel (to check the scheduler)."""
    await call.answer()
    await call.message.answer('Send the phone number of the user you wish to time travel.')
    await call.message.delete()
    await state.set_state(YandexInternshipAdminEnrollment.time_travel_phone)


@dp.message_handler(state=YandexInternshipAdminEnrollment.time_travel_phone)
async def admin_time_travel_handler_0(msg: types.Message, state: FSMContext):
    """Handle the time travel of a user (get the number of days)."""
    await state.update_data(phone=int(msg.text))
    await msg.answer('For how many hours?')
    await state.set_state(YandexInternshipAdminEnrollment.time_travel_hours)


@dp.message_handler(state=YandexInternshipAdminEnrollment.time_travel_hours)
async def admin_time_travel_handler_1(msg: types.Message, state: FSMContext):
    """Handle the time travel of a user (get the number of hours)."""
    data = await state.get_data()
    await state.finish()
    await msg.answer('Please note that in the backend, user\'s timestamps will be reduced by the amount \
of hours you specified.')
    try:
        db.dec_ya_int_user_timestamps(data['phone'], timedelta(hours=int(msg.text)))
    except AttributeError:
        await msg.answer('Invalid phone number (user not found).')
        return
    await msg.answer('Done.')
# endregion


# noinspection PyProtectedMember
def setup(dispatcher: Dispatcher,
          bot_obj: Bot,
          database: DBManager,
          logger: Logger,
          broadcast: BotBroadcastFunctions,
          generic: BotGenericFunctions):
    """Set up handlers for dispatcher."""
    global bot
    global db
    global log
    global bot_broadcast
    global bot_generic
    bot = bot_obj
    bot_broadcast = broadcast
    bot_generic = generic
    log = logger
    db = database
    loop = get_event_loop()
    loop.create_task(ya_loops.yandex_internship_loop(db, bot, log))
    for func in globals().values():
        if hasattr(func, '_handlers'):
            for handler_type, args, kwargs in func._handlers:
                if handler_type == 'message':
                    dispatcher.register_message_handler(func, *args, **kwargs)
                elif handler_type == 'callback_query':
                    dispatcher.register_callback_query_handler(func, *args, **kwargs)
