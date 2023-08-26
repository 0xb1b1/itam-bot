#!/usr/bin/env python3

from modules.static import btntext
from aiogram.types import InlineKeyboardButton

inl_open = InlineKeyboardButton(btntext.OPEN_COWORKING, callback_data='coworking:open')
inl_close = InlineKeyboardButton(btntext.CLOSE_COWORKING, callback_data='coworking:close')
inl_temp_close = InlineKeyboardButton(btntext.TEMP_CLOSE_COWORKING, callback_data='coworking:temp_close')
inl_event_open = InlineKeyboardButton(btntext.EVENT_OPEN_COWORKING, callback_data='coworking:event_open')
inl_event_close = InlineKeyboardButton(btntext.EVENT_CLOSE_COWORKING, callback_data='coworking:event_close')
inl_take_responsibility = InlineKeyboardButton(btntext.COWORKING_TAKE_RESPONSIBILITY,
                                               callback_data='coworking:take_responsibility')

inl_location = InlineKeyboardButton(btntext.COWORKING_LOCATION, callback_data='coworking:location')
inl_location_short = InlineKeyboardButton(btntext.COWORKING_LOCATION_SHORT, callback_data='coworking:location')
