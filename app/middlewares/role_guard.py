from typing import Any, Callable, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

from app.db.base import fetch_one


class AdminGuard(BaseMiddleware):
    """Only allow admin users."""

    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: dict[str, Any],
    ) -> Any:
        user_id = event.from_user.id
        row = await fetch_one(
            "SELECT telegram_id FROM admins WHERE telegram_id = ?", (user_id,)
        )
        if not row:
            texts = data.get("texts", {})
            msg = texts.get("access_denied", "⛔ Ruxsat yo'q")
            if isinstance(event, CallbackQuery):
                await event.answer(msg, show_alert=True)
            else:
                await event.answer(msg)
            return
        return await handler(event, data)


class BarberGuard(BaseMiddleware):
    """Only allow approved barbers."""

    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: dict[str, Any],
    ) -> Any:
        user_id = event.from_user.id
        row = await fetch_one(
            "SELECT status FROM barbers WHERE telegram_id = ?", (user_id,)
        )
        if not row or row["status"] != "APPROVED":
            texts = data.get("texts", {})
            msg = texts.get("access_denied", "⛔ Ruxsat yo'q")
            if isinstance(event, CallbackQuery):
                await event.answer(msg, show_alert=True)
            else:
                await event.answer(msg)
            return
        return await handler(event, data)


class ClientGuard(BaseMiddleware):
    """Only allow registered clients."""

    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: dict[str, Any],
    ) -> Any:
        user_id = event.from_user.id
        row = await fetch_one(
            "SELECT telegram_id FROM clients WHERE telegram_id = ?", (user_id,)
        )
        if not row:
            texts = data.get("texts", {})
            msg = texts.get("access_denied", "⛔ Ruxsat yo'q")
            if isinstance(event, CallbackQuery):
                await event.answer(msg, show_alert=True)
            else:
                await event.answer(msg)
            return
        return await handler(event, data)
