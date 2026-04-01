import httpx
import streamlit as st
from scr.infra.config import settings
from scr.infra.schemas import LoginRequest, RegisterRequest


class AuthClient:
    def __init__(self, base_url: str, timeout_seconds: float = 10.0):
        self.base_url = base_url
        self.timeout_seconds = timeout_seconds
        self.cookies = {}
        self.access_token: str | None = None

    def _client(self):
        return httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout_seconds,
            cookies=self.cookies,
        )

    def _update_cookies(self, response: httpx.Response):
        for k, v in response.cookies.items():
            self.cookies[k] = v

    def _auth_headers(self) -> dict[str, str]:
        if not self.access_token:
            return {}
        return {"Authorization": f"Bearer {self.access_token}"}

    def register(self, payload: RegisterRequest) -> dict:
        with self._client() as client:
            r = client.post("/auth/register", json=payload.model_dump())
            r.raise_for_status()
            self._update_cookies(r)
            return r.json()

    def login(self, payload: LoginRequest) -> dict:
        with self._client() as client:
            r = client.post(
                "/auth/login",
                json=payload.model_dump(exclude_none=True),
            )
            r.raise_for_status()
            self._update_cookies(r)
            data = r.json()
            self.access_token = data.get("access_token")
            return data

    def refresh(self, fingerprint: str | None = None) -> dict:
        with self._client() as client:
            params = {"fingerprint": fingerprint} if fingerprint else None
            r = client.post(
                "/auth/refresh",
                params=params,
            )
            r.raise_for_status()
            self._update_cookies(r)
            data = r.json()
            self.access_token = data.get("access_token")
            return data

    def logout(self):
        with self._client() as client:
            r = client.post(
                "/auth/logout",
                headers=self._auth_headers(),
            )
            r.raise_for_status()
            self._update_cookies(r)

        self.access_token = None
        self.cookies = {}

    def is_authenticated(self) -> bool:
        return bool(self.access_token) or ("refresh_token" in self.cookies)


def get_auth_client():
    if "auth_client" not in st.session_state:
        st.session_state["auth_client"] = AuthClient(
            base_url=settings.AUTH_BASE_URL,
            timeout_seconds=settings.REQUEST_TIMEOUT_SECONDS,
        )
    return st.session_state["auth_client"]