"""Barber registration FSM handlers — Revised for Reply Keyboards."""
import logging
import re

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from app.states.barber_reg import BarberRegFSM
from app.services import user_service, barber_service, admin_service
from app.db.base import fetch_all, fetch_one
from app.keyboards.inline import (
    admin_barber_approve_keyboard,
    barber_reg_edit_keyboard,
)
from app.keyboards.reply import (
    phone_request_keyboard,
    location_request_keyboard,
    region_reply_keyboard,
    district_reply_keyboard,
    confirm_reply_keyboard,
    remove_keyboard,
    main_menu_reply_keyboard,
)
from app.utils.flow_message import ensure_flow_message
from app.loader import bot

logger = logging.getLogger("barbershop")

router = Router(name="barber_reg")

PHONE_RE = re.compile(r"^\+998\d{9}$")


def get_lang(texts: dict) -> str:
    """Detect language from texts dict (heuristic)."""
    return "ru" if texts.get("btn_client") == "👤 Клиент" else "uz"


# ── Step 1: Name ──

@router.message(BarberRegFSM.name, F.text)
async def on_barber_name(message: Message, state: FSMContext, texts: dict, **kwargs):
    name = message.text.strip()
    if len(name) < 2 or len(name) > 100:
        await message.answer(texts["enter_name"])
        return
    await state.update_data(name=name)
    await state.set_state(BarberRegFSM.phone)
    await message.answer(texts["share_phone"], reply_markup=phone_request_keyboard(texts))


# ── Step 2: Phone ──

@router.message(BarberRegFSM.phone, F.contact)
async def on_barber_phone_contact(message: Message, state: FSMContext, texts: dict, **kwargs):
    phone = message.contact.phone_number
    if not phone.startswith("+"):
        phone = "+" + phone
    await _process_phone(message, state, texts, phone)


@router.message(BarberRegFSM.phone, F.text.in_(["🏠 Asosiy menyu", "🏠 Главное меню"]))
async def on_barber_reg_interrupt(message: Message, state: FSMContext, texts: dict, **kwargs):
    from app.keyboards.inline import role_keyboard
    await state.clear()
    await message.answer(texts["choose_role"], reply_markup=role_keyboard(texts))


@router.message(BarberRegFSM.phone, F.text)
async def on_barber_phone_text(message: Message, state: FSMContext, texts: dict, **kwargs):
    phone = message.text.strip()
    if not PHONE_RE.match(phone):
        await message.answer(texts["invalid_phone"])
        return
    await _process_phone(message, state, texts, phone)


async def _process_phone(message: Message, state: FSMContext, texts: dict, phone: str):
    await state.update_data(phone=phone)
    await state.set_state(BarberRegFSM.region)
    
    # Fetch regions
    regions = await fetch_all("SELECT id, name_uz, name_ru FROM regions ORDER BY id")
    if not regions:
        await message.answer("Error: No regions found.")
        return

    lang = get_lang(texts)
    names = [r[f"name_{lang}"] for r in regions]
    
    await message.answer(
        texts["choose_region"],
        reply_markup=region_reply_keyboard(names, texts)
    )


# ── Step 3: Region ──

@router.message(BarberRegFSM.region, F.text.in_(["🏠 Asosiy menyu", "🏠 Главное меню"]))
async def on_barber_region_interrupt(message: Message, state: FSMContext, texts: dict, **kwargs):
    await on_barber_reg_interrupt(message, state, texts, **kwargs)


