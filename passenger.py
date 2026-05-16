from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import (get_user, get_active_rides, create_booking, get_booking,
                      get_ride, get_passenger_bookings, update_user_role, get_setting,
                      create_passenger_request, get_passenger_request,
                      update_passenger_request_msg)
from keyboards import (passenger_menu_kb, driver_menu_kb, booking_kb, cancel_kb,
                       passenger_request_kb, search_confirm_kb, search_edit_kb)

router = Router()


class SearchStates(StatesGroup):
    from_city   = State()
    to_city     = State()
    dep_date    = State()
    seats       = State()
    confirm     = State()   # тасдиқлаш экрани
    edit_field  = State()   # бир майдонни тахрирлаш


def _summary(data: dict) -> str:
    return (
        f"📋 <b>Сизиң буйыртпаңыз:</b>\n\n"
        f"📍 <b>Қайдан:</b> {data.get('from_city', '—')}\n"
        f"🏁 <b>Қайда:</b> {data.get('to_city', '—')}\n"
        f"📅 <b>Ўақыты:</b> {data.get('dep_date', '—')}\n"
        f"👥 <b>Адам саны:</b> {data.get('seats', '—')} та\n\n"
        f"Маълыматлар дурыс па?"
    )


# ─── ТИЙКАРҒЫ МЕНЮДАН ────────────────────────────────────────────────────────

