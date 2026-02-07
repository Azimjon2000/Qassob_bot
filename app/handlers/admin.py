"""Admin handlers - management and broadcast."""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from app.config import ADMINS

from app.states import AdminBroadcast, AdminSupport, AdminAddAdmin, AdminButcherMessage
from app.services.user_service import get_user_counts, get_user_by_id, get_user, upsert_user, set_role
from app.services.butcher_service import (
    get_butcher_counts, get_pending_butchers, get_butcher_detail,
    approve_butcher, block_butcher, unblock_butcher, toggle_closed, delete_butcher, get_all_butchers_paginated
)
from app.services.broadcast_service import send_broadcast
from app.services.donate_service import (
    get_donate_settings, set_donate_card_number,
    get_support_profile, set_support_profile, set_donate_default_amount
)
from app.keyboards.reply import admin_main_kb, back_kb
from app.keyboards.inline import (
    admin_butcher_kb, broadcast_target_kb, confirmation_inline_kb,
    admin_butchers_list_kb, admin_butcher_detail_kb
)

router = Router()


# ==================== MIDDLEWARE / FILTER ====================

def is_admin(telegram_id: int) -> bool:
    return telegram_id in ADMINS

@router.message(lambda m: not is_admin(m.from_user.id))
async def not_admin_handler(message: Message):
    """Ignore non-admin messages if they reach here."""
    pass


# ==================== STATISTICS ====================

@router.message(F.text == "📊 Statistika", F.from_user.id.in_(ADMINS))
async def cmd_statistics(message: Message):
    """Show statistics."""
    user_counts = await get_user_counts()
    butcher_counts = await get_butcher_counts()
    
    text = (
        "📊 <b>Statistika</b>\n\n"
        f"👥 <b>Foydalanuvchilar:</b>\n"
        f"• Jami: {user_counts['total']}\n"
        f"• Client: {user_counts['client']}\n"
        f"• Butcher: {user_counts['butcher']}\n"
        f"• Admin: {user_counts['admin']}\n\n"
        f"🏪 <b>Qassobxonalar:</b>\n"
        f"• Jami: {butcher_counts['total']}\n"
        f"• Tasdiqlangan: {butcher_counts['approved']}\n"
        f"• Kutilmoqda: {butcher_counts['pending']}\n"
        f"• Bloklangan: {butcher_counts['blocked']}"
    )
    
    await message.answer(text, parse_mode="HTML")


# ==================== BUTCHER MANAGEMENT ====================

@router.message(F.text == "🏪 Qassobxonalar", F.from_user.id.in_(ADMINS))
async def cmd_manage_butchers(message: Message):
    """Show all butchers list (paginated)."""
    # Use page 0 by default
    result = await get_all_butchers_paginated(0)
    
    if not result["items"]:
        await message.answer("✅ Qassobxonalar topilmadi.")
        return
        
    await message.answer(
        f"📋 <b>Barcha qassobxonalar ({result['total']} ta):</b>\n"
        "Batafsil ma'lumot olish uchun tanlang:",
        reply_markup=admin_butchers_list_kb(result["items"], 0, result["total_pages"]),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("admin_butchers_page:"), F.from_user.id.in_(ADMINS))
async def process_butchers_page(callback: CallbackQuery):
    """Handle butcher list pagination."""
    page = int(callback.data.split(":")[1])
    result = await get_all_butchers_paginated(page)
    
    await callback.message.edit_text(
        f"📋 <b>Barcha qassobxonalar ({result['total']} ta):</b>\n"
        "Batafsil ma'lumot olish uchun tanlang:",
        reply_markup=admin_butchers_list_kb(result["items"], page, result["total_pages"]),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("admin_butcher_view:"), F.from_user.id.in_(ADMINS))
