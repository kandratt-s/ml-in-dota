from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Main menu keyboard with persistent action buttons."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🔄 Перерегистрация"),
                KeyboardButton(text="🔑 Мой токен"),
            ],
        ],
        resize_keyboard=True,
    )
