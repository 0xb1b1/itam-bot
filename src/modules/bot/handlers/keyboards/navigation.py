#!/usr/bin/env python3

"""Directions-related keyboards."""
from typing import List
from aiogram.types import InlineKeyboardMarkup as InlKbMkup
from aiogram.types import InlineKeyboardButton as InlKbBtn

from modules.models import Skill
from modules.static import btntext as btns
from modules.replies import skill_names as profile_skill_names


def main_menu() -> InlKbMkup:
    """Get inline keyboard for directions main menu."""
    kb = InlKbMkup(row_width=1)
    kb.add(InlKbBtn('Корпус', callback_data='navigation:buildings'))
    kb.add(InlKbBtn('Аудитория', callback_data='navigation:audiences'))
    kb.add(InlKbBtn('Назад', callback_data='navigation:back'))
    return kb