async def process_butcher_view(callback: CallbackQuery):
    """Show butcher details."""
    user = await get_user(callback.from_user.id)
    lang = user.get("language", "uz") if user else "uz"

    butcher_id = int(callback.data.split(":")[1])
    butcher = await get_butcher_detail(butcher_id)
    
    if not butcher:
        await callback.answer("❌ Ma'lumot topilmadi", show_alert=True)
        return
        
    # Construct detail message
    status = "✅ Faol" if butcher['is_approved'] else "⏳ Kutilmoqda"
    if butcher.get('is_blocked'):
        status = "🚫 Bloklangan"
    if butcher.get('is_closed'):
        status += " | 🟠 Yopiq"
        
    text = (
        f"🏪 <b>{butcher['shop_name']}</b>\n\n"
        f"👤 <b>Egasi:</b> {butcher['owner_name']}\n"
        f"📞 <b>Telefon:</b> {butcher['phone']}\n"
    )
    
    # Needs to fetch user for TG ID
    target_user = await get_user_by_id(butcher['user_id'])
    if target_user:
        text += f"🆔 <b>Telegram ID:</b> <code>{target_user['telegram_id']}</code>\n"
        
    text += (
        f"📍 <b>Manzil:</b> {butcher['region_name']}, {butcher['district_name']}\n"
        f"🕒 <b>Ish vaqti:</b> {butcher['work_time'] or 'Kiritilmagan'}\n"
        f"📊 <b>Holati:</b> {status}\n"
        f"📅 <b>Ro'yxatdan o'tgan:</b> {butcher['created_at']}"
    )
    
    # V8: Pass all status flags to admin_butcher_kb
    markup = admin_butcher_kb(
        butcher_id, 
        is_approved=bool(butcher['is_approved']),
        is_blocked=bool(butcher.get('is_blocked')),
        is_closed=bool(butcher.get('is_closed')),
        lang=lang
    )
    
    # If image exists, send as photo, otherwise text
    if butcher.get('image_file_id'):
        await callback.message.delete() # Delete list message
        await callback.message.answer_photo(
            butcher['image_file_id'],
            caption=text,
            reply_markup=markup,
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            text,
            reply_markup=markup,
            parse_mode="HTML"
        )


@router.callback_query(F.data == "admin_back_to_list", F.from_user.id.in_(ADMINS))
async def back_to_butcher_list(callback: CallbackQuery):
    """Back to page 0 of butcher list."""
    # We could try to delete the photo message if it was a photo
    if callback.message.content_type == "photo":
        await callback.message.delete()
        # Send new message with list
        result = await get_all_butchers_paginated(0)
        await callback.message.answer(
            f"📋 <b>Barcha qassobxonalar ({result['total']} ta):</b>\n"
            "Batafsil ma'lumot olish uchun tanlang:",
            reply_markup=admin_butchers_list_kb(result["items"], 0, result["total_pages"]),
            parse_mode="HTML"
        )
    else:
        # Edit text
        await process_butchers_page(callback) # This won't work because callback data is different.
        # We need to manually call get_all_butchers_paginated(0) and edit
        result = await get_all_butchers_paginated(0)
        await callback.message.edit_text(
            f"📋 <b>Barcha qassobxonalar ({result['total']} ta):</b>\n"
            "Batafsil ma'lumot olish uchun tanlang:",
            reply_markup=admin_butchers_list_kb(result["items"], 0, result["total_pages"]),
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("approve:"), F.from_user.id.in_(ADMINS))
async def process_approve(callback: CallbackQuery):
    """Approve butcher."""
    butcher_id = int(callback.data.split(":")[1])
    await approve_butcher(butcher_id)
    
    await callback.message.edit_text(
        f"{callback.message.html_text}\n\n✅ <b>TASDIQLANDI</b>",
        parse_mode="HTML"
    )
    
    # Notify butcher? (Would need bot instance and user_id)
    butcher = await get_butcher_detail(butcher_id)
    if butcher:
        user = await get_user_by_id(butcher['user_id'])
        if user:
            try:
                await callback.bot.send_message(
                    user['telegram_id'],
                    f"✅ Tabriklaymiz! Sizning '{butcher['shop_name']}' do'koningiz tasdiqlandi.\n"
                    "Endi siz narxlarni boshqarishingiz mumkin."
                )
            except:
                pass


@router.callback_query(F.data.startswith("block:"), F.from_user.id.in_(ADMINS))
async def process_block(callback: CallbackQuery):
    """Block butcher."""
    butcher_id = int(callback.data.split(":")[1])
    # Show confirmation
    await callback.message.edit_reply_markup(
        reply_markup=confirmation_inline_kb("block", butcher_id)
    )


@router.callback_query(F.data.startswith("confirm_block:"), F.from_user.id.in_(ADMINS))
async def confirm_block(callback: CallbackQuery):
    """Confirm block."""
    butcher_id = int(callback.data.split(":")[1])
    await block_butcher(butcher_id)
    
    await callback.message.edit_text(
        f"{callback.message.html_text}\n\n🚫 <b>BLOKLANDI</b>",
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("unblock:"), F.from_user.id.in_(ADMINS))
async def process_unblock(callback: CallbackQuery):
    """Unblock butcher."""
    butcher_id = int(callback.data.split(":")[1])
    await unblock_butcher(butcher_id)
    
    await callback.answer("✅ Blokdan chiqarildi!")
    
    # Refresh the view
    butcher = await get_butcher_detail(butcher_id)
    if butcher:
        markup = admin_butcher_kb(
            butcher_id, 
            is_approved=bool(butcher['is_approved']),
            is_blocked=False,
            is_closed=bool(butcher.get('is_closed'))
        )
        try:
            await callback.message.edit_reply_markup(reply_markup=markup)
        except:
            pass


