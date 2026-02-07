"""Butcher handlers - registration and profile management."""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from app.states import ButcherReg, ButcherUpdate
from app.services.user_service import get_user, set_role
from app.services.butcher_service import create_butcher, get_butcher_by_user, update_butcher
from app.services.admin_notify_service import notify_new_user
from app.services.region_service import list_regions, list_districts, get_region, get_district
from app.services.donate_service import get_donate_message
from app.services.price_service import upsert_price, get_prices
from app.keyboards.reply import (
    butcher_main_kb, request_contact_kb, request_location_kb,
    back_kb, skip_kb, confirm_kb
)
from app.keyboards.inline import regions_kb, districts_kb, price_categories_kb
from app.utils.i18n import t

router = Router()


# ==================== REGISTRATION ====================

@router.message(F.text == "🥩 Qassob bo'lish")
async def start_butcher_registration(message: Message, state: FSMContext):
    """Start butcher registration flow."""
    telegram_id = message.from_user.id
    user = await get_user(telegram_id)
    lang = user.get("language", "uz") if user else "uz"
    
    # Check if already a butcher
    user = await get_user(telegram_id)
    if user:
        butcher = await get_butcher_by_user(user["id"])
        if butcher:
            await message.answer(
                "❌ Siz allaqachon qassob sifatida ro'yxatdan o'tgansiz.",
                reply_markup=butcher_main_kb()
            )
            return
    
    await message.answer(
        "🥩 Qassob ro'yxatdan o'tish\n\n"
        "Do'kon nomini kiriting:",
        reply_markup=back_kb()
    )
    await state.set_state(ButcherReg.shop_name)


@router.message(ButcherReg.shop_name)
async def process_shop_name(message: Message, state: FSMContext):
    """Process shop name."""
    if message.text == "⬅️ Orqaga":
        await state.clear()
        await message.answer("❌ Ro'yxatdan o'tish bekor qilindi.")
        return
    
    shop_name = message.text.strip()
    if len(shop_name) < 3:
        await message.answer("❌ Do'kon nomi juda qisqa. Kamida 3 ta belgi kiriting:")
        return
    
    await state.update_data(shop_name=shop_name)
    await message.answer(
        f"✅ Do'kon nomi: {shop_name}\n\n"
        "Endi egasi ismini kiriting:",
        reply_markup=back_kb()
    )
    await state.set_state(ButcherReg.owner_name)


@router.message(ButcherReg.owner_name)
async def process_owner_name(message: Message, state: FSMContext):
    """Process owner name."""
    if message.text == "⬅️ Orqaga":
        await message.answer("Do'kon nomini kiriting:", reply_markup=back_kb())
        await state.set_state(ButcherReg.shop_name)
        return
    
    owner_name = message.text.strip()
    await state.update_data(owner_name=owner_name)
    
    await message.answer(
        f"✅ Egasi: {owner_name}\n\n"
        "Telefon raqamingizni yuboring:",
        reply_markup=request_contact_kb()
    )
    await state.set_state(ButcherReg.phone)


@router.message(ButcherReg.phone, F.contact)
async def process_butcher_phone_contact(message: Message, state: FSMContext):
    """Process phone from contact."""
    phone = message.contact.phone_number
    await state.update_data(phone=phone)
    
    # Show regions
    regions = await list_regions()
    await message.answer(
        "✅ Telefon saqlandi!\n\n"
        "Viloyatni tanlang:",
        reply_markup=regions_kb(regions)
    )
    await state.set_state(ButcherReg.region)


@router.message(ButcherReg.phone)
async def process_butcher_phone_text(message: Message, state: FSMContext):
    """Ask for contact button press."""
    await message.answer(
        "❌ Iltimos, telefon raqamni pastdagi tugma orqali yuboring:",
        reply_markup=request_contact_kb()
    )


@router.callback_query(ButcherReg.region, F.data.startswith("region:"))
async def process_butcher_region(callback: CallbackQuery, state: FSMContext):
    """Process region selection."""
    region_id = int(callback.data.split(":")[1])
    region = await get_region(region_id)
    
    await state.update_data(region_id=region_id, region_name=region["name_uz"])
    
    districts = await list_districts(region_id)
    await callback.message.edit_text(
        f"✅ Viloyat: {region['name_uz']}\n\n"
        "Tuman/shaharni tanlang:",
        reply_markup=districts_kb(districts, region_id)
    )
    await state.set_state(ButcherReg.district)
    await callback.answer()


