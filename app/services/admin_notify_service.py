"""Admin notification service."""
from datetime import datetime
from aiogram import Bot
from app.config import ADMINS
from app.services.user_service import assign_reg_no, get_user


async def notify_new_user(bot: Bot, telegram_id: int):
    """
    Assign reg_no and notify admins about new user.
    Only notifies if user gets a NEW reg_no.
    """
    # 1. Skip if admin (optional per requirements, but good practice)
    if telegram_id in ADMINS:
         # Check if we should assign reg_no anyway? 
         # User said: "Default: DO NOT spam admins about admins."
         # And admin bypasses reg flow usually. 
         # Safest is to just return if admin.
         return

    # 2. Assign reg_no
    reg_no, is_new = await assign_reg_no(telegram_id)
    
    # 3. If not new (already assigned), do not notify
    if not is_new:
        return

    # 4. Get latest user data
    user = await get_user(telegram_id)
    if not user:
        return

    # 5. Prepare message
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    name = user.get("name", "Noma'lum")
    phone = user.get("phone", "Noma'lum")
    role = user.get("role", "pending")
    
    text = (
        f"🆕 <b>Yangi foydalanuvchi ro‘yxatdan o‘tdi</b>\n"
        f"🔢 <b>Tartib raqami:</b> #{reg_no}\n"
        f"👤 <b>Ism:</b> {name}\n"
        f"📞 <b>Tel:</b> {phone}\n"
        f"🎭 <b>Rol:</b> {role}\n"
        f"🆔 <b>Telegram ID:</b> <code>{telegram_id}</code>\n"
        f"🕒 <b>Sana:</b> {now}"
    )

    # 6. Notify all admins
    for admin_id in ADMINS:
        try:
            await bot.send_message(chat_id=admin_id, text=text, parse_mode="HTML")
        except Exception:
            # Log error or ignore
            pass
