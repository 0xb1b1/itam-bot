#!/usr/bin/env python3

from datetime import datetime

# region Local dependencies
from modules import btntext as btn
from modules.models import CoworkingStatus
# endregion


def welcome_message(uname) -> str:
    return f"""{f"{uname}, давай знакомиться!" if uname else "Давай знакомиться!"}

Я — твой Telegram-бот ITAM ✨
Помогу тебе узнать статус коворкинга, получать обновления от твоих любимых клубов, искать команды на хаки и многое \
другое 😉

Рад видеть тебя в нашем сообществе 💚"""


def welcome_message_instructions() -> str:
    return f"""Ты, наверное, задаешься вопросом: «Как мне пользоваться этим ботом?» 🤔
Все очень просто!

Нажми на любую интересующую тебя кнопку в меню ниже — так ты можешь взаимодействовать со мной 🤖
Вот краткое описание функционала, чтобы ты не заблудился:
{btn.CLUBS_BTN} — покажет тебе список клубов, их описания и ссылки на ресурсы 📚
{btn.COWORKING_STATUS} — покажет тебе статус коворкинга, а также его местоположение на карте и подробное описание \
пути до заветного кабинета 🗺
{btn.PROFILE_INFO} — покажет тебе информацию о твоем профиле, а также позволит ее редактировать 🧑‍💼
{btn.HELP_MAIN} — покажет тебе меню помощи и информации о сообществе и боте 💃

Буду с нетерпением ждать твоих команд! 🤩
"""


def welcome_message_go() -> str:
    return f"""Поехали! 🚀"""


def start_command_found_calling_skill() -> str:
    return "🔎 Диплинк найден! Вызываю навык... 🚀"


def start_command_not_found() -> str:
    return "❌ Диплинк не найден. Попробуй /start"


def permission_denied() -> str:
    return "❌ У вас недостаточно прав для выполнения этой команды"


def skill_names() -> dict:
    return {
        'backend': 'Backend',
        'frontend': 'Frontend',
        'devops': 'DevOps',
        'analytics': 'Аналитика',
        'infosec': 'Инфобез',
        'mobile_dev': 'Мобильная разработка',
        'design': 'Дизайн',
        'robotics': 'Робототехника',
        'gamedev': 'Геймдев'
    }


def profile_fields() -> dict:
    return {
        "first_name": "Имя",
        "last_name": "Фамилия",
        "gname": "Группа",
        "birthday": "День рождения",
        "phone": "Телефон",
        "email": "Почта",
        "bio": "Био",
        "resume": "Резюме",
        "skills": "Компетенции"
    }


def profile_info(info) -> str:
    fields = profile_fields()
    return f"""🛂 Информация о пользователе

{fields['first_name']}: {is_set(info['first_name'])}
{fields['last_name']}: {is_set(info['last_name'])}
{fields['gname']}: {info['gname']}
{fields['birthday']}: {datetime.strftime(info['birthday'],
                                         "%d.%m.%Y") 
    if info['birthday'] is not None else is_set(None)}
{fields['phone']}: {f"+{info['phone']}" if info['phone'] is not None else btn.NOT_SET}
{fields['email']}: {is_set(info['email'])}
{fields['skills']}: {btn.NOT_SET if len(info['skills']) == 0
    else ', '.join(skill_names()[skill.name] for skill in info['skills'])}"""


def profile_edit_first_name(first_name: str, last_name: str) -> str:
    return f"""🛂 Изменение имени

Текущее имя: {first_name}
Фамилия: {last_name}

Отправь новое имя"""


def profile_edit_last_name(first_name: str, last_name: str) -> str:
    return f"""🛂 Изменение фамилии

Имя: {first_name}
Текущая фамилия: {last_name}

Отправь новую фамилию"""


def profile_edit_birthday(birthday: datetime):
    return f"""🛂 Изменение даты рождения

Текущая дата рождения: {datetime.strftime(birthday, "%d.%m.%Y") if birthday else "None"}

Отправь новую дату в формате DD.MM.YYYY"""


def profile_edit_email(email: str) -> str:
    return f"""🛂 Изменение даты рождения

Текущий email: {email}

Формат: example@exampledomain.com
Отправь новый адрес электронной почты"""