@router.message(F.text == "🔍 Жолаўшы режими")
async def open_passenger_menu(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    if not user or not user["phone"]:
        await message.answer("❌ Дәслеп /start арқалы дизимнен өтиң!")
        return
    await state.clear()
    await message.answer("🔍 Жолаўшы режиминдесиз.", reply_markup=passenger_menu_kb())


# ─── МАЪЛУМОТ ЖЫЙНАЎ ─────────────────────────────────────────────────────────

@router.message(F.text == "🔍 Машина излеў")
async def search_start(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    if not user or not user["phone"]:
        await message.answer("❌ Дәслеп /start арқалы дизимнен өтиң!")
        return
    await state.clear()
    await message.answer(
        "📍 <b>Қай жерден жол аласыз?</b>\n\nДәслепки қаланы киргизиң:",
        parse_mode="HTML", reply_markup=cancel_kb()
    )
    await state.set_state(SearchStates.from_city)


@router.message(SearchStates.from_city, F.text != "❌ Бийкарлаў")
async def search_get_from(message: Message, state: FSMContext):
    await state.update_data(from_city=message.text.strip())
    await message.answer("🏁 <b>Қай жерге барасыз?</b>\n\nМәнзил қаланы киргизиң:", parse_mode="HTML")
    await state.set_state(SearchStates.to_city)


@router.message(SearchStates.to_city, F.text != "❌ Бийкарлаў")
async def search_get_to(message: Message, state: FSMContext):
    await state.update_data(to_city=message.text.strip())
    await message.answer("📅 <b>Қашан жол аласыз?</b>\n\nМәселен: Бүгин 14:00, Ертең 08:00", parse_mode="HTML")
    await state.set_state(SearchStates.dep_date)


@router.message(SearchStates.dep_date, F.text != "❌ Бийкарлаў")
async def search_get_date(message: Message, state: FSMContext):
    await state.update_data(dep_date=message.text.strip())
    await message.answer("👥 <b>Неше адам жол аласыз?</b>\n\nСанды киргизиң (мысалы: 1, 2, 3):", parse_mode="HTML")
    await state.set_state(SearchStates.seats)


@router.message(SearchStates.seats, F.text != "❌ Бийкарлаў")
async def search_get_seats(message: Message, state: FSMContext):
    try:
        seats = int(message.text.strip())
        if seats < 1 or seats > 10:
            raise ValueError
    except ValueError:
        await message.answer("❌ Надурыс! 1-10 арасында сан киргизиң:")
        return

    await state.update_data(seats=seats)
    data = await state.get_data()

    # Тасдиқлаш экрани
    await message.answer(
        _summary(data),
        parse_mode="HTML",
        reply_markup=search_confirm_kb()
    )
    await state.set_state(SearchStates.confirm)


# ─── ТАСДИҚЛАШ / ӨЗГЕРТИЎ ────────────────────────────────────────────────────

@router.callback_query(SearchStates.confirm, F.data == "search_confirm:yes")
async def search_confirm_yes(call: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.clear()

    user = await get_user(call.from_user.id)
    channel_id = await get_setting("channel_id")

    request_id = await create_passenger_request(
        passenger_id=call.from_user.id,
        from_city=data["from_city"],
        to_city=data["to_city"],
        dep_date=data["dep_date"],
        seats=data["seats"]
    )

    channel_text = (
        f"🙋 <b>Жолаўшы машина излемекте!</b>\n\n"
        f"📍 <b>Қайдан:</b> {data['from_city']}\n"
        f"🏁 <b>Қайда:</b> {data['to_city']}\n"
        f"📅 <b>Ўақыты:</b> {data['dep_date']}\n"
        f"👥 <b>Адам саны:</b> {data['seats']} та\n\n"
        f"👇 Қабыллаў ушын төмендеги түймени басың:"
    )

    try:
        msg = await bot.send_message(
            channel_id, channel_text,
            parse_mode="HTML",
            reply_markup=passenger_request_kb(request_id)
        )
        await update_passenger_request_msg(request_id, msg.message_id)
        await call.message.edit_text(
            f"✅ <b>Буйыртпа каналга жарияланды!</b>\n\n"
            f"📍 {data['from_city']} → {data['to_city']}\n"
            f"📅 {data['dep_date']}\n"
            f"👥 {data['seats']} адам\n\n"
            f"⏳ Такси айдаўшылар хабарыңызды кўрип, Сиз бенен байланысады!",
            parse_mode="HTML"
        )
        # Reply keyboard қайтарыў
        await call.message.answer("🏠 Тийкарғы меню:", reply_markup=passenger_menu_kb())
    except Exception:
        await call.message.answer("⚠️ Каналга жариялаўда қәте кетти. Админ менен байланысың.",
                                  reply_markup=passenger_menu_kb())

    await call.answer()


@router.callback_query(SearchStates.confirm, F.data == "search_confirm:edit")
async def search_confirm_edit(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(
        "✏️ <b>Қайси маълыматты өзгертмекшисиз?</b>",
        parse_mode="HTML",
        reply_markup=search_edit_kb()
    )
    await call.answer()


@router.callback_query(F.data.startswith("search_edit:"))
async def search_edit_field(call: CallbackQuery, state: FSMContext):
    field = call.data.split(":")[1]

    if field == "back":
        data = await state.get_data()
        await call.message.edit_text(
            _summary(data), parse_mode="HTML", reply_markup=search_confirm_kb()
        )
        await state.set_state(SearchStates.confirm)
        await call.answer()
        return

    prompts = {
        "from_city": "📍 Жаңа <b>қайдан</b> қаланы киргизиң:",
        "to_city":   "🏁 Жаңа <b>қайда</b> қаланы киргизиң:",
        "dep_date":  "📅 Жаңа <b>ўақытты</b> киргизиң (мысалы: Бүгин 14:00):",
        "seats":     "👥 Жаңа <b>адам санын</b> киргизиң (1-10):",
    }
    await state.update_data(editing_field=field)
    await call.message.answer(prompts[field], parse_mode="HTML", reply_markup=cancel_kb())
    await state.set_state(SearchStates.edit_field)
    await call.answer()


@router.message(SearchStates.edit_field, F.text != "❌ Бийкарлаў")
async def search_save_edit(message: Message, state: FSMContext):
    data = await state.get_data()
    field = data.get("editing_field")

    if field == "seats":
        try:
            val = int(message.text.strip())
            if val < 1 or val > 10:
                raise ValueError
            await state.update_data(seats=val)
        except ValueError:
            await message.answer("❌ Надурыс! 1-10 арасында сан киргизиң:")
            return
    else:
        await state.update_data(**{field: message.text.strip()})

    data = await state.get_data()
    await message.answer(
        _summary(data),
        parse_mode="HTML",
        reply_markup=search_confirm_kb()
    )
    await state.set_state(SearchStates.confirm)


# ─── АЙДОВЧИ "ҚАБЫЛЛАЎ" БАСҚАНДА ────────────────────────────────────────────

@router.callback_query(F.data.startswith("accept_req:"))
async def accept_passenger_request(call: CallbackQuery, bot: Bot):
    request_id = int(call.data.split(":")[1])
    driver = await get_user(call.from_user.id)

    if not driver:
        await call.answer("❌ Дәслеп /start арқалы дизимнен өтиң!", show_alert=True)
        return

    req = await get_passenger_request(request_id)
    if not req:
        await call.answer("❌ Бул буйыртпа табылмады!", show_alert=True)
        return

    if req["passenger_id"] == call.from_user.id:
        await call.answer("❌ Өз буйыртпаңызды қабыллай алмайсыз!", show_alert=True)
        return

    try:
        await bot.send_message(
            call.from_user.id,
            f"✅ <b>Жолаўшы буйыртпасын қабыллдыңыз!</b>\n\n"
            f"📍 {req['from_city']} → {req['to_city']}\n"
            f"📅 {req['dep_date']}\n"
            f"👥 {req['seats']} адам\n\n"
            f"📞 <b>Жолаўшы телефоны: {req['phone']}</b>\n\n"
            f"Жолаўшыға хабарласың!",
            parse_mode="HTML"
        )
    except Exception:
        await call.answer("❌ Хабар жиберип болмады!", show_alert=True)
        return

    try:
        await bot.send_message(
            req["passenger_id"],
            f"🚖 <b>Такси айдаўшы сизиң буйыртпаңызды қабыллады!</b>\n\n"
            f"📍 {req['from_city']} → {req['to_city']}\n"
            f"📅 {req['dep_date']}\n\n"
            f"⏳ Жақын арада айдаўшы сиз бенен байланысады.",
            parse_mode="HTML"
        )
    except Exception:
        pass

    channel_id = await get_setting("channel_id")
    try:
        await bot.edit_message_text(
            f"✅ <b>Бул буйыртпа қабыл етилди!</b>\n\n"
            f"📍 {req['from_city']} → {req['to_city']}\n"
            f"📅 {req['dep_date']}\n"
            f"👥 {req['seats']} адам",
            chat_id=channel_id,
            message_id=req["channel_msg_id"],
            parse_mode="HTML"
        )
    except Exception:
        pass

    await call.answer("✅ Қабыл етилди! Жолаўшы телефоны жиберилди.", show_alert=True)


# ─── БРОН ҚЫЛЫЎ ──────────────────────────────────────────────────────────────

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
        await call.answer("⚠️ Сиз әллеқашан бул сапарды бәнтлеп қойыпсыз!", show_alert=True)
        return

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
    except Exception:
        pass

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
        except Exception:
            pass

    await call.answer(
        f"✅ Буйыртпа жиберилди! Такси айдаўшы {driver['phone'] if driver else ''} Сиз бенен байланысады.",
        show_alert=True
    )


# ─── МЕНЫҢ БРОНЛАРЫМ ─────────────────────────────────────────────────────────

@router.message(F.text == "📜 Меның бронларым")
async def my_bookings(message: Message):
    bookings = await get_passenger_bookings(message.from_user.id)
    if not bookings:
        await message.answer("📜 Ҳәзирше бронлар жоқ.")
        return
    await message.answer(f"📜 <b>Бронларым</b> ({len(bookings)} та):", parse_mode="HTML")
    for b in bookings:
        status_map = {
            "pending":  "⏳ Күтилмекте",
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


# ─── ТАКСИ АЙДАЎШЫ БОЛЫЎ ─────────────────────────────────────────────────────

@router.message(F.text == "🚖 Такси айдаўшы болыў")
async def become_driver_from_passenger(message: Message):
    await update_user_role(message.from_user.id, "both")
    await message.answer(
        "✅ Енди сиз такси айдаўшы болдыныз!\n\nТакси айдаўшы менюсына өтиў ушын:",
        reply_markup=driver_menu_kb()
    )


# ─── БИЙКАРЛАЎ ───────────────────────────────────────────────────────────────

@router.message(F.text == "❌ Бийкарлаў")
async def cancel_search(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Бийкарланды.", reply_markup=passenger_menu_kb())
