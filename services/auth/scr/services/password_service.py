from passlib.context import CryptContext
from scr.core.config import settings


# CryptContext — абстракция над алгоритмами.
# deprecated="auto" означает: если пользователь логинится
# со старым хэшом (например md5), passlib автоматически
# пересчитает его в bcrypt при следующем login.
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=settings.BCRYPT_ROUNDS,
)


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def needs_rehash(hashed: str) -> bool:
    """
    True если хэш создан со старыми параметрами (меньше rounds).
    Используется в login: если True — пересохраняем с новым хэшом.
    """
    return pwd_context.needs_update(hashed)