@router.message(BarberRegFSM.region, F.text)
async def on_barber_region_text(message: Message, state: FSMContext, texts: dict, **kwargs):
    text = message.text.strip()
    regions = await fetch_all("SELECT id, name_uz, name_ru FROM regions")
    
    lang = get_lang(texts)
    selected_region = None
    for r in regions:
        if r[f"name_{lang}"] == text:
            selected_region = r
            break
            
    if not selected_region:
        # Invalid region name
        names = [r[f"name_{lang}"] for r in regions]
        await message.answer(texts["choose_region"], reply_markup=region_reply_keyboard(names, texts))
        return

    await state.update_data(region_id=selected_region["id"], region_name=selected_region["name_uz"])
    await state.set_state(BarberRegFSM.district)
    
    # Fetch districts
    districts = await fetch_all(
        "SELECT id, name_uz, name_ru FROM districts WHERE region_id = ? ORDER BY id",
        (selected_region["id"],)
    )
    names = [d[f"name_{lang}"] for d in districts]
    
    await message.answer(
        texts["choose_district"],
        reply_markup=district_reply_keyboard(names, texts)
    )


# ── Step 4: District ──

@router.message(BarberRegFSM.district, F.text.in_(["🏠 Asosiy menyu", "🏠 Главное меню"]))
async def on_barber_district_interrupt(message: Message, state: FSMContext, texts: dict, **kwargs):
    await on_barber_reg_interrupt(message, state, texts, **kwargs)


@router.message(BarberRegFSM.district, F.text)
async def on_barber_district_text(message: Message, state: FSMContext, texts: dict, **kwargs):
    text = message.text.strip()
    
    # Handle Back
    if text in [texts["back"], "⬅️ Orqaga", "◀️ Назад"]:
        # Go back to Region
        await state.set_state(BarberRegFSM.region)
        regions = await fetch_all("SELECT id, name_uz, name_ru FROM regions ORDER BY id")
        lang = get_lang(texts)
        names = [r[f"name_{lang}"] for r in regions]
        await message.answer(texts["choose_region"], reply_markup=region_reply_keyboard(names, texts))
        return

    data = await state.get_data()
    region_id = data.get("region_id")
    districts = await fetch_all(
        "SELECT id, name_uz, name_ru FROM districts WHERE region_id = ?",
        (region_id,)
    )
    
    lang = get_lang(texts)
    selected_district = None
    for d in districts:
        if d[f"name_{lang}"] == text:
            selected_district = d
            break
            
    if not selected_district:
        names = [d[f"name_{lang}"] for d in districts]
        await message.answer(texts["choose_district"], reply_markup=district_reply_keyboard(names, texts))
        return

    await state.update_data(district_id=selected_district["id"], district_name=selected_district["name_uz"])
    await state.set_state(BarberRegFSM.salon_name)
    
    # Remove keyboard for text input
    await message.answer(texts["enter_salon_name"], reply_markup=remove_keyboard())


# ── Step 5: Salon Name ──

@router.message(BarberRegFSM.salon_name, F.text)
async def on_barber_salon_name(message: Message, state: FSMContext, texts: dict, **kwargs):
    salon_name = message.text.strip()
    if len(salon_name) < 2 or len(salon_name) > 100:
        await message.answer(texts["enter_salon_name"])
        return
    await state.update_data(salon_name=salon_name)
    await state.set_state(BarberRegFSM.photo)
    await message.answer(texts["send_salon_photo"])


# ── Step 6: Photo ──

@router.message(BarberRegFSM.photo, F.photo)
async def on_barber_photo(message: Message, state: FSMContext, texts: dict, **kwargs):
    photo_file_id = message.photo[-1].file_id
    await state.update_data(photo_file_id=photo_file_id)
    await state.set_state(BarberRegFSM.location)
    await message.answer(texts["share_location"], reply_markup=location_request_keyboard(texts))


@router.message(BarberRegFSM.photo)
async def on_barber_photo_invalid(message: Message, state: FSMContext, texts: dict, **kwargs):
    await message.answer(texts["send_salon_photo"])


# ── Step 7: Location ──

@router.message(BarberRegFSM.location, F.text.in_(["🏠 Asosiy menyu", "🏠 Главное меню"]))
async def on_barber_location_interrupt(message: Message, state: FSMContext, texts: dict, **kwargs):
    await on_barber_reg_interrupt(message, state, texts, **kwargs)


