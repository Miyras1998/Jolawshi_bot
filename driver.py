from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import (get_user, update_user_role, create_ride, get_driver_rides,
                      get_ride, cancel_ride, update_ride_channel_msg, get_ride_bookings,
                      update_booking_status, get_setting)
from keyboards import (driver_menu_kb, passenger_menu_kb, price_kb, seats_kb,
                       ride_actions_kb, accept_reject_kb, cancel_kb)

router = Router()

PRESET_PRICES = [10000, 15000, 20000, 25000, 30000]


class DriverStates(StatesGroup):
    # Yangi safar
    from_city = State()
    to_city = State()
    dep_time = State()
    price = State()
    price_manual = State()
    seats = State()
    confirm = State()
    # Tahrirlash
    edit_time = State()
    edit_price = State()
    edit_price_manual = State()


# ─── HAYDOVCHI BO'LISH ────────────────────────────────────────────────────────

@router.message(F.text == "🚖 Haydovchi sifatida kirish")
async def become_driver(message: Message):
    user = await get_user(message.from_user.id)
    if not user or not user["phone"]:
        await message.answer("❌ Avval /start orqali ro'yxatdan o'ting!")
        return
    await update_user_role(message.from_user.id, "driver")
    await message.answer(
        "✅ Siz haydovchi sifatida ro'yxatdan o'tdingiz!\n\n"
        "Endi yo'lovchilar uchun safarlar qo'sha olasiz.",
        reply_markup=driver_menu_kb()
    )


@router.message(F.text == "👫 Yo'lovchi rejimi")
async def switch_to_passenger(message: Message):
    await message.answer("🔍 Yo'lovchi rejimidasiz.", reply_markup=passenger_menu_kb())


# ─── YANGI SAFAR ─────────────────────────────────────────────────────────────

