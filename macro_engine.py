"""
Macro Engine: konteks makroekonomi dan sentimen pasar IHSG.
- IDX Fear & Greed Index (custom model).
- Macro Dashboard: USD/IDR, Minyak WTI, Emas, Bitcoin.
Sumber utama: yfinance. Fallback opsional: Alpha Vantage untuk USD/IDR dan BTC (lihat data_fallback.py).
Retry + jeda antar-request untuk kurangi "offline" saat jam buka. Tidak mengubah struktur data lain.
"""
import time
import pandas as pd
import numpy as np
import yfinance as yf

# Retry dan jeda untuk kurangi rate limit / gagal sementara Yahoo
_MACRO_RETRIES = 3
_MACRO_DELAY_SEC = 1.2
_SYMBOL_DELAY_SEC = 0.8


def _download_with_retry(ticker: str, period: str = "5d", retries: int = _MACRO_RETRIES, delay: float = _MACRO_DELAY_SEC):
    """Download dengan retry; jeda antar percobaan. Return DataFrame atau None."""
    for attempt in range(retries):
        try:
            df = yf.download(ticker, period=period, auto_adjust=True, progress=False, threads=False)
            if df is None or df.empty:
                raise ValueError("Empty")
            if isinstance(df.columns, pd.MultiIndex):
                df = df.copy()
                df.columns = df.columns.get_level_values(0)
            return df
        except Exception:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                return None
    return None


