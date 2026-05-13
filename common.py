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
            "Kegeyли — Nukus yo'nalishidagi eng qulay yo'lovchi tizimi.\n\n"
            "📱 Davom etish uchun telefon raqamingizni yuboring:",
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
        f"✅ Ro'yxatdan o'tdingiz!\n📱 Raqam: <b>{phone}</b>",
        parse_mode="HTML"
    )
    await show_main_menu(message, user)


@router.message(RegStates.waiting_phone)
async def wrong_phone(message: Message):
    await message.answer("📱 Iltimos, tugma orqali telefon raqamingizni yuboring!", reply_markup=phone_kb())


async def show_main_menu(message: Message, user):
    if message.from_user.id in ADMIN_IDS:
        role_text = "🛡️ Admin"
    elif user and user["role"] in ("driver", "both"):
        role_text = "🚖 Haydovchi"
    else:
        role_text = "🔍 Yo'lovchi"

    await message.answer(
        f"🏠 <b>Asosiy menyu</b> | {role_text}\n\nQuyidagi bo'limlardan birini tanlang:",
        parse_mode="HTML",
        reply_markup=main_menu_kb()
    )


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Sizda admin huquqi yo'q!")
        return
    await message.answer("🛡️ <b>Admin panel</b>ga xush kelibsiz!", parse_mode="HTML", reply_markup=admin_menu_kb())


@router.message(F.text == "🔙 Asosiy menyu")
async def back_to_main(message: Message, state: FSMContext):
    await state.clear()
    user = await get_user(message.from_user.id)
    await show_main_menu(message, user)


@router.message(F.text == "👤 Profil")
async def show_profile(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("Profil topilmadi. /start bosing.")
        return

    role_map = {"passenger": "Yo'lovchi", "driver": "Haydovchi", "both": "Haydovchi + Yo'lovchi"}
    role = role_map.get(user["role"], "Yo'lovchi")

    text = (
        f"👤 <b>Profil</b>\n\n"
        f"👤 Ism: <b>{user['full_name']}</b>\n"
        f"📱 Telefon: <b>{user['phone'] or 'Kiritilmagan'}</b>\n"
        f"🎭 Rol: <b>{role}</b>\n"
        f"📅 Ro'yxat: <b>{user['created_at'][:10]}</b>"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "💬 Yordam")
async def show_help(message: Message):
    await message.answer(
        "💬 <b>Yordam</b>\n\n"
        "🚖 Bu bot Kegeyli — Nukus yo'nalishida haydovchi va yo'lovchilarni bog'laydi.\n\n"
        "<b>Yo'lovchi uchun:</b>\n"
        "• 📋 Safarlar ro'yxatidan mos safar toping\n"
        "• 🚕 Qabul qilish tugmasini bosing\n"
        "• Haydovchi siz bilan bog'lanadi\n\n"
        "<b>Haydovchi uchun:</b>\n"
        "• ➕ Yangi safar qo'shing\n"
        "• Yo'lovchilar sizga murojaat qiladi\n\n"
        "📞 Muammo: @taxibot_support",
        parse_mode="HTML"
    )
