"""
Manajemen Login & Register menggunakan Firebase Auth REST API.
Semua API Key diambil dari st.secrets - JANGAN hardcode.
"""
import streamlit as st
import requests


def get_firebase_api_key():
    """Ambil Web API Key Firebase dari st.secrets."""
    try:
        if hasattr(st.secrets, "firebase_auth") and st.secrets.firebase_auth:
            return st.secrets.firebase_auth.get("api_key") or st.secrets.firebase_auth.get("web_api_key")
        if hasattr(st.secrets, "FIREBASE_WEB_API_KEY"):
            return st.secrets.FIREBASE_WEB_API_KEY
        return None
    except Exception:
        return None


def login(email: str, password: str):
    """
    Login dengan Firebase Auth REST API.
    Return (success: bool, message: str, user_data: dict or None)
    """
    api_key = get_firebase_api_key()
    if not api_key:
        return False, "Firebase Auth tidak dikonfigurasi. Isi api_key di secrets.", None

    url = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
    params = {"key": api_key}
    payload = {"email": email, "password": password, "returnSecureToken": True}

    try:
        r = requests.post(url, params=params, json=payload, timeout=10)
        data = r.json()
        if r.status_code == 200:
            return True, "Login berhasil", {
                "uid": data.get("localId"),
                "email": data.get("email"),
                "display_name": data.get("displayName") or email.split("@")[0],
            }
        err = data.get("error", {}).get("message", r.text)
        return False, f"Login gagal: {err}", None
    except Exception as e:
        return False, str(e), None


def register(email: str, password: str, display_name: str = ""):
    """
    Daftar akun baru via Firebase Auth REST API.
    Return (success: bool, message: str, user_data: dict or None)
    """
    api_key = get_firebase_api_key()
    if not api_key:
        return False, "Firebase Auth tidak dikonfigurasi. Isi api_key di secrets.", None

    url = "https://identitytoolkit.googleapis.com/v1/accounts:signUp"
    params = {"key": api_key}
    payload = {"email": email, "password": password, "returnSecureToken": True}
    if display_name:
        payload["displayName"] = display_name

    try:
        r = requests.post(url, params=params, json=payload, timeout=10)
        data = r.json()
        if r.status_code == 200:
            return True, "Registrasi berhasil", {
                "uid": data.get("localId"),
                "email": data.get("email"),
                "display_name": display_name or email.split("@")[0],
            }
        err = data.get("error", {}).get("message", r.text)
        return False, f"Registrasi gagal: {err}", None
    except Exception as e:
        return False, str(e), None


def init_session():
    """Inisialisasi session state untuk auth."""
    if "user" not in st.session_state:
        st.session_state.user = None
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False


def set_user(user_data: dict):
    """Set user login ke session."""
    st.session_state.user = user_data
    st.session_state.logged_in = True


def logout():
    """Logout: hapus user dari session."""
    st.session_state.user = None
    st.session_state.logged_in = False


def get_current_user():
    """Return user dict jika sudah login, else None."""
    init_session()
    return st.session_state.user if st.session_state.logged_in else None


def require_login():
    """Return True jika user sudah login."""
    return get_current_user() is not None
