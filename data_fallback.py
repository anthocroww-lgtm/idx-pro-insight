"""
Sumber data alternatif (fallback) selain Yahoo Finance.
Digunakan hanya ketika yfinance gagal; output dinormalisasi agar tidak mengubah tampilan atau struktur data.
- Alpha Vantage (opsional): API key di secrets → [alpha_vantage] api_key = "..."
  Free tier: 25 req/hari. Daftar: https://www.alphavantage.co/support/#api-key
"""
import time
import requests

_BASE_AV = "https://www.alphavantage.co/query"
_AV_TIMEOUT = 12


def _av_request(params: dict, api_key: str) -> dict | None:
    """Request ke Alpha Vantage. Return JSON dict atau None."""
    if not api_key or not str(api_key).strip():
        return None
    params = {**params, "apikey": api_key.strip()}
    try:
        r = requests.get(_BASE_AV, params=params, timeout=_AV_TIMEOUT)
        if r.status_code != 200:
            return None
        data = r.json()
        if not data or "Error Message" in data or "Note" in data:
            return None
        return data
    except Exception:
        return None


def fetch_fx_av(api_key: str, from_currency: str = "USD", to_currency: str = "IDR") -> dict | None:
    """
    Fallback USD/IDR dari Alpha Vantage (FX_DAILY).
    Return: {"price": float, "pct_change": float} atau None.
    """
    data = _av_request({
        "function": "FX_DAILY",
        "from_symbol": from_currency,
        "to_symbol": to_currency,
        "outputsize": "compact",
    }, api_key)
    if not data:
        return None
    series = data.get("Time Series FX (Daily)")
    if not series or not isinstance(series, dict):
        return None
    dates = sorted(series.keys(), reverse=True)
    if len(dates) < 2:
        return None
    try:
        d0 = series[dates[0]]
        d1 = series[dates[1]]
        close_key = "4. close"
        last = float(d0.get(close_key, 0))
        prev = float(d1.get(close_key, 0))
        if prev <= 0:
            return {"price": last, "pct_change": 0.0}
        pct = (last / prev - 1) * 100
        return {"price": last, "pct_change": round(pct, 2)}
    except (TypeError, ValueError, KeyError):
        return None


def fetch_crypto_av(api_key: str, symbol: str = "BTC", market: str = "USD") -> dict | None:
    """
    Fallback harga crypto dari Alpha Vantage (DIGITAL_CURRENCY_DAILY).
    Return: {"price": float, "pct_change": float} atau None.
    """
    data = _av_request({
        "function": "DIGITAL_CURRENCY_DAILY",
        "symbol": symbol,
        "market": market,
    }, api_key)
    if not data:
        return None
    key = "Time Series (Digital Currency Daily)"
    series = data.get(key)
    if not series or not isinstance(series, dict):
        return None
    dates = sorted(series.keys(), reverse=True)
    if len(dates) < 2:
        return None
    try:
        d0 = series[dates[0]]
        d1 = series[dates[1]]
        close_key = None
        for k in d0:
            if "close" in k.lower() and "usd" in k.lower():
                close_key = k
                break
        if not close_key:
            close_key = "4a. close (USD)"
        last = float(d0.get(close_key, 0))
        prev = float(d1.get(close_key, 0))
        if prev <= 0:
            return {"price": last, "pct_change": 0.0}
        pct = (last / prev - 1) * 100
        return {"price": last, "pct_change": round(pct, 2)}
    except (TypeError, ValueError, KeyError):
        return None


def get_av_key_from_secrets():
    """Ambil Alpha Vantage API key dari st.secrets (opsional). Tidak error jika streamlit tidak ada."""
    try:
        import streamlit as st
        if hasattr(st, "secrets") and st.secrets:
            av = getattr(st.secrets, "alpha_vantage", None) or st.secrets.get("alpha_vantage")
            if av:
                return getattr(av, "api_key", None) or (av.get("api_key") if isinstance(av, dict) else None)
            return st.secrets.get("ALPHA_VANTAGE_API_KEY")
    except Exception:
        pass
    return None
