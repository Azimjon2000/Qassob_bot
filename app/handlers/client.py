"""Client handlers - search and price viewing."""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from app.states import ClientSearch
from app.services.user_service import update_user, get_user
from app.services.butcher_service import find_nearby_by_radius, find_by_district, get_butcher_detail, find_all_approved
from app.services.region_service import list_regions, list_districts, get_region
from app.services.geo_service import sort_by_distance
from app.services.price_service import get_cheapest_prices_by_district, get_prices
from app.keyboards.reply import (
    search_mode_kb, request_location_kb, client_main_kb, back_kb
)
from app.keyboards.inline import (
    regions_kb, districts_kb, butcher_list_kb, butcher_detail_kb,
    client_menu_kb, client_settings_kb, language_inline_kb
)
from app.config import PAGE_SIZE, RADIUS_OPTIONS

router = Router()


# ==================== MAIN MENU & SETTINGS HANDLERS ====================

@router.message(F.text == "🏠 Asosiy menyu")
async def show_main_menu_text(message: Message, state: FSMContext):
    """Resend main menu."""
    from app.services.user_service import get_user
    user = await get_user(message.from_user.id)
    role = user.get("role") if user else "client"
    
    if role == "client":
        await message.answer("🏠 Asosiy menyu", reply_markup=client_main_kb())
        await message.answer("Bo'limni tanlang:", reply_markup=client_menu_kb())
        await state.clear()


@router.callback_query(F.data == "client:about")
async def client_about_handler(callback: CallbackQuery):
    """Show about info."""
    from app.services.donate_service import get_support_profile
    contact = await get_support_profile()
    
    text = (
        "🥩 <b>Qassobxona topish boti</b>\n\n"
        "Bu bot orqali siz:\n"
        "• Yaqin atrofdagi qassobxonalarni topishingiz\n"
        "• Go'sht narxlarini solishtirishingiz\n"
        "• Eng arzon narxlarni ko'rishingiz mumkin\n\n"
        f"📞 Murojaat uchun: {contact}"
    )
    from app.keyboards.inline import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Asosiy menyu", callback_data="back_to_menu")
    
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data == "client:settings")
async def client_settings_handler(callback: CallbackQuery):
    """Show client settings."""
    await callback.message.edit_text("⚙️ Sozlamalar", reply_markup=client_settings_kb())
    await callback.answer()


@router.callback_query(F.data == "settings:contact")
async def client_contact_handler(callback: CallbackQuery):
    """Show admin contact."""
    from app.services.donate_service import get_support_profile
    contact = await get_support_profile()
    text = (
        "📩 Adminga murojaat qilish uchun quyidagi kontaktga yozing:\n\n"
        f"{contact}"
    )
    from app.keyboards.inline import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Orqaga", callback_data="client:settings")
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data == "settings:lang")
async def client_lang_handler(callback: CallbackQuery):
    """Show language selection."""
    await callback.message.edit_text("🌐 Tilni tanlang:", reply_markup=language_inline_kb())
    await callback.answer()


@router.callback_query(F.data.startswith("lang:"))
async def client_lang_process(callback: CallbackQuery):
    """Process language selection."""
    lang = callback.data.split(":")[1]
    await update_user(callback.from_user.id, language=lang)
    
    # Show success alert
    msg = "🇺🇿 Til o'zgartirildi!" if lang == "uz" else "🇷🇺 Язык изменен!"
    await callback.answer(msg, show_alert=True)
    
    # Go back to settings
    await callback.message.edit_text("⚙️ Sozlamalar", reply_markup=client_settings_kb())


# ==================== NEARBY BUTCHERS ====================

@router.callback_query(F.data == "client:count")
async def show_user_count_client(callback: CallbackQuery):
    """Show total user count for client."""
    from app.services.user_service import get_all_users_count
    count = await get_all_users_count()
    await callback.answer(f"👥 Botdagi foydalanuvchilar soni: {count} ta", show_alert=True)


@router.callback_query(F.data == "client:nearby")
async def start_nearby_search(callback: CallbackQuery, state: FSMContext):
    """Start nearby search flow."""
    # Delete menu message to clean up
    await callback.message.delete()
    
    await callback.message.answer(
        "📍 Iltimos, lokatsiyangizni yuboring:",
        reply_markup=request_location_kb()
    )
    await state.set_state(ClientSearch.waiting_location)
    await callback.answer()


