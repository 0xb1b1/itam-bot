#!/usr/bin/env python3
# region Local dependencies
from modules import btntext as btn
# endregion

def pong():
    return "Pong!"

def welcome_message(uname) -> str:
    return f"""Привет, {uname}!

Я — Telegram-бот ITAM. Помогу тебе узнать статус коворкинга, получать обновления от твоих любимых клубов и искать команды на хаки.

Поехали!"""

def coworking_status(is_open: bool) -> str:
    status_str = "открыт" if is_open else "закрыт"
    return f"🔑{'🟢' if is_open else  '🔴'} Коворкинг сейчас {status_str}"

def permission_denied() -> str:
    return "❌ У вас недостаточно прав для выполнения этой команды"

def profile_fields() -> dict:
    return {
        "name": "Имя",
        "gname": "Группа",
        "birthday": "День рождения",
        "phone": "Телефон",
        "email": "Почта",
        "bio": "Био",
        "resume": "Резюме"
    }

def profile_info(info) -> str:
    fields = profile_fields()
    return f"""🛂 Информация о пользователе

Имя: {info['name']}
{fields['gname']}: {info['gname']}
{fields['birthday']}: {is_set(info['birthday'])}
{fields['phone']}: {is_set(info['phone'])}
{fields['email']}: {is_set(info['email'])}
{fields['bio']}: /bio
{fields['resume']}: /resume"""

def is_set(data) -> str:
    return data if data else btn.NOT_SET

def coworking_notifications_on() -> str:
    return "🔔🟢 Уведомления о статусе коворкинга включены"

def coworking_notifications_off() -> str:
    return "🔔🔴 Уведомления о статусе коворкинга выключены"

def coworking_status_changed(is_open: bool) -> str:
    status_str = "открыт" if is_open else "закрыт"
    return f"🔑{'🟢' if is_open else  '🔴'} Коворкинг ITAM (Г-511) {status_str}!"

def profile_info_only_in_pm() -> str:
    return "🛂‼️ Эту команду можно использовать только в личных сообщениях"

def help_message() -> str:
    return """Список команд:

/notify — 🔔 включить/выключить уведомления о статусе коворкинга"""

def cancel_action() -> str:
    return "/cancel — ❌ Отменить действие"

def admin_panel(is_coworking_open: bool) -> str:
    return f"""🛂 Панель администратора

Команды:
/admin — 🛂 Показать эту панель
/stats — 📊 Показать статистику
/coworking_toggle — 🔑🟢🔴 Переключить статус коворкинга (сейчас {'открыт 🟢' if is_coworking_open else 'закрыт 🔴'})
/coworking_open — 🔑🟢 Открыть коворкинг
/coworking_close — 🔑🔴 Закрыть коворкинг
/broadcast — 📢 Рассылка
/get_users — 📋 Получить список пользователей
/get_users_verbose — 📋📝 Получить список пользователей с подробной информацией
/get_notif_db — 📋🔔 Получить список пользователей и их настройки уведомлений

/cancel — ❌ Отменить любой flow"""

def stats(stats: dict) -> str:
    """Display statistics for admins"""
    return f"""📊 Статистика

💃 Пользователей: {stats['users']}
🧑‍💻 Администраторов: {stats['admins']}
🔑 Статус коворкинга: {'🟢 Открыт' if stats['coworking_status'] else '🔴 Закрыт'}
💫 Изменений статуса коворкинга: {stats['coworking_log_count']}
🔔 Пользователей с включенными уведомлениями: {stats['coworking_notifications']}"""

def club_info_general() -> str:
    return """👩‍🎨🥷🎮💸🧑‍💻
Информация о клубах"""

def ctf_club_info() -> str:
    return """🥷🧑‍💻 CTF Клуб

CTF клуб занимается изучением программного обеспечения для дальшего поиска уязвимостей и обеспечения информационной безопасности.

CTF (Capture the Flag/Захват Флага) — командные совернования в области компьютерной (информационной) безопасности. Разностороннее развитие в IT, компетентность и глубокий уровень познаний — все это получают ученики CTF клуба.

Члены CTF клуба принимают участие в регулярных внутренних соревнованиях, которые помогают отточить навыки для дальнейшего участия в городских, федеральных и международных конкурсах.
"""

def hackathon_club_info() -> str:
    return """💸🧑‍💻 Хакатон Клуб

Здесь должен быть текст!
"""

def gamedev_club_info() -> str:
    return """🎮🧑‍💻 Gamedev Клуб

В клубе игровых разработчиков студенты совместно изучают особенности игровой индустрии, учаться работать с различными технологиями для разработки игр
и участвуют в соревнованиях игровых разработчиков GameJam.
"""

def design_club_info() -> str:
    return """👩‍🎨🧑‍💻 Дизайн Клуб

Здесь должен быть текст!
"""