@router.callback_query(ButcherReg.district, F.data == "back_to_regions")
async def back_to_regions_butcher(callback: CallbackQuery, state: FSMContext):
    """Go back to region selection."""
    regions = await list_regions()
    await callback.message.edit_text(
        "Viloyatni tanlang:",
        reply_markup=regions_kb(regions)
    )
    await state.set_state(ButcherReg.region)
    await callback.answer()


@router.callback_query(ButcherReg.district, F.data.startswith("district:"))
async def process_butcher_district(callback: CallbackQuery, state: FSMContext):
    """Process district selection."""
    district_id = int(callback.data.split(":")[1])
    district = await get_district(district_id)
    
    await state.update_data(district_id=district_id, district_name=district["name_uz"])
    
    await callback.message.edit_text(
        f"✅ Tuman: {district['name_uz']}\n\n"
        "Endi do'kon lokatsiyasini yuboring:"
    )
    await callback.message.answer(
        "📍 Lokatsiyani yuboring:",
        reply_markup=request_location_kb()
    )
    await state.set_state(ButcherReg.location)
    await callback.answer()


@router.message(ButcherReg.location, F.location)
async def process_butcher_location(message: Message, state: FSMContext):
    """Process butcher location."""
    lat = message.location.latitude
    lon = message.location.longitude
    
    await state.update_data(lat=lat, lon=lon)
    
    await message.answer(
        "✅ Lokatsiya saqlandi!\n\n"
        "Ish vaqtingizni kiriting (masalan: 08:00 - 20:00):",
        reply_markup=skip_kb()
    )
    await state.set_state(ButcherReg.work_time)


@router.message(ButcherReg.location)
async def process_butcher_location_invalid(message: Message, state: FSMContext):
    """Ask for location button press."""
    await message.answer(
        "❌ Iltimos, lokatsiyani pastdagi tugma orqali yuboring:",
        reply_markup=request_location_kb()
    )


@router.message(ButcherReg.work_time)
async def process_work_time(message: Message, state: FSMContext):
    """Process work time."""
    if message.text == "⏭ O'tkazib yuborish":
        work_time = None
    else:
        work_time = message.text.strip()
    
    await state.update_data(work_time=work_time)
    
    # V8: Ask for shop image (mandatory)
    await message.answer(
        "📷 Do'koningiz rasmini yuboring (majburiy):",
        reply_markup=back_kb()
    )
    await state.set_state(ButcherReg.image)


@router.message(ButcherReg.image, F.photo)
async def process_registration_image(message: Message, state: FSMContext):
    """Process shop image for registration."""
    photo = message.photo[-1]  # Largest size
    file_id = photo.file_id
    
    await state.update_data(image_file_id=file_id)
    
    # Show confirmation with all data
    data = await state.get_data()
    
    summary = (
        "📋 <b>Ro'yxatdan o'tish ma'lumotlari:</b>\n\n"
        f"🏪 Do'kon: {data.get('shop_name')}\n"
        f"👤 Egasi: {data.get('owner_name')}\n"
        f"📞 Telefon: {data.get('phone')}\n"
        f"📍 Viloyat: {data.get('region_name')}\n"
        f"🏘 Tuman: {data.get('district_name')}\n"
        f"🕒 Ish vaqti: {data.get('work_time') or 'Ko`rsatilmagan'}\n"
        "📷 Rasm: ✅\n\n"
        "Tasdiqlaysizmi?"
    )
    
    await message.answer(summary, parse_mode="HTML", reply_markup=confirm_kb())
    await state.set_state(ButcherReg.confirm)


@router.message(ButcherReg.image)
async def process_registration_image_invalid(message: Message, state: FSMContext):
    """Ask for photo if not provided."""
    if message.text == "⬅️ Orqaga":
        await message.answer(
            "🕒 Ish vaqtini kiriting (masalan: 08:00 - 20:00):",
            reply_markup=skip_kb()
        )
        await state.set_state(ButcherReg.work_time)
        return
    
    await message.answer(
        "❌ Iltimos, do'kon rasmini yuboring (foto sifatida):",
        reply_markup=back_kb()
    )


@router.message(ButcherReg.confirm, F.text == "✅ Tasdiqlash")
async def confirm_registration(message: Message, state: FSMContext):
    """Confirm and save butcher registration."""
    data = await state.get_data()
    telegram_id = message.from_user.id
    
    # Get user id
    user = await get_user(telegram_id)
    if not user:
        await message.answer("❌ Xatolik yuz berdi. Iltimos, /start buyrug'ini yuboring.")
        await state.clear()
        return
    
    # Create butcher
    butcher_id = await create_butcher(user["id"], data)
    
    # Update user role
    await set_role(telegram_id, "butcher")
    
    # V8: Notify admins about new registration
    await notify_new_user(message.bot, telegram_id)
    
    await message.answer(
        "✅ Ro'yxatdan o'tish yakunlandi!\n\n"
        "Admin tasdiqidan so'ng siz qassobxonalar ro'yxatida ko'rinasiz.\n"
        "Tasdiq haqida xabar beramiz.",
        reply_markup=butcher_main_kb()
    )
    await state.clear()


