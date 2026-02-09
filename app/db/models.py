from app.db.session import get_db


async def init_db():
    """Initialize database with all required tables."""
    db = await get_db()
    try:
        # Users table with reg_no
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            role TEXT NOT NULL DEFAULT 'pending',
            name TEXT,
            phone TEXT,
            lat REAL,
            lon REAL,
            language TEXT NOT NULL DEFAULT 'uz',
            reg_no INTEGER UNIQUE,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """)
        
        # Safe migration for reg_no
        try:
            await db.execute("ALTER TABLE users ADD COLUMN reg_no INTEGER")
            await db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_reg_no ON users(reg_no)")
        except:
            pass


        # Regions table (viloyatlar)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS regions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name_uz TEXT NOT NULL,
            name_ru TEXT
        );
        """)

        # Districts table (tumanlar)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS districts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            region_id INTEGER NOT NULL,
            name_uz TEXT NOT NULL,
            name_ru TEXT,
            FOREIGN KEY (region_id) REFERENCES regions(id)
        );
        """)

        # Butchers table (qassobxonalar)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS butchers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            shop_name TEXT NOT NULL,
            owner_name TEXT,
            phone TEXT,
            region_id INTEGER,
            district_id INTEGER,
            lat REAL,
            lon REAL,
            address_text TEXT,
            work_time TEXT,
            image_file_id TEXT,
            extra_info TEXT,
            video_file_id TEXT,
            is_approved INTEGER NOT NULL DEFAULT 0,
            is_blocked INTEGER NOT NULL DEFAULT 0,
            is_closed INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (region_id) REFERENCES regions(id),
            FOREIGN KEY (district_id) REFERENCES districts(id)
        );
        """)

        # Prices table with UNIQUE constraint for UPSERT
        await db.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            butcher_id INTEGER NOT NULL,
            price_type TEXT NOT NULL CHECK(price_type IN ('SELL', 'BUY')),
            category TEXT NOT NULL,
            price INTEGER NOT NULL,
            updated_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (butcher_id) REFERENCES butchers(id)
        );
        """)

        # Create unique index for UPSERT on prices
        await db.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ux_prices
        ON prices(butcher_id, price_type, category);
        """)

        # Broadcasts table with media support
        await db.execute("""
        CREATE TABLE IF NOT EXISTS broadcasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_target TEXT NOT NULL,
            message TEXT,
            media_type TEXT,
            media_file_id TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """)
        

        # Safe migration: add columns if they don't exist (for existing databases)
        try:
            await db.execute("ALTER TABLE broadcasts ADD COLUMN media_type TEXT")
        except:
            pass  # Column already exists
        try:
            await db.execute("ALTER TABLE broadcasts ADD COLUMN media_file_id TEXT")
        except:
            pass  # Column already exists

        # V9 Migration: Add extra_info and video_file_id to butchers
        try:
            await db.execute("ALTER TABLE butchers ADD COLUMN extra_info TEXT")
        except:
            pass
        try:
            await db.execute("ALTER TABLE butchers ADD COLUMN video_file_id TEXT")
        except:
            pass


        # Bot settings (Donat info)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS bot_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            donate_card_number TEXT,
            donate_default_amount INTEGER DEFAULT 10000,
            donate_message_uz TEXT,
            support_profile TEXT,
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """)

        # Seed bot_settings
        cursor = await db.execute("SELECT COUNT(*) FROM bot_settings")
        if (await cursor.fetchone())[0] == 0:
            await db.execute("INSERT INTO bot_settings (donate_card_number) VALUES (NULL)")

        # V8 MANDATORY: Create all required indexes
        await db.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
        """)
        await db.execute("""
        CREATE INDEX IF NOT EXISTS idx_butchers_location ON butchers(lat, lon);
        """)
        await db.execute("""
        CREATE INDEX IF NOT EXISTS idx_butchers_region ON butchers(region_id);
        """)
        await db.execute("""
        CREATE INDEX IF NOT EXISTS idx_butchers_district ON butchers(district_id);
        """)
        await db.execute("""
        CREATE INDEX IF NOT EXISTS idx_prices_lookup ON prices(butcher_id, price_type, category);
        """)

        await db.commit()
    finally:
        await db.close()