@router.callback_query(F.data.startswith("toggle_closed:"), F.from_user.id.in_(ADMINS))
async def process_toggle_closed(callback: CallbackQuery):
    """Toggle closed status."""
    butcher_id = int(callback.data.split(":")[1])
    new_status = await toggle_closed(butcher_id)
    
    status_text = "🟠 Yopiq qilindi" if new_status else "🟢 Ochiq qilindi"
    await callback.answer(status_text)
    
    # Refresh the view
    butcher = await get_butcher_detail(butcher_id)
    if butcher:
        markup = admin_butcher_kb(
            butcher_id, 
            is_approved=bool(butcher['is_approved']),
            is_blocked=bool(butcher.get('is_blocked')),
            is_closed=new_status
        )
        try:
            await callback.message.edit_reply_markup(reply_markup=markup)
        except:
            pass


@router.callback_query(F.data.startswith("admin_msg:"), F.from_user.id.in_(ADMINS))
async def start_admin_message(callback: CallbackQuery, state: FSMContext):
    """Start admin message to butcher flow."""
    butcher_id = int(callback.data.split(":")[1])
    await state.update_data(admin_msg_butcher_id=butcher_id)
    
    await callback.message.answer(
        "📩 Qassobga yubormoqchi bo'lgan xabaringizni yozing:",
        reply_markup=back_kb()
    )
    await state.set_state(AdminButcherMessage.waiting_message)
    await callback.answer()


@router.message(AdminButcherMessage.waiting_message, F.from_user.id.in_(ADMINS))
async def process_admin_message(message: Message, state: FSMContext):
    """Send admin message to butcher."""
    if message.text == "⬅️ Orqaga":
        await state.clear()
        await message.answer("Bekor qilindi", reply_markup=admin_main_kb())
        return
    
    data = await state.get_data()
    butcher_id = data.get("admin_msg_butcher_id")
    
    if not butcher_id:
        await message.answer("❌ Xatolik yuz berdi", reply_markup=admin_main_kb())
        await state.clear()
        return
    
    # Get butcher's telegram ID
    butcher = await get_butcher_detail(butcher_id)
    if not butcher:
        await message.answer("❌ Qassob topilmadi", reply_markup=admin_main_kb())
        await state.clear()
        return
    
    target_user = await get_user_by_id(butcher['user_id'])
    if not target_user:
        await message.answer("❌ Foydalanuvchi topilmadi", reply_markup=admin_main_kb())
        await state.clear()
        return
    
    try:
        await message.bot.send_message(
            target_user['telegram_id'],
            f"📩 <b>Admin xabari:</b>\n\n{message.text}",
            parse_mode="HTML"
        )
        await message.answer(
            f"✅ Xabar yuborildi: {butcher['shop_name']}",
            reply_markup=admin_main_kb()
        )
    except Exception as e:
        await message.answer(f"❌ Xabar yuborib bo'lmadi: {str(e)}", reply_markup=admin_main_kb())
    
    await state.clear()

@router.callback_query(F.data.startswith("delete:"), F.from_user.id.in_(ADMINS))
async def process_delete(callback: CallbackQuery):
    """Delete butcher."""
    butcher_id = int(callback.data.split(":")[1])
    # Show confirmation
    await callback.message.edit_reply_markup(
        reply_markup=confirmation_inline_kb("delete", butcher_id)
    )

@router.callback_query(F.data.startswith("confirm_delete:"), F.from_user.id.in_(ADMINS))
async def confirm_delete(callback: CallbackQuery):
    """Confirm delete."""
    butcher_id = int(callback.data.split(":")[1])
    await delete_butcher(butcher_id)
    
    await callback.message.delete()
    await callback.answer("🗑 O'chirildi")

@router.callback_query(F.data.startswith("cancel_"), F.from_user.id.in_(ADMINS))
async def cancel_action(callback: CallbackQuery):
    """Cancel block/delete."""
    action, butcher_id = callback.data.split("_")[1].split(":")
    # Restore original markup
    # We don't know if it was pending or approved, assume approved if managing?
    # Actually simpler to just remove the confirm markup and show admin kb
    # But we are editing a message that has text.
    await callback.message.edit_reply_markup(
        reply_markup=admin_butcher_kb(int(butcher_id))
    )


