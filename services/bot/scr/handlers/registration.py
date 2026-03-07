from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from scr.keyboards import main_menu_keyboard
from scr.states import RegistrationStates
from scr.user_token import generate_token
from scr.models.database import get_db_manager
from db.users import UserRepository
from scr.schemas.users import UserCreate

registration_router = Router(name="registration")

WELCOME_TEXT = (
    "👋 Добро пожаловать в <b>ML-in-Dota Bot</b>!\n\n"
    "Для регистрации мне понадобятся:\n"
    "1️⃣ Ваш <b>Steam Account ID</b>\n"
    "2️⃣ Придуманный вами <b>пароль</b>\n\n"
    "Начнём! Введите ваш <b>Steam Account ID</b>:"
)

NO_REGISTRATION_TEXT = (
    "❌ Вы ещё не зарегистрированы.\n"
    "Нажмите /start для начала регистрации."
)


@registration_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    """Handle /start — begin registration flow."""
    await state.clear()
    await message.answer(WELCOME_TEXT, parse_mode="HTML")
    await state.set_state(RegistrationStates.waiting_for_account_id)


@registration_router.message(F.text == "🔄 Перерегистрация")
async def btn_reregister(message: Message, state: FSMContext) -> None:
    """Handle re-registration button — restart the flow."""
    await state.clear()
    await message.answer(
        "🔄 Начинаем перерегистрацию.\n\nВведите ваш <b>Steam Account ID</b>:",
        parse_mode="HTML",
    )
    await state.set_state(RegistrationStates.waiting_for_account_id)


@registration_router.message(F.text == "🔑 Мой токен")
async def btn_my_token(message: Message, state: FSMContext) -> None:
    """Handle token request button — show stored token from database."""
    async with get_db_manager().get_session() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
    
    if user is None:
        await message.answer(NO_REGISTRATION_TEXT)
        return

    await message.answer(
        f"🔑 Ваш токен:\n<code>{user.token}</code>",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )


@registration_router.message(RegistrationStates.waiting_for_account_id)
async def process_account_id(message: Message, state: FSMContext) -> None:
    """Receive and validate Steam Account ID."""
    account_id = (message.text or "").strip()

    if not account_id.isdigit():
        await message.answer(
            "⚠️ Account ID должен содержать только цифры. Попробуйте снова:"
        )
        return

    await state.update_data(account_id=account_id)
    await message.answer("Отлично! Теперь введите ваш <b>пароль</b>:", parse_mode="HTML")
    await state.set_state(RegistrationStates.waiting_for_password)


@registration_router.message(RegistrationStates.waiting_for_password)
async def process_password(message: Message, state: FSMContext) -> None:
    """Receive password, generate token, save to database, complete registration."""
    password = (message.text or "").strip()

    if len(password) < 4:
        await message.answer("⚠️ Пароль должен быть не менее 4 символов. Попробуйте снова:")
        return

    data = await state.get_data()
    account_id: str = data["account_id"]

    token = generate_token(account_id, password)
    
    # Save user to database
    try:
        async with get_db_manager().get_session() as session:
            user_repo = UserRepository(session)
            
            # Check if user exists and update or create
            existing_user = await user_repo.get_user_by_telegram_id(message.from_user.id)
            if existing_user:
                user = await user_repo.update_user_token(message.from_user.id, token)
            else:
                user_data = UserCreate(telegram_id=message.from_user.id, token=token)
                user = await user_repo.create_user(user_data)
        
        await state.clear()

        await message.answer(
            f"✅ Регистрация завершена!\n\n"
            f"🆔 Account ID: <code>{account_id}</code>\n"
            f"🔑 Ваш токен:\n<code>{token}</code>\n\n"
            f"Сохраните токен — он понадобится для авторизации.",
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(),
        )
        
    except Exception as e:
        await message.answer(
            "❌ Произошла ошибка при регистрации. Попробуйте позже.",
            reply_markup=main_menu_keyboard(),
        )
        # Log error for debugging
        import logging
        logging.getLogger(__name__).error(f"Registration error: {e}")
