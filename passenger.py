from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database import (get_user, get_active_rides, create_booking, get_booking,
                      get_ride, get_passenger_bookings, update_user_role, get_setting)
from keyboards import passenger_menu_kb, driver_menu_kb, booking_kb

router = Router()


def is_rides_open(open_h, open_m, close_h, close_m) -> bool:
    from datetime import datetime
    now = datetime.now()
    cur = now.hour * 60 + now.minute
    return (open_h * 60 + open_m) <= cur < (close_h * 60 + close_m)


@router.message(F.text == "🔍 Машина излеў")
async def search_rides(message: Message):
    user = await get_user(message.from_user.id)
    if not user or not user["phone"]:
        await message.answer("❌ Дәслеп /start арқалы дизимнен өтиң!")
        return
    await message.answer("🔍 Жолаўшы режиминдесиз.", reply_markup=passenger_menu_kb())


@router.message(F.text == "📋 Сапарлар дизими")
async def show_rides(message: Message):
    # Ўақыт тексериў
    open_h = int(await get_setting("rides_open_hour") or 6)
    open_m = int(await get_setting("rides_open_minute") or 0)
    close_h = int(await get_setting("rides_close_hour") or 22)
    close_m = int(await get_setting("rides_close_minute") or 0)

    if not is_rides_open(open_h, open_m, close_h, close_m):
        await message.answer(
            f"🔒 <b>Сапарлар дизими ҳәзир жабық</b>\n\n"
            f"🟢 Ашылады: <b>{open_h:02d}:{open_m:02d}</b>\n"
            f"🔴 Жабылады: <b>{close_h:02d}:{close_m:02d}</b>\n\n"
            "Кейинирек қайта көриң!",
            parse_mode="HTML"
        )
        return

    rides = await get_active_rides()
    expire_h = int(await get_setting("ride_expire_hours") or 24)

    if not rides:
        await message.answer("😔 Ҳәзирше актив сапарлар жоқ.\n\nКейинирек қайтып келиң!")
        return

    await message.answer(f"📋 <b>Актив сапарлар</b> ({len(rides)} ta):", parse_mode="HTML")

    from datetime import datetime
    count = 0
    for r in rides:
        # Мүддети өткенлерди шығармаў
        created = datetime.fromisoformat(r["created_at"])
        age_h = (datetime.now() - created).total_seconds() / 3600
        if age_h >= expire_h:
            continue

        remain_h = expire_h - age_h
        if remain_h < 1:
            remain = f"{int(remain_h * 60)} daqiqa"
        else:
            remain = f"{int(remain_h)} soat"

        text = (
            f"🆔 #{r['id']}\n"
            f"📍 <b>{r['from_city']}</b> → <b>{r['to_city']}</b>\n"
            f"📅 {r['departure_time']}\n"
            f"👥 {r['seats']} o'rin · 💰 {r['price']:,} сум / адам\n"
            f"📞 {r['phone']}\n"
            f"⏳ {remain} қалды"
        ).replace(",", " ")

        await message.answer(text, parse_mode="HTML", reply_markup=booking_kb(r["id"]))
        count += 1

    if count == 0:
        await message.answer("😔 Ҳәзирше актив сапарлар жоқ.")


@router.callback_query(F.data.startswith("book:"))
async def book_ride(call: CallbackQuery, bot: Bot):
    ride_id = int(call.data.split(":")[1])
    user = await get_user(call.from_user.id)

    if not user or not user["phone"]:
        await call.answer("❌ Дәслеп /start арқалы дизимнен өтиң!", show_alert=True)
        return

    ride = await get_ride(ride_id)
    if not ride or ride["status"] != "active":
        await call.answer("❌ Бул сапар жоқ ямаса бийкар етилген!", show_alert=True)
        return

    if ride["driver_id"] == call.from_user.id:
        await call.answer("❌ Өз сапарыңызды бронлай алмайсыз!", show_alert=True)
        return

    booking_id = await create_booking(ride_id, call.from_user.id)
    if not booking_id:
        await call.answer("⚠️ Сиз әллеқашан бул сапарыңызды бәнтлеп қойыпсыз!", show_alert=True)
        return

    # Такси айдаўшыға хабар
    driver = await get_user(ride["driver_id"])
    from keyboards import accept_reject_kb
    try:
        await bot.send_message(
            ride["driver_id"],
            f"🔔 <b>Жаңа брон!</b>\n\n"
            f"👤 Жолаўшы: <b>{user['full_name']}</b>\n"
            f"📱 Телефон: <b>{user['phone']}</b>\n"
            f"📍 {ride['from_city']} → {ride['to_city']}\n"
            f"📅 {ride['departure_time']}",
            parse_mode="HTML",
            reply_markup=accept_reject_kb(booking_id)
        )
    except:
        pass

    # Каналда хабарды жаңалаў
    channel_id = await get_setting("channel_id")
    if ride["channel_msg_id"]:
        try:
            await bot.edit_message_text(
                f"✅ <b>Бул сапар қабыл етилди!</b>\n\n"
                f"📍 {ride['from_city']} → {ride['to_city']}\n"
                f"📅 {ride['departure_time']}",
                chat_id=channel_id,
                message_id=ride["channel_msg_id"],
                parse_mode="HTML"
            )
        except:
            pass

    await call.answer(
        f"✅ Буйыртпа жиберилди! Такси айдаўшы {driver['phone'] if driver else ''} Сиз бенен байланысады.",
        show_alert=True
    )


@router.message(F.text == "📜 Меның бронларым")
async def my_bookings(message: Message):
    bookings = await get_passenger_bookings(message.from_user.id)
    if not bookings:
        await message.answer("📜 Ҳәзирше бронлар жоқ.")
        return

    await message.answer(f"📜 <b>Бронларым</b> ({len(bookings)} ta):", parse_mode="HTML")
    for b in bookings:
        status_map = {
            "pending": "⏳ Күтилмекте",
            "accepted": "✅ Қабыл етилди",
            "rejected": "❌ Бийкар етилди"
        }
        text = (
            f"📍 {b['from_city']} → {b['to_city']}\n"
            f"📅 {b['departure_time']}\n"
            f"💰 {b['price']:,} сум\n"
            f"📌 {status_map.get(b['status'], b['status'])}"
        ).replace(",", " ")
        await message.answer(text, parse_mode="HTML")


@router.message(F.text == "🚖 Такси айдаўшы болыў")
async def become_driver_from_passenger(message: Message):
    await update_user_role(message.from_user.id, "both")
    await message.answer(
        "✅ Енди сиз такси айдаўшы болдыныз.!\n\nТакси айдаўшы менюсына өтиў ушын:",
        reply_markup=driver_menu_kb()
    )
