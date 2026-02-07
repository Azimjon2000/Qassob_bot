from typing import Optional, List, Dict
from app.db.session import get_db
from app.services.geo_service import haversine, bounding_box


async def create_butcher(user_id: int, data: dict) -> int:
    """Create a new butcher profile. Returns butcher id."""
    db = await get_db()
    try:
        cursor = await db.execute("""
        INSERT INTO butchers (
            user_id, shop_name, owner_name, phone,
            region_id, district_id, lat, lon,
            address_text, work_time, image_file_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            data.get("shop_name"),
            data.get("owner_name"),
            data.get("phone"),
            data.get("region_id"),
            data.get("district_id"),
            data.get("lat"),
            data.get("lon"),
            data.get("address_text"),
            data.get("work_time"),
            data.get("image_file_id")
        ))
        await db.commit()
        return cursor.lastrowid
    finally:
        await db.close()


async def update_butcher(butcher_id: int, **kwargs):
    """Update butcher fields."""
    if not kwargs:
        return
    
    db = await get_db()
    try:
        set_clause = ", ".join(f"{k} = ?" for k in kwargs.keys())
        values = list(kwargs.values()) + [butcher_id]
        await db.execute(
            f"UPDATE butchers SET {set_clause} WHERE id = ?",
            values
        )
        await db.commit()
    finally:
        await db.close()


async def get_butcher_by_user(user_id: int) -> Optional[dict]:
    """Get butcher by user_id."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM butchers WHERE user_id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None
    finally:
        await db.close()


async def get_butcher_detail(butcher_id: int) -> Optional[dict]:
    """Get full butcher info."""
    db = await get_db()
    try:
        cursor = await db.execute("""
        SELECT b.*, r.name_uz as region_name, d.name_uz as district_name
        FROM butchers b
        LEFT JOIN regions r ON b.region_id = r.id
        LEFT JOIN districts d ON b.district_id = d.id
        WHERE b.id = ?
        """, (butcher_id,))
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None
    finally:
        await db.close()


async def find_by_district(district_id: int) -> list:
    """Find approved butchers in a district."""
    db = await get_db()
    try:
        cursor = await db.execute("""
        SELECT * FROM butchers
        WHERE district_id = ? AND is_approved = 1 AND is_blocked = 0
        ORDER BY shop_name
        """, (district_id,))
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def find_all_approved() -> list:
    """Get all approved and not blocked butchers."""
    db = await get_db()
    try:
        cursor = await db.execute("""
        SELECT * FROM butchers
        WHERE is_approved = 1 AND is_blocked = 0
        """)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def find_nearby_by_radius(lat: float, lon: float, radius_km: int) -> list:
    """
    Find butchers within radius using V8 optimized approach:
    1. SQL bounding-box filter first (uses idx_butchers_location index)
    2. Haversine only on filtered results (CPU efficient)
    """
    # Get bounding box for SQL pre-filter
    min_lat, max_lat, min_lon, max_lon = bounding_box(lat, lon, radius_km)
    
    db = await get_db()
    try:
        # V8: SQL bounding-box filter first
        cursor = await db.execute("""
        SELECT * FROM butchers
        WHERE is_approved = 1 AND is_blocked = 0
          AND lat BETWEEN ? AND ?
          AND lon BETWEEN ? AND ?
        """, (min_lat, max_lat, min_lon, max_lon))
        rows = await cursor.fetchall()
        butchers = [dict(row) for row in rows]
    finally:
        await db.close()
    
    # Now apply precise haversine on filtered results only
    result = []
    for b in butchers:
        if b.get('lat') and b.get('lon'):
            dist = haversine(lat, lon, b['lat'], b['lon'])
            if dist <= radius_km:
                b['distance_km'] = round(dist, 1)
                b['distance'] = dist  # For compatibility
                result.append(b)
    
    # Sort by distance
    result.sort(key=lambda x: x['distance_km'])
    return result


async def get_pending_butchers() -> list:
    """Get butchers pending approval."""
    db = await get_db()
    try:
        cursor = await db.execute("""
        SELECT b.*, r.name_uz as region_name, d.name_uz as district_name
        FROM butchers b
        LEFT JOIN regions r ON b.region_id = r.id
        LEFT JOIN districts d ON b.district_id = d.id
        WHERE b.is_approved = 0 AND b.is_blocked = 0
        ORDER BY b.created_at DESC
        """)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def approve_butcher(butcher_id: int):
    """Approve butcher."""
    await update_butcher(butcher_id, is_approved=1)


async def block_butcher(butcher_id: int):
    """Block butcher."""
    await update_butcher(butcher_id, is_blocked=1)


async def unblock_butcher(butcher_id: int):
    """Unblock butcher."""
    await update_butcher(butcher_id, is_blocked=0)


async def toggle_closed(butcher_id: int) -> bool:
    """Toggle is_closed status. Returns new status."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT is_closed FROM butchers WHERE id = ?", (butcher_id,)
        )
        row = await cursor.fetchone()
        if row:
            new_status = 0 if row[0] else 1
            await db.execute(
                "UPDATE butchers SET is_closed = ? WHERE id = ?",
                (new_status, butcher_id)
            )
            await db.commit()
            return bool(new_status)
        return False
    finally:
        await db.close()


async def delete_butcher(butcher_id: int):
    """Delete butcher."""
    db = await get_db()
    try:
        await db.execute("DELETE FROM prices WHERE butcher_id = ?", (butcher_id,))
        await db.execute("DELETE FROM butchers WHERE id = ?", (butcher_id,))
        await db.commit()
    finally:
        await db.close()


async def get_butcher_counts() -> dict:
    """Get butcher statistics."""
    db = await get_db()
    try:
        counts = {"total": 0, "approved": 0, "pending": 0, "blocked": 0}
        
        cursor = await db.execute("SELECT COUNT(*) FROM butchers")
        counts["total"] = (await cursor.fetchone())[0]
        
        cursor = await db.execute("SELECT COUNT(*) FROM butchers WHERE is_approved = 1 AND is_blocked = 0")
        counts["approved"] = (await cursor.fetchone())[0]
        
        cursor = await db.execute("SELECT COUNT(*) FROM butchers WHERE is_approved = 0 AND is_blocked = 0")
        counts["pending"] = (await cursor.fetchone())[0]
        
        cursor = await db.execute("SELECT COUNT(*) FROM butchers WHERE is_blocked = 1")
        counts["blocked"] = (await cursor.fetchone())[0]
        
        return counts
    finally:
        await db.close()


async def get_all_butchers_paginated(page: int = 0, page_size: int = 8) -> dict:
    """Get all butchers with pagination."""
    db = await get_db()
    try:
        offset = page * page_size
        
        # Get total count
        cursor = await db.execute("SELECT COUNT(*) FROM butchers")
        total_count = (await cursor.fetchone())[0]
        
        # Get items
        cursor = await db.execute("""
            SELECT b.*, r.name_uz as region_name, d.name_uz as district_name
            FROM butchers b
            LEFT JOIN regions r ON b.region_id = r.id
            LEFT JOIN districts d ON b.district_id = d.id
            ORDER BY b.created_at DESC
            LIMIT ? OFFSET ?
        """, (page_size, offset))
        
        rows = await cursor.fetchall()
        items = [dict(row) for row in rows]
        
        return {
            "items": items,
            "total": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_count + page_size - 1) // page_size
        }
    finally:
        await db.close()
