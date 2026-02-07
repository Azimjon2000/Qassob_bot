"""User service for database operations."""
from app.db.session import get_db


async def upsert_user(telegram_id: int, name: str | None = None, phone: str | None = None,
                      lat: float | None = None, lon: float | None = None):
    """Insert or update user in database."""
    db = await get_db()
    try:
        await db.execute("""
        INSERT INTO users (telegram_id, name, phone, lat, lon)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(telegram_id) DO UPDATE SET
            name = COALESCE(excluded.name, users.name),
            phone = COALESCE(excluded.phone, users.phone),
            lat = COALESCE(excluded.lat, users.lat),
            lon = COALESCE(excluded.lon, users.lon)
        """, (telegram_id, name, phone, lat, lon))
        await db.commit()
    finally:
        await db.close()


async def get_user(telegram_id: int) -> dict | None:
    """Get user by telegram_id."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM users WHERE telegram_id = ?",
            (telegram_id,)
        )
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None
    finally:
        await db.close()


async def update_user(telegram_id: int, **kwargs):
    """Update user fields."""
    if not kwargs:
        return
    
    db = await get_db()
    try:
        set_clause = ", ".join(f"{k} = ?" for k in kwargs.keys())
        values = list(kwargs.values()) + [telegram_id]
        await db.execute(
            f"UPDATE users SET {set_clause} WHERE telegram_id = ?",
            values
        )
        await db.commit()
    finally:
        await db.close()


async def set_role(telegram_id: int, role: str):
    """Change user role."""
    await update_user(telegram_id, role=role)


async def get_user_by_id(user_id: int) -> dict | None:
    """Get user by internal id."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None
    finally:
        await db.close()


async def get_user_counts() -> dict:
    """Get user statistics."""
    db = await get_db()
    try:
        counts = {"total": 0, "client": 0, "butcher": 0, "admin": 0}
        
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        counts["total"] = (await cursor.fetchone())[0]
        
        cursor = await db.execute("SELECT role, COUNT(*) FROM users GROUP BY role")
        rows = await cursor.fetchall()
        for row in rows:
            counts[row[0]] = row[1]
        
        return counts
    finally:
        await db.close()


async def get_all_users_by_role(role: str | None = None) -> list:
    """Get all users, optionally filtered by role."""
    db = await get_db()
    try:
        if role and role != "all":
            cursor = await db.execute(
                "SELECT * FROM users WHERE role = ?",
                (role,)
            )
        else:
            cursor = await db.execute("SELECT * FROM users")
        
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def is_registered(telegram_id: int) -> bool:
    """Check if user has completed registration (has name and phone)."""
    user = await get_user(telegram_id)
    if not user:
        return False
    return bool(user.get("name") and user.get("phone"))


async def assign_reg_no(telegram_id: int) -> tuple[int, bool]:
    """
    Assign registration number to user if not exists.
    Returns (reg_no, is_newly_assigned).
    """
    db = await get_db()
    try:
        # Check if already has reg_no
        cursor = await db.execute("SELECT reg_no FROM users WHERE telegram_id = ?", (telegram_id,))
        row = await cursor.fetchone()
        if row and row[0]:
            return row[0], False

        # Assign new reg_no atomically
        # Get max reg_no
        cursor = await db.execute("SELECT COALESCE(MAX(reg_no), 0) FROM users")
        max_reg = (await cursor.fetchone())[0]
        new_reg = max_reg + 1
        
        await db.execute(
            "UPDATE users SET reg_no = ? WHERE telegram_id = ?",
            (new_reg, telegram_id)
        )
        await db.commit()
        return new_reg, True
    finally:
        await db.close()
