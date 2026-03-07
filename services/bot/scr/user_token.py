import hashlib
import hmac

from scr.config import settings


def generate_token(account_id: str, password: str) -> str:
    """Generate a deterministic token from Steam account_id and user password."""
    secret = settings.TOKEN_SECRET.encode("utf-8")
    payload = f"{account_id}:{password}".encode("utf-8")
    digest = hmac.new(secret, payload, hashlib.sha256).hexdigest()
    return digest[:32]
