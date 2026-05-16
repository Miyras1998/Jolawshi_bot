from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


# ─── MAIN MENUS ──────────────────────────────────────────────────────────────

def main_menu_kb():
    kb = ReplyKeyboardBuilder()
    kb.button(text="🔍 Жолаўшы режими")
    kb.button(text="🚖 Такси айдаўшы сыпатында кириў")
    kb.adjust(1)
    return kb.as_markup(resize_keyboard=True)


def passenger_menu_kb():
    kb = ReplyKeyboardBuilder()
    kb.button(text="🔍 Машина излеў")
    kb.button(text="🚖 Такси айдаўшы болыў")
    kb.button(text="📋 Меның буйыртпаларым")
    kb.button(text="👤 Профил")
    kb.button(text="💬 Жәрдем")
    kb.adjust(2, 2, 1)
    return kb.as_markup(resize_keyboard=True)


def driver_menu_kb():
    kb = ReplyKeyboardBuilder()
    kb.button(text="➕ Жаңа сапар")
    kb.button(text="🚗 Меның сапарларым")
    kb.button(text="📋 Актив буйыртпалар")
    kb.button(text="📊 Статистика")
    kb.button(text="👫 Жолаўшы режими")
    kb.button(text="👤 Профил")
    kb.adjust(2, 2, 2)
    return kb.as_markup(resize_keyboard=True)


def admin_menu_kb():
    kb = ReplyKeyboardBuilder()
    kb.button(text="📊 Статистика")
    kb.button(text="⚙️ Сазламалар")
    kb.button(text="👥 Пайдаланыўшылар")
    kb.button(text="🚗 Барлық сапарлар")
    kb.button(text="📢 Хабар жибериў")
    kb.button(text="🔙 Тийкарғы меню")
    kb.adjust(2, 2, 2)
    return kb.as_markup(resize_keyboard=True)


# ─── PHONE ───────────────────────────────────────────────────────────────────

def phone_kb():
    kb = ReplyKeyboardBuilder()
    kb.button(text="📱 Телефон номерин жибериў", request_contact=True)
    return kb.as_markup(resize_keyboard=True, one_time_keyboard=True)


# ─── PRICE PICKER ────────────────────────────────────────────────────────────

def price_kb():
    kb = InlineKeyboardBuilder()
    prices = [10000, 15000, 20000, 25000, 30000]
    for p in prices:
        kb.button(text=f"{p:,} so'm".replace(",", " "), callback_data=f"price:{p}")
    kb.button(text="✏️ Қолда киргизиў", callback_data="price:manual")
    kb.adjust(2, 2, 1, 1)
    return kb.as_markup()


# ─── SEATS ───────────────────────────────────────────────────────────────────

def seats_kb():
    kb = InlineKeyboardBuilder()
    for i in range(1, 5):
        kb.button(text=f"{i} адам", callback_data=f"seats:{i}")
    kb.adjust(4)
    return kb.as_markup()


# ─── RIDE ACTIONS ────────────────────────────────────────────────────────────

def ride_actions_kb(ride_id: int):
    kb = InlineKeyboardBuilder()
    kb.button(text="✏️ Ўақытты өзгертиў", callback_data=f"edit_time:{ride_id}")
    kb.button(text="💰 Баҳаны өзгертиў", callback_data=f"edit_price:{ride_id}")
    kb.button(text="❌ Бийкарлаў", callback_data=f"cancel_ride:{ride_id}")
    kb.adjust(2, 1)
    return kb.as_markup()


def ride_join_kb(ride_id: int):
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Қабыллаў", callback_data=f"join_ride:{ride_id}")
    kb.adjust(1)
    return kb.as_markup()


def accept_reject_kb(booking_id: int):
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Қабыллаў", callback_data=f"accept:{booking_id}")
    kb.button(text="❌ Бийкарлаў", callback_data=f"reject:{booking_id}")
    kb.adjust(2)
    return kb.as_markup()


# ─── ADMIN ───────────────────────────────────────────────────────────────────

def admin_settings_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="🕐 Ашылыў ўақты", callback_data="admin_set:open_time")
    kb.button(text="🔒 Жабылыў ўақыты", callback_data="admin_set:close_time")
    kb.button(text="⏳ Дағаза мүддети", callback_data="admin_set:expire_hours")
    kb.button(text="📢 Канал ID", callback_data="admin_set:channel_id")
    kb.button(text="🔴 Ботты тоқтатыў", callback_data="admin_set:bot_stop")
    kb.button(text="🟢 Ботты иске түсириў", callback_data="admin_set:bot_start")
    kb.adjust(2, 1, 1, 2)
    return kb.as_markup()


def user_actions_kb(user_id: int, is_blocked: int):
    kb = InlineKeyboardBuilder()
    if is_blocked:
        kb.button(text="✅ Блоктан шығарыў", callback_data=f"unblock:{user_id}")
    else:
        kb.button(text="🚫 Блоклаў", callback_data=f"block:{user_id}")
    kb.button(text="📨 Хабар жибериў", callback_data=f"msg_user:{user_id}")
    kb.adjust(1)
    return kb.as_markup()


def cancel_kb():
    kb = ReplyKeyboardBuilder()
    kb.button(text="❌ Бийкарлаў")
    return kb.as_markup(resize_keyboard=True)


def passenger_request_kb(request_id: int):
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Қабыллаў", callback_data=f"accept_req:{request_id}")
    kb.adjust(1)
    return kb.as_markup()


def search_confirm_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Тастыйықлаў", callback_data="search_confirm:yes")
    kb.button(text="✏️ Өзгертиў", callback_data="search_confirm:edit")
    kb.adjust(2)
    return kb.as_markup()


def search_edit_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="📍 Қайдан", callback_data="search_edit:from_city")
    kb.button(text="🏁 Қайда", callback_data="search_edit:to_city")
    kb.button(text="📅 Ўақыты", callback_data="search_edit:dep_date")
    kb.button(text="👥 Адам саны", callback_data="search_edit:seats")
    kb.button(text="◀️ Артқа", callback_data="search_edit:back")
    kb.adjust(2, 2, 1)
    return kb.as_markup()


def rating_kb(request_id: int, driver_id: int):
    kb = InlineKeyboardBuilder()
    for i in range(1, 6):
        stars = "⭐" * i
        kb.button(text=stars, callback_data=f"rate:{request_id}:{driver_id}:{i}")
    kb.adjust(5)
    return kb.as_markup()


def confirm_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Аўа, тастыйықлаў", callback_data="confirm:yes")
    kb.button(text="❌ Жоқ", callback_data="confirm:no")
    kb.adjust(2)
    return kb.as_markup()
