from aiogram.dispatcher.filters.state import State, StatesGroup

class AdminChangeUserGroup(StatesGroup):
    user_id = State()
    group_id = State()

class AdminBroadcast(StatesGroup):
    message = State()
    scope = State()
    confirm = State()

class AdminCoworkingTempCloseFlow(StatesGroup):
    delta = State()
    notification = State()
    confirm = State()

class UserEditProfile(StatesGroup):
    selector = State()
    first_name = State()
    last_name = State()
    birthday = State()
    email = State()
    phone = State()
