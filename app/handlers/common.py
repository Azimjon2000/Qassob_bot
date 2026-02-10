"""Common handlers - /start, settings, about."""
from aiogram import Router, F
from aiogram.types import Message, ContentType, ReplyKeyboardMarkup, KeyboardButton, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext

from app.states import ClientReg, RoleSelect, ButcherReg, Settings
from app.services.user_service import upsert_user, get_user, is_registered, update_user, set_role
from app.services.admin_notify_service import notify_new_user
from app.services.donate_service import get_support_profile
from app.keyboards.reply import (
    client_main_kb, butcher_main_kb, admin_main_kb,
    request_contact_kb, request_location_kb, settings_kb, butcher_settings_kb,
    role_picker_kb, back_kb
)
from app.keyboards.inline import client_menu_kb, client_settings_kb
from app.config import ADMINS, add_admin
from app.utils.i18n import t

router = Router()


def get_main_kb_for_role(role: str, telegram_id: int):
    """Get appropriate main keyboard based on role."""
    if telegram_id in ADMINS:
        return admin_main_kb()
    if role == "butcher":
        return butcher_main_kb()
    return client_main_kb()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Handle /start command."""
    telegram_id = message.from_user.id
    
    # Check user
    user = await get_user(telegram_id)
    
    # If new user, create with pending role
    if not user:
        await upsert_user(telegram_id=telegram_id, name=message.from_user.full_name)
        user = {"role": "pending", "name": message.from_user.full_name}
    
    role = user.get("role", "pending")
    
    # ADMIN CHECK - both from config and database
    is_admin = telegram_id in ADMINS or role == "admin"
    
    if is_admin:
        # Ensure role is set to admin in database
        if role != "admin":
            await set_role(telegram_id, "admin")
        
        # Ensure in ADMINS list
        if telegram_id not in ADMINS:
            add_admin(telegram_id)
        
        await message.answer(
            f"👑 Xush kelibsiz, Admin {message.from_user.first_name}!", 
            reply_markup=admin_main_kb()
        )
        await state.clear()
        return
    
    # IF ROLE IS PENDING -> SHOW INLINE PICKER
    if role == "pending" or not role:
        from app.keyboards.inline import role_select_kb
        await message.answer(
            f"👋 Assalomu alaykum, {user.get('name', 'foydalanuvchi')}!\n\n"
            "Botdan foydalanish uchun rolingizni tanlang:",
            reply_markup=role_select_kb()
        )
        # We don't need a specific state for inline callback, 
        # but clearing state is good practice to avoid interference.
        await state.clear()
        return

    # IF ROLE EXISTS -> CHECK REGISTRATION OR SHOW MENU

    if role == "client":
        # Always show main menu for client (no registration check needed as we skip it)
        await message.answer(
            "🏠 Asosiy menyu",
            reply_markup=client_main_kb()
        )
        await message.answer(
            "Xush kelibsiz! Bo'limni tanlang:",
            reply_markup=client_menu_kb()
        )
        await state.clear()
            
    elif role == "butcher":
        await message.answer(
            "🏠 Asosiy menyu (Qassob)",
            reply_markup=butcher_main_kb()
        )
        await state.clear()


@router.callback_query(F.data.startswith("role:"))
async def process_role_selection_inline(callback: CallbackQuery, state: FSMContext):
    """Process role selection from inline keyboard."""
    role_type = callback.data.split(":")[1]
    telegram_id = callback.from_user.id
    name = callback.from_user.full_name
    
    # Delete the inline keyboard message
    await callback.message.delete()
    
    if role_type == "client":
        await update_user(telegram_id, name=name)
        await set_role(telegram_id, "client")
        await notify_new_user(callback.bot, telegram_id)

        await callback.message.answer(
            "🏠 Asosiy menyu",
            reply_markup=client_main_kb()
        )
        await callback.message.answer(
            f"✅ Xush kelibsiz, {name}!\n"
            "Bo'limni tanlang:",
            reply_markup=client_menu_kb()
        )
        
    elif role_type == "butcher":
        await set_role(telegram_id, "butcher")
        await callback.message.answer(
            "✅ Siz <b>Qassob</b> rolini tanladingiz.\n\n"
            "Do'kon nomini kiriting:",
            parse_mode="HTML",
            reply_markup=back_kb()
        )
        await state.set_state(ButcherReg.shop_name)
    
    await callback.answer()


# ==================== CLIENT REGISTRATION ====================

@router.message(ClientReg.waiting_name)
async def process_name(message: Message, state: FSMContext):
    """Process user name input."""
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("❌ Ism juda qisqa. Iltimos, to'liq ismingizni kiriting:")
        return
    
    await state.update_data(name=name)
    await update_user(message.from_user.id, name=name)
    
    await message.answer(
        f"✅ Rahmat, {name}!\n\n"
        "Endi telefon raqamingizni yuboring:",
        reply_markup=request_contact_kb()
    )
    await state.set_state(ClientReg.waiting_phone)


@router.message(ClientReg.waiting_phone, F.contact)
async def process_phone_contact(message: Message, state: FSMContext):
    """Process phone from contact."""
    phone = message.contact.phone_number
    await state.update_data(phone=phone)
    await update_user(message.from_user.id, phone=phone)
    
    await message.answer(
        "✅ Telefon raqam saqlandi!\n\n"
        "Endi lokatsiyangizni yuboring:",
        reply_markup=request_location_kb()
    )
    await state.set_state(ClientReg.waiting_location)


@router.message(ClientReg.waiting_phone)
async def process_phone_text(message: Message, state: FSMContext):
    """Ask for contact button press."""
    await message.answer(
        "❌ Iltimos, telefon raqamni pastdagi tugma orqali yuboring:",
        reply_markup=request_contact_kb()
    )


@router.message(ClientReg.waiting_location, F.location)
async def process_location(message: Message, state: FSMContext):
    """Process location and complete registration."""
    lat = message.location.latitude
    lon = message.location.longitude
    telegram_id = message.from_user.id
    
    await update_user(telegram_id, lat=lat, lon=lon)
    
    user = await get_user(telegram_id)
    role = user.get("role", "client") if user else "client"
    
    # V8: Notify admins about new registration
    await notify_new_user(message.bot, telegram_id)
    
    await message.answer(
        "✅ Ro'yxatdan o'tish yakunlandi!\n\n"
        "🥩 Endi yaqin atrofdagi qassobxonalarni topishingiz mumkin.",
        reply_markup=get_main_kb_for_role(role, telegram_id)
    )
    await state.clear()


@router.message(ClientReg.waiting_location)
async def process_location_invalid(message: Message, state: FSMContext):
    """Ask for location button press."""
    await message.answer(
        "❌ Iltimos, lokatsiyani pastdagi tugma orqali yuboring:",
        reply_markup=request_location_kb()
    )


# ==================== SETTINGS ====================

@router.message(F.text == "⚙️ Sozlamalar")
async def show_settings(message: Message):
    """Show settings menu."""
    user = await get_user(message.from_user.id)
    role = user.get("role") if user else "client"
    
    if role == "butcher":
        await message.answer("⚙️ Sozlamalar", reply_markup=butcher_settings_kb())
    else:
        await message.answer("⚙️ Sozlamalar", reply_markup=settings_kb())


@router.message(F.text == "⬅️ Orqaga")
async def go_back(message: Message, state: FSMContext):
    """Go back to main menu."""
    await state.clear()
    telegram_id = message.from_user.id
    user = await get_user(telegram_id)
    role = user.get("role", "client") if user else "client"
    
    await message.answer(
        "🏠 Asosiy menyu",
        reply_markup=get_main_kb_for_role(role, telegram_id)
    )
    # If client, also send inline menu
    if role == "client":
        await message.answer(
            "Bo'limni tanlang:",
            reply_markup=client_menu_kb()
        )


@router.message(F.text == "ℹ️ Bot haqida")
async def about_bot(message: Message):
    """Show bot info."""
    contact = await get_support_profile()
    
    await message.answer(
        "🥩 <b>Qassobxona topish boti</b>\n\n"
        "Bu bot orqali siz:\n"
        "• Yaqin atrofdagi qassobxonalarni topishingiz\n"
        "• Go'sht narxlarini solishtirishingiz\n"
        "• Eng arzon narxlarni ko'rishingiz mumkin\n\n"
        f"📞 Murojaat uchun: {contact}",
        parse_mode="HTML"
    )


@router.message(F.text == "📩 Adminga murojaat")
async def contact_admin(message: Message):
    """Show admin contact."""
    contact = await get_support_profile()
    
    await message.answer(
        "📩 Adminga murojaat qilish uchun quyidagi kontaktga yozing:\n\n"
        f"{contact}\n\n"

    )


# ==================== SETTINGS EDIT HANDLERS ====================

def language_kb() -> ReplyKeyboardMarkup:
    """Language selection keyboard."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🇺🇿 O'zbek"), KeyboardButton(text="🇷🇺 Русский")],
            [KeyboardButton(text="⬅️ Orqaga")]
        ],
        resize_keyboard=True
    )


