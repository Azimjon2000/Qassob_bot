import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import BOT_TOKEN
from app.db.models import init_db, seed_regions_districts
from app.handlers import common, client, butcher, admin


async def main():
    # Initialize database
    await init_db()
    await seed_regions_districts()

    # Create bot and dispatcher with FSM storage
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Include routers
    dp.include_router(common.router)
    dp.include_router(client.router)
    dp.include_router(butcher.router)
    dp.include_router(admin.router)

    print("🥩 Qassobxona Bot ishga tushdi!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
