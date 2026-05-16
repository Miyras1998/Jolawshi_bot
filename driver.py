from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import (get_user, update_user_role, create_ride, get_driver_rides,
                      get_ride, cancel_ride, update_ride_channel_msg, get_setting)
from keyboards import (driver_menu_kb, passenger_menu_kb, price_kb, seats_kb,
                       ride_actions_kb, cancel_kb)

router = Router()

PRESET_PRICES = [10000, 15000, 20000, 25000, 30000]


class DriverStates(StatesGroup):
    # Жаңа сапар
    from_city = State()
    to_city = State()
    dep_time = State()
    price = State()
    price_manual = State()
    seats = State()
    confirm = State()
    # Өзгертиў
    edit_time = State()
    edit_price = State()
    edit_price_manual = State()


# ─── HAYDOVCHI BO'LISH ────────────────────────────────────────────────────────

@router.message(F.text == "🚖 Такси айдаўшы сыпатында кириў")
async def become_driver(message: Message):
    user = await get_user(message.from_user.id)
    if not user or not user["phone"]:
        await message.answer("❌ Дәслеп /start арқалы дизимнен өтиң!")
        return
    await update_user_role(message.from_user.id, "driver")
    await message.answer(
        "✅ Сиз такси айдаўшы сыпатында дизимнен өттиңиз!\n\n"
        "Енди жолаўшылар ушын сапарлар қоса аласыз.",
        reply_markup=driver_menu_kb()
    )


@router.message(F.text == "👫 Жолаўшы режими")
async def switch_to_passenger(message: Message):
      await message.answer("🔍 Жолаўшы режиминдесиз.", reply_markup=passenger_menu_kb())


# ─── YANGI SAFAR ─────────────────────────────────────────────────────────────

