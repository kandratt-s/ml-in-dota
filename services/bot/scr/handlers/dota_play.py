from aiogram import F, Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from scr.config import settings

from scr.keyboards import main_menu_keyboard
from scr.states import DotaPlayStates
from db.users import UserRepository
from scr.models.database import get_db_manager

dota_play_router = Router(name="dota_play")

@dota_play_router.message(F.text == "🎮 Play Dota 2")
async def btn_dota(message: Message, state: FSMContext) -> None:
    """Handle Play Dota 2 button — ask if user is playing."""
    await message.answer(
        "OK, жди предикты",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard()
    )
    await state.set_state(DotaPlayStates.is_playing)

    async with get_db_manager().get_session() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)

        await state.update_data(user_token=user.token)


@dota_play_router.message(F.text == "📊 Stop play Dota 2", DotaPlayStates.is_playing)
async def btn_stop_dota(message: Message, state: FSMContext) -> None:
    """Handle Stop play Dota 2 button."""
    await message.answer(
        "OK, остановил предикты",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard()
    )
    await state.clear()