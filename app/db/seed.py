import json
import logging
from pathlib import Path

from app.db.base import get_db

logger = logging.getLogger("barbershop")

REGIONS_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "regions.json"


async def seed_regions():
    """Seed regions and districts from JSON if tables are empty."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT COUNT(*) as cnt FROM regions")
        row = await cursor.fetchone()
        if row and row["cnt"] > 0:
            logger.info("Regions already seeded, skipping.")
            return

        with open(REGIONS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        for region in data["regions"]:
            cursor = await db.execute(
                "INSERT INTO regions (name_uz, name_ru) VALUES (?, ?)",
                (region["name_uz"], region["name_ru"]),
            )
            region_id = cursor.lastrowid
            for district in region["districts"]:
                await db.execute(
                    "INSERT INTO districts (region_id, name_uz, name_ru) VALUES (?, ?, ?)",
                    (region_id, district["name_uz"], district["name_ru"]),
                )
        await db.commit()
        logger.info("Regions and districts seeded successfully.")
    finally:
        await db.close()