@router.message(F.text == "➕ Yangi safar")
async def new_ride_start(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    if not user or user["role"] not in ("driver", "both"):
        await message.answer("❌ Avval haydovchi sifatida ro'yxatdan o'ting!")
        return
    await message.answer("📍 <b>Qayerdan?</b>\n\nBoshlang'ich shaharni kiriting:", parse_mode="HTML", reply_markup=cancel_kb())
    await state.set_state(DriverStates.from_city)


@router.message(DriverStates.from_city, F.text != "❌ Bekor qilish")
async def get_from_city(message: Message, state: FSMContext):
    await state.update_data(from_city=message.text.strip())
    await message.answer("🏁 <b>Qayerga?</b>\n\nManzil shaharni kiriting:", parse_mode="HTML")
    await state.set_state(DriverStates.to_city)


@router.message(DriverStates.to_city, F.text != "❌ Bekor qilish")
async def get_to_city(message: Message, state: FSMContext):
    await state.update_data(to_city=message.text.strip())
    await message.answer("📅 <b>Jo'nash vaqti?</b>\n\nMasalan: Bugun 14:30 yoki Ertaga 08:00", parse_mode="HTML")
    await state.set_state(DriverStates.dep_time)


@router.message(DriverStates.dep_time, F.text != "❌ Bekor qilish")
async def get_dep_time(message: Message, state: FSMContext):
    await state.update_data(dep_time=message.text.strip())
    await message.answer(
        "💰 <b>Narx tanlang</b> (har bir kishi uchun):",
        parse_mode="HTML",
        reply_markup=price_kb()
    )
    await state.set_state(DriverStates.price)


@router.callback_query(DriverStates.price, F.data.startswith("price:"))
async def get_price(call: CallbackQuery, state: FSMContext):
    val = call.data.split(":")[1]
    if val == "manual":
        await call.message.answer("✏️ Narxni so'mda kiriting (faqat raqam):")
        await state.set_state(DriverStates.price_manual)
    else:
        price = int(val)
        await state.update_data(price=price)
        await call.message.answer(
            f"✅ Narx: <b>{price:,} so'm</b>\n\n👥 <b>O'rinlar sonini tanlang:</b>".replace(",", " "),
            parse_mode="HTML",
            reply_markup=seats_kb()
        )
        await state.set_state(DriverStates.seats)
    await call.answer()


@router.message(DriverStates.price_manual, F.text != "❌ Bekor qilish")
async def get_price_manual(message: Message, state: FSMContext):
    try:
        price = int(message.text.strip().replace(" ", ""))
        if price < 1000:
            raise ValueError
        await state.update_data(price=price)
        await message.answer(
            f"✅ Narx: <b>{price:,} so'm</b>\n\n👥 <b>O'rinlar sonini tanlang:</b>".replace(",", " "),
            parse_mode="HTML",
            reply_markup=seats_kb()
        )
        await state.set_state(DriverStates.seats)
    except ValueError:
        await message.answer("❌ Noto'g'ri narx! Faqat raqam kiriting (masalan: 15000):")


@router.callback_query(DriverStates.seats, F.data.startswith("seats:"))
async def get_seats(call: CallbackQuery, state: FSMContext, bot: Bot):
    seats = int(call.data.split(":")[1])
    await state.update_data(seats=seats)
    data = await state.get_data()

    text = (
        f"✅ <b>Safar ma'lumotlari:</b>\n\n"
        f"📍 Qayerdan: <b>{data['from_city']}</b>\n"
        f"🏁 Qayerga: <b>{data['to_city']}</b>\n"
        f"📅 Vaqt: <b>{data['dep_time']}</b>\n"
        f"💰 Narx: <b>{data['price']:,} so'm</b> / kishi\n"
        f"👥 O'rinlar: <b>{seats} ta</b>\n\n"
        "Tasdiqlaysizmi?"
    ).replace(",", " ")

    from keyboards import confirm_kb
    await call.message.answer(text, parse_mode="HTML", reply_markup=confirm_kb())
    await state.set_state(DriverStates.confirm)
    await call.answer()


@router.callback_query(DriverStates.confirm, F.data == "confirm:yes")
async def confirm_ride(call: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    user = await get_user(call.from_user.id)

    ride_id = await create_ride(
        driver_id=call.from_user.id,
        from_city=data["from_city"],
        to_city=data["to_city"],
        departure_time=data["dep_time"],
        seats=data["seats"],
        price=data["price"]
    )

    channel_id = await get_setting("channel_id")
    channel_text = (
        f"🚖 <b>Yangi safar!</b>\n\n"
        f"📍 {data['from_city']} → {data['to_city']}\n"
        f"📅 Vaqt: <b>{data['dep_time']}</b>\n"
        f"👥 O'rinlar: <b>{data['seats']} ta</b>\n"
        f"💰 Narx: <b>{data['price']:,} so'm</b> / kishi\n"
        f"📞 Haydovchi: <b>{user['phone']}</b>\n\n"
        f"🆔 Safar ID: #{ride_id}"
    ).replace(",", " ")

    from keyboards import booking_kb
    try:
        msg = await bot.send_message(channel_id, channel_text, parse_mode="HTML", reply_markup=booking_kb(ride_id))
        await update_ride_channel_msg(ride_id, msg.message_id)
    except Exception as e:
        pass

    await call.message.answer(
        f"✅ <b>Safar muvaffaqiyatli qo'shildi!</b>\n🆔 Safar ID: #{ride_id}",
        parse_mode="HTML",
        reply_markup=driver_menu_kb()
    )
    await state.clear()
    await call.answer()


@router.callback_query(DriverStates.confirm, F.data == "confirm:no")
async def cancel_confirm(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer("❌ Bekor qilindi.", reply_markup=driver_menu_kb())
    await call.answer()


# ─── MENING SAFARLARIM ────────────────────────────────────────────────────────

@router.message(F.text == "🚗 Mening safarlarim")
async def my_rides(message: Message):
    rides = await get_driver_rides(message.from_user.id)
    if not rides:
        await message.answer("🚗 Hali safar qo'shilmagan.\n\n➕ Yangi safar tugmasini bosing.")
        return

    for r in rides[:5]:
        status_map = {"active": "🟢 Faol", "cancelled": "🔴 Bekor", "completed": "✅ Tugallangan"}
        status = status_map.get(r["status"], r["status"])
        text = (
            f"🆔 #{r['id']}\n"
            f"📍 {r['from_city']} → {r['to_city']}\n"
            f"📅 {r['departure_time']}\n"
            f"💰 {r['price']:,} so'm | 👥 {r['seats']} o'rin\n"
            f"📌 {status}"
        ).replace(",", " ")

        kb = ride_actions_kb(r["id"]) if r["status"] == "active" else None
        await message.answer(text, reply_markup=kb)


# ─── RIDE ACTIONS CALLBACKS ───────────────────────────────────────────────────

@router.callback_query(F.data.startswith("edit_time:"))
async def edit_time_start(call: CallbackQuery, state: FSMContext):
    ride_id = int(call.data.split(":")[1])
    await state.update_data(edit_ride_id=ride_id)
    await call.message.answer("📅 Yangi vaqtni kiriting (masalan: Ertaga 09:00):", reply_markup=cancel_kb())
    await state.set_state(DriverStates.edit_time)
    await call.answer()


@router.message(DriverStates.edit_time, F.text != "❌ Bekor qilish")
async def edit_time_done(message: Message, state: FSMContext):
    data = await state.get_data()
    from database import DB_PATH
    import aiosqlite
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE rides SET departure_time = ? WHERE id = ?",
                         (message.text.strip(), data["edit_ride_id"]))
        await db.commit()
    await state.clear()
    await message.answer("✅ Vaqt yangilandi!", reply_markup=driver_menu_kb())


@router.callback_query(F.data.startswith("edit_price:"))
async def edit_price_start(call: CallbackQuery, state: FSMContext):
    ride_id = int(call.data.split(":")[1])
    await state.update_data(edit_ride_id=ride_id)
    await call.message.answer("💰 Yangi narxni tanlang:", reply_markup=price_kb())
    await state.set_state(DriverStates.edit_price)
    await call.answer()


@router.callback_query(DriverStates.edit_price, F.data.startswith("price:"))
async def edit_price_done(call: CallbackQuery, state: FSMContext):
    val = call.data.split(":")[1]
    if val == "manual":
        await call.message.answer("✏️ Yangi narxni kiriting:")
        await state.set_state(DriverStates.edit_price_manual)
    else:
        data = await state.get_data()
        from database import DB_PATH
        import aiosqlite
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE rides SET price = ? WHERE id = ?", (int(val), data["edit_ride_id"]))
            await db.commit()
        await state.clear()
        await call.message.answer(f"✅ Narx {int(val):,} so'mga yangilandi!".replace(",", " "), reply_markup=driver_menu_kb())
    await call.answer()


@router.message(DriverStates.edit_price_manual)
async def edit_price_manual_done(message: Message, state: FSMContext):
    try:
        price = int(message.text.strip().replace(" ", ""))
        data = await state.get_data()
        from database import DB_PATH
        import aiosqlite
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE rides SET price = ? WHERE id = ?", (price, data["edit_ride_id"]))
            await db.commit()
        await state.clear()
        await message.answer(f"✅ Narx {price:,} so'mga yangilandi!".replace(",", " "), reply_markup=driver_menu_kb())
    except ValueError:
        await message.answer("❌ Faqat raqam kiriting!")


@router.callback_query(F.data.startswith("cancel_ride:"))
async def cancel_ride_cb(call: CallbackQuery, bot: Bot):
    ride_id = int(call.data.split(":")[1])
    ride = await get_ride(ride_id)
    if ride and ride["driver_id"] == call.from_user.id:
        await cancel_ride(ride_id)
        if ride["channel_msg_id"]:
            channel_id = await get_setting("channel_id")
            try:
                await bot.delete_message(channel_id, ride["channel_msg_id"])
            except:
                pass
        await call.message.answer("✅ Safar bekor qilindi.", reply_markup=driver_menu_kb())
    await call.answer()


@router.callback_query(F.data.startswith("ride_bookings:"))
async def show_ride_bookings(call: CallbackQuery):
    ride_id = int(call.data.split(":")[1])
    bookings = await get_ride_bookings(ride_id)
    if not bookings:
        await call.answer("Hali bronlar yo'q.", show_alert=True)
        return
    for b in bookings:
        status_map = {"pending": "⏳ Kutilmoqda", "accepted": "✅ Qabul", "rejected": "❌ Rad"}
        text = (
            f"👤 {b['full_name']}\n"
            f"📱 {b['phone']}\n"
            f"📌 {status_map.get(b['status'], b['status'])}"
        )
        kb = accept_reject_kb(b["id"]) if b["status"] == "pending" else None
        await call.message.answer(text, reply_markup=kb)
    await call.answer()


@router.callback_query(F.data.startswith("accept:"))
async def accept_booking(call: CallbackQuery, bot: Bot):
    booking_id = int(call.data.split(":")[1])
    booking = await get_booking(booking_id)
    if not booking:
        await call.answer("Bron topilmadi!", show_alert=True)
        return
    await update_booking_status(booking_id, "accepted")
    ride = await get_ride(booking["ride_id"])
    driver = await get_user(call.from_user.id)
    try:
        await bot.send_message(
            booking["passenger_id"],
            f"✅ <b>Broningiz qabul qilindi!</b>\n\n"
            f"📍 {ride['from_city']} → {ride['to_city']}\n"
            f"📅 {ride['departure_time']}\n"
            f"📞 Haydovchi: <b>{driver['phone']}</b>",
            parse_mode="HTML"
        )
    except:
        pass
    await call.message.edit_text(call.message.text + "\n\n✅ Qabul qilindi!")
    await call.answer("✅ Qabul qilindi!")


@router.callback_query(F.data.startswith("reject:"))
async def reject_booking(call: CallbackQuery, bot: Bot):
    booking_id = int(call.data.split(":")[1])
    booking = await get_booking(booking_id)
    if not booking:
        await call.answer("Bron topilmadi!", show_alert=True)
        return
    await update_booking_status(booking_id, "rejected")
    try:
        await bot.send_message(booking["passenger_id"], "❌ Afsuski, broningiz rad etildi.")
    except:
        pass
    await call.message.edit_text(call.message.text + "\n\n❌ Rad etildi!")
    await call.answer("❌ Rad etildi!")


@router.message(F.text == "📊 Statistika")
async def driver_stats(message: Message):
    rides = await get_driver_rides(message.from_user.id)
    active = len([r for r in rides if r["status"] == "active"])
    completed = len([r for r in rides if r["status"] == "completed"])
    cancelled = len([r for r in rides if r["status"] == "cancelled"])

    await message.answer(
        f"📊 <b>Sizning statistikangiz</b>\n\n"
        f"🟢 Faol safarlar: <b>{active}</b>\n"
        f"✅ Tugallangan: <b>{completed}</b>\n"
        f"🔴 Bekor qilingan: <b>{cancelled}</b>\n"
        f"📋 Jami: <b>{len(rides)}</b>",
        parse_mode="HTML"
    )
