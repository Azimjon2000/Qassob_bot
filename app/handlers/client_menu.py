"""Client menu handlers: settings, stats, support, about."""
import logging
import re

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from app.states.client_menu import ClientMenuFSM
from app.services import client_service, admin_service, user_service, barber_service
from app.keyboards.inline import (
    client_menu_keyboard, client_settings_keyboard, lang_keyboard,
    ok_keyboard,
)
from app.keyboards.reply import main_menu_reply_keyboard, phone_request_keyboard
from app.utils.flow_message import ensure_flow_message, send_ok_popup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.keyboards.inline import back_button

logger = logging.getLogger("barbershop")

router = Router(name="client_menu")

PHONE_RE = re.compile(r"^\+998\d{9}$")


# ═══════════════════════════════════════════
# Client Main Menu
# ═══════════════════════════════════════════

@router.callback_query(F.data == "back:cmenu")
async def back_to_client_menu(callback: CallbackQuery, state: FSMContext, texts: dict, **kwargs):
    await state.clear()
    await ensure_flow_message(callback, texts["client_menu_title"], state,
                               keyboard=client_menu_keyboard(texts))

# ═══════════════════════════════════════════
# Active Orders
# ═══════════════════════════════════════════

@router.callback_query(F.data == "cmenu:active_orders")
async def client_active_orders(callback: CallbackQuery, state: FSMContext, texts: dict, **kwargs):
    # This handler is now reached via "View Active Booking" button from blocking message
    from app.services import booking_service
    from app.utils.time_utils import slot_to_hour, today_tashkent, now_tashkent
    
    user_id = callback.from_user.id
    bookings = await booking_service.get_client_future_confirmed_bookings(user_id)
    
    if not bookings:
        await send_ok_popup(callback, texts["no_active_orders"])
        return

    # Filter out if (date==today and hour < now) inside python if SQL was loose
    # We only want future or current slots
    valid_bookings = []
    now = now_tashkent()
    today_str = today_tashkent()
    current_hour = now.hour

    for b in bookings:
        if b["date"] > today_str:
            valid_bookings.append(b)
        elif b["date"] == today_str:
            # If hour_slot (start time) + 1 hour is passed, it is effectively done/past
            # User wants to see ACTIVE. Let's say if it's 14:00 slot, it's active until 15:00.
            # slot_to_hour returns start hour.
            if slot_to_hour(b["hour_slot"]) + 1 > current_hour:
                valid_bookings.append(b)

    if not valid_bookings:
        await send_ok_popup(callback, texts["no_active_orders"])
        return

    # Show first valid booking (or list them? User asked for "xabari chiqarilsin" - likely one by one or list. 
    # Let's show the first one or a list. Detailed view is large. 
    # Let's iterate and send messages for each active booking or just the soonest.
    # User said "bu tugma bosilganda qilgan faol broni xabari chiqarilsin". 
    # Let's show the nearest one properly.
    
    b = valid_bookings[0]
    hour = slot_to_hour(b["hour_slot"])
    
    # Detailed text
    # sartaroshxona surati, sartarosh ismi, tel raqami, tanlangan vaqti, lokatsiyasi
    price_info = await barber_service.get_prices(b["barber_id"])
    
    text = (
        f"📅 <b>{texts['active_order_title']}</b>\n\n"
        f"💈 <b>{b['barber_name']}</b> — {b['salon_name']}\n"
        f"📱 {b['barber_phone']}\n"
        f"🕐 {hour}:00 | {b['date']}\n"
    )
    
    # Add prices if available
    if price_info:
        text += (
            f"💇 {texts['hair_price']}: {price_info.get('hair_price', '—')}\n"
            f"🧔 {texts['beard_price']}: {price_info.get('beard_price', '—')}\n"
        )
    
    text += f"📍 <a href='https://www.google.com/maps/search/?api=1&query={b['lat']},{b['lon']}'>{texts['view_location']}</a>\n\n"

    kb = InlineKeyboardMarkup(inline_keyboard=[[back_button("cmenu", texts)]])

    # If has photo, send photo with caption
    if b.get("photo_file_id"):
        await ensure_flow_message(callback, text, state, keyboard=kb, photo=b["photo_file_id"])
    else:
        await ensure_flow_message(callback, text, state, keyboard=kb)


