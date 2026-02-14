import asyncio
import aiosqlite
from pathlib import Path

from app.config import DB_PATH

_write_lock = asyncio.Lock()


def _db_dir_ensure():
    """Ensure the directory for the DB file exists."""
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)


async def get_db() -> aiosqlite.Connection:
    """Open a new aiosqlite connection with mandatory PRAGMAs for 1GB RAM server."""
    _db_dir_ensure()
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    
    # Mandatory PRAGMAs for Oracle E2 Micro (1GB RAM) stability
    pragmas = [
        "PRAGMA journal_mode=WAL",
        "PRAGMA synchronous=NORMAL",
        "PRAGMA busy_timeout=10000",
        "PRAGMA foreign_keys=ON",
        "PRAGMA temp_store=MEMORY",
        "PRAGMA wal_autocheckpoint=1000",
        "PRAGMA journal_size_limit=67108864",  # ~64MB
        "PRAGMA cache_size=-2000",             # ~2MB RAM
    ]
    for pragma in pragmas:
        await db.execute(pragma)
        
    return db


async def execute_write(query: str, params: tuple = ()):
    """Execute a single write query under the write lock."""
    async with _write_lock:
        db = await get_db()
        try:
            await db.execute(query, params)
            await db.commit()
        finally:
            await db.close()


async def execute_write_returning(query: str, params: tuple = ()):
    """Execute a write query and return lastrowid."""
    async with _write_lock:
        db = await get_db()
        try:
            cursor = await db.execute(query, params)
            await db.commit()
            return cursor.lastrowid
        finally:
            await db.close()


async def fetch_one(query: str, params: tuple = ()):
    """Fetch a single row."""
    db = await get_db()
    try:
        cursor = await db.execute(query, params)
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def fetch_all(query: str, params: tuple = ()):
    """Fetch all rows."""
    db = await get_db()
    try:
        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        await db.close()


async def init_db():
    """Create all tables."""
    from app.db.models import SCHEMA_SQL
    _db_dir_ensure()
    db = await get_db()
    try:
        await db.executescript(SCHEMA_SQL)
        await db.commit()
    finally:
        await db.close()
