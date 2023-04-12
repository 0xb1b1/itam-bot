#!/usr/bin/env python3


"""Yandex Internship keyboards."""
from typing import List
from aiogram.types import InlineKeyboardMarkup as InlKbMkup
from aiogram.types import InlineKeyboardButton as InlKbBtn

from modules.models import Skill
from modules.replies import skill_names as profile_skill_names


def get_skill_inl_kb(active_skills: List[Skill]) -> InlKbMkup:
    """Get inline keyboard with skills and marks for editing."""
    kb = InlKbMkup()
    # Get all skills from Skill class
    skills = [x for x in Skill]
    skill_names = profile_skill_names()
    for skill in skills:
        if skill in active_skills:
            kb.add(InlKbBtn(f'✅ {skill_names[skill.name]}',
                   callback_data=f'skill:yandex_internship:setup:skills:remove:{skill.name}'))
        else:
            kb.add(InlKbBtn(f'🅾️ {skill_names[skill.name]}',
                   callback_data=f'skill:yandex_internship:setup:skills:add:{skill.name}'))
    kb.add(InlKbBtn('Готово', callback_data='skill:yandex_internship:setup:done'))
    return kb


def inl_profile_edit_done_later() -> InlKbMkup:
    """Get inline keyboard for profile edit done later."""
    kb = InlKbMkup()
    kb.add(InlKbBtn('Хочу все-таки податься',
                    callback_data='skill:yandex_internship:setup:finalize:upsell:agree'))
    kb.add(InlKbBtn('Подожду другого времени',
                    callback_data='skill:yandex_internship:setup:finalize:upsell:later'))
    return kb


def inl_timer_ask_enroll() -> InlKbMkup:
    """Get inline keyboard for timer ask participate."""
    kb = InlKbMkup()
    kb.add(InlKbBtn('Я в деле',
                    callback_data='skill:yandex_internship:timer:enroll:agree'))
    kb.add(InlKbBtn('Не в этот раз',
                    callback_data='skill:yandex_internship:timer:enroll:disagree'))
    return kb


def inl_registration_confirmed() -> InlKbMkup:
    """Get inline keyboard for registration confirmed."""
    kb = InlKbMkup()
    kb.add(InlKbBtn('Начать неделю мотивации',
                    callback_data='skill:yandex_internship:flow:begin'))
    return kb
