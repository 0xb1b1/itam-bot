#!/usr/bin/env python3


"""Yandex Internship Skill asyncio event loops."""
from asyncio import sleep as asleep
from datetime import datetime, timedelta
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup as InlKbMarkup, InlineKeyboardButton as InlKbBtn
from logging import Logger
from aiogram.types import ChatActions
from aiogram.types.message import ParseMode

from modules.db import DBManager
from ..replies import yandex_internship as ya_replies
from ..keyboards import yandex_internship as ya_kbs
from ..buttons import yandex_internship as ya_btns
from ..media import yandex_internship as ya_media


flow_timeline = {
    'day_1': {
        'msg_1': {
            'hour_start': 8,  # Hours are in UTC
            'video_notes': [],
            'text': [ya_replies.flow_day_1_msg_1()]
        },
        'msg_2': {
            'hour_start': 10,
            'video_notes': [ya_media.DAY_1_MSG_2],
            'text': [ya_replies.flow_day_1_msg_2()]
        },
        'msg_3': {
            'hour_start': 15,
            'video_notes': [],
            'text': [ya_replies.flow_day_1_msg_3()],
            'documents': [ya_media.GROCK_ALGOS_BOOK]
        },
    },
    'day_2': {
        'msg_1': {
            'hour_start': 6,
            'video_notes': [],
            'text': [ya_replies.flow_day_2_msg_1()]
        },
        'msg_2': {
            'hour_start': 7,
            'video_notes': [ya_media.DAY_2_MSG_2],
            'text': []
        },
        'msg_3': {
            'hour_start': 10,
            'video_notes': [],
            'text': [ya_replies.flow_day_2_msg_3()]
        },
        'msg_4': {
            'hour_start': 15,
            'video_notes': [ya_media.DAY_2_MSG_4],
            'text': []
        },
    },
    'day_3': {
        'msg_1': {
            'hour_start': 7,
            'video_notes': [],
            'text': [ya_replies.flow_day_3_msg_1()]
        },
        'msg_2': {
            'hour_start': 10,
            'video_notes': [ya_media.DAY_3_MSG_2],
            'text': []
        },
        'msg_3': {
            'hour_start': 12,
            'video_notes': [],
            'text': [ya_replies.flow_day_3_msg_3()],
            'animations': [ya_media.ANIMATION_MORIARTY_MEME]
        },
        'msg_4': {
            'hour_start': 15,
            'video_notes': [ya_media.DAY_3_MSG_4],
            'text': []
        },
    },
    'day_4': {
        'msg_1': {
            'hour_start': 7,
            'video_notes': [],
            'text': [ya_replies.flow_day_4_msg_1()]
        },
        'msg_2': {
            'hour_start': 10,
            'video_notes': [ya_media.DAY_4_MSG_2],
            'text': []
        },
        'msg_3': {
            'hour_start': 12,
            'video_notes': [],
            'text': [ya_replies.flow_day_4_msg_3()]
        },
        'msg_4': {
            'hour_start': 15,
            'video_notes': [],
            'text': [ya_replies.flow_day_4_msg_4()]
        },
    },
    'day_5': {
        'msg_1': {
            'hour_start': 7,
            'video_notes': [],
            'text': [ya_replies.flow_day_5_msg_1()]
        },
        'msg_2': {
            'hour_start': 12,
            'video_notes': [ya_media.DAY_5_MSG_2],
            'text': [ya_replies.flow_day_5_msg_2()]
        },
        'msg_3': {
            'hour_start': 14,
            'video_notes': [],
            'text': [ya_replies.flow_day_5_msg_3()]
        }
    }
}


