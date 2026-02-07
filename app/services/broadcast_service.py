"""Broadcast service with media support."""
import asyncio
from aiogram import Bot
from app.db.session import get_db
from app.services.user_service import get_all_users_by_role


async def log_broadcast(
    role_target: str, 
    message: str = None, 
    media_type: str = None, 
    media_file_id: str = None
):
    """Log broadcast to database with optional media info."""
    db = await get_db()
    try:
        await db.execute("""
        INSERT INTO broadcasts (role_target, message, media_type, media_file_id)
        VALUES (?, ?, ?, ?)
        """, (role_target, message, media_type, media_file_id))
        await db.commit()
    finally:
        await db.close()


async def send_broadcast(
    bot: Bot, 
    role_target: str, 
    message: str = None,
    media_type: str = None,
    media_file_id: str = None
) -> dict:
    """
    Send broadcast message to target users.
    Supports: text, photo, video (using Telegram file_id only).
    Returns stats: {"total": 100, "success": 95, "failed": 5}
    """
    # 1. Get users
    target = role_target
    if role_target == "all":
        target = None  # get all
    
    users = await get_all_users_by_role(target)
    
    # 2. Log to DB
    await log_broadcast(role_target, message, media_type, media_file_id)
    
    # 3. Send messages with throttling: 25 msg then 1 sec pause
    stats = {"total": len(users), "success": 0, "failed": 0}
    batch_count = 0
    
    for user in users:
        try:
            chat_id = user["telegram_id"]
            
            if media_type == "photo":
                await bot.send_photo(
                    chat_id=chat_id,
                    photo=media_file_id,
                    caption=message
                )
            elif media_type == "video":
                await bot.send_video(
                    chat_id=chat_id,
                    video=media_file_id,
                    caption=message
                )
            else:
                # Text only
                await bot.send_message(
                    chat_id=chat_id,
                    text=message
                )
            
            stats["success"] += 1
        except Exception:
            # User blocked/deactivated - minimal logging per requirements
            stats["failed"] += 1
        
        batch_count += 1
        
        # Throttling: 25 messages then 1 second pause
        if batch_count >= 25:
            await asyncio.sleep(1)
            batch_count = 0
        
    return stats
