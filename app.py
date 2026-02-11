"""
IDX-Pro Insight Terminal - Sistem Pendukung Keputusan Saham IDX.
4 Pilar: ATR (Risiko), Mansfield RS (Momentum), Seasonality, Sentimen Leksikon.
Login via Firebase Auth; data disimpan di Firestore. Bahasa Indonesia.
"""
__version__ = "1.3.0"

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime

from auth_manager import init_session, login, register, logout, get_current_user, set_user
from firebase_config import save_to_firestore, get_from_firestore, verify_firebase_id_token
from analysis_engine import ensure_jk, run_full_analysis, get_history, get_macro_symbol
from data_engine import get_stock_data, get_benchmark, get_stock_and_benchmark
from quant_engine import compute_atr, safe_entry_calculator, compute_mansfield_rs, compute_seasonality
from sentiment_engine import sentiment_score, gauge_value
from utils import format_idr, format_pct
from market_scanner import run_scan, get_ihsg_today, get_intraday_15m, vwap_intraday, fetch_market_data, get_top_sectors
from macro_engine import calculate_market_mood, get_macro_indicators


@st.cache_data(ttl=120)
def _cached_market_mood():
    return calculate_market_mood()


@st.cache_data(ttl=120)
def _cached_macro_indicators():
    return get_macro_indicators()


@st.cache_data(ttl=120)
def _cached_sector_leaderboard():
    data = fetch_market_data()
    return get_top_sectors(data) if data else []