async def yandex_internship_loop(db: DBManager, bot: Bot, log: Logger):
    """Yandex Internship main asyncio event loop."""
    while True:
        await asleep(10)  # TODO: Prod sleep is 120 ~
        users = db.get_all_ya_int_users()
        log.debug(f"[Yandex Internship] Checking {len(users)} users:\n{', '.join([str(x.uid) for x in users])}")
        for user in users:
            timestamp = user.ts
            log.debug(f"[Yandex Internship] Checking user {user.uid} in loop...")
            if not user.agreed:
                #                 log.debug(f"[Yandex Internship] User {user.uid}: {((datetime.utcnow() - timestamp)
                #                                                                   .seconds)} seconds passed; \
                # Time: now: {datetime.utcnow()} | timestamp: {timestamp}; Current hour: {datetime.utcnow().hour} | \
                # Timeframe check: {9 <= datetime.utcnow().hour <= 17} | Notified later: {user.is_notified_later}")
                # If more than 2 days passed since the user started the skill,
                # send them a message asking them to agree (with two buttons)
                # (after 9AM UTC and before 5PM UTC)
                if (datetime.utcnow() - timestamp).days >= 2 and 9 <= datetime.utcnow().hour <= 17\
                        and not user.is_notified_later:
                    try:
                        await bot.send_message(user.uid, ya_replies.timer_ask_enroll(),
                                               reply_markup=ya_kbs.inl_timer_ask_enroll())
                    except Exception as exc:
                        log.error(f"[Yandex Internship] Failed to send timed enrollment message to user {user.uid}: \
{exc}")
                    db.set_ya_int_is_notified_later(user.uid, True)
                    log.debug(f"[Yandex Internship] Sent timed enrollment message to user {user.uid}")

            else:  # TODO: Add a check to not check the user's messages if the last message has been marked as sent
                # If the user agreed, check whether they have been validated by an admin
                # If this is the case, ask user to confirm registration
                if (user.is_registered
                        and not user.is_registered_confirmed
                        and not user.registered_notified_stage >= 3):
                    if 17 <= datetime.utcnow().hour <= 18:
                        # Check if the previous message was sent more than 20 hours ago
                        # If so, send a new message
                        if (datetime.utcnow() - user.registered_notified_last_ts) >= timedelta(hours=20):
                            kb = InlKbMarkup()
                            match user.registered_notified_stage:
                                case 0:
                                    text = ya_replies.registration_confirm_0()
                                    kb.add(InlKbBtn(ya_btns.REGISTRATION_CONFIRM_BTN_0,
                                                    callback_data='skill:yandex_internship:registration:confirm'))
                                case 1:
                                    text = ya_replies.registration_confirm_1()
                                    kb.add(InlKbBtn(ya_btns.REGISTRATION_CONFIRM_BTN_1,
                                                    callback_data='skill:yandex_internship:registration:confirm'))
                                case 2:
                                    text = ya_replies.registration_confirm_2()
                                    kb.add(InlKbBtn(ya_btns.REGISTRATION_CONFIRM_BTN_2,
                                                    callback_data='skill:yandex_internship:registration:confirm'))
                                case _:
                                    text = "UNKNOWN STAGE"
                                    kb.add(InlKbBtn("UNKNOWN STAGE",
                                                    callback_data='sinkhole'))
                            try:
                                await bot.send_message(user.uid, text,
                                                       parse_mode=ParseMode.HTML,
                                                       reply_markup=kb)
                            except Exception as exc:
                                log.error(f"[Yandex Internship] Failed to send timed registration confirmation \
message to user {user.uid}: {exc}")
                            db.inc_ya_int_registered_notified_stage(user.uid)
                            db.set_ya_int_registered_notified_last_ts(user.uid)
                            log.debug(f"[Yandex Internship] Sent timed registration confirmation \
message to user {user.uid}")
                elif user.is_registered and user.is_registered_confirmed and user.is_flow_activated:
                    # If the user is registered, confirmed, and flow is activated, get user JSON
                    # and send them messages depending on the flags in the JSON.
                    # JSON schema:
                    # {
                    #     "day_1": {
                    #         "msg_1": False,
                    #         "msg_2": False,
                    #         ...
                    #     },
                    #     ...
                    # }
                    # Use `flow_timeline` dict to get the messages
                    # After sending them, set their respective flags to True
                    user_json = dict(user.flow_json)
                    log.debug(f"[Yandex Internship] user_json for user {user.uid}: {user_json}")
                    # Run if user.flow_last_ts is at least 22 hours ago
                    log.debug("User flow last ts: " + str(user.flow_last_ts))
                    first_day_sent = user_json['day_1']['msg_1'] and user_json['day_1']['msg_2'] \
                        and user_json['day_1']['msg_3']
                    if not first_day_sent or (datetime.utcnow() - user.flow_last_ts) >= timedelta(hours=22):
                        for day in user_json:
                            message_found = False
                            log.debug(f"[Yandex Internship] Checking timed flow message (day: \
`{day} to user {user.uid}")
                            for msg in user_json[day].items():
                                if msg[1]:  # If the message has already been sent, skip it
                                    log.debug(f"[Yandex Internship] Skipping timed flow message (day: `{day}` | \
msg: `{msg[0]}` to user {user.uid}: message already sent")
                                    continue
                                # Check if the current hour is greater or equal to the hour_start of the message
                                # If so, send the message and set the flag to True
                                hr_start = flow_timeline[day][msg[0]]['hour_start']
                                log.debug(f"[Yandex Internship] Checking day {day} | msg {msg[0]} for user {user.uid} \
| {hr_start=} | {datetime.utcnow().hour=}, condition is {hr_start + 4 > datetime.utcnow().hour >= hr_start}")
                                if hr_start + 4 > datetime.utcnow().hour >= hr_start:
                                    log.debug(f"[Yandex Internship] Sending timed flow message (day: `{day}` | \
    msg: `{msg[0]}` to user {user.uid}")
                                    try:
                                        for video_note in flow_timeline[day][msg[0]]['video_notes']:
                                            await bot.send_chat_action(user.uid, ChatActions.UPLOAD_VIDEO_NOTE)
                                            await asleep(0.7)
                                            await bot.send_video_note(user.uid, video_note)
                                        for text in flow_timeline[day][msg[0]]['text']:
                                            await bot.send_chat_action(user.uid, ChatActions.TYPING)
                                            await asleep(0.5)
                                            await bot.send_message(user.uid, text, parse_mode=ParseMode.HTML)
                                        # If field `documents` exists, send the documents
                                        if 'documents' in flow_timeline[day][msg[0]]:
                                            for document in flow_timeline[day][msg[0]]['documents']:
                                                await bot.send_chat_action(user.uid, ChatActions.UPLOAD_DOCUMENT)
                                                await asleep(0.7)
                                                await bot.send_document(user.uid, document)
                                        if 'animations' in flow_timeline[day][msg[0]]:
                                            for animation in flow_timeline[day][msg[0]]['animations']:
                                                await bot.send_chat_action(user.uid, ChatActions.UPLOAD_DOCUMENT)
                                                await asleep(0.7)
                                                await bot.send_animation(user.uid, animation)
                                    except Exception as exc:
                                        log.error(f"[Yandex Internship] Failed to send timed flow message \
(day: `{day}` | msg: `{msg[0]}` to user {user.uid}: {exc}")
                                    user_json[day][msg[0]] = True
                                    db.set_ya_int_flow_json(user.uid, user_json)
                                    db.set_ya_int_flow_last_ts(user.uid)
                                    log.debug(f"[Yandex Internship] Sent timed flow message (day: `{day}` | \
    msg: `{msg[0]}` to user {user.uid}")
                                    message_found = True
                                    break
                                else:  # If not in constraints, flag message_found and break
                                    message_found = True
                                    break
                            if message_found:
                                break