@router.message(ClientSearch.waiting_location, F.location)
async def process_search_location(message: Message, state: FSMContext):
    """Process location for search."""
    lat = message.location.latitude
    lon = message.location.longitude
    
    # Update user location in DB
    await update_user(message.from_user.id, lat=lat, lon=lon)
    await state.update_data(lat=lat, lon=lon)
    
    await message.answer(
        "🔎 Qidiruv turini tanlang:",
        reply_markup=search_mode_kb()
    )
    await state.set_state(ClientSearch.waiting_search_mode)


@router.message(ClientSearch.waiting_search_mode)
async def process_search_mode(message: Message, state: FSMContext):
    """Process search mode selection."""
    text = message.text
    
    if text == "⬅️ Orqaga":
        await state.clear()
        # Restore Main Menu (Reply + Inline)
        await message.answer("🏠 Asosiy menyu", reply_markup=client_main_kb())
        await message.answer("Bo'limni tanlang:", reply_markup=client_menu_kb())
        return

    if text == "🗺 Qo'lda tanlash":
        # Manual selection - showing regions
        regions = await list_regions()
        await message.answer(
            "Viloyatni tanlang:",
            reply_markup=regions_kb(regions)
        )
        await state.set_state(ClientSearch.waiting_region)
        return

    # Check for radius options
    radius = None
    for r in RADIUS_OPTIONS:
        if text == f"{r} km":
            radius = r
            break
    
    if radius:
        # Radius search
        data = await state.get_data()
        lat, lon = data.get("lat"), data.get("lon")
        
        # We need a new service function or use logic here
        # Let's get all approved butchers and filter/sort
        butchers = await find_all_approved()
        
        # Calculate distance and sort
        sorted_butchers = sort_by_distance(butchers, lat, lon)
        
        # Filter by radius
        nearby_butchers = [b for b in sorted_butchers if b["distance"] <= radius]
        
        if not nearby_butchers:
            await message.answer(
                f"😕 {radius} km radiusda qassobxonalar topilmadi.",
                reply_markup=search_mode_kb()
            )
            return

        # Show results (paginated)
        await state.update_data(
            search_results=nearby_butchers, 
            total_pages=(len(nearby_butchers) + PAGE_SIZE - 1) // PAGE_SIZE,
            current_page=0,
            show_distance=True
        )
        
        page_butchers = nearby_butchers[:PAGE_SIZE]
        total_pages = (len(nearby_butchers) + PAGE_SIZE - 1) // PAGE_SIZE
        
        await message.answer(
            f"📍 {radius} km radiusda {len(nearby_butchers)} ta qassobxona topildi:",
            reply_markup=ReplyKeyboardRemove() # Remove reply keyboard to show results clearly
        )
        await message.answer(
            "Natijalar:",
            reply_markup=butcher_list_kb(page_butchers, 0, total_pages, show_distance=True)
        )
        # Avoid clearing state so pagination works (or use specific state)
        # We can keep waiting_search_mode or switch to a list viewing state
    else:
        await message.answer("❌ Noto'g'ri buyruq. Qidiruv turini tanlang:")


# ==================== MANUAL SEARCH & CHEAPEST PRICES ====================

@router.callback_query(F.data == "client:prices")
async def start_price_search(callback: CallbackQuery, state: FSMContext):
    """Start price search flow."""
    regions = await list_regions()
    await callback.message.edit_text(
        "Viloyatni tanlang:",
        reply_markup=regions_kb(regions)
    )
    # Reuse waiting_region state but with a flag
    await state.update_data(search_type="prices")
    await state.set_state(ClientSearch.waiting_region)
    await callback.answer()


@router.callback_query(ClientSearch.waiting_region, F.data.startswith("region:"))
async def process_region_selection(callback: CallbackQuery, state: FSMContext):
    """Process region for manual search or price search."""
    region_id = int(callback.data.split(":")[1])
    districts = await list_districts(region_id)
    
    await state.update_data(region_id=region_id)
    await callback.message.edit_text(
        "Tuman/shaharni tanlang:",
        reply_markup=districts_kb(districts, region_id)
    )
    await state.set_state(ClientSearch.waiting_district)
    await callback.answer()


@router.callback_query(ClientSearch.waiting_district, F.data == "back_to_regions")
async def back_to_regions_client(callback: CallbackQuery, state: FSMContext):
    """Back to region list."""
    regions = await list_regions()
    await callback.message.edit_text(
        "Viloyatni tanlang:",
        reply_markup=regions_kb(regions)
    )
    await state.set_state(ClientSearch.waiting_region)
    await callback.answer()


