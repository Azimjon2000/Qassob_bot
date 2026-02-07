import aiosqlite
from app.config import DB_PATH


async def get_db() -> aiosqlite.Connection:
    """Get database connection with performance optimizations."""
    # Ensure data directory exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    db = await aiosqlite.connect(str(DB_PATH))
    db.row_factory = aiosqlite.Row
    
    # V8 MANDATORY: PRAGMA optimizations for Google Cloud e2-micro
    await db.execute("PRAGMA journal_mode=WAL;")
    await db.execute("PRAGMA synchronous=NORMAL;")
    await db.execute("PRAGMA temp_store=MEMORY;")
    await db.execute("PRAGMA cache_size=10000;")
    
    return db
