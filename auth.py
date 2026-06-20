"""
Lightweight username/password auth for Paisa Tracker.

No external dependencies — uses only Python's stdlib (hashlib + secrets) for
salted PBKDF2 password hashing. Credentials live in data/users.csv (one row
per user: username, salt, password_hash). Passwords are never stored or
logged in plain text.

Usage in app.py (must be the very first thing that runs, before any data
files are touched):

    import auth
    username = auth.require_login()   # blocks with a login/signup form until
                                       # the user is authenticated, then returns
                                       # their username and lets the script continue
"""

import os
import secrets
import hashlib

import pandas as pd
import streamlit as st

USERS_FILE = os.path.join("data", "users.csv")
PBKDF2_ITERATIONS = 200_000


def _load_users() -> pd.DataFrame:
    if os.path.exists(USERS_FILE):
        return pd.read_csv(USERS_FILE, dtype=str).fillna("")
    return pd.DataFrame(columns=["username", "salt", "password_hash"])


def _save_users(df: pd.DataFrame) -> None:
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    df.to_csv(USERS_FILE, index=False)


def _hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    if salt is None:
        salt = secrets.token_hex(16)
    pwd_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), PBKDF2_ITERATIONS
    ).hex()
    return salt, pwd_hash


def _verify_password(password: str, salt: str, expected_hash: str) -> bool:
    _, computed = _hash_password(password, salt)
    return secrets.compare_digest(computed, expected_hash)


def _username_taken(users: pd.DataFrame, username: str) -> bool:
    return bool((users["username"].str.lower() == username.lower()).any())


def _create_user(username: str, password: str) -> tuple[bool, str]:
    username = username.strip()
    if not username or not password:
        return False, "Username and password are required."
    if len(username) < 3:
        return False, "Username must be at least 3 characters."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    users = _load_users()
    if _username_taken(users, username):
        return False, "That username is already taken."
    salt, pwd_hash = _hash_password(password)
    new_row = pd.DataFrame([{"username": username, "salt": salt, "password_hash": pwd_hash}])
    _save_users(pd.concat([users, new_row], ignore_index=True))
    return True, "Account created \u2014 you can log in now."


def _check_login(username: str, password: str) -> bool:
    users = _load_users()
    if users.empty:
        return False
    row = users[users["username"].str.lower() == username.strip().lower()]
    if row.empty:
        return False
    return _verify_password(password, row.iloc[0]["salt"], row.iloc[0]["password_hash"])


def _render_login_signup() -> None:
    st.markdown(
        "<div style='text-align:center;font-family:\"Space Grotesk\",sans-serif;"
        "font-size:30px;font-weight:700;margin:48px 0 24px;"
        "background:linear-gradient(135deg,#6366f1,#a78bfa,#ec4899);"
        "-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;'>"
        "\U0001F4B0 Paisa Tracker</div>",
        unsafe_allow_html=True,
    )
    _, mid, _ = st.columns([1, 1.3, 1])
    with mid:
        tab_login, tab_signup = st.tabs(["Log in", "Sign up"])

        with tab_login:
            with st.form("login_form"):
                u = st.text_input("Username", key="login_username")
                p = st.text_input("Password", type="password", key="login_password")
                submitted = st.form_submit_button("Log in", use_container_width=True)
            if submitted:
                if _check_login(u, p):
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = u.strip()
                    st.rerun()
                else:
                    st.error("Incorrect username or password.")

        with tab_signup:
            with st.form("signup_form"):
                nu = st.text_input("Choose a username", key="signup_username")
                np1 = st.text_input("Choose a password", type="password", key="signup_password")
                np2 = st.text_input("Confirm password", type="password", key="signup_password2")
                submitted_su = st.form_submit_button("Create account", use_container_width=True)
            if submitted_su:
                if np1 != np2:
                    st.error("Passwords don't match.")
                else:
                    ok, msg = _create_user(nu, np1)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)


def require_login() -> str:
    """Blocks (via st.stop()) until the user is logged in, then returns their username."""
    if st.session_state.get("authenticated") and st.session_state.get("username"):
        return st.session_state["username"]

    _render_login_signup()
    st.stop()


def logout_button(container=st) -> None:
    """Renders a small 'logged in as ... / Log out' control. Call from the sidebar."""
    username = st.session_state.get("username", "")
    container.caption(f"Logged in as **{username}**")
    if container.button("Log out", use_container_width=True, key="logout_btn"):
        for k in ("authenticated", "username"):
            st.session_state.pop(k, None)
        st.rerun()
