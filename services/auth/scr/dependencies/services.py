# dependencies/services.py
from scr.repositories.auth_repo import AuthRepository
from scr.services.auth_service import AuthService

# Создаются один раз при старте приложения
_auth_repository = AuthRepository()
_auth_service = AuthService(_auth_repository)


def get_auth_service() -> AuthService:
    return _auth_service