@router.callback_query(ClientSearch.waiting_district, F.data.startswith("district:"))
async def process_district_selection(callback: CallbackQuery, state: FSMContext):
    """Process district selection."""
    district_id = int(callback.data.split(":")[1])
    data = await state.get_data()
    search_type = data.get("search_type")
    
    if search_type == "prices":
        # Show cheapest prices
        prices = await get_cheapest_prices_by_district(district_id)
        
        if not prices:
            # Delete inline message first, then send new message with ReplyKeyboard
            await callback.message.delete()
            await callback.message.answer(
                "😕 Bu tumanda hozircha narxlar kiritilmagan.",
                reply_markup=client_main_kb()
            )
            await state.clear()
            return

        text = "📉 <b>Eng arzon go'sht narxlari:</b>\n\n"
        for cat, info in prices.items():
            price_fmt = f"{info['price']:,}".replace(",", " ")
            text += f"🥩 <b>{cat}</b>: {price_fmt} so'm\n"
            text += f"🏪 {info['shop_name']} ({info['phone']})\n"
            text += f"🕒 {info['updated_at'][:16]}\n\n"
        
        await callback.message.edit_text(text, parse_mode="HTML")
        # Give back button to menu
        from app.keyboards.inline import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        builder.button(text="⬅️ Asosiy menyu", callback_data="back_to_menu")
        await callback.message.edit_reply_markup(reply_markup=builder.as_markup())
        await state.clear()
        
    else:
        # Manual search - show butchers in district
        butchers = await find_by_district(district_id)
        
        if not butchers:
            await callback.message.edit_text(
                "😕 Bu tumanda qassobxonalar topilmadi."
            )
            return

        # Show list
        await state.update_data(
            search_results=butchers,
            total_pages=(len(butchers) + PAGE_SIZE - 1) // PAGE_SIZE,
            current_page=0,
            show_distance=False
        )
        
        page_butchers = butchers[:PAGE_SIZE]
        total_pages = (len(butchers) + PAGE_SIZE - 1) // PAGE_SIZE
        
        await callback.message.edit_text(
            f"📍 Tumanda {len(butchers)} ta qassobxona topildi:",
            reply_markup=butcher_list_kb(page_butchers, 0, total_pages, show_distance=False)
        )


# ==================== PAGINATION & DETAIL ====================

@router.callback_query(F.data.startswith("page:"))
async def process_pagination(callback: CallbackQuery, state: FSMContext):
    """Handle pagination."""
    page = int(callback.data.split(":")[1])
    data = await state.get_data()
    butchers = data.get("search_results", [])
    show_distance = data.get("show_distance", False)
    
    total_pages = (len(butchers) + PAGE_SIZE - 1) // PAGE_SIZE
    
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    page_butchers = butchers[start:end]
    
    await callback.message.edit_reply_markup(
        reply_markup=butcher_list_kb(page_butchers, page, total_pages, show_distance=show_distance)
    )
    await state.update_data(current_page=page)
    await callback.answer()


@router.callback_query(F.data == "noop")
async def noop_handler(callback: CallbackQuery):
    """Do nothing."""
    await callback.answer()


@router.callback_query(F.data == "back_to_menu")
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):
    """Go back to main reply menu."""
    await callback.message.delete()
    await callback.message.answer("🏠 Asosiy menyu", reply_markup=client_main_kb())
    await callback.message.answer("Bo'limni tanlang:", reply_markup=client_menu_kb())
    await state.clear()


