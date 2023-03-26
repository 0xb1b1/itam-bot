#!/usr/bin/env python3

"""Handles Telegram bot button creation and mapping"""
import os
from dotenv import load_dotenv
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from modules import btntext as btn


# Menu button
btnMain = KeyboardButton(btn.MAIN_MENU)

# Main menu
# btnInfo = KeyboardButton(btntext.MAIN_INFO)
inlEditProfileBtn = InlineKeyboardButton(btn.INL_EDIT_PROFILE, callback_data='edit_profile')
inlProfileMenu = InlineKeyboardMarkup().add(inlEditProfileBtn)

inlEditBioBtn = InlineKeyboardButton(btn.INL_EDIT_BIO, callback_data='edit_bio')
inlBioMenu = InlineKeyboardMarkup().add(inlEditBioBtn)

inlEditResumeBtn = InlineKeyboardButton(btn.INL_EDIT_RESUME, callback_data='edit_resume')
inlResumeMenu = InlineKeyboardMarkup().add(inlEditResumeBtn)

inlCancelBtn = InlineKeyboardButton('Отмена', callback_data='cancel')
inlCancelMenu = InlineKeyboardMarkup().add(inlCancelBtn)

bcScopeUsers = KeyboardButton(btn.USERS)
bcScopeAdmins = KeyboardButton(btn.ADMINS)
bcScopeEveryone = KeyboardButton(btn.EVERYONE)
adminBroadcastScopeMenu = ReplyKeyboardMarkup(resize_keyboard=True).add(bcScopeUsers,
                                                                        bcScopeAdmins,
                                                                        bcScopeEveryone)

confirmBtn = KeyboardButton(btn.CONFIRM)
cancelBtn = KeyboardButton(btn.CANCEL)
confirmMenu = ReplyKeyboardMarkup(resize_keyboard=True).add(confirmBtn,
                                                            cancelBtn)

inlCTFClubBtn = InlineKeyboardButton(btn.CTF_CLUB, callback_data='ctf_club_info')
inlDesignClubBtn = InlineKeyboardButton(btn.DESIGN_CLUB, callback_data='design_club_info')
inlGameDevClubBtn = InlineKeyboardButton(btn.GAMEDEV_CLUB, callback_data='gamedev_club_info')
inlHackathonClubBtn = InlineKeyboardButton(btn.HACKATHON_CLUB, callback_data='hackathon_club_info')
inlRoboticsClubBtn = InlineKeyboardButton(btn.ROBOTICS_CLUB, callback_data='robotics_club_info')
# inlMLClubBtn = InlineKeyboardButton(btn.ML_CLUB, callback_data='ml_club_info')
inlClubsMenu = InlineKeyboardMarkup().add(inlCTFClubBtn,
                                          inlDesignClubBtn,
                                          inlHackathonClubBtn,
                                          inlGameDevClubBtn,
                                          inlRoboticsClubBtn)

cwTempClose15Btn = KeyboardButton("15")
cwTempClose20Btn = KeyboardButton("20")
cwTempClose30Btn = KeyboardButton("30")
cwTempClose45Btn = KeyboardButton("45")
coworkingTempCloseDeltaMenu = ReplyKeyboardMarkup(resize_keyboard=True).add(cwTempClose15Btn,
                                                                            cwTempClose20Btn,
                                                                            cwTempClose30Btn,
                                                                            cwTempClose45Btn)