@router.message(ButcherReg.confirm, F.text == "❌ Bekor qilish")
async def cancel_registration(message: Message, state: FSMContext):
    """Cancel registration."""
    await state.clear()
    await message.answer("❌ Ro'yxatdan o'tish bekor qilindi.")


# ==================== PROFILE UPDATE ====================

@router.message(F.text == "📌 Lokatsiyani yangilash")
async def update_location_start(message: Message, state: FSMContext):
    """Start location update."""
    await message.answer(
        "📍 Yangi lokatsiyangizni yuboring:",
        reply_markup=request_location_kb()
    )
    await state.set_state(ButcherUpdate.updating_location)


@router.message(ButcherUpdate.updating_location, F.location)
async def update_location_process(message: Message, state: FSMContext):
    """Process location update."""
    lat = message.location.latitude
    lon = message.location.longitude
    telegram_id = message.from_user.id
    
    user = await get_user(telegram_id)
    if user:
        butcher = await get_butcher_by_user(user["id"])
        if butcher:
            await update_butcher(butcher["id"], lat=lat, lon=lon)
            await message.answer(
                "✅ Lokatsiya yangilandi!",
                reply_markup=butcher_main_kb()
            )
    
    await state.clear()


@router.message(F.text == "📞 Kontaktni yangilash")
async def update_phone_start(message: Message, state: FSMContext):
    """Start phone update."""
    await message.answer(
        "📱 Yangi telefon raqamingizni yuboring:",
        reply_markup=request_contact_kb()
    )
    await state.set_state(ButcherUpdate.updating_phone)


@router.message(ButcherUpdate.updating_phone, F.contact)
async def update_phone_process(message: Message, state: FSMContext):
    """Process phone update."""
    phone = message.contact.phone_number
    telegram_id = message.from_user.id
    
    user = await get_user(telegram_id)
    if user:
        butcher = await get_butcher_by_user(user["id"])
        if butcher:
            await update_butcher(butcher["id"], phone=phone)
            await message.answer(
                "✅ Telefon raqam yangilandi!",
                reply_markup=butcher_main_kb()
            )
    
    await state.clear()


@router.message(F.text == "🕒 Ish vaqti")
async def update_work_time_start(message: Message, state: FSMContext):
    """Start work time update."""
    await message.answer(
        "🕒 Yangi ish vaqtini kiriting (masalan: 08:00 - 20:00):",
        reply_markup=back_kb()
    )
    await state.set_state(ButcherUpdate.updating_work_time)


@router.message(ButcherUpdate.updating_work_time)
async def update_work_time_process(message: Message, state: FSMContext):
    """Process work time update."""
    if message.text == "⬅️ Orqaga":
        await state.clear()
        await message.answer("🏠 Asosiy menyu", reply_markup=butcher_main_kb())
        return
    
    work_time = message.text.strip()
    telegram_id = message.from_user.id
    
    user = await get_user(telegram_id)
    if user:
        butcher = await get_butcher_by_user(user["id"])
        if butcher:
            await update_butcher(butcher["id"], work_time=work_time)
            await message.answer(
                "✅ Ish vaqti yangilandi!",
                reply_markup=butcher_main_kb()
            )
    
    await state.clear()


@router.message(F.text == "🖼 Do'kon rasmini yangilash")
async def update_image_start(message: Message, state: FSMContext):
    """Start image update."""
    await message.answer(
        "📷 Do'koningiz rasmini yuboring:",
        reply_markup=back_kb()
    )
    await state.set_state(ButcherUpdate.uploading_image)


@router.message(ButcherUpdate.uploading_image, F.photo)
async def update_image_process(message: Message, state: FSMContext):
    """Process image update."""
    photo = message.photo[-1]  # Largest size
    file_id = photo.file_id
    telegram_id = message.from_user.id
    
    user = await get_user(telegram_id)
    if user:
        butcher = await get_butcher_by_user(user["id"])
        if butcher:
            await update_butcher(butcher["id"], image_file_id=file_id)
            await message.answer(
                "✅ Rasm saqlandi!",
                reply_markup=butcher_main_kb()
            )
    
    await state.clear()


