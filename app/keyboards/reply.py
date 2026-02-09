"""Reply keyboards for the bot."""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from app.utils.i18n import t


def role_picker_kb() -> ReplyKeyboardMarkup:
    """Role selection keyboard."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👤 Mijoz"), KeyboardButton(text="🥩 Qassob")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def client_main_kb() -> ReplyKeyboardMarkup:
    """Main menu for clients."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Yaqin qassobxonalar")],
            [KeyboardButton(text="🥩 Go'sht narxlari"), KeyboardButton(text="👥 Foydalanuvchilar soni")],
            [KeyboardButton(text="ℹ️ Bot haqida"), KeyboardButton(text="⚙️ Sozlamalar")]
        ],
        resize_keyboard=True
    )


def butcher_main_kb(lang: str = "uz") -> ReplyKeyboardMarkup:
    """Main menu for butchers."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📌 Lokatsiyani yangilash")],
            [KeyboardButton(text="📞 Kontaktni yangilash"), KeyboardButton(text="🕒 Ish vaqti")],
            [KeyboardButton(text="📝 Qo‘shimcha ma’lumot yozish"), KeyboardButton(text="🎥 Mahsulotlar videosi")],
            [KeyboardButton(text="💰 Sotish narxlari"), KeyboardButton(text="🐄 Sotib olish narxlari")],
            [KeyboardButton(text="⚙️ Sozlamalar"), KeyboardButton(text="💳 Donat")],
            [KeyboardButton(text="👥 Foydalanuvchilar soni")]
        ],
        resize_keyboard=True
    )

def butcher_settings_kb() -> ReplyKeyboardMarkup:
    """Settings menu for butchers."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🖼 Do'kon rasmini yangilash")],
            [KeyboardButton(text="🌐 Tilni o'zgartirish")],
            [KeyboardButton(text="⬅️ Orqaga")]
        ],
        resize_keyboard=True
    )


def admin_main_kb() -> ReplyKeyboardMarkup:
    """Main menu for admins."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="🏪 Qassobxonalar")],
            [KeyboardButton(text="📢 Xabar yuborish")],
            [KeyboardButton(text="🛠 Qo'llab-quvvatlash"), KeyboardButton(text="💳 Donat sozlamalari")],
            [KeyboardButton(text="➕ Admin qo'shish"), KeyboardButton(text="🗑 Foydalanuvchini o'chirish")],
            [KeyboardButton(text="⚙️ Sozlamalar")]
        ],
        resize_keyboard=True
    )


def search_mode_kb() -> ReplyKeyboardMarkup:
    """Search mode selection."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="10 km"), KeyboardButton(text="20 km"), KeyboardButton(text="30 km")],
            [KeyboardButton(text="🗺 Qo'lda tanlash")],
            [KeyboardButton(text="⬅️ Orqaga")]
        ],
        resize_keyboard=True
    )


def request_contact_kb() -> ReplyKeyboardMarkup:
    """Request phone contact."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def request_location_kb() -> ReplyKeyboardMarkup:
    """Request location."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Lokatsiyani yuborish", request_location=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def back_kb() -> ReplyKeyboardMarkup:
    """Back button only."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="⬅️ Orqaga")]],
        resize_keyboard=True
    )


def skip_kb() -> ReplyKeyboardMarkup:
    """Skip button."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="⏭ O'tkazib yuborish")]],
        resize_keyboard=True
    )


def confirm_kb() -> ReplyKeyboardMarkup:
    """Confirm/Cancel buttons."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Tasdiqlash")],
            [KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True
    )


def settings_kb() -> ReplyKeyboardMarkup:
    """Settings menu."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🌐 Tilni o'zgartirish")],
            [KeyboardButton(text="👤 Ismni o'zgartirish")],
            [KeyboardButton(text="📱 Telefonni o'zgartirish")],
            [KeyboardButton(text="📩 Adminga murojaat")],
            [KeyboardButton(text="⬅️ Orqaga")]
        ],
        resize_keyboard=True
    )


def remove_kb() -> ReplyKeyboardRemove:
    """Remove keyboard."""
    return ReplyKeyboardRemove()