# ==================== BROADCAST ====================

@router.message(F.text == "📢 Xabar yuborish", F.from_user.id.in_(ADMINS))
async def cmd_broadcast(message: Message, state: FSMContext):
    """Start broadcast."""
    await message.answer(
        "Kimlarga xabar yubormoqchisiz?",
        reply_markup=broadcast_target_kb()
    )
    await state.set_state(AdminBroadcast.select_target)


@router.callback_query(AdminBroadcast.select_target, F.data.startswith("broadcast:"))
async def process_broadcast_target(callback: CallbackQuery, state: FSMContext):
    """Process broadcast target."""
    target = callback.data.split(":")[1]
    
    if target == "cancel":
        await callback.message.delete()
        await callback.message.answer("❌ Bekor qilindi")
        await state.clear()
        return
        
    await state.update_data(target=target)
    
    target_names = {
        "client": "Barcha mijozlar",
        "butcher": "Barcha qassoblar",
        "all": "Barcha foydalanuvchilar"
    }
    
    await callback.message.edit_text(
        f"Tanlandi: {target_names.get(target, target)}\n\n"
        "Xabar matnini yuboring (rasm, video yoki matn):"
    )
    # Use reply keyboard back?
    await state.set_state(AdminBroadcast.wait_content)


@router.message(AdminBroadcast.wait_content)
async def process_broadcast_content(message: Message, state: FSMContext):
    """Send broadcast with text, photo, or video support."""
    data = await state.get_data()
    target = data.get("target")
    
    # Prepare broadcast data
    text = None
    media_type = None
    media_file_id = None
    
    if message.text:
        # Plain text message
        text = message.text
        media_type = None
        media_file_id = None
    elif message.photo:
        # Photo with optional caption
        media_type = "photo"
        media_file_id = message.photo[-1].file_id  # Largest size
        text = message.caption
    elif message.video:
        # Video with optional caption
        media_type = "video"
        media_file_id = message.video.file_id
        text = message.caption
    else:
        # Unsupported content type
        await message.answer("Faqat matn, rasm yoki video yuboring.")
        return
    
    await message.answer("⏳ Xabar yuborilmoqda...")
    
    stats = await send_broadcast(
        bot=message.bot, 
        role_target=target, 
        message=text,
        media_type=media_type,
        media_file_id=media_file_id
    )
    
    await message.answer(
        f"✅ Xabar yuborildi!\n\n"
        f"Jami: {stats['total']}\n"
        f"Muvaffaqiyatli: {stats['success']}\n"
        f"Xatolik: {stats['failed']}",
        reply_markup=admin_main_kb()
    )
    await state.clear()



# ==================== DONATE SETTINGS ====================

@router.message(F.text == "💳 Donat sozlamalari", F.from_user.id.in_(ADMINS))
async def cmd_donate_settings(message: Message):
    """Show donate settings."""
    settings = await get_donate_settings()
    card = settings.get("donate_card_number") or "Kiritilmagan"
    amount = settings.get("donate_default_amount", 10000)
    amount_fmt = f"{amount:,}".replace(",", " ")
    
    await message.answer(
        f"💳 <b>Donat sozlamalari</b>\n\n"
        f"Hozirgi karta raqami: <code>{card}</code>\n"
        f"Standart donat miqdori: <b>{amount_fmt} so'm</b>\n\n"
        "O'zgartirish uchun quyidagi tugmalardan birini bosing:",
        parse_mode="HTML"
    )
    
    markup = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📩 Karta raqamini yangilash")],
            [KeyboardButton(text="💰 Donat miqdorini yangilash")],
            [KeyboardButton(text="⬅️ Orqaga")]
        ],
        resize_keyboard=True
    )
    await message.answer("Tanlang:", reply_markup=markup)


@router.message(F.text == "📩 Karta raqamini yangilash", F.from_user.id.in_(ADMINS))
async def ask_donate_card(message: Message, state: FSMContext):
    await message.answer("Yangi karta raqamini kiriting:", reply_markup=back_kb())
    await state.set_state(AdminBroadcast.donate_card_update_wait)


