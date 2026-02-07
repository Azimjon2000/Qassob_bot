"""Donate service for handling donation settings."""
from app.db.session import get_db


async def get_donate_settings() -> dict:
    """Get donation settings."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM bot_settings LIMIT 1")
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return {"donate_card_number": None, "donate_default_amount": 10000}
    finally:
        await db.close()


async def set_donate_card_number(card_number: str):
    """Set donation card number."""
    db = await get_db()
    try:
        await db.execute(
            "UPDATE bot_settings SET donate_card_number = ?, updated_at = datetime('now')",
            (card_number,)
        )
        await db.commit()
    finally:
        await db.close()


async def get_donate_message(language: str = "uz") -> str:
    """Get donation message text."""
    settings = await get_donate_settings()
    card = settings.get("donate_card_number")
    
    if not card:
        return "⚠️ Donat uchun karta raqami hali sozlanmagan. Keyinroq urinib ko'ring."
        
    card_fmt = f"{card[:4]} {card[4:8]} {card[8:12]} {card[12:]}" if len(card) == 16 else card
    
    amount = settings.get("donate_default_amount", 10000)
    amount_fmt = f"{amount:,}".replace(",", " ")
    
    return (
        "🇺🇿 <b>Bot rivoji uchun hissa qo'shing!</b>\n\n"
        f"Faoliyatimiz to'xtovsiz ishlashi uchun quyidagi karta raqamiga oyiga atigi {amount_fmt} so'm o'tkazishingizni iltimos qilamiz.\n"
        "O'tkazish summasi ixtiyoriy.\n\n"
        f"💳 Karta: <code>{card_fmt}</code>"
    )


async def set_donate_default_amount(amount: int):
    """Set donation default amount."""
    db = await get_db()
    try:
        await db.execute(
            "UPDATE bot_settings SET donate_default_amount = ?, updated_at = datetime('now')",
            (amount,)
        )
        await db.commit()
    finally:
        await db.close()


async def get_support_profile() -> str:
    """Get support profile text."""
    settings = await get_donate_settings()
    return settings.get("support_profile") or "@admin"


async def set_support_profile(text: str):
    """Set support profile text."""
    db = await get_db()
    try:
        await db.execute(
            "UPDATE bot_settings SET support_profile = ?, updated_at = datetime('now')",
            (text,)
        )
        await db.commit()
    finally:
        await db.close()
