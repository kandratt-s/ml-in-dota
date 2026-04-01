import streamlit as st
import httpx
from pydantic import ValidationError

from scr.api.auth_client import get_auth_client
from scr.infra.schemas import RegisterRequest, LoginRequest


def _show_http_error(prefix: str, exc: httpx.HTTPStatusError) -> None:
    detail = exc.response.text
    try:
        data = exc.response.json()
        if isinstance(data, dict) and "detail" in data:
            detail = str(data["detail"])
    except Exception:
        pass
    st.error(f"{prefix}: {detail}")


def _show_validation_error(exc: ValidationError) -> None:
    messages: list[str] = []
    for err in exc.errors():
        field = ".".join(str(p) for p in err.get("loc", []))
        msg = err.get("msg", "Invalid value")
        messages.append(f"{field}: {msg}" if field else str(msg))
    st.error("Validation failed: " + "; ".join(messages))

def render_auth():
    auth_client = get_auth_client()
    st.title("Auth")

    tab1, tab2 = st.tabs(["Login", "Register"])

    # ---------- LOGIN ----------
    with tab1:
        with st.form("login_form"):
            account_id = st.number_input("account_id", min_value=0, step=1)
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")

        if submit:
            try:
                payload = LoginRequest(
                    account_id=int(account_id),
                    password=password,
                )
                auth_client.login(payload)
                st.session_state["authenticated"] = True
                st.session_state["account_id"] = payload.account_id
                st.rerun()
            except ValidationError as e:
                _show_validation_error(e)
            except httpx.HTTPStatusError as e:
                _show_http_error("Login failed", e)
            except Exception as e:
                st.error(f"Error: {e}")

    # ---------- REGISTER ----------
    with tab2:
        with st.form("register_form"):
            account_id = st.number_input("New account_id", min_value=0, step=1)
            password = st.text_input("New password", type="password")
            submit = st.form_submit_button("Register")

        if submit:
            try:
                payload = RegisterRequest(
                    account_id=int(account_id),
                    password=password,
                )
                auth_client.register(payload)
                st.success("Registered successfully")
            except ValidationError as e:
                _show_validation_error(e)
            except httpx.HTTPStatusError as e:
                _show_http_error("Register failed", e)
            except Exception as e:
                st.error(f"Error: {e}")

    if st.button("Refresh access token"):
        try:
            auth_client.refresh()
            st.success("Access token refreshed")
        except httpx.HTTPStatusError as e:
            _show_http_error("Refresh failed", e)
        except Exception as e:
            st.error(f"Error: {e}")


def render_logout():
    auth_client = get_auth_client()
    if st.button("Logout"):
        try:
            auth_client.logout()
            st.session_state["authenticated"] = False
            st.session_state.pop("account_id", None)
            st.rerun()
        except httpx.HTTPStatusError as e:
            _show_http_error("Logout failed", e)
        except Exception as e:
            st.error(f"Error: {e}")