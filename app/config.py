import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Bot token
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN topilmadi. .env faylga BOT_TOKEN kiriting.")

# Admin telegram IDs
ADMINS = [int(x.strip()) for x in os.getenv("ADMINS", "").split(",") if x.strip()]

# Database path
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "bot.db"

# Pagination
PAGE_SIZE = 8

# Radius options in km
RADIUS_OPTIONS = [10, 20, 30]

# Throttle settings
THROTTLE_BATCH = 25
THROTTLE_SLEEP = 1

# Meat categories
MEAT_SELL_CATEGORIES = ["Mol", "Qo'y", "Tovuq", "Qiyma", "Jigar"]
MEAT_BUY_CATEGORIES = ["Mol", "Qo'y"]

DEFAULT_LANGUAGE = "uz"