@router.message(BarberRegFSM.location, F.location)
async def on_barber_location(message: Message, state: FSMContext, texts: dict, **kwargs):
    lat = message.location.latitude
    lon = message.location.longitude
    await state.update_data(lat=lat, lon=lon)
    await _show_confirmation(message, state, texts)


@router.message(BarberRegFSM.location)
async def on_barber_location_invalid(message: Message, state: FSMContext, texts: dict, **kwargs):
    await message.answer(texts["share_location"], reply_markup=location_request_keyboard(texts))


async def _show_confirmation(message: Message, state: FSMContext, texts: dict):
    await state.set_state(BarberRegFSM.confirm)
    data = await state.get_data()
    confirm_text = texts["confirm_registration"].format(
        name=data["name"],
        phone=data["phone"],
        region=data.get("region_name", "?"),
        district=data.get("district_name", "?"),
        salon_name=data["salon_name"],
    )
    await message.answer(confirm_text, reply_markup=confirm_reply_keyboard(texts), parse_mode="HTML")


# ── Step 8: Confirmation ──

@router.message(BarberRegFSM.confirm, F.text)
async def on_barber_confirm_text(message: Message, state: FSMContext, texts: dict, **kwargs):
    text = message.text.strip()
    
    if text == texts["confirm"]:
        await _finalize_registration(message, state, texts)
    elif text == texts["cancel"]:
        # Cancel
        await on_barber_reg_interrupt(message, state, texts, **kwargs)
    elif text in ["The texts['main_menu']", "🏠 Asosiy menyu", "🏠 Главное меню"]:
        await on_barber_reg_interrupt(message, state, texts, **kwargs)
    else:
        # Invalid input, show confirm again
        await _show_confirmation(message, state, texts)


async def _finalize_registration(message: Message, state: FSMContext, texts: dict):
    data = await state.get_data()
    user_id = message.from_user.id
    lang = data.get("lang", "uz")

    await user_service.upsert_user(user_id, "barber")
    await barber_service.create_barber(
        telegram_id=user_id,
        name=data["name"],
        phone=data["phone"],
        region_id=data["region_id"],
        district_id=data["district_id"],
        salon_name=data["salon_name"],
        photo_file_id=data.get("photo_file_id"),
        lat=data.get("lat"),
        lon=data.get("lon"),
        lang=lang,
    )

    await state.clear()
    await message.answer(texts["reg_sent_pending"], reply_markup=main_menu_reply_keyboard(texts))

    # Notify admins
    admin_ids = await admin_service.get_all_admin_ids()
    
    from app.utils.time_utils import now_tashkent
    total_users = await user_service.get_total_users()
    dt = now_tashkent().strftime("%Y-%m-%d %H:%M:%S")

    # Inline format to match requirements: Sequence, Name, Phone, ID, Date
    # Plus standard barber info for approval
    admin_text = (
        f"🆕 <b>Yangi Sartarosh (Barber) Ro'yxatdan o'tdi</b>\n\n"
        f"🔢 №: {total_users}\n"
        f"👤 Ism: {data['name']}\n"
        f"📱 Tel: {data['phone']}\n"
        f"🆔 ID: {user_id}\n"
        f"🕒 Vaqt: {dt}\n\n"
        f"💈 Salon: {data['salon_name']}\n"
        f"📍 Manzil: {data.get('region_name', '?')}, {data.get('district_name', '?')}"
    )
    
    for admin_id in admin_ids:
        try:
            if data.get("photo_file_id"):
                await bot.send_photo(
                    chat_id=admin_id,
                    photo=data["photo_file_id"],
                    caption=admin_text,
                    reply_markup=admin_barber_approve_keyboard(user_id, texts),
                    parse_mode="HTML",
                )
            else:
                await bot.send_message(
                    chat_id=admin_id,
                    text=admin_text,
                    reply_markup=admin_barber_approve_keyboard(user_id, texts),
                    parse_mode="HTML",
                )
        except Exception as e:
            logger.warning(f"Failed to notify admin {admin_id}: {e}")
