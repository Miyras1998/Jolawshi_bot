from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Filter

from config import ADMIN_IDS
from database import (get_stats, get_all_users, get_all_rides_admin,
                      block_user, get_setting, set_setting, get_all_settings)
from keyboards import admin_menu_kb, admin_settings_kb, user_actions_kb, cancel_kb

router = Router()


class IsAdmin(Filter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in ADMIN_IDS


class AdminStates(StatesGroup):
    set_open_time = State()
    set_close_time = State()
    set_expire = State()
    set_channel = State()
    broadcast = State()
    msg_user = State()
    msg_user_id = State()


# ─── ADMIN PANEL ─────────────────────────────────────────────────────────────

@router.message(IsAdmin(), F.text == "📊 Statistika")
async def admin_stats(message: Message):
    stats = await get_stats()
    await message.answer(
        f"📊 <b>Bot statistikasi</b>\n\n"
        f"👥 Жәми пайдаланыўшылар: <b>{stats['total_users']}</b>\n"
        f"🚖 Такси айдаўшылар: <b>{stats['total_drivers']}</b>\n"
        f"🔍 Жолаўшылар: <b>{stats['total_users'] - stats['total_drivers']}</b>\n\n"
        f"🚗 Жәми сапарлар: <b>{stats['total_rides']}</b>\n"
        f"🟢 Актив сапарлар: <b>{stats['active_rides']}</b>\n"
        f"📋 Жәми броньлаўлар: <b>{stats['total_bookings']}</b>",
        parse_mode="HTML"
    )


@router.message(IsAdmin(), F.text == "⚙️ Sozlamalar")
async def admin_settings(message: Message):
    s = await get_all_settings()
    text = (
        f"⚙️ <b>Sozlamalar</b>\n\n"
        f"🕐 Ашылыў: <b>{s.get('rides_open_hour','6'):>02}:{s.get('rides_open_minute','0'):>02}</b>\n"
        f"🔒 Жабылыў: <b>{s.get('rides_close_hour','22'):>02}:{s.get('rides_close_minute','0'):>02}</b>\n"
        f"⏳ Дағаза мүддети: <b>{s.get('ride_expire_hours','24')} soat</b>\n"
        f"📢 Канал: <b>{s.get('channel_id','—')}</b>\n"
        f"🤖 Бот жағдайы: <b>{'🟢 Актив' if s.get('bot_active','1')=='1' else '🔴 Тоқтатылған'}</b>"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=admin_settings_kb())


@router.callback_query(F.data.startswith("admin_set:"))
async def admin_set_cb(call: CallbackQuery, state: FSMContext):
    if call.from_user.id not in ADMIN_IDS:
        await call.answer("❌ Рухсат жоқ!")
        return
    action = call.data.split(":")[1]

    if action == "open_time":
        await call.message.answer("🕐 Ашылыў ўақтын киргизиң (Masalan: 06:00):", reply_markup=cancel_kb())
        await state.set_state(AdminStates.set_open_time)
    elif action == "close_time":
        await call.message.answer("🔒 Жабылыў ўақтын киргизиң (Masalan: 22:00):", reply_markup=cancel_kb())
        await state.set_state(AdminStates.set_close_time)
    elif action == "expire_hours":
        await call.message.answer("⏳ Хабарландырыў неше сааттан кейин өшсин? (Masalan: 24):", reply_markup=cancel_kb())
        await state.set_state(AdminStates.set_expire)
    elif action == "channel_id":
        await call.message.answer("📢 Канал username киргизиң (Masalan: @mening_kanalim):", reply_markup=cancel_kb())
        await state.set_state(AdminStates.set_channel)
    elif action == "bot_stop":
        await set_setting("bot_active", "0")
        await call.message.answer("🔴 Бот тоқтатылды!")
    elif action == "bot_start":
        await set_setting("bot_active", "1")
        await call.message.answer("🟢 Бот иске түсирилди!")
    await call.answer()


@router.message(AdminStates.set_open_time, F.text != "❌ Бийкарлаў")
async def set_open_time(message: Message, state: FSMContext):
    try:
        parts = message.text.strip().split(":")
        h, m = int(parts[0]), int(parts[1])
        assert 0 <= h <= 23 and 0 <= m <= 59
        await set_setting("rides_open_hour", str(h))
        await set_setting("rides_open_minute", str(m))
        await state.clear()
        await message.answer(f"✅ Ашылыў ўақты: <b>{h:02d}:{m:02d}</b>", parse_mode="HTML", reply_markup=admin_menu_kb())
    except:
        await message.answer("❌ Надурис формат! Мәселен: 06:00")


@router.message(AdminStates.set_close_time, F.text != "❌ Бийкарлаў")
async def set_close_time(message: Message, state: FSMContext):
    try:
        parts = message.text.strip().split(":")
        h, m = int(parts[0]), int(parts[1])
        assert 0 <= h <= 23 and 0 <= m <= 59
        await set_setting("rides_close_hour", str(h))
        await set_setting("rides_close_minute", str(m))
        await state.clear()
        await message.answer(f"✅ Жабылыў ўақты: <b>{h:02d}:{m:02d}</b>", parse_mode="HTML", reply_markup=admin_menu_kb())
    except:
        await message.answer("❌ Надурис формат! Мәселен: 22:00")


@router.message(AdminStates.set_expire, F.text != "❌ Бийкарлаў")
async def set_expire(message: Message, state: FSMContext):
    try:
        h = int(message.text.strip())
        assert 1 <= h <= 168
        await set_setting("ride_expire_hours", str(h))
        await state.clear()
        await message.answer(f"✅ Дағаза мүддети: <b>{h} soat</b>", parse_mode="HTML", reply_markup=admin_menu_kb())
    except:
        await message.answer("❌ 1-168 арасына сан киргизиң!")


@router.message(AdminStates.set_channel, F.text != "❌ Бийкарлаў")
async def set_channel(message: Message, state: FSMContext):
    channel = message.text.strip()
    await set_setting("channel_id", channel)
    await state.clear()
    await message.answer(f"✅ Канал: <b>{channel}</b>", parse_mode="HTML", reply_markup=admin_menu_kb())


# ─── USERS ───────────────────────────────────────────────────────────────────

@router.message(IsAdmin(), F.text == "👥 Пайдаланыўшылар")
async def admin_users(message: Message):
    users = await get_all_users()
    await message.answer(f"👥 <b>Пайдаланыўшылар</b> ({len(users)} ta):", parse_mode="HTML")
    for u in users[:20]:
        blocked = "🚫" if u["is_blocked"] else "✅"
        role_map = {"passenger": "Жолаўшы", "driver": "Такси айдаўшы", "both": "Екеўи де"}
        text = (
            f"{blocked} <b>{u['full_name']}</b>\n"
            f"📱 {u['phone'] or '—'}\n"
            f"🎭 {role_map.get(u['role'], u['role'])}"
        )
        await message.answer(text, parse_mode="HTML", reply_markup=user_actions_kb(u["telegram_id"], u["is_blocked"]))


@router.callback_query(F.data.startswith("block:"))
async def block_user_cb(call: CallbackQuery):
    if call.from_user.id not in ADMIN_IDS:
        return
    user_id = int(call.data.split(":")[1])
    await block_user(user_id, 1)
    await call.message.edit_reply_markup(reply_markup=user_actions_kb(user_id, 1))
    await call.answer("🚫 Блокланды!")


@router.callback_query(F.data.startswith("unblock:"))
async def unblock_user_cb(call: CallbackQuery):
    if call.from_user.id not in ADMIN_IDS:
        return
    user_id = int(call.data.split(":")[1])
    await block_user(user_id, 0)
    await call.message.edit_reply_markup(reply_markup=user_actions_kb(user_id, 0))
    await call.answer("✅ Блоктан шығарылды!")


@router.callback_query(F.data.startswith("msg_user:"))
async def msg_user_start(call: CallbackQuery, state: FSMContext):
    if call.from_user.id not in ADMIN_IDS:
        return
    user_id = int(call.data.split(":")[1])
    await state.update_data(target_user_id=user_id)
    await call.message.answer("✉️ Жибермекши болған хабарыңызды киргизиң:", reply_markup=cancel_kb())
    await state.set_state(AdminStates.msg_user)
    await call.answer()


@router.message(AdminStates.msg_user, F.text != "❌ Бийкарлаў")
async def msg_user_send(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    try:
        await bot.send_message(data["target_user_id"], f"📨 <b>Админ хабары:</b>\n\n{message.text}", parse_mode="HTML")
        await message.answer("✅ Xabar yuborildi!", reply_markup=admin_menu_kb())
    except:
        await message.answer("❌ Хабар жиберип болмайды!", reply_markup=admin_menu_kb())
    await state.clear()


# ─── ALL RIDES ───────────────────────────────────────────────────────────────

@router.message(IsAdmin(), F.text == "🚗 Барлық сапарлар")
async def admin_all_rides(message: Message):
    rides = await get_all_rides_admin()
    if not rides:
        await message.answer("🚗 Еле сапарлар жоқ.")
        return
    await message.answer(f"🚗 <b>Барлық сапарлар</b> ({len(rides)} ta):", parse_mode="HTML")
    for r in rides[:15]:
        status_map = {"active": "🟢", "cancelled": "🔴", "completed": "✅"}
        text = (
            f"{status_map.get(r['status'],'•')} #{r['id']} | {r['from_city']} → {r['to_city']}\n"
            f"📅 {r['departure_time']} | 💰 {r['price']:,} so'm\n"
            f"👤 {r['full_name']} | 📱 {r['phone']}"
        ).replace(",", " ")
        await message.answer(text, parse_mode="HTML")


# ─── BROADCAST ───────────────────────────────────────────────────────────────

@router.message(IsAdmin(), F.text == "📢 Хабар жибериў")
async def broadcast_start(message: Message, state: FSMContext):
    await message.answer(
        "📢 <b>Ғалаба хабар</b>\n\nБарлық пайдаланыўшыларға жиберилетуғын хабарды киргизиң:",
        parse_mode="HTML",
        reply_markup=cancel_kb()
    )
    await state.set_state(AdminStates.broadcast)


@router.message(AdminStates.broadcast, F.text != "❌ Бийкарлаў")
async def broadcast_send(message: Message, state: FSMContext, bot: Bot):
    users = await get_all_users()
    sent, failed = 0, 0
    await message.answer(f"📤 {len(users)} пайдаланыўшыларға жиберилмекте...")
    for u in users:
        if u["is_blocked"]:
            continue
        try:
            await bot.send_message(u["telegram_id"], f"📢 <b>Админ хабары:</b>\n\n{message.text}", parse_mode="HTML")
            sent += 1
        except:
            failed += 1
    await state.clear()
    await message.answer(
        f"✅ <b>Жиберилди!</b>\n\n✅ Табыслы: {sent}\n❌ Қәте: {failed}",
        parse_mode="HTML",
        reply_markup=admin_menu_kb()
    )


# ─── CANCEL ──────────────────────────────────────────────────────────────────

@router.message(IsAdmin(), F.text == "❌ Бийкарлаў")
async def admin_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Бийкарланды.", reply_markup=admin_menu_kb())