# --- Konfigurasi halaman ---
st.set_page_config(
    page_title=f"IDX-Pro Insight Terminal (v{__version__})",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Tema Modern Minimalis - teks terbaca di dark theme ---
st.markdown("""
<style>
    /* Warna teks netral agar kelihatan di dark background */
    .stApp { background: linear-gradient(180deg, #0d1117 0%, #161b22 100%); min-height: 100vh; }
    .main .block-container { padding: 2rem 2.5rem; max-width: 1320px; }
    
    /* Semua teks utama: abu-abu terang netral */
    .stApp p, .stApp span, .stApp label, .stApp div[data-testid="stMarkdown"] p,
    .stApp div[data-testid="stMarkdown"] li, .stApp .stCaption, .stApp small {
        color: #c9d1d9 !important;
    }
    .stApp label { color: #b1bac4 !important; }
    
    /* Heading */
    h1, h2, h3 { color: #f0f6fc !important; font-weight: 600; letter-spacing: -0.02em; }
    h2 { font-size: 1.35rem; margin-top: 1.5rem; padding-bottom: 0.5rem; border-bottom: 1px solid rgba(48,54,61,0.8); }
    h3 { font-size: 1.1rem; color: #e6edf3 !important; font-weight: 500; }
    
    /* Sidebar - tema gelap elegan (paksa override tema default Streamlit) */
    section[data-testid="stSidebar"],
    div[data-testid="stSidebar"],
    [data-testid="stSidebar"] > div,
    .stApp [data-testid="stSidebar"],
    section[data-testid="stSidebar"] > div {
        background: linear-gradient(180deg, #0f1419 0%, #151b23 50%, #0d1117 100%) !important;
        border-right: 1px solid rgba(48,54,61,0.6) !important;
    }
    section[data-testid="stSidebar"] { padding: 1.25rem 1rem !important; }
    div[data-testid="stSidebar"] { padding: 1.25rem 1rem !important; }
    [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span { color: #e6edf3 !important; }
    [data-testid="stSidebar"] label { color: #f0f6fc !important; font-weight: 500; font-size: 0.875rem; }
    [data-testid="stSidebar"] .stCaption { color: #8b949e !important; font-size: 0.8rem; }
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div { padding: 0.35rem 0; }
    [data-testid="stSidebar"] hr { border-color: rgba(48,54,61,0.4) !important; margin: 1rem 0; }
    [data-testid="stSidebar"] input {
        color: #e6edf3 !important;
        background: rgba(22,27,34,0.9) !important;
        border: 1px solid rgba(48,54,61,0.6) !important;
        border-radius: 8px;
    }
    [data-testid="stSidebar"] input:focus { border-color: rgba(88,166,255,0.6) !important; box-shadow: 0 0 0 2px rgba(88,166,255,0.2); }
    [data-testid="stSidebar"] [data-testid="stRadio"] label { color: #e6edf3 !important; }
    [data-testid="stSidebar"] [data-baseweb="radio-group"] { margin: 0.5rem 0; padding: 0.25rem 0; }
    [data-testid="stSidebar"] [data-baseweb="radio-group"] [role="radiogroup"] {
        background: rgba(22,27,34,0.7) !important;
        border-radius: 10px;
        padding: 0.35rem;
        border: 1px solid rgba(48,54,61,0.5);
    }
    [data-testid="stSidebar"] [data-testid="stCheckbox"] label { color: #c9d1d9 !important; font-weight: 400; font-size: 0.85rem; }
    [data-testid="stSidebar"] .stButton > button { border-radius: 10px; font-weight: 500; padding: 0.5rem 1rem; }
    [data-testid="stSidebar"] h3 { font-size: 1rem; font-weight: 600; letter-spacing: -0.01em; margin-bottom: 0.15rem; color: #f0f6fc !important; }
    /* Pastikan blok konten di dalam sidebar juga gelap */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"], [data-testid="stSidebar"] [class*="block-container"] { background: transparent !important; }
    
    /* Expander - judul & isi terbaca */
    div[data-testid="stExpander"] {
        background: rgba(22,27,34,0.6);
        border: 1px solid rgba(48,54,61,0.5);
        border-radius: 12px;
        margin: 0.75rem 0;
        overflow: hidden;
    }
    div[data-testid="stExpander"] summary { padding: 0.85rem 1rem; font-weight: 500; color: #f0f6fc !important; }
    div[data-testid="stExpander"] p, div[data-testid="stExpander"] .stCaption, div[data-testid="stExpander"] span { color: #c9d1d9 !important; }
    
    /* Metrics - label & value terbaca */
    [data-testid="stMetric"] {
        background: rgba(22,27,34,0.5);
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid rgba(48,54,61,0.4);
    }
    [data-testid="stMetric"] label { color: #b1bac4 !important; font-size: 0.8rem; }
    [data-testid="stMetric"] [data-testid="stMetricValue"] { color: #79c0ff !important; font-weight: 600; }
    
    /* Button teks */
    .stButton > button { border-radius: 8px; font-weight: 500; color: #f0f6fc; transition: all 0.2s ease; }
    .stButton > button[kind="primary"] { background: #238636; border: none; color: #fff !important; }
    .stButton > button[kind="primary"]:hover { background: #2ea043; color: #fff !important; }
    
    /* Input - label & placeholder */
    .stTextInput label, .stTextInput input::placeholder { color: #b1bac4 !important; }
    .stTextInput input { color: #e6edf3 !important; }
    .stTextInput > div > div input { border-radius: 8px; border-color: rgba(48,54,61,0.8); background: rgba(22,27,34,0.8); }
    
    /* Radio - label terbaca */
    .stRadio label { color: #c9d1d9 !important; }
    
    /* Alert / Info / Success / Error - teks kontras */
    div[data-testid="stAlert"] { border-radius: 10px; border: 1px solid rgba(48,54,61,0.5); }
    div[data-testid="stAlert"] p, div[data-testid="stAlert"] span { color: #e6edf3 !important; }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 0.25rem; }
    .stTabs [data-baseweb="tab"] { border-radius: 8px; padding: 0.5rem 1rem; color: #c9d1d9 !important; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { color: #f0f6fc !important; }
    
    /* Tab halus (radio horizontal Analisis): tampilan seperti tab, transisi halus */
    .main [data-baseweb="radio-group"] [role="radiogroup"] {
        display: flex; gap: 0.2rem; flex-wrap: wrap;
        background: rgba(22,27,34,0.6); border-radius: 12px; padding: 0.4rem;
        border: 1px solid rgba(48,54,61,0.5);
    }
    .main [data-baseweb="radio-group"] label {
        padding: 0.55rem 1rem; border-radius: 10px; transition: background 0.2s ease, color 0.2s ease;
        margin: 0; font-weight: 500; cursor: pointer;
    }
    .main [data-baseweb="radio-group"] label:hover { background: rgba(48,54,61,0.35); }
    
    hr { margin: 1.25rem 0; border-color: rgba(48,54,61,0.4); }
    .main .block-container > div { margin-bottom: 0.5rem; }
</style>
""", unsafe_allow_html=True)

# --- Cookie manager (untuk tetap login setelah refresh) ---
_cookies = None
try:
    _cookie_pwd = (st.secrets.get("app") or {}).get("cookie_password") or "idx_pro_insight_cookie_key"
    from streamlit_cookies_manager import EncryptedCookieManager
    _cookies = EncryptedCookieManager(prefix="idxpro/", password=_cookie_pwd)
except Exception:
    pass

# --- Inisialisasi session ---
init_session()
if "remembered_email" not in st.session_state:
    st.session_state.remembered_email = ""
if "remembered_password" not in st.session_state:
    st.session_state.remembered_password = ""
if "ticker_input" not in st.session_state:
    st.session_state.ticker_input = "BBCA"

# Restore login dari cookie (setelah refresh) — tidak mengubah data, hanya session
# Jangan st.rerun() saat cookie belum ready agar halaman tetap bisa tampil (hindari loading tak selesai)
if _cookies is not None and _cookies.ready() and not st.session_state.logged_in:
    _token = None
    try:
        _token = _cookies["idx_token"]
    except (KeyError, TypeError, Exception):
        pass
    if _token:
        _decoded = verify_firebase_id_token(_token)
        if _decoded and _decoded.get("uid"):
            set_user(_decoded)
        else:
            try:
                del _cookies["idx_token"]
                _cookies.save()
            except Exception:
                pass

user = get_current_user()
logged_in = user is not None

# --- Sidebar ---
def get_invite_code():
    """Ambil kode undangan dari st.secrets (opsional)."""
    try:
        if hasattr(st.secrets, "app") and st.secrets.app:
            sec = st.secrets.app
            return sec.get("invite_code") if isinstance(sec, dict) else getattr(sec, "invite_code", None)
        if hasattr(st.secrets, "INVITE_CODE"):
            return st.secrets.INVITE_CODE
    except Exception:
        return None


with st.sidebar:
    st.markdown("### IDX-Pro Insight")
    st.caption(f"Terminal · Analisis Saham IDX · **v{__version__}**")
    st.divider()

    if logged_in:
        st.success(f"👤 {user.get('display_name', user.get('email', 'User'))}")
        st.caption(user.get("email", ""))
    else:
        st.caption("Akses fitur Pro & Portofolio Cloud")
        auth_tab = st.radio("Pilih", ["Masuk", "Daftar (kode undangan)"], key="auth_tab", label_visibility="collapsed", horizontal=True)
        st.markdown("")  # jarak
        if auth_tab.startswith("Masuk"):
            # Form login (seperti biasa)
            if st.session_state.remembered_email and "login_email" not in st.session_state:
                st.session_state.login_email = st.session_state.remembered_email
            if st.session_state.remembered_password and "login_pass" not in st.session_state:
                st.session_state.login_pass = st.session_state.remembered_password
            email_login = st.text_input("Email", value=st.session_state.remembered_email, key="login_email", placeholder="nama@email.com", label_visibility="visible")
            pass_login = st.text_input("Kata sandi", value=st.session_state.remembered_password, type="password", key="login_pass", placeholder="••••••••", label_visibility="visible")
            st.caption("Centang agar email & kata sandi terisi otomatis lain waktu (tidak perlu mengetik terus).")
            ingat_saya = st.checkbox("Ingat email & kata sandi", value=bool(st.session_state.remembered_email or st.session_state.remembered_password), key="ingat_saya")
            if st.button("Masuk", type="primary", use_container_width=True):
                err = []
                if not (email_login or "").strip():
                    err.append("Email harus diisi.")
                if not (pass_login or "").strip():
                    err.append("Kata sandi harus diisi.")
                if err:
                    st.error(" ".join(err))
                elif email_login and pass_login:
                    ok, msg, u = login(email_login.strip(), pass_login)
                    if ok and u:
                        if ingat_saya:
                            st.session_state.remembered_email = email_login.strip()
                            st.session_state.remembered_password = pass_login
                        else:
                            st.session_state.remembered_email = ""
                            st.session_state.remembered_password = ""
                        set_user(u)
                        if _cookies is not None and u.get("id_token"):
                            try:
                                _cookies["idx_token"] = u["id_token"]
                                _cookies.save()
                            except Exception:
                                pass
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
        else:
            # Form daftar dengan kode undangan
            st.markdown("_Pendaftaran hanya untuk yang memiliki kode undangan dari admin._")
            name_reg = st.text_input("Nama lengkap", key="reg_name", placeholder="Nama Anda", label_visibility="visible")
            email_reg = st.text_input("Email", key="reg_email", placeholder="nama@email.com", label_visibility="visible")
            pass_reg = st.text_input("Kata sandi", type="password", key="reg_pass", placeholder="Min. 6 karakter", label_visibility="visible")
            invite_input = st.text_input("Kode undangan", type="password", key="reg_invite", placeholder="Kode dari admin", label_visibility="visible")
            if st.button("Daftar", type="primary", use_container_width=True):
                err = []
                if not (email_reg or "").strip():
                    err.append("Email harus diisi.")
                if not (pass_reg or "").strip():
                    err.append("Kata sandi harus diisi.")
                if not (invite_input or "").strip():
                    err.append("Kode undangan harus diisi.")
                expected_code = (get_invite_code() or "").strip()
                if expected_code and invite_input.strip() != expected_code:
                    err.append("Kode undangan salah.")
                if not expected_code:
                    err.append("Kode undangan belum dikonfigurasi. Hubungi admin.")
                if err:
                    st.error(" ".join(err))
                elif email_reg and pass_reg and expected_code and invite_input.strip() == expected_code:
                    ok, msg, u = register(email_reg.strip(), pass_reg, name_reg.strip())
                    if ok and u:
                        set_user(u)
                        if _cookies is not None and u.get("id_token"):
                            try:
                                _cookies["idx_token"] = u["id_token"]
                                _cookies.save()
                            except Exception:
                                pass
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
        st.divider()

    st.divider()
    # Redirect dari "Analisa Mendalam Saham Ini" di Peluang Hari Ini
    if st.session_state.get("force_menu") and st.session_state.get("analysis_ticker"):
        st.session_state["ticker_input"] = str(st.session_state["analysis_ticker"]).replace(".JK", "").upper()
    menu_options = (
        ["Peluang Hari Ini", "Analisis Mendalam", "Tanya Gemini", "Portofolio Saya", "Logout"] if logged_in
        else ["Peluang Hari Ini", "Market Overview", "Tanya Gemini"]
    )
    # Tetap di halaman yang sama setelah refresh: baca menu dari URL
    _qmenu = st.query_params.get("menu")
    if _qmenu in menu_options:
        default_idx = menu_options.index(_qmenu)
    elif st.session_state.get("force_menu") and "Analisis Mendalam" in menu_options:
        default_idx = menu_options.index("Analisis Mendalam") if "Analisis Mendalam" in menu_options else 0
    else:
        default_idx = 0
    menu = st.radio("Menu", menu_options, index=min(default_idx, len(menu_options) - 1), key="menu_radio", label_visibility="collapsed")
    if st.query_params.get("menu") != menu:
        st.query_params["menu"] = menu
    if st.session_state.get("force_menu"):
        del st.session_state["force_menu"]
    if st.session_state.get("analysis_ticker"):
        del st.session_state["analysis_ticker"]

    if menu == "Logout":
        logout()
        if _cookies is not None:
            try:
                del _cookies["idx_token"]
                _cookies.save()
            except Exception:
                pass
        st.rerun()

    st.divider()
    raw_ticker = st.text_input("Kode Saham", value=st.session_state.get("ticker_input", "BBCA"), key="ticker_input", placeholder="Contoh: BBCA, GOTO").strip().upper() or "BBCA"
    # Validasi: hanya huruf/angka, maks 10 karakter (kode IDX umum 2–5)
    raw_ticker = "".join(c for c in raw_ticker if c.isalnum())[:10] or "BBCA"
    ticker = ensure_jk(raw_ticker)
    st.caption(f"Simbol: {ticker}")

# --- Main content ---
if menu == "Peluang Hari Ini":
    # ========== DAILY OPPORTUNITY DASHBOARD (Landing Page) ==========
    st.header("Peluang Hari Ini")
    st.caption("Saham apa yang bagus untuk dibeli hari ini? Hasil pemindaian otomatis saham likuid (LQ45 & IDX80).")
    try:
        ihsg_close, ihsg_pct, _ = get_ihsg_today()
        if ihsg_close is not None and ihsg_pct is not None:
            col_ihsg1, col_ihsg2 = st.columns([3, 1])
            with col_ihsg1:
                st.subheader("IHSG (^JKSE)")
            with col_ihsg2:
                st.metric("Harga", f"{ihsg_close:,.0f}", f"{ihsg_pct:+.2f}%")
                color = "#3fb950" if ihsg_pct >= 0 else "#f85149"
                label = "Hijau" if ihsg_pct >= 0 else "Merah"
                st.markdown(f"<span style='color: {color}; font-size: 1.1rem;'>{label}</span>", unsafe_allow_html=True)
    except Exception:
        st.warning("Data IHSG hari ini tidak tersedia (pasar mungkin tutup).")

    with st.spinner("Memindai pasar..."):
        scan = run_scan()
    if scan.get("error"):
        st.warning(scan["error"])
    day_list = scan.get("day_trade") or []
    swing_list = scan.get("swing") or []
    invest_list = scan.get("invest") or []
    defensive_list = scan.get("defensive") or []
    if not scan.get("error") and not day_list and not swing_list and not invest_list:
        st.info("Tidak ada saham yang memenuhi kriteria pemindaian hari ini. Coba lagi saat pasar buka atau besok.")
        if defensive_list:
            st.markdown("**Saham Defensif (saat pasar sulit)**")
            st.caption("Consumer non-cyclical / bluechip defensif — referensi saja, bukan rekomendasi beli.")
            for i, p in enumerate(defensive_list[:3], 1):
                sym = p.get("ticker", "").replace(".JK", "")
                st.markdown(f"**#{i} {sym}** · {format_idr(p.get('close', 0), 0)} · **{p.get('pct_change', 0):+.2f}%**")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**Day Trade Picks**")
        st.caption("Saham dengan lonjakan volume tinggi hari ini.")
        for i, p in enumerate(day_list[:3], 1):
            sym = p.get("ticker", "").replace(".JK", "")
            st.markdown(f"**#{i} {sym}** · {format_idr(p.get('close', 0), 0)} · **{p.get('pct_change', 0):+.2f}%**")
    with c2:
        st.markdown("**Swing Trade Picks**")
        st.caption("Saham uptrend yang potensial lanjut naik.")
        for i, p in enumerate(swing_list[:3], 1):
            sym = p.get("ticker", "").replace(".JK", "")
            dist = p.get("dist_support_pct", 0)
            st.markdown(f"**#{i} {sym}** · Jarak ke MA20: **{dist:.2f}%**")
    with c3:
        st.markdown("**Invest Picks**")
        st.caption("Saham bluechip yang sedang koreksi wajar.")
        for i, p in enumerate(invest_list[:3], 1):
            sym = p.get("ticker", "").replace(".JK", "")
            disc = p.get("discount_pct", 0)
            st.markdown(f"**#{i} {sym}** · Diskon dari ATH 52w: **{disc:.1f}%**")

    # Instant Chart: Day #1, atau fallback saham defensif #1, atau BBCA
    day_picks = day_list
    if day_picks:
        chart_ticker = day_picks[0]["ticker"].replace(".JK", "")
    elif defensive_list:
        chart_ticker = defensive_list[0]["ticker"].replace(".JK", "")
    else:
        chart_ticker = "BBCA"
    chart_ticker_jk = ensure_jk(chart_ticker)
    intraday_interval = st.radio("Interval grafik intraday", ["5m", "15m"], horizontal=True, key="intraday_interval", index=0)
    st.subheader(f"Grafik Intraday {intraday_interval} · {chart_ticker}")
    try:
        idf, last_ts = get_intraday_15m(chart_ticker_jk, interval=intraday_interval)
        if idf is not None and not idf.empty:
            vwap_series = vwap_intraday(idf)
            fig_c = go.Figure()
            fig_c.add_trace(go.Candlestick(
                x=idf.index, open=idf["Open"], high=idf["High"], low=idf["Low"], close=idf["Close"],
                name="Harga",
            ))
            if vwap_series is not None and not vwap_series.empty:
                fig_c.add_trace(go.Scatter(x=vwap_series.index, y=vwap_series.values, name="VWAP", line=dict(color="#d29922", width=2)))
            fig_c.update_layout(
                template="plotly_dark",
                height=400,
                # Aktifkan pan & zoom nyaman (bisa geser kiri/kanan setelah zoom)
                dragmode="pan",
                xaxis_rangeslider_visible=True,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(22,27,34,0.4)",
                xaxis=dict(
                    rangebreaks=[
                        dict(bounds=["sat", "mon"]),
                        dict(bounds=[11.5, 13.5], pattern="hour"),  # Istirahat bursa 11:30–13:30 WIB
                    ],
                    type="date",
                ),
            )
            st.plotly_chart(fig_c, use_container_width=True)
            if last_ts is not None:
                ts_str = last_ts.strftime("%d/%m/%Y %H:%M") if hasattr(last_ts, "strftime") else str(last_ts)
                st.caption(f"Data intraday: terakhir sebelum pasar tutup — {ts_str} WIB.")
        else:
            st.info("Data intraday tidak tersedia (pasar tutup atau ticker tidak aktif).")
    except Exception as e:
        st.warning(f"Grafik intraday tidak dapat dimuat: {e}")

    if st.button("Analisa Mendalam Saham Ini"):
        st.session_state["force_menu"] = True
        st.session_state["analysis_ticker"] = chart_ticker
        st.rerun()

elif menu == "Analisis Mendalam" or menu == "Market Overview":
    if menu == "Market Overview" and not logged_in:
        st.header("Market Overview")
        st.info("Login untuk mengakses analisis lengkap, Portofolio, dan Trading Plan.")
        try:
            ihsg = get_history("^JKSE", period="1y")
            if not ihsg.empty:
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=ihsg.index, y=ihsg["Close"], mode="lines", name="IHSG", line=dict(color="#58a6ff", width=2)))
                fig.update_layout(
                    title="",
                    template="plotly_dark",
                    height=380,
                    margin=dict(t=24, b=40, l=50, r=24),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(22,27,34,0.4)",
                    font=dict(color="#8b949e", size=11),
                    xaxis=dict(showgrid=True, gridcolor="rgba(48,54,61,0.4)", zeroline=False),
                    yaxis=dict(showgrid=True, gridcolor="rgba(48,54,61,0.4)", zeroline=False),
                )
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning(f"Data IHSG tidak dapat dimuat: {e}")
        st.stop()

    # --- Analisis dengan 4 Tab: Dashboard, Risiko, Musiman, Sentimen ---
    st.header("IDX-Pro Insight Terminal")
    if not raw_ticker:
        st.warning("Masukkan kode saham di sidebar.")
        st.stop()

    with st.spinner("Memuat data..."):
        result = run_full_analysis(ticker, period="1y")

    if not result.get("success"):
        st.error(result.get("error", "Data tidak ditemukan atau ticker delisting. Cek kode saham."))
        st.stop()

    df = result["df"]
    tech = result["technical"]
    bandar = result["bandarmology"]
    fund = result["fundamental"]
    plan = result["trading_plan"]
    macro_narrative = result.get("macro_narrative", "")
    key_levels = result.get("key_levels") or {}
    obv = result.get("obv")
    support_resistance = result.get("support_resistance") or {}
    insight_summary = result.get("insight_summary") or ""
    recommendation = result.get("recommendation") or {}
    data_as_of = result.get("data_as_of")
    trading_days_count = result.get("trading_days_count", 0)

    # Pilih bagian (radio agar tetap di tab yang sama saat input berubah; st.tabs tidak simpan state saat rerun)
    _tab_names = ["Dashboard Utama", "Manajemen Risiko (ATR)", "Analisis Musiman", "Sentimen Berita"]
    if "analisis_sub_tab" not in st.session_state:
        st.session_state.analisis_sub_tab = _tab_names[0]
    col_tab, col_refresh = st.columns([5, 1])
    with col_tab:
        sub_tab = st.radio(
            "Bagian",
            _tab_names,
            key="analisis_sub_tab",
            horizontal=True,
            label_visibility="collapsed",
        )
    with col_refresh:
        if st.button("Refresh data", help="Perbarui data pasar dan analisis (clear cache)"):
            st.cache_data.clear()
            st.rerun()

    _chart_layout = dict(
        template="plotly_dark",
        margin=dict(t=20, b=40, l=50, r=24),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(22,27,34,0.4)",
        font=dict(color="#8b949e", size=11),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(showgrid=True, gridcolor="rgba(48,54,61,0.4)", zeroline=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(48,54,61,0.4)", zeroline=False),
    )

    # ========== TAB 1: Dashboard Utama — Cockpit Trader + Analisis ==========
    if sub_tab == "Dashboard Utama":
        # --- Cockpit Trader: Market Context & Psychology ---
        st.subheader("Cockpit Trader · Market Context & Psychology")
        mood = _cached_market_mood()
        macro = _cached_macro_indicators()
        sector_leaderboard = _cached_sector_leaderboard()

        # Baris 1: Market Mood Meter (Fear & Greed Gauge)
        if mood.get("error"):
            st.warning(mood["error"])
            if logged_in and st.button("Catat ke Jurnal: Data Makro offline", key="catat_makro_offline"):
                catatan_entry = {
                    "type": "catatan_makro",
                    "note": "Data Makro sedang offline.",
                    "created_at": datetime.now().isoformat(),
                }
                ok, msg = save_to_firestore(user["uid"], "trading_journal", catatan_entry)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)
        else:
            score = mood.get("score", 50)
            label = mood.get("label", "Neutral")
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=score,
                number={"suffix": "", "font": {"size": 28}},
                gauge={
                    "axis": {"range": [0, 100], "tickvals": [0, 20, 40, 60, 80, 100],
                             "ticktext": ["0", "20", "40", "60", "80", "100"]},
                    "bar": {"color": "#58a6ff"},
                    "steps": [
                        {"range": [0, 40], "color": "rgba(248,81,73,0.6)"},
                        {"range": [40, 60], "color": "rgba(210,153,34,0.6)"},
                        {"range": [60, 100], "color": "rgba(63,185,80,0.6)"},
                    ],
                    "threshold": {"line": {"color": "#f0f6fc", "width": 2}, "value": score},
                },
                title={"text": f"Market Mood · {label}"},
            ))
            fig_gauge.update_layout(template="plotly_dark", height=220, paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=50, b=30))
            st.plotly_chart(fig_gauge, use_container_width=True)
            st.caption("0–40: Fear (Buy Zone) · 40–60: Netral · 60–100: Greed (Sell Zone). Bantu putuskan apakah hari ini agresif atau defensif.")

        # Baris 2: Macro Grid (4 kolom)
        m1, m2, m3, m4 = st.columns(4)
        _fmt = lambda v: f"{v:,.2f}" if v is not None and abs(v) < 1e6 else (f"{v:,.0f}" if v is not None else "-")
        with m1:
            idr = macro.get("idr", {})
            if idr.get("error"):
                st.metric("USD/IDR (IDR=X)", "-", "Data offline")
            else:
                pct = idr.get("pct_change", 0) or 0
                st.metric("USD/IDR (Arus Asing)", _fmt(idr.get("price")), f"{-pct:+.2f}%")
                st.caption("Inverse: IDR naik = merah (melemah)")
        with m2:
            oil = macro.get("oil", {})
            if oil.get("error"):
                st.metric("Minyak WTI (CL=F)", "-", "Data offline")
            else:
                st.metric("Minyak WTI (Energi)", _fmt(oil.get("price")), f"{oil.get('pct_change', 0):+.2f}%")
        with m3:
            gold = macro.get("gold", {})
            if gold.get("error"):
                st.metric("Emas (GC=F)", "-", "Data offline")
            else:
                st.metric("Emas (Tambang)", _fmt(gold.get("price")), f"{gold.get('pct_change', 0):+.2f}%")
        with m4:
            btc = macro.get("btc", {})
            if btc.get("error"):
                st.metric("BTC/USD (Risk-On)", "-", "Data offline")
            else:
                st.metric("Bitcoin (Risk-On Global)", _fmt(btc.get("price")), f"{btc.get('pct_change', 0):+.2f}%")

        # Baris 3: Sector Leaderboard (Top 3 sektor terkuat)
        if sector_leaderboard:
            top3 = sector_leaderboard[:3]
            parts = [f"{i}. {s['sector']} ({s['pct_change']:+.1f}%)" for i, s in enumerate(top3, 1)]
            st.markdown("**Sektor terkuat hari ini:** " + " · ".join(parts))
            st.caption("Uang mengalir ke sektor Leading; sektor Lagging di bawah.")
        else:
            st.caption("Sector leaderboard tidak tersedia (data pasar offline atau belum di-refresh).")

        st.markdown("---")
        if data_as_of or trading_days_count:
            st.caption(f"**Data harga per {data_as_of or '-'}** · Berdasarkan {trading_days_count} hari perdagangan. Sumber: Yahoo Finance. Data dapat tertunda.")
        if insight_summary:
            st.markdown("#### Ringkasan Telaah")
            st.markdown(insight_summary)

        # Kesimpulan & Rekomendasi: saran beli/tidak + range harga (lebih terstruktur dan rinci)
        if recommendation:
            rec_style = recommendation.get("style", "")
            rec_label = recommendation.get("style_label", "")
            buy_low = recommendation.get("buy_range_low")
            buy_high = recommendation.get("buy_range_high")
            tgt_low = recommendation.get("target_low")
            tgt_high = recommendation.get("target_high")
            avoid = recommendation.get("avoid_reason")
            summary = recommendation.get("summary", "")
            st.markdown("---")
            st.subheader("Kesimpulan & Rekomendasi")
            if avoid:
                st.warning(f"**{rec_label}** — {avoid}")
            else:
                st.success(f"**{rec_label}**")
            if buy_low is not None and buy_high is not None:
                st.markdown(f"**Area beli disarankan:** Rp {buy_low:,.0f} – Rp {buy_high:,.0f}")
            if tgt_low is not None and tgt_high is not None:
                st.markdown(f"**Target / resistance:** Rp {tgt_low:,.0f} – Rp {tgt_high:,.0f}")
            # Risk/Reward ratio (dari plan: jarak target vs jarak SL)
            plan_support = plan.get("support")
            plan_resistance = plan.get("resistance")
            plan_sl = plan.get("stop_loss_value")
            if plan_support and plan_resistance and plan_sl and plan_support > plan_sl:
                risk_r = plan_resistance - plan_support
                risk_l = plan_support - plan_sl
                if risk_l > 0:
                    rr = risk_r / risk_l
                    st.metric("Risk/Reward (R:R)", f"1 : {rr:.1f}", "Semakin tinggi semakin menguntungkan")
            st.markdown("**Rincian kesimpulan:**")
            st.markdown(summary)
            if logged_in:
                if st.button("Simpan rekomendasi ke Jurnal", key="save_rec"):
                    rec_entry = {
                        "ticker": ticker,
                        "type": "rekomendasi",
                        "recommendation_style": rec_label,
                        "recommendation_buy_range": f"Rp {buy_low:,.0f} – Rp {buy_high:,.0f}" if buy_low and buy_high else "-",
                        "recommendation_target": f"Rp {tgt_low:,.0f} – Rp {tgt_high:,.0f}" if tgt_low and tgt_high else "-",
                        "recommendation_summary": summary,
                        "avoid_reason": avoid,
                        "created_at": datetime.now().isoformat(),
                    }
                    ok, msg = save_to_firestore(user["uid"], "trading_journal", rec_entry)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
            st.caption(
                "**Disclaimer:** Aplikasi ini untuk **pembelajaran** agar Anda dapat membuat **kesimpulan secara mandiri**. "
                "Analisis disajikan secara mendalam sebagai **bahan pengambilan keputusan**—dengan bantuan aplikasi ini Anda dapat mengambil keputusan sendiri. "
                "Ini bukan saran atau rekomendasi investasi dari pihak lain; keputusan dan risiko sepenuhnya ada di tangan pemodal. "
                "Gunakan hasil analisis dengan bijak, lakukan riset tambahan bila perlu."
            )
            st.markdown("---")

        st.subheader(f"Chart Teknikal · {ticker}")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=df["Close"], name="Harga", line=dict(color="#58a6ff", width=2)))
        if "BB_upper" in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df["BB_upper"], name="BB Upper", line=dict(color="#f85149", width=1, dash="dot")))
            fig.add_trace(go.Scatter(x=df.index, y=df["BB_mid"], name="BB Mid", line=dict(color="#8b949e", width=1)))
            fig.add_trace(go.Scatter(x=df.index, y=df["BB_lower"], name="BB Lower", line=dict(color="#3fb950", width=1, dash="dot")))
        if "MA20" in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df["MA20"], name="MA20", line=dict(color="#d29922", width=1.5)))
        if "MA50" in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df["MA50"], name="MA50", line=dict(color="#a371f7", width=1.5)))
        if "MA200" in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df["MA200"], name="MA200", line=dict(color="#39c5cf", width=1.5)))
        # Pan & zoom: geser kiri/kanan setelah zoom (rangeslider hanya untuk Candlestick, bukan Scatter)
        fig.update_layout(
            **_chart_layout,
            height=420,
            yaxis_title="Harga (Rp)",
            dragmode="pan",
        )
        st.plotly_chart(fig, use_container_width=True)

        if "RSI" in df.columns:
            fig_rsi = go.Figure()
            fig_rsi.add_trace(go.Scatter(x=df.index, y=df["RSI"], name="RSI(14)", line=dict(color="#a371f7", width=2)))
            fig_rsi.add_hline(y=70, line_dash="dash", line_color="rgba(248,81,73,0.6)", annotation_text="Overbought")
            fig_rsi.add_hline(y=30, line_dash="dash", line_color="rgba(63,185,80,0.6)", annotation_text="Oversold")
            fig_rsi.update_layout(
                **_chart_layout,
                height=200,
                yaxis_range=[0, 100],
                yaxis_title="RSI",
                dragmode="pan",
            )
            st.plotly_chart(fig_rsi, use_container_width=True)

        # Mansfield Relative Strength vs IHSG (momentum komparatif)
        df_stock, df_bench = get_stock_and_benchmark(ticker, "1y")
        mr_df = compute_mansfield_rs(df_stock, df_bench, period_sma=52)
        if not mr_df.empty:
            st.subheader("Momentum Komparatif · Mansfield RS vs IHSG")
            last_rs = mr_df["Mansfield_RS"].iloc[-1]
            st.caption("Stronger than Market" if last_rs > 0 else "Weaker than Market")
            fig_mr = go.Figure()
            colors = ["#3fb950" if x >= 0 else "#f85149" for x in mr_df["Mansfield_RS"]]
            fig_mr.add_trace(go.Scatter(
                x=mr_df.index, y=mr_df["Mansfield_RS"], fill="tozeroy", name="Mansfield RS",
                line=dict(color="#58a6ff"), fillcolor="rgba(63,185,80,0.3)" if last_rs >= 0 else "rgba(248,81,73,0.3)"
            ))
            fig_mr.add_hline(y=0, line_dash="dash", line_color="rgba(139,148,158,0.6)")
            fig_mr.update_layout(
                **_chart_layout,
                height=220,
                yaxis_title="Mansfield RS",
                dragmode="pan",
            )
            st.plotly_chart(fig_mr, use_container_width=True)

        if key_levels:
            st.subheader("Key Levels · 52 Minggu & 20 Hari")
            k1, k2, k3, k4 = st.columns(4)
            with k1:
                st.metric("52w High", format_idr(key_levels.get("high_52w")), f"{key_levels.get('pct_from_52w_high') or 0:+.1f}% dari sekarang")
            with k2:
                st.metric("52w Low", format_idr(key_levels.get("low_52w")), f"{key_levels.get('pct_from_52w_low') or 0:+.1f}% dari sekarang")
            with k3:
                st.metric("20d High", format_idr(key_levels.get("high_20d")), f"{key_levels.get('pct_from_20d_high') or 0:+.1f}%")
            with k4:
                st.metric("20d Low", format_idr(key_levels.get("low_20d")), f"{key_levels.get('pct_from_20d_low') or 0:+.1f}%")
            st.caption("Jarak harga saat ini ke level-level penting. Buy on dip sering di area 52w low atau koreksi 5–15% dari 52w high.")

        if obv is not None and not obv.empty:
            st.subheader("On-Balance Volume (OBV)")
            st.caption("Konfirmasi volume: OBV naik = volume mengikuti kenaikan harga.")
            fig_obv = go.Figure()
            fig_obv.add_trace(go.Scatter(x=obv.index, y=obv.values, name="OBV", line=dict(color="#39c5cf", width=2)))
            fig_obv.update_layout(
                **_chart_layout,
                height=220,
                yaxis_title="OBV",
                dragmode="pan",
            )
            st.plotly_chart(fig_obv, use_container_width=True)

        sr = support_resistance
        if sr.get("support") or sr.get("resistance"):
            with st.expander("Support & Resistance (20 hari)", expanded=False):
                st.markdown("**Resistance (area jual):** " + ", ".join([format_idr(x) for x in sr.get("resistance", [])]))
                st.markdown("**Support (area beli):** " + ", ".join([format_idr(x) for x in sr.get("support", [])]))

        with st.expander("Ringkasan Teknikal & Tren", expanded=True):
            st.markdown(f"**Tren:** {tech['trend']}")
            st.markdown(f"**RSI:** {tech['rsi_label']}")
            if tech.get("squeeze"):
                st.markdown("**Bollinger:** Squeeze terdeteksi (potensi breakout)")
            for d in tech.get("details", []):
                st.caption(f"· {d}")
            st.caption("RSI = momentum (<30 oversold, >70 overbought). MA = Moving Average tren.")

        with st.expander("Sinyal Bandarmology (VPA)", expanded=True):
            st.markdown(f"**Sinyal:** {bandar['signal']}")
            st.caption(bandar["description"])
            if bandar.get("volume_ratio"):
                st.caption(f"Rasio volume vs rata-rata 20 hari: {bandar['volume_ratio']:.2f}x")
            zscore = bandar.get("volume_zscore")
            if zscore is not None:
                st.metric("Volume Z-Score", f"{zscore:.2f}", "((Vol hari ini − Rata² 20d) / Std 20d)")
            if bandar.get("volume_spike_extreme"):
                st.error("⚠️ **Volume Spike Ekstrem (Anomali)** — Indikasi kuat aksi Bandar. Volume hari ini > 3× standar deviasi di atas rata-rata 20 hari.")
            st.caption("Proksi aliran uang besar lewat Volume Price Analysis.")

        with st.expander("Fundamental & Valuasi", expanded=True):
            if fund.get("error"):
                st.warning(fund["error"])
            else:
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.metric("PER", f"{fund.get('per') or '-'}")
                with c2:
                    st.metric("PBV", f"{fund.get('pbv') or '-'}")
                with c3:
                    roe = fund.get("roe")
                    st.metric("ROE (%)", f"{roe:.1f}" if roe is not None else "-")
                with c4:
                    der = fund.get("der")
                    st.metric("DER", f"{der:.2f}" if der is not None else "-")
                for lbl in fund.get("labels", []):
                    if "Hidden Gem" in lbl:
                        st.success(lbl)
                    elif "High Debt" in lbl:
                        st.warning(lbl)
                    else:
                        st.info(lbl)
                st.caption("PER, PBV, ROE, DER — metrik valuasi & kesehatan keuangan.")

        if macro_narrative:
            with st.expander("Korelasi Makro & Komoditas", expanded=True):
                st.info(macro_narrative)
                macro_sym, macro_label = get_macro_symbol(ticker)
                macro_df = result.get("macro_df")
                if macro_sym and macro_df is not None and not macro_df.empty:
                    mdf = macro_df
                    fig_m = go.Figure()
                    fig_m.add_trace(go.Scatter(x=mdf.index, y=mdf["Close"], mode="lines", name=macro_label, line=dict(color="#d29922", width=2)))
                    fig_m.update_layout(**_chart_layout, height=240)
                    st.plotly_chart(fig_m, use_container_width=True)

        st.subheader("Rencana Trading")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**Buy Area**")
            st.info(plan.get("buy_area", "-"))
            st.caption("Support / Lower BB")
        with col2:
            st.markdown("**Target**")
            st.success(plan.get("target_profit", "-"))
            st.caption("Resistance / Upper BB")
        with col3:
            st.markdown("**Stop Loss**")
            st.error(plan.get("stop_loss", "-"))
            st.caption("≈4% di bawah support")

        if logged_in:
            if st.button("Simpan ke Jurnal", type="primary"):
                journal_entry = {
                    "ticker": ticker,
                    "buy_area": plan.get("buy_area"),
                    "target_profit": plan.get("target_profit"),
                    "stop_loss": plan.get("stop_loss"),
                    "support": plan.get("support"),
                    "resistance": plan.get("resistance"),
                    "stop_loss_value": plan.get("stop_loss_value"),
                    "current_price": plan.get("current_price"),
                    "technical_trend": tech.get("trend"),
                    "rsi_label": tech.get("rsi_label"),
                    "bandar_signal": bandar.get("signal"),
                    "created_at": datetime.now().isoformat(),
                }
                ok, msg = save_to_firestore(user["uid"], "trading_journal", journal_entry)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)
        else:
            st.caption("Login untuk menyimpan rencana ke Jurnal Cloud.")

        if logged_in:
            st.divider()
            if st.button("Tambah ke Watchlist"):
                watch_entry = {
                    "ticker": ticker,
                    "company": fund.get("company_name", ticker),
                    "trend": tech.get("trend"),
                    "added_at": datetime.now().isoformat(),
                }
                ok, msg = save_to_firestore(user["uid"], "watchlist", watch_entry)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)

    # ========== TAB 2: Manajemen Risiko (ATR & Safe Entry Calculator) ==========
    elif sub_tab == "Manajemen Risiko (ATR)":
        st.subheader("Safe Entry Calculator · Manajemen Risiko Berbasis ATR")
        st.caption("Position sizing berdasarkan volatilitas (ATR 14). Stop Loss = ATR × multiplier (skenario Long).")
        modal_rp = st.number_input("Modal Trading (Rp)", min_value=1_000_000, value=100_000_000, step=10_000_000, key="modal_rp")
        risk_pct = st.select_slider("Risiko Maksimal per Trade (%)", options=[0.5, 1.0, 1.5, 2.0, 2.5, 3.0], value=1.0, key="risk_pct")
        stop_mult = st.slider("Stop Loss Multiplier (× ATR)", min_value=1.0, max_value=4.0, value=2.0, step=0.5, key="stop_mult")
        atr_series = compute_atr(df, period=14)
        last_close = float(df["Close"].iloc[-1])
        atr_val = float(atr_series.iloc[-1]) if not atr_series.empty and pd.notna(atr_series.iloc[-1]) else 0.0
        calc = safe_entry_calculator(last_close, atr_val, modal_rp, risk_pct, stop_mult)
        st.markdown("---")
        st.markdown("**Rekomendasi Safe Entry**")
        r1, r2, r3, r4, r5 = st.columns(5)
        with r1:
            st.metric("Jarak Stop Loss", format_idr(calc["jarak_sl"], 2))
        with r2:
            st.metric("Harga Stop Loss", format_idr(calc["harga_sl"], 2))
        with r3:
            st.metric("Risk Amount (Rp)", format_idr(calc["risk_amount"]))
        with r4:
            st.metric("Max Lembar", f"{calc['max_lembar']:,}")
        with r5:
            st.metric("Max Lot", f"{calc['max_lot']:,}")
        st.warning(f"**Kerugian maksimal jika SL kena (per trade):** {format_idr(calc.get('risk_amount', 0))}")
        st.info("ATR 14 mengukur volatilitas harian. Posisi maksimal dihitung agar kerugian per trade tidak melebihi risiko yang Anda pilih.")

    # ========== TAB 3: Analisis Musiman (Seasonality Matrix) ==========
    elif sub_tab == "Analisis Musiman":
        st.subheader("Probabilitas Musiman · Rata-rata Return & Win Rate per Bulan")
        st.caption("Data historis minimal 10 tahun. Pola Window Dressing / January Effect.")
        df_10y = get_stock_data(ticker, "10y")
        seas = compute_seasonality(df_10y, min_years=5)
        if seas["heatmap_df"] is None or seas["heatmap_df"].empty:
            st.warning("Data historis belum cukup untuk analisis musiman (perlu minimal ~5 tahun).")
        else:
            month_names = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
            heatmap_df = seas["heatmap_df"]
            heatmap_df.columns = [month_names[i - 1] for i in heatmap_df.columns]
            fig_heat = go.Figure(data=go.Heatmap(
                z=heatmap_df.values,
                x=heatmap_df.columns.tolist(),
                y=heatmap_df.index.tolist(),
                colorscale="RdYlGn",
                zmid=0,
                text=[[format_pct(v) if pd.notna(v) else "" for v in row] for row in heatmap_df.values],
                texttemplate="%{text}",
                textfont={"size": 10},
            ))
            fig_heat.update_layout(
                title="Return Bulanan per Tahun",
                template="plotly_dark",
                height=400,
                xaxis_title="Bulan",
                yaxis_title="Tahun",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(22,27,34,0.4)",
            )
            st.plotly_chart(fig_heat, use_container_width=True)
            if seas["avg_return_by_month"] is not None and not seas["avg_return_by_month"].empty:
                st.subheader("Rata-rata Return per Bulan")
                avg = seas["avg_return_by_month"]
                x_months = [month_names[i - 1] for i in avg.index]
                fig_bar = go.Figure(go.Bar(x=x_months, y=avg.values, name="Avg Return", marker_color=["#3fb950" if v >= 0 else "#f85149" for v in avg.values]))
                fig_bar.update_layout(template="plotly_dark", height=280, yaxis_tickformat=".2%", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(22,27,34,0.4)")
                st.plotly_chart(fig_bar, use_container_width=True)
            if seas["win_rate_by_month"] is not None and not seas["win_rate_by_month"].empty:
                wr = seas["win_rate_by_month"]
                st.caption("Win rate (% bulan positif): " + ", ".join([f"{month_names[i-1]} {wr.get(i, 0):.0f}%" for i in range(1, 13) if i in wr.index]))

    # ========== TAB 4: Sentimen Berita (Leksikon Indonesia) ==========
    elif sub_tab == "Sentimen Berita":
        st.subheader("Analisis Sentimen Berita · Leksikon Pasar Modal Indonesia")
        st.caption("Tempel judul/teks berita terkini tentang saham. Skor dari kata kunci positif vs negatif.")
        news_text = st.text_area("Teks berita (copy-paste judul atau isi)", height=120, placeholder="Contoh: Emiten catat laba naik 20%, dividen melonjak...")
        if st.button("Hitung Sentimen"):
            if not (news_text or "").strip():
                st.warning("Masukkan teks berita terlebih dahulu.")
            else:
                res = sentiment_score(news_text)
                g = gauge_value(res["score"])
                st.metric("Skor Sentimen", f"{res['score']} ({res['label']})")
                st.caption(f"Kata positif: {res['pos_count']} · Kata negatif: {res['neg_count']}")
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=g,
                    number={"suffix": "", "font": {"size": 24}},
                    gauge={
                        "axis": {"range": [0, 1], "tickvals": [0, 0.5, 1], "ticktext": ["Bearish", "Netral", "Bullish"]},
                        "bar": {"color": "#58a6ff"},
                        "steps": [
                            {"range": [0, 0.33], "color": "rgba(248,81,73,0.6)"},
                            {"range": [0.33, 0.67], "color": "rgba(210,153,34,0.6)"},
                            {"range": [0.67, 1], "color": "rgba(63,185,80,0.6)"},
                        ],
                        "threshold": {"line": {"color": "#f0f6fc", "width": 2}, "value": g},
                    },
                    title={"text": "Sentimen"},
                ))
                fig_gauge.update_layout(template="plotly_dark", height=280, paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=50, b=30))
                st.plotly_chart(fig_gauge, use_container_width=True)