@router.message(F.text == "👤 Ismni o'zgartirish")
async def edit_name_start(message: Message, state: FSMContext):
    """Start name edit."""
    user = await get_user(message.from_user.id)
    lang = user.get("language", "uz") if user else "uz"
    
    await message.answer(
        t(lang, "enter_name"),
        reply_markup=back_kb()
    )
    await state.set_state(Settings.edit_name_wait)


@router.message(Settings.edit_name_wait)
async def edit_name_process(message: Message, state: FSMContext):
    """Process name edit."""
    if message.text == "⬅️ Orqaga":
        await state.clear()
        user = await get_user(message.from_user.id)
        role = user.get("role", "client") if user else "client"
        if role == "butcher":
            await message.answer("⚙️ Sozlamalar", reply_markup=butcher_settings_kb())
        else:
            await message.answer("⚙️ Sozlamalar", reply_markup=settings_kb())
        return
    
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("❌ Ism juda qisqa. Iltimos, to'liq ismingizni kiriting:")
        return
    
    await update_user(message.from_user.id, name=name)
    user = await get_user(message.from_user.id)
    lang = user.get("language", "uz") if user else "uz"
    
    await message.answer(t(lang, "name_updated"))
    await state.clear()
    
    role = user.get("role", "client") if user else "client"
    if role == "butcher":
        await message.answer("⚙️ Sozlamalar", reply_markup=butcher_settings_kb())
    else:
        await message.answer("⚙️ Sozlamalar", reply_markup=settings_kb())