@router.message(F.text == "➕ Жаңа сапар")
async def new_ride_start(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    if not user or user["role"] not in ("driver", "both"):
        await message.answer("❌ Дәслеп такси айдаўшы сыпатында дизимнен өтиң!")
        return
    await message.answer("📍 <b>Қай жерден?</b>\n\nДәслепки қаланы киргизиң:", parse_mode="HTML", reply_markup=cancel_kb())
    await state.set_state(DriverStates.from_city)


@router.message(DriverStates.from_city, F.text != "❌ Бийкарлаў")
async def get_from_city(message: Message, state: FSMContext):
    await state.update_data(from_city=message.text.strip())
    await message.answer("🏁 <b>Қай жерге?</b>\n\nМәнзил қаланы киргизиң:", parse_mode="HTML")
    await state.set_state(DriverStates.to_city)


@router.message(DriverStates.to_city, F.text != "❌ Бийкарлаў")
async def get_to_city(message: Message, state: FSMContext):
    await state.update_data(to_city=message.text.strip())
    await message.answer("📅 <b>Жөнелис ўақты?</b>\n\nМәселен: Бүгин 14:30 ямаса Ертең 08:00", parse_mode="HTML")
    await state.set_state(DriverStates.dep_time)


@router.message(DriverStates.dep_time, F.text != "❌ Бийкарлаў")
async def get_dep_time(message: Message, state: FSMContext):
    await state.update_data(dep_time=message.text.strip())
    await message.answer(
        "💰 <b>Баҳаны таңлаң</b> (ҳәр бир адам ушын):",
        parse_mode="HTML",
        reply_markup=price_kb()
    )
    await state.set_state(DriverStates.price)


@router.callback_query(DriverStates.price, F.data.startswith("price:"))
async def get_price(call: CallbackQuery, state: FSMContext):
    val = call.data.split(":")[1]
    if val == "manual":
        await call.message.answer("✏️ Баҳаны сумда киргизиң (faqat raqam):")
        await state.set_state(DriverStates.price_manual)
    else:
        price = int(val)
        await state.update_data(price=price)
        await call.message.answer(
            f"✅ Баҳасы: <b>{price:,} сум</b>\n\n👥 <b>Орынлар санын таңлаң:</b>".replace(",", " "),
            parse_mode="HTML",
            reply_markup=seats_kb()
        )
        await state.set_state(DriverStates.seats)
    await call.answer()


@router.message(DriverStates.price_manual, F.text != "❌ Бийкарлаў")
async def get_price_manual(message: Message, state: FSMContext):
    try:
        price = int(message.text.strip().replace(" ", ""))
        if price < 1000:
            raise ValueError
        await state.update_data(price=price)
        await message.answer(
            f"✅ Баҳасы: <b>{price:,} сум</b>\n\n👥 <b>Орынлар санын таңлаң:</b>".replace(",", " "),
            parse_mode="HTML",
            reply_markup=seats_kb()
        )
        await state.set_state(DriverStates.seats)
    except ValueError:
        await message.answer("❌ Надурыс баҳа! Тек сан киргизиң (мысалы: 15000):")


@router.callback_query(DriverStates.seats, F.data.startswith("seats:"))
async def get_seats(call: CallbackQuery, state: FSMContext, bot: Bot):
    seats = int(call.data.split(":")[1])
    await state.update_data(seats=seats)
    data = await state.get_data()

    text = (
        f"✅ <b>Сапар мағлыўматлары:</b>\n\n"
        f"📍 Қай жерден: <b>{data['from_city']}</b>\n"
        f"🏁 Қай жерге: <b>{data['to_city']}</b>\n"
        f"📅 Ўақыт: <b>{data['dep_time']}</b>\n"
        f"💰 Баҳасы: <b>{data['price']:,} so'm</b> / kishi\n"
        f"👥 Орынлар: <b>{seats} ta</b>\n\n"
        "Тастыйықлайсызба?"
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

    from database import get_driver_rating
    rating = await get_driver_rating(call.from_user.id)
    if rating["count"] > 0:
        stars = "⭐" * round(rating["avg"])
        rating_str = f"{stars} ({rating['count']} баҳо)"
    else:
        rating_str = "Ҳәзирше баҳо жоқ"

    channel_id = await get_setting("channel_id")
    channel_text = (
        f"🚖 <b>Жаңа сапар!</b>\n\n"
        f"📍 <b>Қайдан:</b> {data['from_city']}\n"
        f"🏁 <b>Қайда:</b> {data['to_city']}\n"
        f"📅 <b>Ўақыт:</b> {data['dep_time']}\n"
        f"👥 <b>Орынлар:</b> {data['seats']} та\n"
        f"💰 <b>Баҳасы:</b> {data['price']:,} сум / адам\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🧑 <b>Айдаўшы:</b> {user['full_name']}\n"
        f"📞 <b>Телефон:</b> {user['phone']}\n"
        f"⭐ <b>Рейтинг:</b> {rating_str}"
    ).replace(",", " ")

    try:
        from keyboards import ride_join_kb
        msg = await bot.send_message(channel_id, channel_text, parse_mode="HTML", reply_markup=ride_join_kb(ride_id))
        await update_ride_channel_msg(ride_id, msg.message_id)
    except Exception:
        pass

    await call.message.answer(
        f"✅ <b>Сапар табыслы қосылды!</b>\n🆔 Сапар ID: #{ride_id}",
        parse_mode="HTML",
        reply_markup=driver_menu_kb()
    )
    await state.clear()
    await call.answer()


@router.callback_query(DriverStates.confirm, F.data == "confirm:no")
async def cancel_confirm(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer("❌ Бийкар етилди.", reply_markup=driver_menu_kb())
    await call.answer()


# ─── MENING SAFARLARIM ────────────────────────────────────────────────────────

@router.message(F.text == "🚗 Меның сапарларым")
async def my_rides(message: Message):
    rides = await get_driver_rides(message.from_user.id)
    if not rides:
        await message.answer("🚗 Еле сапар қосылмаған.\n\n➕ Жаңа сапар түймесин басың.")
        return

    for r in rides[:5]:
        status_map = {"active": "🟢 Актив", "cancelled": "🔴 Бийкар", "completed": "✅ Тамамланған"}
        status = status_map.get(r["status"], r["status"])
        text = (
            f"🆔 #{r['id']}\n"
            f"📍 {r['from_city']} → {r['to_city']}\n"
            f"📅 {r['departure_time']}\n"
            f"💰 {r['price']:,} сум | 👥 {r['seats']} орын\n"
            f"📌 {status}"
        ).replace(",", " ")

        kb = ride_actions_kb(r["id"]) if r["status"] == "active" else None
        await message.answer(text, reply_markup=kb)


# ─── RIDE ACTIONS CALLBACKS ───────────────────────────────────────────────────

@router.callback_query(F.data.startswith("edit_time:"))
async def edit_time_start(call: CallbackQuery, state: FSMContext):
    ride_id = int(call.data.split(":")[1])
    await state.update_data(edit_ride_id=ride_id)
    await call.message.answer("📅 Жаңа ўақытты киргизиң (мысалы: Ертең 09:00):", reply_markup=cancel_kb())
    await state.set_state(DriverStates.edit_time)
    await call.answer()


@router.message(DriverStates.edit_time, F.text != "❌ Бийкарлаў")
async def edit_time_done(message: Message, state: FSMContext):
    data = await state.get_data()
    from database import DB_PATH
    import aiosqlite
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE rides SET departure_time = ? WHERE id = ?",
                         (message.text.strip(), data["edit_ride_id"]))
        await db.commit()
    await state.clear()
    await message.answer("✅ Ўақыт жаңаланды!", reply_markup=driver_menu_kb())


@router.callback_query(F.data.startswith("edit_price:"))
async def edit_price_start(call: CallbackQuery, state: FSMContext):
    ride_id = int(call.data.split(":")[1])
    await state.update_data(edit_ride_id=ride_id)
    await call.message.answer("💰 Жаңа баҳаны таңлаң:", reply_markup=price_kb())
    await state.set_state(DriverStates.edit_price)
    await call.answer()


@router.callback_query(DriverStates.edit_price, F.data.startswith("price:"))
async def edit_price_done(call: CallbackQuery, state: FSMContext):
    val = call.data.split(":")[1]
    if val == "manual":
        await call.message.answer("✏️ Жаңа баҳаны киргизиң:")
        await state.set_state(DriverStates.edit_price_manual)
    else:
        data = await state.get_data()
        from database import DB_PATH
        import aiosqlite
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE rides SET price = ? WHERE id = ?", (int(val), data["edit_ride_id"]))
            await db.commit()
        await state.clear()
        await call.message.answer(f"✅ Баҳасы {int(val):,} сумға жаңаланды!".replace(",", " "), reply_markup=driver_menu_kb())
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
        await message.answer(f"✅ Баҳасы {price:,} сумға жаңаланды!".replace(",", " "), reply_markup=driver_menu_kb())
    except ValueError:
        await message.answer("❌ Тек номер киргизиң!")


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
        await call.message.answer("✅ Сапар бийкар етилди.", reply_markup=driver_menu_kb())
    await call.answer()


@router.message(F.text == "📋 Актив буйыртпалар")
async def active_orders(message: Message):
    # Haydovchining barcha safarlarini bazadan olib kelish
    rides = await get_driver_rides(message.from_user.id)
    
    # Faqat statusi 'active' bo'lgan safarlarni saralab olish
    active_rides = [r for r in rides if r["status"] == "active"]
    
    if not active_rides:
        await message.answer("Сизде ҳәзирше актив буйыртпалар жоқ.")
        return
        
    text = f"📋 <b>Актив буйыртпалар</b> ({len(active_rides)} та):\n\n"
    for r in active_rides:
        text += (
            f"📍 <b>{r['from_city']}</b> → <b>{r['to_city']}</b>\n"
            f"📅 Ўақты: {r['departure_time']}\n"
            f"👥 Бос орын: {r['seats']} та\n"
            f"💰 Бахасы: {r['price']} сум\n"
            f"──────────────\n"
        )
    
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "📊 Статистика")
async def driver_stats(message: Message):
    rides = await get_driver_rides(message.from_user.id)
    active = len([r for r in rides if r["status"] == "active"])
    completed = len([r for r in rides if r["status"] == "completed"])
    cancelled = len([r for r in rides if r["status"] == "cancelled"])

    await message.answer(
        f"📊 <b>Сизиң статистикасыңыз</b>\n\n"
        f"🟢 Актив сапарлар: <b>{active}</b>\n"
        f"✅ Тамамланған: <b>{completed}</b>\n"
        f"🔴 Бийкар етилген: <b>{cancelled}</b>\n"
        f"📋 Жәми: <b>{len(rides)}</b>",
        parse_mode="HTML"
    )
