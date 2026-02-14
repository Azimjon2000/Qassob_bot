"""Rating flow handlers: receive stars, optional comment."""
import logging

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from app.states.client_menu import ClientMenuFSM
from app.services import rating_service, booking_service, barber_service
from app.keyboards.inline import rating_comment_keyboard, client_menu_keyboard
from app.utils.flow_message import ensure_flow_message, send_ok_popup

logger = logging.getLogger("barbershop")

router = Router(name="rating")


@router.callback_query(F.data.startswith("crate:start:"))
async def on_rate_start(callback: CallbackQuery, state: FSMContext, texts: dict, **kwargs):
    booking_id = int(callback.data.split(":")[2])
    booking = await booking_service.get_booking(booking_id)
    if not booking:
        await callback.answer(texts["error_generic"], show_alert=True)
        return

    barber = await barber_service.get_barber(booking["barber_id"])
    barber_name = barber["name"] if barber else "?"

    from app.keyboards.inline import rating_stars_keyboard
    await ensure_flow_message(
        callback,
        texts["rate_barber_prompt"].format(barber_name=barber_name),
        state,
        keyboard=rating_stars_keyboard(booking_id)
    )


@router.callback_query(F.data.startswith("crate:"))
async def on_rate_stars(callback: CallbackQuery, state: FSMContext, texts: dict, **kwargs):
    parts = callback.data.split(":")
    stars = int(parts[1])
    booking_id = int(parts[2])

    booking = await booking_service.get_booking(booking_id)
    if not booking:
        await callback.answer(texts["error_generic"], show_alert=True)
        return

    # Phase 8 FIX: Check if already rated to prevent IntegrityError
    from app.services.rating_service import get_rating_by_booking
    existing = await get_rating_by_booking(booking_id)
    if existing:
        await callback.answer(texts["already_rated"], show_alert=True)
        return

    # Save rating
    await rating_service.create_rating(
         booking_id=booking_id,
         barber_id=booking["barber_id"],
         client_id=callback.from_user.id,
         stars=stars,
    )

    # Ask for comment
    await state.set_state(ClientMenuFSM.rate_comment)
    await state.update_data(rating_booking_id=booking_id)
    
    # We can't edit the rating message easily if it was a simple message with inline keyboard.
    # But usually rating prompt is a new message.
    # Let's edit it to show comment prompt.
    await ensure_flow_message(
        callback,
        texts["rate_comment_prompt"],
        state,
        keyboard=rating_comment_keyboard(booking_id, texts)
    )


@router.callback_query(F.data.startswith("ccomment:skip:"))
async def on_skip_comment(callback: CallbackQuery, state: FSMContext, texts: dict, **kwargs):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(texts["rate_thank_you"])
    
    # Show user menu
    await callback.message.answer(
        texts["client_menu_title"], 
        reply_markup=client_menu_keyboard(texts),
        parse_mode="HTML"
    )


@router.message(ClientMenuFSM.rate_comment, F.text)
async def on_rate_comment(message: Message, state: FSMContext, texts: dict, **kwargs):
    data = await state.get_data()
    booking_id = data.get("rating_booking_id")
    
    comment = message.text.strip()[:300]
    if booking_id:
        await rating_service.update_comment(booking_id, comment)
    
    await state.clear()
    await message.answer(texts["rate_comment_saved"])
    
    # Show user menu
    await message.answer(
        texts["client_menu_title"], 
        reply_markup=client_menu_keyboard(texts),
        parse_mode="HTML"
    )