def _rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """RSI(period) dari harga penutupan."""
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    avg_gain = gain.rolling(period, min_periods=period).mean()
    avg_loss = loss.rolling(period, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def _atr_series(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """ATR(period) untuk deteksi volatilitas."""
    if df is None or df.empty or len(df) < 2:
        return pd.Series(dtype=float)
    high = df["High"]
    low = df["Low"]
    close = df["Close"]
    prev = close.shift(1)
    tr = pd.concat([high - low, (high - prev).abs(), (low - prev).abs()], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()
    return atr


def calculate_market_mood() -> dict:
    """
    IDX Fear & Greed Index (0-100). Base 50.
    - Momentum IHSG (RSI 14): <30 +10 (Fear Opportunity), >70 -10 (Extreme Greed).
    - Trend IHSG: Harga > MA200 +10 (Optimism), < MA200 -10 (Pessimism).
    - Kurs IDR: melemah (harga IDR=X > MA20) -5, menguat +5 (opsional; jika IDR gagal, mood tetap dari IHSG).
    - Volatilitas IHSG (ATR spike) -5.
    Return: score (0-100), label, error. Error hanya jika IHSG benar-benar tidak tersedia.
    """
    out = {"score": 50, "label": "Neutral", "error": None}
    try:
        ihsg = _download_with_retry("^JKSE", period="1y", retries=_MACRO_RETRIES, delay=_MACRO_DELAY_SEC)
        if ihsg is None or ihsg.empty or len(ihsg) < 100:
            ihsg = _download_with_retry("^JKSE", period="6mo", retries=2, delay=_MACRO_DELAY_SEC)
        if ihsg is None or ihsg.empty or len(ihsg) < 50:
            out["error"] = "Data IHSG tidak cukup untuk Market Mood. Coba refresh beberapa saat lagi."
            return out
        time.sleep(_SYMBOL_DELAY_SEC)
        idr = _download_with_retry("IDR=X", period="3mo", retries=2, delay=_MACRO_DELAY_SEC)
        score = 50.0
        close = ihsg["Close"] if "Close" in ihsg.columns else ihsg.iloc[:, 0]
        n = len(ihsg)
        ihsg = ihsg.copy()
        ihsg["MA200"] = close.rolling(min(200, n)).mean()
        ihsg["RSI"] = _rsi(close, 14)
        atr = _atr_series(ihsg, 14)
        last = ihsg.iloc[-1]
        rsi = last.get("RSI")
        ma200 = last.get("MA200")
        price = float(last["Close"]) if "Close" in last.index else float(last.iloc[0])
        if pd.notna(rsi):
            if rsi < 30:
                score += 10
            elif rsi > 70:
                score -= 10
        if pd.notna(ma200) and ma200 > 0:
            if price > ma200:
                score += 10
            else:
                score -= 10
        if idr is not None and not idr.empty and len(idr) >= 20:
            idr_close = idr["Close"] if "Close" in idr.columns else idr.iloc[:, 0]
            idr_ma20 = idr_close.rolling(20).mean().iloc[-1]
            idr_last = float(idr_close.iloc[-1])
            if pd.notna(idr_ma20) and idr_ma20 > 0:
                if idr_last > idr_ma20:
                    score -= 5
                else:
                    score += 5
        if not atr.empty and len(atr) >= 20:
            atr_last = atr.iloc[-1]
            atr_mean_20 = atr.iloc[-20:].mean()
            if pd.notna(atr_last) and pd.notna(atr_mean_20) and atr_mean_20 > 0 and atr_last > atr_mean_20 * 1.3:
                score -= 5
        score = max(0.0, min(100.0, score))
        out["score"] = round(score, 1)
        if score <= 20:
            out["label"] = "Extreme Fear"
        elif score <= 40:
            out["label"] = "Fear"
        elif score <= 60:
            out["label"] = "Neutral"
        elif score <= 80:
            out["label"] = "Greed"
        else:
            out["label"] = "Extreme Greed"
        return out
    except Exception:
        out["error"] = "Data Makro sementara tidak tersedia. Coba refresh dalam beberapa saat."
        return out


def get_macro_indicators() -> dict:
    """
    Harga real-time: USD/IDR (IDR=X), Minyak WTI (CL=F), Emas (GC=F), BTC (BTC-USD).
    Sumber utama: Yahoo Finance (yfinance). Jika gagal untuk IDR/BTC, coba fallback Alpha Vantage (opsional).
    Return: dict dengan key idr, oil, gold, btc; masing-masing {price, pct_change, error}.
    """
    symbols = {"idr": "IDR=X", "oil": "CL=F", "gold": "GC=F", "btc": "BTC-USD"}
    result = {}
    av_key = None
    try:
        from data_fallback import get_av_key_from_secrets, fetch_fx_av, fetch_crypto_av
        av_key = get_av_key_from_secrets()
    except Exception:
        pass

    for key, ticker in symbols.items():
        result[key] = {"price": None, "pct_change": 0.0, "error": None}
        df = _download_with_retry(ticker, period="5d", retries=_MACRO_RETRIES, delay=_MACRO_DELAY_SEC)
        if df is None or len(df) < 2:
            result[key]["error"] = "Data sementara tidak tersedia"
            if av_key and key == "idr":
                time.sleep(_SYMBOL_DELAY_SEC)
                fallback = fetch_fx_av(av_key, "USD", "IDR")
                if fallback:
                    result[key]["price"] = fallback["price"]
                    result[key]["pct_change"] = fallback["pct_change"]
                    result[key]["error"] = None
            elif av_key and key == "btc":
                time.sleep(_SYMBOL_DELAY_SEC)
                fallback = fetch_crypto_av(av_key, "BTC", "USD")
                if fallback:
                    result[key]["price"] = fallback["price"]
                    result[key]["pct_change"] = fallback["pct_change"]
                    result[key]["error"] = None
        else:
            try:
                close = df["Close"] if "Close" in df.columns else df.iloc[:, 0]
                last = float(close.iloc[-1])
                prev = float(close.iloc[-2])
                pct = (last / prev - 1) * 100 if prev and prev > 0 else 0.0
                result[key]["price"] = last
                result[key]["pct_change"] = round(pct, 2)
            except Exception:
                result[key]["error"] = "Data sementara tidak tersedia"
        time.sleep(_SYMBOL_DELAY_SEC)
    return result