def profile_edit_phone(phone: int) -> str:
    return f"""🛂 Изменение номера телефона

Текущий номер: {phone}

Формат: +79991230101 или 79991230101
Отправь новый номер телефона"""


def profile_edit_skills() -> str:
    return f"""🛂 Изменение компетенций

Выбери компетенции, которые тебе ближе"""


def invalid_date_try_again() -> str:
    return f"""❌ Неверный формат даты

Формат: DD.MM.YYYY
Попробуй еще раз :)"""


def invalid_email_try_again() -> str:
    return f"""❌ Неверный формат email

Формат: example@exampledomain.com
Попробуй еще раз :)"""


def invalid_phone_try_again() -> str:
    return f"""❌ Неверный формат номера телефона

Формат: +79991230101 или 79991230101
Попробуй еще раз :)"""


def please_start_bot() -> str:
    return f"""❌ Что-то пошло не так... Давай попробуем восстановить твой аккаунт: /start"""


# region Profile setup
def profile_setup_first_name() -> str:
    return """🛂 Настройка профиля

Отправь свое имя"""


def profile_setup_last_name(first_name: str) -> str:
    return f"""🛂 Настройка профиля
✅ Имя установлено: {first_name}

Отправь свою фамилию"""


def profile_setup_birthday(last_name: str) -> str:
    return f"""🛂 Настройка профиля
✅ Фамилия установлена: {last_name}

Отправь свою дату рождения в формате DD.MM.YYYY"""


def profile_setup_email(birthday: datetime) -> str:
    return f"""🛂 Настройка профиля
✅ Дата рождения установлена: {datetime.strftime(birthday, "%d.%m.%Y")}

Отправь свой email"""


def profile_setup_phone(email: str) -> str:
    return f"""🛂 Настройка профиля
✅ Email установлен: {email}

Отправь свой номер телефона в формате +79991230101 или 79991230101"""


def profile_setup_skills(phone: int) -> str:
    return f"""🛂 Настройка профиля
✅ Номер телефона установлен: +{str(phone)}

Укажи компетенции, которые тебе ближе"""


# def profile_setup_success(phone: int) -> str:
#     return f"""🛂 Настройка профиля
# ✅ Номер телефона установлен: +{str(phone)}

# 🎉 Профиль успешно настроен!"""
# endregion


def profile_edit_success() -> str:
    return "✅ Информация обновлена"


def is_set(data) -> str:
    return data if data else btn.NOT_SET


def coworking_notifications_on() -> str:
    return "🔔🟢 Уведомления о статусе коворкинга включены"


def coworking_notifications_off() -> str:
    return "🔔🔴 Уведомления о статусе коворкинга выключены"


def get_coworking_status_reply_data(status: CoworkingStatus,
                                    responsible_uname: str = None,
                                    delta_mins: int = 0,
                                    responsible_account: bool = True,
                                    one_newline: bool = False) -> tuple:
    """Return reply data for coworking status"""
    newline = "\n" if one_newline else "\n\n"
    postfix_msg = f"{newline}Ответственный: @{responsible_uname}" if responsible_account else ""
    if delta_mins > 0 and delta_mins is not None:
        postfix_msg = f" (на {delta_mins} минут)!" + postfix_msg
    if status == CoworkingStatus.open:
        status_icon = "🟢"
        status_str = f"открыт{postfix_msg}"
    elif status == CoworkingStatus.event_open:
        status_icon = "🟡"
        status_str = f"открыт (проходит мероприятие!){postfix_msg}"
    elif status == CoworkingStatus.event_closed:
        status_icon = "⛔️"
        status_str = f"закрыт на мероприятие{postfix_msg}"
    elif status == CoworkingStatus.temp_closed:
        status_icon = "🟠"
        status_str = f"временно закрыт{postfix_msg}"  # User without `@`
    elif status == CoworkingStatus.closed:
        status_icon = "🔴"
        status_str = f"закрыт{postfix_msg}"
    else:
        status_icon = "❓"
        status_str = "[статус неизвестен]"
    return status_icon, status_str


def coworking_status_reply(status: CoworkingStatus,
                           responsible_uname: str = "(не назначен)",
                           delta_mins: int = 0) -> str:
    """Return coworking status reply string"""
    status_icon, status_str = get_coworking_status_reply_data(status,
                                                              responsible_uname=responsible_uname,
                                                              delta_mins=delta_mins)
    return f"🔑{status_icon} Коворкинг ITAM (Г-511) {status_str}"