# ═══════════════════════════════════════════
# Settings
# ═══════════════════════════════════════════

@router.callback_query(F.data == "cmenu:settings")
async def client_settings(callback: CallbackQuery, state: FSMContext, texts: dict, **kwargs):
    await ensure_flow_message(callback, texts["client_settings_title"], state,
                               keyboard=client_settings_keyboard(texts))


# ── Name ──

@router.callback_query(F.data == "cset:name")
async def cset_name_start(callback: CallbackQuery, state: FSMContext, texts: dict, **kwargs):
    await state.set_state(ClientMenuFSM.edit_name)
    await ensure_flow_message(callback, texts["enter_new_name"], state)


@router.message(ClientMenuFSM.edit_name, F.text)
async def cset_name_receive(message: Message, state: FSMContext, texts: dict, **kwargs):
    name = message.text.strip()
    if len(name) < 2 or len(name) > 100:
        await message.answer(texts["enter_new_name"])
        return
    await client_service.update_client_field(message.from_user.id, "name", name)
    await state.clear()
    await send_ok_popup(message, texts["settings_saved"])
    await ensure_flow_message(message, texts["client_settings_title"], state,
                               keyboard=client_settings_keyboard(texts))


# ── Phone ──

@router.callback_query(F.data == "cset:phone")
async def cset_phone_start(callback: CallbackQuery, state: FSMContext, texts: dict, **kwargs):
    await state.set_state(ClientMenuFSM.edit_phone)
    await callback.message.answer(texts["share_phone"], reply_markup=phone_request_keyboard(texts))
    await callback.answer()


@router.message(ClientMenuFSM.edit_phone, F.contact)
async def cset_phone_contact(message: Message, state: FSMContext, texts: dict, **kwargs):
    phone = message.contact.phone_number
    if not phone.startswith("+"):
        phone = "+" + phone
    if not PHONE_RE.match(phone):
        await message.answer(texts["invalid_phone"])
        return
    await client_service.update_client_field(message.from_user.id, "phone", phone)
    await state.clear()
    await message.answer("⠀", reply_markup=main_menu_reply_keyboard(texts))
    await send_ok_popup(message, texts["settings_saved"])
    await ensure_flow_message(message, texts["client_settings_title"], state,
                               keyboard=client_settings_keyboard(texts))


@router.message(ClientMenuFSM.edit_phone, F.text)
async def cset_phone_text(message: Message, state: FSMContext, texts: dict, **kwargs):
    phone = message.text.strip()
    if not PHONE_RE.match(phone):
        await message.answer(texts["invalid_phone"])
        return
    await client_service.update_client_field(message.from_user.id, "phone", phone)
    await state.clear()
    await message.answer("⠀", reply_markup=main_menu_reply_keyboard(texts))
    await send_ok_popup(message, texts["settings_saved"])
    await ensure_flow_message(message, texts["client_settings_title"], state,
                               keyboard=client_settings_keyboard(texts))


# ── Language ──

@router.callback_query(F.data == "cset:lang")
async def cset_lang(callback: CallbackQuery, state: FSMContext, texts: dict, **kwargs):
    await ensure_flow_message(callback, texts["choose_lang"], state,
                               keyboard=lang_keyboard())


# ═══════════════════════════════════════════
# Users Count / Support / About
# ═══════════════════════════════════════════

@router.callback_query(F.data == "cmenu:users_count")
async def client_users_count(callback: CallbackQuery, state: FSMContext, texts: dict, **kwargs):
    total = await user_service.get_total_users()
    await send_ok_popup(callback, texts["total_users"].format(count=total))


@router.callback_query(F.data == "cmenu:support")
async def client_support(callback: CallbackQuery, state: FSMContext, texts: dict, **kwargs):
    username = await admin_service.get_support_username()
    await send_ok_popup(callback, texts["support_contact"].format(username=username))


@router.callback_query(F.data == "cmenu:about")
async def client_about(callback: CallbackQuery, state: FSMContext, texts: dict, **kwargs):
    await send_ok_popup(callback, texts["client_about"])