# ==================== PRICE MANAGEMENT ====================

@router.message(F.text == "💰 Sotish narxlari")
async def manage_sell_prices(message: Message, state: FSMContext):
    """Manage sell prices."""
    # Check if approved
    user = await get_user(message.from_user.id)
    if not user:
        return
        
    butcher = await get_butcher_by_user(user["id"])
    if not butcher or not butcher["is_approved"]:
        await message.answer("❌ Profilingiz hali tasdiqlanmagan.")
        return

    # Show categories
    prices = await get_prices(butcher["id"], "SELL")
    text = "💰 <b>Sotish narxlaringiz:</b>\n\n"
    
    if prices:
        for cat, price in prices.items():
            price_fmt = f"{price:,}".replace(",", " ")
            text += f"▪️ {cat}: {price_fmt} so'm\n"
    else:
        text += "Narxlar kiritilmagan.\n"
        
    text += "\nO'zgartirish uchun kategoriyani tanlang:"
    
    await message.answer(text, parse_mode="HTML", reply_markup=price_categories_kb("SELL"))


@router.message(F.text == "🐄 Sotib olish narxlari")
async def manage_buy_prices(message: Message, state: FSMContext):
    """Manage buy prices."""
    # Check if approved
    user = await get_user(message.from_user.id)
    if not user:
        return
        
    butcher = await get_butcher_by_user(user["id"])
    if not butcher or not butcher["is_approved"]:
        await message.answer("❌ Profilingiz hali tasdiqlanmagan.")
        return

    # Show categories
    prices = await get_prices(butcher["id"], "BUY")
    text = "🐄 <b>Sotib olish narxlaringiz:</b>\n\n"
    
    if prices:
        for cat, price in prices.items():
            price_fmt = f"{price:,}".replace(",", " ")
            text += f"▪️ {cat}: {price_fmt} so'm\n"
    else:
        text += "Narxlar kiritilmagan.\n"
        
    text += "\nO'zgartirish uchun kategoriyani tanlang:"
    
    await message.answer(text, parse_mode="HTML", reply_markup=price_categories_kb("BUY"))


@router.callback_query(F.data == "back_to_butcher_menu")
async def back_to_butcher_menu(callback: CallbackQuery):
    """Back to main menu from inline."""
    await callback.message.delete()
    await callback.message.answer("🏠 Asosiy menyu", reply_markup=butcher_main_kb())


@router.callback_query(F.data.startswith("price_"))
async def process_price_category(callback: CallbackQuery, state: FSMContext):
    """Process category selection for price update."""
    parts = callback.data.split(":")
    # price_sell:Mol or price_buy:Qo'y
    price_type = "SELL" if "sell" in parts[0] else "BUY"
    category = parts[1]
    
    await state.update_data(
        price_type=price_type,
        price_category=category
    )
    
    type_text = "sotish" if price_type == "SELL" else "sotib olish"
    
    await callback.message.edit_text(
        f"🥩 <b>{category}</b> ({type_text}) narxini kiriting:\n\n"
        "Faqat raqam yozing (masalan, 65000):",
        parse_mode="HTML"
    )
    await state.set_state(ButcherUpdate.price_value)
    
    # We can't delete the inline keyboard easily if we edit text, so we assume user enters text next.
    # But wait, edit_text removes the previous markup by default if not provided.
    await callback.answer()


@router.message(ButcherUpdate.price_value)
async def process_price_value(message: Message, state: FSMContext):
    """Process price value input."""
    text = message.text.strip().replace(" ", "")
    
    if not text.isdigit():
        await message.answer("❌ Iltimos, faqat raqam kiriting (masalan, 65000):")
        return
        
    price = int(text)
    data = await state.get_data()
    price_type = data.get("price_type")
    category = data.get("price_category")
    
    telegram_id = message.from_user.id
    user = await get_user(telegram_id)
    butcher = await get_butcher_by_user(user["id"])
    
    if butcher:
        await upsert_price(butcher["id"], price_type, category, price)
        
        type_text = "sotish" if price_type == "SELL" else "sotib olish"
        price_fmt = f"{price:,}".replace(",", " ")
        
        await message.answer(
            f"✅ {category} ({type_text}) narxi yangilandi: {price_fmt} so'm",
            reply_markup=butcher_main_kb()
        )
    
    await state.clear()


@router.message(F.text == "💳 Donat")
async def cmd_donate(message: Message):
    """Show donate info."""
    text = await get_donate_message()
    await message.answer(text, parse_mode="HTML")