@router.message(AdminBroadcast.donate_card_update_wait)
async def process_donate_card(message: Message, state: FSMContext):
    if message.text == "⬅️ Orqaga":
        await state.clear()
        await message.answer("Bekor qilindi", reply_markup=admin_main_kb())
        return

    card = message.text.strip().replace(" ", "")
    if not card.isdigit() or len(card) < 8:
        await message.answer("❌ Karta raqami noto'g'ri. Iltimos tekshirib qayta kiriting:")
        return

    await set_donate_card_number(card)
    await message.answer(f"✅ Karta raqami saqlandi: {card}", reply_markup=admin_main_kb())
    await state.clear()


@router.message(F.text == "💰 Donat miqdorini yangilash", F.from_user.id.in_(ADMINS))
async def ask_donate_amount(message: Message, state: FSMContext):
    await message.answer("Yangi donat miqdorini kiriting (faqat raqam):", reply_markup=back_kb())
    await state.set_state(AdminBroadcast.donate_amount_update_wait)


@router.message(AdminBroadcast.donate_amount_update_wait)
async def process_donate_amount(message: Message, state: FSMContext):
    if message.text == "⬅️ Orqaga":
        await state.clear()
        await message.answer("Bekor qilindi", reply_markup=admin_main_kb())
        # Ideally return to settings, but admin_main_kb is safe fallback
        await cmd_donate_settings(message)
        return

    if not message.text.isdigit():
        await message.answer("Faqat son yuboring. Masalan: 10000")
        return

    amount = int(message.text)
    await set_donate_default_amount(amount)
    
    amount_fmt = f"{amount:,}".replace(",", " ")
    await message.answer(
        f"✅ Donat miqdori yangilandi: <b>{amount_fmt} so'm</b>",
        parse_mode="HTML"
    )
    await cmd_donate_settings(message)
    await state.clear()


# ==================== SUPPORT SETTINGS ====================

@router.message(F.text == "🛠 Qo'llab-quvvatlash", F.from_user.id.in_(ADMINS))
async def cmd_support_settings(message: Message):
    """Show support settings."""
    profile = await get_support_profile()
    
    await message.answer(
        f"🛠 <b>Qo'llab-quvvatlash profili</b>\n\n"
        f"Hozirgi profil: {profile}\n\n"
        "O'zgartirish uchun quyidagi tugmani bosing:",
        parse_mode="HTML"
    )
    
    markup = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Support profilni yangilash")],
            [KeyboardButton(text="⬅️ Orqaga")]
        ],
        resize_keyboard=True
    )
    await message.answer("Tanlang:", reply_markup=markup)


@router.message(F.text == "📝 Support profilni yangilash", F.from_user.id.in_(ADMINS))
async def ask_support_profile(message: Message, state: FSMContext):
    await message.answer(
        "Yangi support profilini kiriting (masalan: @admin yoki telefon raqam):", 
        reply_markup=back_kb()
    )
    await state.set_state(AdminSupport.support_profile_update_wait)


@router.message(AdminSupport.support_profile_update_wait)
async def process_support_profile(message: Message, state: FSMContext):
    if message.text == "⬅️ Orqaga":
        await state.clear()
        await message.answer("Bekor qilindi", reply_markup=admin_main_kb())
        return

    text = message.text.strip()
    await set_support_profile(text)
    await message.answer(f"✅ Profil saqlandi: {text}", reply_markup=admin_main_kb())
    await state.clear()


# ==================== ADMIN MANAGEMENT ====================

@router.message(F.text == "➕ Admin qo'shish", F.from_user.id.in_(ADMINS))
async def cmd_add_admin(message: Message, state: FSMContext):
    """Start add admin flow."""
    await message.answer(
        "Yangi admin Telegram ID sini kiriting:\n\n"
        "ID ni topish uchun @userinfobot ga /start yuboring.",
        reply_markup=back_kb()
    )
    await state.set_state(AdminAddAdmin.waiting_telegram_id)


@router.message(AdminAddAdmin.waiting_telegram_id)
async def process_add_admin(message: Message, state: FSMContext):
    """Process new admin ID."""
    if message.text == "⬅️ Orqaga":
        await state.clear()
        await message.answer("Bekor qilindi", reply_markup=admin_main_kb())
        return
    
    text = message.text.strip()
    if not text.isdigit():
        await message.answer("❌ Iltimos, faqat raqam kiriting:")
        return
    
    new_admin_id = int(text)
    
    # Check if user exists, if not create
    user = await get_user(new_admin_id)
    if not user:
        await upsert_user(new_admin_id)
    
    # Set role to admin
    await set_role(new_admin_id, "admin")
    
    await message.answer(
        f"✅ Yangi admin qo'shildi!\n\n"
        f"Telegram ID: {new_admin_id}",
        reply_markup=admin_main_kb()
    )
    await state.clear()