elif menu == "Tanya Gemini":
    st.header("Tanya Gemini · Asisten Belajar Saham")
    st.caption("Ajukan pertanyaan seputar saham, teknikal, fundamental, atau istilah pasar. Untuk **pembelajaran** dan **bahan pengambilan keputusan** Anda—bukan saran investasi. Jawaban AI dapat tidak akurat; gunakan sebagai referensi dan lakukan riset mandiri.")
    gemini_key = None
    try:
        if hasattr(st.secrets, "gemini") and st.secrets.gemini:
            gemini_key = getattr(st.secrets.gemini, "api_key", None) or (st.secrets.gemini.get("api_key") if isinstance(st.secrets.gemini, dict) else None)
        if not gemini_key and hasattr(st.secrets, "GEMINI_API_KEY"):
            gemini_key = st.secrets.GEMINI_API_KEY
    except Exception:
        pass
    if not gemini_key or not str(gemini_key).strip():
        st.info("Untuk mengaktifkan asisten, tambahkan **Gemini API key** di `.streamlit/secrets.toml` (blok `[gemini]` → `api_key = \"...\"`). Dapatkan key gratis di [Google AI Studio](https://aistudio.google.com/apikey).")
        st.stop()
    if "gemini_messages" not in st.session_state:
        st.session_state.gemini_messages = []
    for msg in st.session_state.gemini_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    prompt = st.chat_input("Tanya tentang saham, RSI, support/resistance, dll.")
    if prompt:
        st.session_state.gemini_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Gemini menjawab..."):
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=gemini_key)
                    system_instruction = (
                        "Kamu asisten edukasi saham untuk pemula di Indonesia. "
                        "Jawab dalam Bahasa Indonesia, singkat dan mudah dipahami. "
                        "Fokus pada penjelasan konsep (teknikal, fundamental, istilah pasar), bukan memberi saran beli/jual. "
                        "Sebutkan bahwa ini untuk pembelajaran dan bukan saran investasi bila relevan."
                    )
                    full_prompt = f"{system_instruction}\n\nPertanyaan pengguna: {prompt}"
                    reply = "Maaf, tidak ada jawaban."
                    last_err = None
                    # Model names from https://ai.google.dev/gemini-api/docs/models (gemini-1.5-flash-latest not available in v1beta)
                    for model_id in ("gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-001"):
                        try:
                            model = genai.GenerativeModel(model_id)
                            response = model.generate_content(full_prompt)
                            if response and response.text:
                                reply = response.text
                            break
                        except Exception as e:
                            last_err = str(e)
                            continue
                    if reply == "Maaf, tidak ada jawaban." and last_err:
                        reply = f"Error: {last_err}. Periksa API key dan koneksi."
                except Exception as e:
                    reply = f"Error: {str(e)}. Periksa API key dan koneksi."
                st.markdown(reply)
        st.session_state.gemini_messages.append({"role": "assistant", "content": reply})
        st.rerun()

