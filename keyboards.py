from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


# ─── MAIN MENUS ──────────────────────────────────────────────────────────────

def main_menu_kb():
    kb = ReplyKeyboardBuilder()
    kb.button(text="🔍 Mashina qidirish")
    kb.button(text="🚖 Haydovchi sifatida kirish")
    kb.adjust(1)
    return kb.as_markup(resize_keyboard=True)


def passenger_menu_kb():
    kb = ReplyKeyboardBuilder()
    kb.button(text="📋 Safarlar ro'yxati")
    kb.button(text="🚖 Haydovchi bo'lish")
    kb.button(text="📜 Mening bronlarim")
    kb.button(text="👤 Profil")
    kb.button(text="💬 Yordam")
    kb.adjust(2, 2, 1)
    return kb.as_markup(resize_keyboard=True)


def driver_menu_kb():
    kb = ReplyKeyboardBuilder()
    kb.button(text="➕ Yangi safar")
    kb.button(text="🚗 Mening safarlarim")
    kb.button(text="📋 Faol buyurtmalar")
    kb.button(text="📊 Statistika")
    kb.button(text="👫 Yo'lovchi rejimi")
    kb.button(text="👤 Profil")
    kb.adjust(2, 2, 2)
    return kb.as_markup(resize_keyboard=True)


def admin_menu_kb():
    kb = ReplyKeyboardBuilder()
    kb.button(text="📊 Statistika")
    kb.button(text="⚙️ Sozlamalar")
    kb.button(text="👥 Foydalanuvchilar")
    kb.button(text="🚗 Barcha safarlar")
    kb.button(text="📢 Xabar yuborish")
    kb.button(text="🔙 Asosiy menyu")
    kb.adjust(2, 2, 2)
    return kb.as_markup(resize_keyboard=True)


# ─── PHONE ───────────────────────────────────────────────────────────────────

def phone_kb():
    kb = ReplyKeyboardBuilder()
    kb.button(text="📱 Telefon raqamni yuborish", request_contact=True)
    return kb.as_markup(resize_keyboard=True, one_time_keyboard=True)


# ─── PRICE PICKER ────────────────────────────────────────────────────────────

def price_kb():
    kb = InlineKeyboardBuilder()
    prices = [10000, 15000, 20000, 25000, 30000]
    for p in prices:
        kb.button(text=f"{p:,} so'm".replace(",", " "), callback_data=f"price:{p}")
    kb.button(text="✏️ Qo'lda kiritish", callback_data="price:manual")
    kb.adjust(2, 2, 1, 1)
    return kb.as_markup()


# ─── SEATS ───────────────────────────────────────────────────────────────────

def seats_kb():
    kb = InlineKeyboardBuilder()
    for i in range(1, 5):
        kb.button(text=f"{i} kishi", callback_data=f"seats:{i}")
    kb.adjust(4)
    return kb.as_markup()


# ─── RIDE ACTIONS ────────────────────────────────────────────────────────────

def ride_actions_kb(ride_id: int):
    kb = InlineKeyboardBuilder()
    kb.button(text="✏️ Vaqtni o'zgartirish", callback_data=f"edit_time:{ride_id}")
    kb.button(text="💰 Narxni o'zgartirish", callback_data=f"edit_price:{ride_id}")
    kb.button(text="❌ Bekor qilish", callback_data=f"cancel_ride:{ride_id}")
    kb.button(text="👥 Bronlar", callback_data=f"ride_bookings:{ride_id}")
    kb.adjust(2, 1, 1)
    return kb.as_markup()


def booking_kb(ride_id: int):
    kb = InlineKeyboardBuilder()
    kb.button(text="🚕 Qabul qilish", callback_data=f"book:{ride_id}")
    kb.adjust(1)
    return kb.as_markup()


def accept_reject_kb(booking_id: int):
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Qabul qilish", callback_data=f"accept:{booking_id}")
    kb.button(text="❌ Rad etish", callback_data=f"reject:{booking_id}")
    kb.adjust(2)
    return kb.as_markup()


# ─── ADMIN ───────────────────────────────────────────────────────────────────

def admin_settings_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="🕐 Ochilish vaqti", callback_data="admin_set:open_time")
    kb.button(text="🔒 Yopilish vaqti", callback_data="admin_set:close_time")
    kb.button(text="⏳ E'lon muddati", callback_data="admin_set:expire_hours")
    kb.button(text="📢 Kanal ID", callback_data="admin_set:channel_id")
    kb.button(text="🔴 Botni to'xtatish", callback_data="admin_set:bot_stop")
    kb.button(text="🟢 Botni ishga tushirish", callback_data="admin_set:bot_start")
    kb.adjust(2, 1, 1, 2)
    return kb.as_markup()


def user_actions_kb(user_id: int, is_blocked: int):
    kb = InlineKeyboardBuilder()
    if is_blocked:
        kb.button(text="✅ Blokdan chiqarish", callback_data=f"unblock:{user_id}")
    else:
        kb.button(text="🚫 Bloklash", callback_data=f"block:{user_id}")
    kb.button(text="📨 Xabar yuborish", callback_data=f"msg_user:{user_id}")
    kb.adjust(1)
    return kb.as_markup()


def cancel_kb():
    kb = ReplyKeyboardBuilder()
    kb.button(text="❌ Bekor qilish")
    return kb.as_markup(resize_keyboard=True)


def confirm_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Ha, tasdiqlash", callback_data="confirm:yes")
    kb.button(text="❌ Yo'q", callback_data="confirm:no")
    kb.adjust(2)
    return kb.as_markup()