async def seed_regions_districts():
    """Seed regions and districts if not already seeded."""
    db = await get_db()
    try:
        # Check if already seeded
        cursor = await db.execute("SELECT COUNT(*) FROM regions")
        count = (await cursor.fetchone())[0]
        if count > 0:
            return  # Already seeded

        # Uzbekistan regions and their districts
        regions_data = {
            "Toshkent shahri": ["Bektemir", "Chilonzor", "Yakkasaroy", "Mirobod", "Mirzo Ulug'bek", 
                                "Sergeli", "Shayxontohur", "Olmazor", "Uchtepa", "Yashnobod", "Yunusobod"],
            "Toshkent viloyati": ["Angren", "Bekobod", "Bo'ka", "Bo'stonliq", "Chinoz", "Qibray", 
                                  "Ohangaron", "Oqqo'rg'on", "Parkent", "Piskent", "Quyi Chirchiq",
                                  "O'rta Chirchiq", "Yuqori Chirchiq", "Yangiyo'l", "Zangiota"],
            "Andijon viloyati": ["Andijon", "Asaka", "Baliqchi", "Bo'z", "Buloqboshi", "Izboskan",
                                 "Jalaquduq", "Xo'jaobod", "Qo'rg'ontepa", "Marhamat", "Oltinko'l",
                                 "Paxtaobod", "Shahrixon", "Ulug'nor"],
            "Buxoro viloyati": ["Buxoro", "G'ijduvon", "Jondor", "Kogon", "Olot", "Peshku",
                                "Qorovulbozor", "Qorako'l", "Romitan", "Shofirkon", "Vobkent"],
            "Farg'ona viloyati": ["Farg'ona", "Bag'dod", "Beshariq", "Buvayda", "Dang'ara", "Furqat",
                                  "Qo'qon", "Quva", "Oltiariq", "O'zbekiston", "Rishton", "So'x",
                                  "Toshloq", "Uchko'prik", "Yozyovon"],
            "Jizzax viloyati": ["Jizzax", "Arnasoy", "Baxmal", "Do'stlik", "Forish", "G'allaorol",
                                "Mirzacho'l", "Paxtakor", "Yangiobod", "Zafarobod", "Zarband", "Zomin"],
            "Xorazm viloyati": ["Urganch", "Bog'ot", "Gurlan", "Xonqa", "Hazorasp", "Xiva",
                                "Qo'shko'pir", "Shovot", "Tuproqqal'a", "Yangiariq", "Yangibozor"],
            "Namangan viloyati": ["Namangan", "Chortoq", "Chust", "Kosonsoy", "Mingbuloq", "Norin",
                                  "Pop", "To'raqo'rg'on", "Uchqo'rg'on", "Uychi", "Yangiqo'rg'on"],
            "Navoiy viloyati": ["Navoiy", "Karmana", "Konimex", "Navbahor", "Nurota", "Qiziltepa",
                                "Tomdi", "Uchquduq", "Xatirchi"],
            "Qashqadaryo viloyati": ["Qarshi", "Chiroqchi", "Dehqonobod", "G'uzor", "Kasbi", "Kitob",
                                      "Koson", "Mirishkor", "Muborak", "Nishon", "Shahrisabz", "Yakkabog'"],
            "Qoraqalpog'iston Respublikasi": ["Nukus", "Amudaryo", "Beruniy", "Chimboy", "Ellikqal'a",
                                              "Kegeyli", "Mo'ynoq", "Nukus tumani", "Qonliko'l", 
                                              "Qo'ng'irot", "Shumanay", "Taxtako'pir", "To'rtko'l", "Xo'jayli"],
            "Samarqand viloyati": ["Samarqand", "Bulung'ur", "Ishtixon", "Jomboy", "Kattaqo'rg'on",
                                   "Narpay", "Nurobod", "Oqdaryo", "Past darg'om", "Payariq",
                                   "Paxtachi", "Qo'shrabot", "Tayloq", "Urgut"],
            "Sirdaryo viloyati": ["Guliston", "Boyovut", "Oqoltin", "Sardoba", "Sayxunobod", "Sirdaryo",
                                  "Xovos", "Mirzaobod"],
            "Surxondaryo viloyati": ["Termiz", "Angor", "Bandixon", "Boysun", "Denov", "Jarqo'rg'on",
                                     "Muzrabot", "Oltinsoy", "Qiziriq", "Qumqo'rg'on", "Sariosiyo",
                                     "Sherobod", "Sho'rchi", "Uzun"]
        }

        for region_name, districts in regions_data.items():
            cursor = await db.execute(
                "INSERT INTO regions (name_uz) VALUES (?)",
                (region_name,)
            )
            region_id = cursor.lastrowid
            
            for district_name in districts:
                await db.execute(
                    "INSERT INTO districts (region_id, name_uz) VALUES (?, ?)",
                    (region_id, district_name)
                )

        await db.commit()
        print(f"✅ Seeded {len(regions_data)} regions with districts")
    finally:
        await db.close()