@router.message(F.text == "📱 Telefonni o'zgartirish")
async def edit_phone_start(message: Message, state: FSMContext):
    """Start phone edit."""
    user = await get_user(message.from_user.id)
    lang = user.get("language", "uz") if user else "uz"
    
    await message.answer(
        t(lang, "enter_phone"),
        reply_markup=request_contact_kb()
    )
    await state.set_state(Settings.edit_phone_wait)


@router.message(Settings.edit_phone_wait, F.contact)
async def edit_phone_process(message: Message, state: FSMContext):
    """Process phone edit."""
    phone = message.contact.phone_number
    await update_user(message.from_user.id, phone=phone)
    
    user = await get_user(message.from_user.id)
    lang = user.get("language", "uz") if user else "uz"
    
    await message.answer(t(lang, "phone_updated"))
    await state.clear()
    
    role = user.get("role", "client") if user else "client"
    if role == "butcher":
        await message.answer("⚙️ Sozlamalar", reply_markup=butcher_settings_kb())
    else:
        await message.answer("⚙️ Sozlamalar", reply_markup=settings_kb())


@router.message(Settings.edit_phone_wait)
async def edit_phone_invalid(message: Message, state: FSMContext):
    """Handle invalid phone input."""
    if message.text == "⬅️ Orqaga":
        await state.clear()
        user = await get_user(message.from_user.id)
        role = user.get("role", "client") if user else "client"
        if role == "butcher":
            await message.answer("⚙️ Sozlamalar", reply_markup=butcher_settings_kb())
        else:
            await message.answer("⚙️ Sozlamalar", reply_markup=settings_kb())
        return
    
    await message.answer(
        "❌ Iltimos, telefon raqamni pastdagi tugma orqali yuboring:",
        reply_markup=request_contact_kb()
    )


@router.message(F.text == "🌐 Tilni o'zgartirish")
async def edit_language_start(message: Message, state: FSMContext):
    """Start language edit."""
    user = await get_user(message.from_user.id)
    lang = user.get("language", "uz") if user else "uz"
    
    await message.answer(
        t(lang, "select_language"),
        reply_markup=language_kb()
    )
    await state.set_state(Settings.edit_language_wait)


@router.message(Settings.edit_language_wait)
async def edit_language_process(message: Message, state: FSMContext):
    """Process language selection."""
    if message.text == "⬅️ Orqaga":
        await state.clear()
        user = await get_user(message.from_user.id)
        role = user.get("role", "client") if user else "client"
        if role == "butcher":
            await message.answer("⚙️ Sozlamalar", reply_markup=butcher_settings_kb())
        else:
            await message.answer("⚙️ Sozlamalar", reply_markup=settings_kb())
        return
    
    lang = None
    if message.text == "🇺🇿 O'zbek":
        lang = "uz"
    elif message.text == "🇷🇺 Русский":
        lang = "ru"
    
    if lang:
        await update_user(message.from_user.id, language=lang)
        await message.answer(t(lang, "language_updated"))
        await state.clear()
        
        user = await get_user(message.from_user.id)
        role = user.get("role", "client") if user else "client"
        if role == "butcher":
            await message.answer("⚙️ Sozlamalar", reply_markup=butcher_settings_kb())
        else:
            await message.answer("⚙️ Sozlamalar", reply_markup=settings_kb())
    else:
        await message.answer(
            "❌ Iltimos, quyidagi tugmalardan birini tanlang:",
            reply_markup=language_kb()
        )