@router.callback_query(F.data.startswith("butcher:"))
async def show_butcher_detail(callback: CallbackQuery, state: FSMContext):
    """Show butcher detail with photo."""
    butcher_id = int(callback.data.split(":")[1])
    butcher = await get_butcher_detail(butcher_id)
    
    if not butcher:
        await callback.answer("❌ Qassobxona topilmadi")
        return
    
    # Get prices
    prices = await get_prices(butcher_id, "SELL")
    price_text = ""
    if prices:
        price_text = "\n💰 <b>Narxlar:</b>\n"
        for cat, price in prices.items():
            price_fmt = f"{price:,}".replace(",", " ")
            price_text += f"- {cat}: {price_fmt} so'm\n"
    
    work_time_str = butcher['work_time'] or "Ko'rsatilmagan"
    
    # V8: Show closed status if applicable
    status_line = ""
    if butcher.get('is_closed'):
        status_line = "🟠 <b>Vaqtincha yopiq</b>\n\n"
    
    detail_text = (
        f"🥩 <b>{butcher['shop_name']}</b>\n\n"
        f"{status_line}"
        f"👤 Egasi: {butcher['owner_name']}\n"
        f"📞 Tel: {butcher['phone']}\n"
        f"📍 Manzil: {butcher['region_name']}, {butcher['district_name']}\n"
        f"🕒 Ish vaqti: {work_time_str}\n"
        f"{price_text}"
    )

    # V9: Add extra info if exists
    if butcher.get('extra_info'):
        import html
        # extra_info is already sanitized when saving, but double check or just print
        # It's better to NOT escape again if it's already escaped, but if we trust DB...
        # Let's assume it was escaped on save. But 'html.escape' was used.
        # So we can just put it. But wait, if I put it in HTML parse mode, escaped chars like &lt; will show as <.
        # Yes, that's what we want if we want to show literal text.
        # But if the user entered formatted text... The requirement said "safe sanitize".
        # So treating it as plain text is safer.
        detail_text += f"\n\n📝 <b>Qo'shimcha ma'lumot:</b>\n{butcher['extra_info']}"

    
    # Delete the list message
    await callback.message.delete()
    
    # Send photo with caption if image exists
    if butcher.get('image_file_id'):
        sent_msg = await callback.message.answer_photo(
            photo=butcher['image_file_id'],
            caption=detail_text,
            reply_markup=butcher_detail_kb(butcher_id),
            parse_mode="HTML"
        )
    else:
        # Fallback to text if no image
        sent_msg = await callback.message.answer(
            detail_text,
            reply_markup=butcher_detail_kb(butcher_id),
            parse_mode="HTML"
        )
    
    # Store message id for back navigation
    await state.update_data(detail_message_id=sent_msg.message_id)
    await callback.answer()

@router.callback_query(F.data == "back_to_list")
async def back_to_list(callback: CallbackQuery, state: FSMContext):
    """Back to list view."""
    data = await state.get_data()
    butchers = data.get("search_results", [])
    page = data.get("current_page", 0)
    show_distance = data.get("show_distance", False)
    
    total_pages = (len(butchers) + PAGE_SIZE - 1) // PAGE_SIZE
    start = page * PAGE_SIZE
    page_butchers = butchers[start:start+PAGE_SIZE]
    
    # Delete current message (photo or text)
    await callback.message.delete()
    
    # Send new list message
    await callback.message.answer(
        "Natijalar:",
        reply_markup=butcher_list_kb(page_butchers, page, total_pages, show_distance=show_distance)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("butcher_loc:"))
async def send_location(callback: CallbackQuery):
    """Send location pin."""
    butcher_id = int(callback.data.split(":")[1])
    butcher = await get_butcher_detail(butcher_id)
    
    if butcher and butcher['lat'] and butcher['lon']:
        await callback.message.answer_location(butcher['lat'], butcher['lon'])
        await callback.answer()
    else:
        await callback.answer("❌ Lokatsiya topilmadi")


@router.callback_query(F.data.startswith("butcher_buy:"))
async def send_buy_prices(callback: CallbackQuery):
    """Send buy prices."""
    butcher_id = int(callback.data.split(":")[1])
    prices = await get_prices(butcher_id, "BUY")
    
    text = "🐄 <b>So'yib olish narximiz (aholining mol/qo'yini so'yib sotib olish narxi):</b>\n\n"
    
    if prices:
        for cat, price in prices.items():
            price_fmt = f"{price:,}".replace(",", " ")
            text += f"▪️ {cat}: {price_fmt} so'm\n"
    else:
        text += "Narxlar kiritilmagan."
        
    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("butcher_video:"))
async def show_butcher_video(callback: CallbackQuery):
    """Show butcher product video."""
    butcher_id = int(callback.data.split(":")[1])
    butcher = await get_butcher_detail(butcher_id)
    
    if butcher and butcher.get('video_file_id'):
        await callback.message.answer_video(
            video=butcher['video_file_id'],
            caption=f"🎥 {butcher['shop_name']} mahsulotlari"
        )
        await callback.answer()
    else:
        await callback.answer("🎥 Video qo'yilmagan", show_alert=True)
