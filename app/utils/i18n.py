"""Internationalization support for the bot."""

TRANSLATIONS = {
    "uz": {
        # General
        "welcome": "👋 Assalomu alaykum, {name}!",
        "select_role": "Botdan foydalanish uchun quyidagi tugmalar orqali o'z statusingizni tanlang:",
        "main_menu": "🏠 Asosiy menyu",
        "back": "⬅️ Orqaga",
        "confirm": "✅ Tasdiqlash",
        "cancel": "❌ Bekor qilish",
        "skip": "⏭ O'tkazib yuborish",
        "saved": "✅ Ma'lumot saqlandi!",
        "error": "❌ Xatolik yuz berdi. Qayta urinib ko'ring.",
        
        # Role picker
        "role_client": "👤 Mijoz",
        "role_butcher": "🥩 Qassob",
        "role_selected_client": "✅ Siz <b>Mijoz</b> rolini tanladingiz.",
        "role_selected_butcher": "✅ Siz <b>Qassob</b> rolini tanladingiz.",
        "select_role_button": "❌ Iltimos, quyidagi tugmalardan birini tanlang:",
        
        # Registration
        "enter_name": "Iltimos, ismingizni kiriting:",
        "name_too_short": "❌ Ism juda qisqa. Iltimos, to'liq ismingizni kiriting:",
        "name_saved": "✅ Rahmat, {name}!",
        "enter_phone": "Endi telefon raqamingizni yuboring:",
        "send_phone_button": "❌ Iltimos, telefon raqamni pastdagi tugma orqali yuboring:",
        "phone_saved": "✅ Telefon raqam saqlandi!",
        "enter_location": "Endi lokatsiyangizni yuboring:",
        "send_location_button": "❌ Iltimos, lokatsiyani pastdagi tugma orqali yuboring:",
        "registration_complete": "✅ Ro'yxatdan o'tish yakunlandi!\n\n🥩 Endi yaqin atrofdagi qassobxonalarni topishingiz mumkin.",
        
        # Client menu
        "nearby_butchers": "📍 Yaqin qassobxonalar",
        "meat_prices": "🥩 Go'sht narxlari",
        "about_bot": "ℹ️ Bot haqida",
        "settings": "⚙️ Sozlamalar",
        "contact_admin": "📩 Adminga murojaat",
        
        # Search
        "send_location_for_search": "📍 Yaqin atrofdagi qassobxonalarni topish uchun lokatsiyangizni yuboring:",
        "select_search_mode": "Qidiruv usulini tanlang:",
        "manual_select": "🗺 Qo'lda tanlash",
        "select_region": "Viloyatni tanlang:",
        "select_district": "Tumanni tanlang:",
        "no_butchers_found": "❌ Bu hududda qassobxona topilmadi.",
        "butchers_found": "🥩 Topilgan qassobxonalar ({count}):",
        "view_location": "📍 Lokatsiyani ko'rish",
        "buy_prices": "🐄 So'yib olish narxlari",
        
        # Butcher menu
        "update_location": "📌 Lokatsiyani yangilash",
        "update_phone": "📞 Kontaktni yangilash",
        "sell_prices": "💰 Sotish narxlari",
        "buy_prices_menu": "🐄 So'yib olish narxlari",
        "work_time": "🕒 Ish vaqti",
        "donate": "💳 Donat",
        "update_image": "🖼 Do'kon rasmini yangilash",
        
        # Butcher registration
        "enter_shop_name": "Do'kon nomini kiriting:",
        "enter_owner_name": "Egasining ismini kiriting:",
        "enter_work_time": "Ish vaqtini kiriting (masalan: 08:00 - 20:00):",
        "send_shop_image": "Do'kon rasmini yuboring:",
        "awaiting_approval": "✅ Ma'lumotlar saqlandi!\n\nAdmin tasdig'iga yuborildi. Tez orada sizga xabar beriladi.",
        
        # Settings
        "edit_name": "✏️ Ismni tahrirlash",
        "edit_phone": "📞 Telefonni yangilash",
        "change_language": "🌐 Tilni o'zgartirish",
        "name_updated": "✅ Ism yangilandi!",
        "phone_updated": "✅ Telefon yangilandi!",
        "language_updated": "✅ Til o'zgartirildi!",
        "image_updated": "✅ Do'kon rasmi yangilandi!",
        "select_language": "Tilni tanlang:",
        
        # Prices
        "select_category": "Kategoriyani tanlang:",
        "enter_price": "Narxni kiriting (so'm/kg):",
        "price_updated": "✅ Yangilandi: {category} — {price} so'm/kg",
        "buy_price_context": "So'yib olish narximiz (aholining mol/qo'yini so'yib sotib olish narxi):",
        "cheapest_prices": "Eng arzon narxlar ({district}):",
        "no_prices": "Bu hududda narxlar topilmadi.",
        
        # Admin
        "admin_welcome": "👑 Xush kelibsiz, Admin {name}!",
        "statistics": "📊 Statistika",
        "butcher_list": "🏪 Qassobxonalar",
        "send_broadcast": "📢 Xabar yuborish",
        "support_settings": "🛠 Qo'llab-quvvatlash",
        "donate_settings": "💳 Donat sozlamalari",
        "add_admin": "➕ Admin qo'shish",
        "butcher_approved": "✅ Qassobxona tasdiqlandi!",
        "butcher_blocked": "🚫 Qassobxona bloklandi!",
        "butcher_unblocked": "✅ Qassobxona blokdan chiqarildi!",
        "enter_broadcast_message": "Xabar matnini kiriting:",
        "broadcast_sent": "✅ Xabar {count} ta foydalanuvchiga yuborildi!",
        "enter_support_profile": "Yangi support profilni kiriting (t.me/username yoki @username):",
        "support_updated": "✅ Qo'llab-quvvatlash profili yangilandi!",
        "enter_donate_card": "Yangi donat kartasini kiriting:",
        "donate_card_updated": "✅ Donat kartasi yangilandi!",
        "enter_admin_id": "Yangi admin Telegram ID sini kiriting:",
        "admin_added": "✅ Admin qo'shildi!",
        
        # Donate
        "donate_text": "🙏 Botni qo'llab-quvvatlash uchun oyiga atigi 10,000 so'm yordam bering.\n\nSumma ixtiyoriy.\n\n💳 Karta: {card}",
        
        # About
        "about_text": "🥩 <b>Qassobxona topish boti</b>\n\nBu bot orqali siz:\n• Yaqin atrofdagi qassobxonalarni topishingiz\n• Go'sht narxlarini solishtirishingiz\n• Eng arzon narxlarni ko'rishingiz mumkin\n\n📞 Murojaat uchun: {contact}",
        
        # Missing keys
        "results": "Natijalar:",
        "owner": "👤 Egasi",
        "phone": "📞 Tel",
        "address": "📍 Manzil",
        "sum": "so'm",
        "butcher_not_found": "❌ Qassobxona topilmadi",
        "not_specified": "Ko'rsatilmagan",
        "location_not_found": "❌ Lokatsiya topilmadi",
        "no_prices_specified": "Narxlar kiritilmagan",
    },
    
    "ru": {
        # General
        "welcome": "👋 Добро пожаловать, {name}!",
        "select_role": "Выберите вашу роль для использования бота:",
        "main_menu": "🏠 Главное меню",
        "back": "⬅️ Назад",
        "confirm": "✅ Подтвердить",
        "cancel": "❌ Отменить",
        "skip": "⏭ Пропустить",
        "saved": "✅ Данные сохранены!",
        "error": "❌ Произошла ошибка. Попробуйте снова.",
        
        # Role picker
        "role_client": "👤 Клиент",
        "role_butcher": "🥩 Мясник",
        "role_selected_client": "✅ Вы выбрали роль <b>Клиент</b>.",
        "role_selected_butcher": "✅ Вы выбрали роль <b>Мясник</b>.",
        "select_role_button": "❌ Пожалуйста, выберите одну из кнопок:",
        
        # Registration
        "enter_name": "Пожалуйста, введите ваше имя:",
        "name_too_short": "❌ Имя слишком короткое. Введите полное имя:",
        "name_saved": "✅ Спасибо, {name}!",
        "enter_phone": "Теперь отправьте ваш номер телефона:",
        "send_phone_button": "❌ Пожалуйста, отправьте номер через кнопку ниже:",
        "phone_saved": "✅ Номер телефона сохранен!",
        "enter_location": "Теперь отправьте вашу локацию:",
        "send_location_button": "❌ Пожалуйста, отправьте локацию через кнопку ниже:",
        "registration_complete": "✅ Регистрация завершена!\n\n🥩 Теперь вы можете найти ближайшие мясные лавки.",
        
        # Client menu
        "nearby_butchers": "📍 Ближайшие мясные",
        "meat_prices": "🥩 Цены на мясо",
        "about_bot": "ℹ️ О боте",
        "settings": "⚙️ Настройки",
        "contact_admin": "📩 Связь с админом",
        
        # Search
        "send_location_for_search": "📍 Отправьте локацию, чтобы найти ближайшие мясные лавки:",
        "select_search_mode": "Выберите способ поиска:",
        "manual_select": "🗺 Выбрать вручную",
        "select_region": "Выберите область:",
        "select_district": "Выберите район:",
        "no_butchers_found": "❌ В этом районе мясных лавок не найдено.",
        "butchers_found": "🥩 Найденные мясные лавки ({count}):",
        "view_location": "📍 Показать локацию",
        "buy_prices": "🐄 Цены на забой",
        
        # Butcher menu
        "update_location": "📌 Обновить локацию",
        "update_phone": "📞 Обновить контакт",
        "sell_prices": "💰 Цены продажи",
        "buy_prices_menu": "🐄 Цены закупки",
        "work_time": "🕒 Время работы",
        "donate": "💳 Донат",
        "update_image": "🖼 Обновить фото",
        
        # Butcher registration
        "enter_shop_name": "Введите название магазина:",
        "enter_owner_name": "Введите имя владельца:",
        "enter_work_time": "Введите время работы (напр: 08:00 - 20:00):",
        "send_shop_image": "Отправьте фото магазина:",
        "awaiting_approval": "✅ Данные сохранены!\n\nОтправлено на проверку админу. Мы скоро уведомим вас.",
        
        # Settings
        "edit_name": "✏️ Изменить имя",
        "edit_phone": "📞 Обновить телефон",
        "change_language": "🌐 Сменить язык",
        "name_updated": "✅ Имя обновлено!",
        "phone_updated": "✅ Телефон обновлен!",
        "language_updated": "✅ Язык изменен!",
        "image_updated": "✅ Фото магазина обновлено!",
        "select_language": "Выберите язык:",
        
        # Prices
        "select_category": "Выберите категорию:",
        "enter_price": "Введите цену (сум/кг):",
        "price_updated": "✅ Обновлено: {category} — {price} сум/кг",
        "buy_price_context": "Наша цена закупки (цена за забой скота населения):",
        "cheapest_prices": "Самые низкие цены ({district}):",
        "no_prices": "В этом районе цены не найдены.",
        
        # Admin
        "admin_welcome": "👑 Добро пожаловать, Админ {name}!",
        "statistics": "📊 Статистика",
        "butcher_list": "🏪 Мясные лавки",
        "send_broadcast": "📢 Рассылка",
        "support_settings": "🛠 Поддержка",
        "donate_settings": "💳 Настройки доната",
        "add_admin": "➕ Добавить админа",
        "butcher_approved": "✅ Мясная лавка одобрена!",
        "butcher_blocked": "🚫 Мясная лавка заблокирована!",
        "butcher_unblocked": "✅ Мясная лавка разблокирована!",
        "enter_broadcast_message": "Введите текст сообщения:",
        "broadcast_sent": "✅ Сообщение отправлено {count} пользователям!",
        "enter_support_profile": "Введите новый профиль поддержки (t.me/username или @username):",
        "support_updated": "✅ Профиль поддержки обновлен!",
        "enter_donate_card": "Введите новую карту для доната:",
        "donate_card_updated": "✅ Карта доната обновлена!",
        "enter_admin_id": "Введите Telegram ID нового админа:",
        "admin_added": "✅ Админ добавлен!",
        
        # Donate
        "donate_text": "🙏 Поддержите бот всего за 10,000 сум в месяц.\n\nСумма не ограничена.\n\n💳 Карта: {card}",
        
        # About
        "about_text": "🥩 <b>Бот поиска мясных лавок</b>\n\nС этим ботом вы можете:\n• Найти ближайшие мясные лавки\n• Сравнить цены на мясо\n• Увидеть самые низкие цены\n\n📞 Контакт: {contact}",
        
        # Missing keys
        "results": "Результаты:",
        "owner": "👤 Владелец",
        "phone": "📞 Тел",
        "address": "📍 Адрес",
        "sum": "сум",
        "butcher_not_found": "❌ Мясная лавка не найдена",
        "not_specified": "Не указано",
        "location_not_found": "❌ Локация не найдена",
        "no_prices_specified": "Цены не указаны",
    }
}


def t(lang: str, key: str, **kwargs) -> str:
    """Get translated string for the given language and key.
    
    Args:
        lang: Language code ('uz' or 'ru')
        key: Translation key
        **kwargs: Format arguments for the string
        
    Returns:
        Translated string, or key if not found
    """
    if lang not in TRANSLATIONS:
        lang = "uz"
    
    translations = TRANSLATIONS.get(lang, TRANSLATIONS["uz"])
    text = translations.get(key, TRANSLATIONS["uz"].get(key, key))
    
    if kwargs:
        try:
            return text.format(**kwargs)
        except KeyError:
            return text
    
    return text
