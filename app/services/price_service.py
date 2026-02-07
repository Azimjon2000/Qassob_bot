"""Price management service."""
from app.db.session import get_db
from app.config import MEAT_SELL_CATEGORIES


async def upsert_price(butcher_id: int, price_type: str, category: str, price: int):
    """
    Insert or update meat price.
    Uses INSERT OR REPLACE (via ON CONFLICT in SQLite/UPSERT).
    """
    db = await get_db()
    try:
        await db.execute("""
        INSERT INTO prices (butcher_id, price_type, category, price, updated_at)
        VALUES (?, ?, ?, ?, datetime('now'))
        ON CONFLICT(butcher_id, price_type, category) DO UPDATE SET
            price = excluded.price,
            updated_at = excluded.updated_at
        """, (butcher_id, price_type, category, price))
        await db.commit()
    finally:
        await db.close()


async def get_prices(butcher_id: int, price_type: str) -> dict:
    """
    Get prices for a butcher by type (SELL/BUY).
    Returns dict mapping category -> price.
    """
    db = await get_db()
    try:
        cursor = await db.execute("""
        SELECT category, price FROM prices
        WHERE butcher_id = ? AND price_type = ?
        """, (butcher_id, price_type))
        rows = await cursor.fetchall()
        return {row["category"]: row["price"] for row in rows}
    finally:
        await db.close()


async def get_cheapest_prices_by_district(district_id: int, price_type: str = "SELL") -> dict:
    """
    Get cheapest prices for each category in a district.
    Returns: {
        "Mol": {"price": 65000, "shop_name": "Ali Qassob", "butcher_id": 1, ...},
        ...
    }
    """
    db = await get_db()
    try:
        result = {}
        for category in MEAT_SELL_CATEGORIES:
            cursor = await db.execute("""
            SELECT p.price, p.updated_at, b.shop_name, b.id as butcher_id, b.phone
            FROM prices p
            JOIN butchers b ON p.butcher_id = b.id
            WHERE b.district_id = ? 
              AND p.price_type = ? 
              AND p.category = ?
              AND b.is_approved = 1 AND b.is_blocked = 0
            ORDER BY p.price ASC
            LIMIT 1
            """, (district_id, price_type, category))
            
            row = await cursor.fetchone()
            if row:
                result[category] = dict(row)
        
        return result
    finally:
        await db.close()
