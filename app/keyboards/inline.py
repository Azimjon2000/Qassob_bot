"""Inline keyboards for the bot."""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.config import PAGE_SIZE, MEAT_SELL_CATEGORIES, MEAT_BUY_CATEGORIES
from app.utils.i18n import t


def regions_kb(regions: list, lang: str = "uz") -> InlineKeyboardMarkup:
    """Inline keyboard with regions."""
    builder = InlineKeyboardBuilder()
    for region in regions:
        # Region names are usually in DB. If we had name_ru, we could pick based on lang.
        # Assuming region dict has name_uz/name_ru or just name.
        # Current implementation likely just returns name_uz or name.
        # Let's use name_uz for now or check if region has localized name.
        # The key in code is `region["name_uz"]`. If we want ru, we might need DB change or logic.
        # For Phase 1/V8, let's just stick to what is available, but update static buttons.
        text = region.get("name_uz", "Region") # Fallback
        builder.button(
            text=text,
            callback_data=f"region:{region['id']}"
        )
    builder.adjust(2)  # 2 columns
    return builder.as_markup()


def districts_kb(districts: list, region_id: int, lang: str = "uz") -> InlineKeyboardMarkup:
    """Inline keyboard with districts."""
    builder = InlineKeyboardBuilder()
    for district in districts:
        text = district.get("name_uz", "District")
        builder.button(
            text=text,
            callback_data=f"district:{district['id']}"
        )
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"back_to_regions"))
    return builder.as_markup()


def butcher_list_kb(butchers: list, page: int = 0, total_pages: int = 1, show_distance: bool = False, lang: str = "uz") -> InlineKeyboardMarkup:
    """Paginated inline keyboard with butcher list."""
    builder = InlineKeyboardBuilder()
    
    for b in butchers:
        if show_distance and "distance" in b:
            text = f"🥩 {b['shop_name']} ({b['distance']:.1f} km)"
        else:
            text = f"🥩 {b['shop_name']}"
        builder.button(text=text, callback_data=f"butcher:{b['id']}")
    
    builder.adjust(1)  # 1 column
    
    # Pagination buttons
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"page:{page-1}"))
    nav_buttons.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"page:{page+1}"))
    
    if len(nav_buttons) > 1:
        builder.row(*nav_buttons)
    
    builder.row(InlineKeyboardButton(text=t(lang, "back"), callback_data="back_to_menu"))
    return builder.as_markup()


def butcher_detail_kb(butcher_id: int, lang: str = "uz") -> InlineKeyboardMarkup:
    """Butcher detail view keyboard."""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📍 Lokatsiyani ko'rish", callback_data=f"butcher_loc:{butcher_id}")
    builder.button(text="🐄 So'yib olish narxlari", callback_data=f"butcher_buy:{butcher_id}")
    builder.button(text="🎥 Mahsulotlar videosi", callback_data=f"butcher_video:{butcher_id}")
    builder.button(text="⬅️ Orqaga", callback_data="back_to_list")
    builder.adjust(1)
    return builder.as_markup()


def admin_butcher_kb(butcher_id: int, is_approved: bool = False, is_blocked: bool = False, is_closed: bool = False, lang: str = "uz") -> InlineKeyboardMarkup:
    """Admin actions for butcher with full V8 controls."""
    builder = InlineKeyboardBuilder()
    
    # Approve button (only if not approved)
    if not is_approved:
        builder.button(text="✅ Tasdiqlash", callback_data=f"approve:{butcher_id}")
    
    # Block/Unblock toggle
    if is_blocked:
        builder.button(text="🔓 Blokdan chiqarish", callback_data=f"unblock:{butcher_id}")
    else:
        builder.button(text="🚫 Bloklash", callback_data=f"block:{butcher_id}")
    
    # Closed/Open toggle
    if is_closed:
        builder.button(text="🟢 Ochiq qilish", callback_data=f"toggle_closed:{butcher_id}")
    else:
        builder.button(text="🟠 Yopiq qilish", callback_data=f"toggle_closed:{butcher_id}")
    
    builder.button(text="🗑 O'chirish", callback_data=f"delete:{butcher_id}")
    builder.button(text="📩 Xabar yuborish", callback_data=f"admin_msg:{butcher_id}")
    builder.button(text="⬅️ Orqaga", callback_data="admin_back_to_list")
    builder.adjust(2)
    return builder.as_markup()


def price_categories_kb(price_type: str = "SELL") -> InlineKeyboardMarkup:
    """Inline keyboard with meat categories for price editing."""
    builder = InlineKeyboardBuilder()
    
    # Use appropriate categories based on price type
    categories = MEAT_SELL_CATEGORIES if price_type == "SELL" else MEAT_BUY_CATEGORIES
    
    for cat in categories:
        builder.button(text=f"🥩 {cat}", callback_data=f"price_{price_type.lower()}:{cat}")
    
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_butcher_menu"))
    return builder.as_markup()


def broadcast_target_kb() -> InlineKeyboardMarkup:
    """Broadcast target selection."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👥 Barcha mijozlar", callback_data="broadcast:client")],
            [InlineKeyboardButton(text="🥩 Barcha qassoblar", callback_data="broadcast:butcher")],
            [InlineKeyboardButton(text="📢 Hammaga", callback_data="broadcast:all")],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="broadcast:cancel")]
        ]
    )


def confirmation_inline_kb(action: str, item_id: int, lang: str = "uz") -> InlineKeyboardMarkup:
    """Confirmation keyboard for dangerous actions."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t(lang, "cancel"), callback_data=f"cancel_{action}:{item_id}")
            ]
        ]
    )


def admin_butchers_list_kb(butchers: list, page: int = 0, total_pages: int = 1) -> InlineKeyboardMarkup:
    """Admin: Paginated list of all butchers."""
    builder = InlineKeyboardBuilder()
    
    for b in butchers:
        # Shop name + Approval status maybe?
        status = "✅" if b.get('is_approved') else "⏳"
        if b.get('is_blocked'):
            status = "🚫"
            
        text = f"{status} {b['shop_name']}"
        builder.button(text=text, callback_data=f"admin_butcher_view:{b['id']}")
    
    builder.adjust(1)
    
    # Pagination
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"admin_butchers_page:{page-1}"))
    
    nav_buttons.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="noop"))
    
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"admin_butchers_page:{page+1}"))
    
    if len(nav_buttons) > 1:
        builder.row(*nav_buttons)
        
    # No back button here? Or back to main admin menu?
    # Usually admin menu is reply keyboard, so this inline is triggered by a reply button.
    # No "Back" needed if message is fresh, but if editing we might want to close?
    # Let's keep it simple.
    
    return builder.as_markup()


def admin_butcher_detail_kb(butcher_id: int, page: int = 0) -> InlineKeyboardMarkup:
    """Admin: Butcher detail view."""
    builder = InlineKeyboardBuilder()
    
    # Actions
    builder.button(text="⬅️ Orqaga", callback_data=f"admin_butchers_page:{page}")
    builder.adjust(1)
    
    return builder.as_markup()
