from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    """FSM states for the registration flow."""

    waiting_for_account_id = State()
    waiting_for_password = State()
