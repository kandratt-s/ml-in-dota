from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Main menu keyboard with persistent action buttons."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🔄 Перерегистрация"),
                KeyboardButton(text="🔑 Мой токен"),
                KeyboardButton(text="🎮 Play Dota 2"),
                KeyboardButton(text="📊 Stop play Dota 2")
            ],
        ],
        resize_keyboard=True,
    )