def switch_coworking_status_inline_binary_action(status: CoworkingStatus) -> str:
    """Return coworking status inline action (to do) string [open/close]"""
    status_icon, status_str = get_coworking_status_reply_data(status, responsible_account=False)
    status_inl = status_str + " " + status_icon
    if status in [CoworkingStatus.open, CoworkingStatus.event_open]:
        action_inl = "Закрыть"
    elif status in [CoworkingStatus.temp_closed, CoworkingStatus.closed]:
        action_inl = "Открыть"
    else:
        raise ValueError("Invalid status")
    return f"{action_inl} коворкинг (сейчас {status_inl})"


def switch_coworking_from_nonbinary_action(status: CoworkingStatus, to_open: bool) -> str:
    """Accepts only CoworkingStatus.temp_closed or CoworkingStatus.event_open"""
    if status not in [CoworkingStatus.temp_closed, CoworkingStatus.event_open]:
        raise ValueError("Invalid status")
    status_icon, status_str = get_coworking_status_reply_data(status, responsible_account=False)
    status_inl = status_str + " " + status_icon
    return f"{'Открыть' if to_open else 'Закрыть'} коворкинг (сейчас {status_inl})"


def coworking_status_changed(status: CoworkingStatus,
                             responsible_uname: str = "(не назначен)",
                             delta_mins: int = 0) -> str:
    status_icon, status_str = get_coworking_status_reply_data(status,
                                                              responsible_uname=responsible_uname,
                                                              delta_mins=delta_mins)
    return f"🔑{status_icon} Коворкинг ITAM (Г-511) {status_str}"


def coworking_status_not_binary() -> str:
    return "❌ Невозможно выполнить действие: коворкинг не в открытом или закрытом состоянии"


def plaintext_answers_reply(status: bool, toggled: bool = False, chat_id: int = None, admin_uname: str = None) -> str:
    return f"Ответы на обычные сообщения{' теперь' if toggled else ''} \
{'включены 🟢' if status else 'выключены 🔴'}{f' для чата {str(chat_id)}' if chat_id else ''}\
{f' администратором @{admin_uname}' if admin_uname else ''}"


def menu_updated_reply(user_count: int, admins_only: bool = False) -> str:
    return f"Меню обновлено для {user_count} {'пользователей' if not admins_only else 'администраторов'}"


def profile_info_only_in_pm() -> str:
    return "🛂‼️ Эту команду можно использовать только в личных сообщениях"


def coworking_status_only_in_pm() -> str:
    return "🔑‼️ Эту команду можно использовать только в личных сообщениях"


def please_click_start() -> str:
    return "🛂‼️ Пожалуйста, нажмите сюда: /start"


def help_message() -> str:
    return """🤨 Помощь ITAM Bot

[Разработчик](https://t.me/oxb1b1)
[Сайт проекта](https://go.itatmisis.ru)"""


def cancel_action() -> str:
    return "/cancel — ❌ Отменить действие"


def admin_panel() -> str:
    return """🛂 Панель администратора

兀 Команды

🧑‍💻 Администрация
/admin — 🛂 Показать эту панель
/stats — 📊 Показать статистику

💃 Пользователи
/get_users — 📋 Получить список пользователей
/get_users_verbose — 📋📝 Получить список пользователей с подробной информацией
/get_notif_db — 📋🔔 Получить список пользователей и их настройки уведомлений

🦊 Разное
/broadcast — 📢 Создать рассылку
/cancel — ❌ Отменить любой flow"""


def stats(statistics: dict) -> str:
    """Display statistics for admins"""
    cw_icon, cw_status = get_coworking_status_reply_data(statistics["coworking_status"],
                                                         responsible_account=False)
    cw_status = f"{cw_icon} {cw_status}"
    return f"""📊 Статистика

💃 Пользователей: {statistics['users']}
🧑‍💻 Администраторов: {statistics['admins']}
🔑 Статус коворкинга: {cw_status}
💫 Изменений статуса коворкинга: {statistics['coworking_log_count']}
🔔 Пользователей с включенными уведомлениями: {statistics['coworking_notifications']}"""


def club_info_general() -> str:
    return """👩‍🎨🥷🎮💸🧑‍💻
Информация о клубах"""


