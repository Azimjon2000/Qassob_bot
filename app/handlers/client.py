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
    regions_kb, districts_kb, butcher_list_kb, butcher_detail_kb
)
from app.config import PAGE_SIZE, RADIUS_OPTIONS

router = Router()


# ==================== NEARBY BUTCHERS ====================

@router.message(F.text == "👥 Foydalanuvchilar soni")
async def show_user_count_client(message: Message):
    """Show total user count for client."""
    from app.services.user_service import get_all_users_count
    count = await get_all_users_count()
    await message.answer(f"👥 Botdagi foydalanuvchilar soni: {count} ta")


@router.message(F.text == "📍 Yaqin qassobxonalar")
async def start_nearby_search(message: Message, state: FSMContext):
    """Start nearby search flow - V8: always request location."""
    # V8 requirement: ALWAYS request location for each search
    await message.answer(
        "📍 Iltimos, lokatsiyangizni yuboring:",
        reply_markup=request_location_kb()
    )
    await state.set_state(ClientSearch.waiting_location)


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
        await message.answer("🏠 Asosiy menyu", reply_markup=client_main_kb())
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

@router.message(F.text == "🥩 Go'sht narxlari")
async def start_price_search(message: Message, state: FSMContext):
    """Start price search flow."""
    regions = await list_regions()
    await message.answer(
        "Viloyatni tanlang:",
        reply_markup=regions_kb(regions)
    )
    # Reuse waiting_region state but with a flag
    await state.update_data(search_type="prices")
    await state.set_state(ClientSearch.waiting_region)


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
        await callback.message.answer("🏠 Asosiy menyu", reply_markup=client_main_kb())
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
