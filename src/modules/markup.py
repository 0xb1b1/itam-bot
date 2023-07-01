#!/usr/bin/env python3

"""Handles Telegram bot button creation and mapping."""
from typing import List
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup as InlKbMarkup
from aiogram.types import InlineKeyboardButton as InlKbBtn
from modules import btntext as btns

from modules import replies
from modules.db import Skill


# Menu button
btnMain = KeyboardButton(btns.MAIN_MENU)

# Main menu
# btnInfo = KeyboardButton(btns.MAIN_INFO)
inlEditProfileBtn = InlKbBtn(btns.INL_EDIT_PROFILE,
                             callback_data='profile:edit')
inlSetupProfileBtn = InlKbBtn(btns.INL_SETUP_PROFILE,
                              callback_data='profile:setup')
inlProfileMenu = InlKbMarkup(row_width=1).add(inlEditProfileBtn, inlSetupProfileBtn)

inlEditBioBtn = InlKbBtn(btns.INL_EDIT_BIO,
                         callback_data='edit_bio')
inlBioMenu = InlKbMarkup().add(inlEditBioBtn)

inlEditResumeBtn = InlKbBtn(btns.INL_EDIT_RESUME,
                            callback_data='edit_resume')
inlResumeMenu = InlKbMarkup().add(inlEditResumeBtn)

inlCancelBtn = InlKbBtn('Отмена', callback_data='cancel')
inlCancelMenu = InlKbMarkup().add(inlCancelBtn)

bc_scope_users = KeyboardButton(btns.USERS)
bc_scope_admins = KeyboardButton(btns.ADMINS)
bc_scope_everyone = KeyboardButton(btns.EVERYONE)
bc_scope_yandex_internship_not_signed_up = KeyboardButton(btns.YANDEX_INTERNSHIP_NOT_SIGNED_UP)
bc_scope_yandex_internship_signed_up = KeyboardButton(btns.YANDEX_INTERNSHIP_SIGNED_UP)
bc_scope_yandex_internship_not_enrolled = KeyboardButton(btns.YANDEX_INTERNSHIP_NOT_ENROLLED)
bc_scope_yandex_internship_enrolled = KeyboardButton(btns.YANDEX_INTERNSHIP_ENROLLED)
bc_scope_yandex_internship_not_flow_started = KeyboardButton(btns.YANDEX_INTERNSHIP_NOT_FLOW_STARTED)
bc_scope_yandex_internship_flow_started = KeyboardButton(btns.YANDEX_INTERNSHIP_FLOW_STARTED)
adminBroadcastScopeMenu = (ReplyKeyboardMarkup(row_width=1)
                           .add(bc_scope_users,
                                bc_scope_admins,
                                bc_scope_everyone,
                                bc_scope_yandex_internship_not_signed_up,
                                bc_scope_yandex_internship_signed_up,
                                bc_scope_yandex_internship_not_enrolled,
                                bc_scope_yandex_internship_enrolled,
                                bc_scope_yandex_internship_not_flow_started,
                                bc_scope_yandex_internship_flow_started))

confirmBtn = KeyboardButton(btns.CONFIRM)
cancelBtn = KeyboardButton(btns.CANCEL)
confirmMenu = ReplyKeyboardMarkup(resize_keyboard=True).add(confirmBtn, cancelBtn)

inlCTFClubBtn = InlKbBtn(btns.CTF_CLUB, callback_data='ctf_club_info')
inlDesignClubBtn = InlKbBtn(btns.DESIGN_CLUB, callback_data='design_club_info')
inlGameDevClubBtn = InlKbBtn(btns.GAMEDEV_CLUB, callback_data='gamedev_club_info')
inlHackathonClubBtn = InlKbBtn(btns.HACKATHON_CLUB, callback_data='hackathon_club_info')
inlRoboticsClubBtn = InlKbBtn(btns.ROBOTICS_CLUB, callback_data='robotics_club_info')
inlClubsMenu = InlKbMarkup().add(inlCTFClubBtn,
                                 inlDesignClubBtn,
                                 inlHackathonClubBtn,
                                 inlGameDevClubBtn,
                                 inlRoboticsClubBtn)

cwTempClose15Btn = KeyboardButton("15")
cwTempClose20Btn = KeyboardButton("20")
cwTempClose30Btn = KeyboardButton("30")
cwTempClose45Btn = KeyboardButton("45")
coworkingTempCloseDeltaMenu = (ReplyKeyboardMarkup(resize_keyboard=True).add(cwTempClose15Btn,
                                                                             cwTempClose20Btn,
                                                                             cwTempClose30Btn,
                                                                             cwTempClose45Btn))

yandexInternshipSkill = InlKbBtn(btns.BOT_SKILL_YANDEX_INTERNSHIP,
                                 callback_data='skill:yandex_internship')
botSkillsMenu = (InlKbMarkup(row_width=1).add(yandexInternshipSkill,
                                              InlKbBtn(btns.BOT_SKILL_INSTITUTIONS,
                                                       callback_data='skill:departments'),
                                              InlKbBtn(btns.BOT_SKILL_NAVIGATION,
                                                       callback_data='skill:navigation')))


def get_skill_inl_kb(active_skills: List[Skill]) -> InlKbMarkup:
    """Get inline keyboard with skills and marks for editing."""
    kb = InlKbMarkup()
    # Get all skills from Skill class
    skills = [x for x in Skill]
    skill_names = replies.skill_names()
    for skill in skills:
        if skill in active_skills:
            kb.add(InlKbBtn(f'✅ {skill_names[skill.name]}',
                   callback_data=f'profile:edit:skill:remove:{skill.name}'))
        else:
            kb.add(InlKbBtn(f'🅾️ {skill_names[skill.name]}',
                   callback_data=f'profile:edit:skill:add:{skill.name}'))
    kb.add(InlKbBtn('Готово',
                    callback_data='profile:edit:skill:done'))
    return kb


def get_profile_edit_fields_kb() -> InlKbMarkup:
    """Get inline keyboard with profile fields for editing."""
    kb = InlKbMarkup()
    fields = replies.profile_fields()
    for key in fields:
        if key in ['uid', 'gname', 'bio', 'resume']:
            continue
        kb.add(InlKbBtn(fields[key], callback_data=f'profile:edit:{key}'))
    kb.add(InlKbBtn('Готово', callback_data='profile:edit:done'))
    return kb


def get_yandex_internship_control_kb() -> InlKbMarkup:
    """Get inline keyboard with Yandex internship control buttons."""
    # All callbacks are in their respective Yandex Internship modules
    kb = InlKbMarkup(row_width=3)
    kb.add(InlKbBtn('📖 Список', callback_data='admin:yandex_internship:enrolled_list'),
           InlKbBtn('⚙️ Валидировать', callback_data='admin:yandex_internship:validate_enrollment'),
           InlKbBtn('❌ Удалить', callback_data='admin:yandex_internship:remove_user'),
           InlKbBtn('🕑 Ускорить', callback_data='admin:yandex_internship:time_travel'),
           InlKbBtn(btns.BACK, callback_data="admin:panel:override"))
    return kb
