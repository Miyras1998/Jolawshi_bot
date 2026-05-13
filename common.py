from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import get_user, create_or_update_user, update_user_phone, update_user_role
from keyboards import main_menu_kb, passenger_menu_kb, driver_menu_kb, phone_kb, admin_menu_kb
from config import ADMIN_IDS

router = Router()


class RegStates(StatesGroup):
    waiting_phone = State()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = await get_user(message.from_user.id)

    if user and user["is_blocked"]:
        await message.answer("🚫 Сиз блоклангансиз. Админ менен байланысың.")
        return

    if not user or not user["phone"]:
        await create_or_update_user(message.from_user.id, message.from_user.full_name)
        await message.answer(
            f"👋 Ассалаўма алейкум, <b>{message.from_user.first_name}</b>!\n\n"
            "🚖 <b>Jolawshi_Bot</b>қа хош келипсиз!\n"
            "Бул бот арқалы сиз мәнзилден мәнзилге қолайлы ҳәм тез такси шақырыўыңыз мүмкин!\n\n"
            "📱 Даўам етиў ушын телефон номериңизди жиберың:",
            parse_mode="HTML",
            reply_markup=phone_kb()
        )
        await state.set_state(RegStates.waiting_phone)
        return

    await show_main_menu(message, user)


@router.message(RegStates.waiting_phone, F.contact)
async def get_phone(message: Message, state: FSMContext):
    phone = message.contact.phone_number
    if not phone.startswith("+"):
        phone = "+" + phone

    await update_user_phone(message.from_user.id, phone)
    await state.clear()

    user = await get_user(message.from_user.id)
    await message.answer(
        f"✅ Дизимнен өттиңиз!\n📱 Телефон номер: <b>{phone}</b>",
        parse_mode="HTML"
    )
    await show_main_menu(message, user)


@router.message(RegStates.waiting_phone)
async def wrong_phone(message: Message):
    await message.answer("📱 Илтимас, түйме арқалы телефон номериңизди жиберың!", reply_markup=phone_kb())


async def show_main_menu(message: Message, user):
    if message.from_user.id in ADMIN_IDS:
        role_text = "🛡️ Админ"
    elif user and user["role"] in ("driver", "both"):
        role_text = "🚖 Такси айдаўшы"
    else:
        role_text = "🔍 Жолаўшы"

    await message.answer(
        f"🏠 <b>Тийкарғы меню</b> | {role_text}\n\nТөмендеги бөлимлерден бирин таңлаң.:",
        parse_mode="HTML",
        reply_markup=main_menu_kb()
    )


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Сизде админ ҳуқықы жоқ!")
        return
    await message.answer("🛡️ <b>Админ панел</b>ге хош келипсиз!", parse_mode="HTML", reply_markup=admin_menu_kb())


@router.message(F.text == "🔙 Тийкарғы меню")
async def back_to_main(message: Message, state: FSMContext):
    await state.clear()
    user = await get_user(message.from_user.id)
    await show_main_menu(message, user)


@router.message(F.text == "👤 Профил")
async def show_profile(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("Профил табылмады. /start басың.")
        return

    role_map = {"passenger": "Жолаўшы", "driver": "Такси айдаўшы", "both": "Такси айдаўшы + Жолаўшы"}
    role = role_map.get(user["role"], "Жолаўшы")

    text = (
        f"👤 <b>Профил</b>\n\n"
        f"👤 Аты: <b>{user['full_name']}</b>\n"
        f"📱 Телефон: <b>{user['phone'] or 'Kiritilmagan'}</b>\n"
        f"🎭 Рол: <b>{role}</b>\n"
        f"📅 Дизим: <b>{user['created_at'][:10]}</b>"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "💬 Жәрдем")
async def show_help(message: Message):
    await message.answer(
        "💬 <b>Жәрдем</b>\n\n"
        "🚖 Бул бот арқалы сиз мәнзилден мәнзилге қолайлы ҳәм тез такси шақырыўыңыз мүмкин.\n\n"
        "<b>Жолаўшы ушын:</b>\n"
        "• 📋 Сапарлар дизиминен сәйкес сапар табың\n"
        "• 🚕 Қабыллаў түймесин басың\n"
        "• Такси айдаўшы сиз бенен байланысады\n\n"
        "<b>Такси айдаўшы ушын:</b>\n"
        "• ➕ Жаңа сапар қосың\n"
        "• Жолаўшылар сизге мүрәжат етеди\n\n"
        "📞 Мүрәжат ушын: @taxibot_support",
        parse_mode="HTML"
    )