def ctf_club_info() -> str:
    return """🥷🧑‍💻 CTF Club

CTF клуб занимается изучением программного обеспечения для дальшего поиска уязвимостей и обеспечения информационной \
безопасности.

CTF (Capture the Flag/Захват Флага) — командные совернования в области компьютерной (информационной) безопасности. \
Разностороннее развитие в IT, компетентность и глубокий уровень познаний — все это получают ученики CTF клуба.

Члены CTF клуба принимают участие в регулярных внутренних соревнованиях, которые помогают отточить навыки для \
дальнейшего участия в городских, федеральных и международных конкурсах.

📌 Контакты

[⚡️ Руководитель](https://t.me/oxb1b1)
[💬 Чат](https://t.me/+lgw8dT2HFuRhZmFi)
[📣 Канал](https://t.me/misis_ctf)
"""


def hackathon_club_info() -> str:
    return """💸🧑‍💻 Hackathon Club

Участники клуба активно принимают участие в хакатонах.
Командам предоставляется экспертная поддержка, технической инфраструктурой.

📌 Контакты

[⚡️ Руководитель](https://t.me/Daniil_Y)
[💬 Чат](https://t.me/+WQeYWDOPnvs5yhhY)
"""


def gamedev_club_info() -> str:
    return """🎮🧑‍💻 GameDev Club

В клубе игровых разработчиков студенты совместно изучают особенности игровой индустрии,
учаться работать с различными технологиями для разработки игр и участвуют в соревнованиях игровых разработчиков GameJam.

📌 Контакты

[⚡️ Руководитель](https://t.me/kerliaa)
[💬 Чат](https://t.me/+MH0JVkTEsmozYzRi)
"""


def design_club_info() -> str:
    return """👩‍🎨🧑‍💻 Design at MISIS Now

DAMN — это не просто клуб, это школа и дизайн-студия, в которой каждый студент может получить теоретические \
и практические навыки.
Участники движения хакатонят и разрабатывают коммерческие продукты.

📌 Контакты

[⚡️ Руководитель](https://t.me/a_asyotr)
[💬 Чат](https://t.me/+zTBGzdqNc4xlZWUy)
"""


def robotics_club_info() -> str:
    return """🤖🧑‍💻 Robotics Club

Клуб робототехников, работающих с передовыми технологиями
в сфере проектирования и программирования роботов.

📌 Контакты

(Crickets' chirp)
"""


def coworking_closed_during_hours() -> str:
    return """🚧 Коворкинг закрыт в рабочее время!"""


def coworking_open_after_hours() -> str:
    return """🚧 Коворкинг открыт в нерабочее время!"""


def coworking_status_already_responsible() -> str:
    return """🔑🚧🔴 Ты уже отвечаешь за коворкинг!"""


def coworking_status_now_responsible() -> str:
    return """🔑🚧🟢 Теперь ты отвечаешь за коворкинг!"""


def bot_credits() -> str:
    return """🤖 Бот разработан в **ITAM**
[💙 Telegram](https://t.me/itatmisis)
[🚾 VK](https://vk.com/itatmisis)

📌 Контакты разработчиков
Аксель @oxb1b1"""


def user_group_changed() -> str:
    return """👥 Группа пользователя изменена"""


def broadcast_successful() -> str:
    return """📢 Рассылка успешна"""


def toggle_coworking_notifications(curr_status: bool) -> str:
    return f"[{'🟢' if curr_status else '🔴'}] {'Выключить' if curr_status else 'Включить'} уведомления"


def coworking_location_info() -> str:
    return """📍 Коворкинг находится в корпусе Г, 5 этаж, 511 кабинет

Чтобы попасть к нам, зайди в Горный институт, поверни направо за лестницей и поднимись на 5 этаж (можно на лифте ;)

Ждем тебя!"""


def coworking_status_explain(responsible_uname: str) -> str:
    return f"""Ответственный за коворкинг — человек, у которого находятся ключи от Г511

Если у тебя возникнут вопросы, связанные с коворкингом ITAM, [напиши этому человеку в ЛС]\
(https://t.me/{responsible_uname})!"""


# region Yandex Internship
def yandex_internship_control_panel() -> str:
    return """🔑 Панель управления Яндекс Стажировкой"""
# endregion