elif menu == "Portofolio Saya":
    if not logged_in:
        st.warning("Silakan login untuk melihat Portofolio.")
        st.stop()
    st.header("Portofolio Saya")
    tab1, tab2 = st.tabs(["Watchlist", "Trading Jurnal"])
    with tab1:
        watchlist = get_from_firestore(user["uid"], "watchlist")
        if not watchlist:
            st.info("Watchlist kosong. Gunakan 'Tambah ke Watchlist' di halaman analisis.")
        else:
            for w in watchlist:
                with st.container():
                    st.markdown(f"**{w.get('ticker', '-')}** · {w.get('company', '-')}")
                    st.caption(f"Tren: {w.get('trend', '-')} · {w.get('added_at', '-')[:10]}")
                    st.divider()
    with tab2:
        journal = get_from_firestore(user["uid"], "trading_journal")
        if not journal:
            st.info("Jurnal kosong. Simpan rencana trading dari halaman analisis.")
        else:
            for j in journal:
                with st.container():
                    created = str(j.get("created_at") or "")[:19]
                    if j.get("type") == "catatan_makro":
                        st.markdown(f"**Catatan Makro** · {created}")
                        st.caption(j.get("note", "Data Makro sedang offline."))
                    elif j.get("type") == "rekomendasi":
                        st.markdown(f"**{j.get('ticker', '-')}** · Rekomendasi · {created}")
                        st.caption(f"**{j.get('recommendation_style', '-')}**")
                        st.caption(f"Area beli: {j.get('recommendation_buy_range', '-')} · Target: {j.get('recommendation_target', '-')}")
                        st.caption(j.get("recommendation_summary", ""))
                        if j.get("avoid_reason"):
                            st.caption(f"Catatan: {j['avoid_reason']}")
                    else:
                        st.markdown(f"**{j.get('ticker', '-')}** · {created}")
                        st.caption(f"Buy: {j.get('buy_area')} · Target: {j.get('target_profit')} · SL: {j.get('stop_loss')}")
                        st.caption(f"Trend: {j.get('technical_trend')} · RSI: {j.get('rsi_label')} · Bandar: {j.get('bandar_signal')}")
                    st.divider()

# (Form Login/Daftar sudah dipindah ke atas sidebar)
