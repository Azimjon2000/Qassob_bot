"""Region and district service."""
from app.db.session import get_db


async def list_regions() -> list:
    """Get all regions."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM regions ORDER BY name_uz")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def list_districts(region_id: int) -> list:
    """Get districts for a region."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM districts WHERE region_id = ? ORDER BY name_uz",
            (region_id,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def get_region(region_id: int) -> dict | None:
    """Get region by id."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM regions WHERE id = ?",
            (region_id,)
        )
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None
    finally:
        await db.close()


async def get_district(district_id: int) -> dict | None:
    """Get district by id."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM districts WHERE id = ?",
            (district_id,)
        )
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None
    finally:
        await db.close()
