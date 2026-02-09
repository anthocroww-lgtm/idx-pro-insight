"""
Macro Engine: konteks makroekonomi dan sentimen pasar IHSG.
- IDX Fear & Greed Index (custom model).
- Macro Dashboard: USD/IDR, Minyak WTI, Emas, Bitcoin.
Semua data via yfinance. Tidak mengubah struktur data lain.
"""
import pandas as pd
import numpy as np
import yfinance as yf


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
    - Kurs IDR: melemah (harga IDR=X > MA20) -5, menguat +5.
    - Volatilitas IHSG (ATR spike) -5.
    Return: score (0-100), label (Extreme Fear, Fear, Neutral, Greed, Extreme Greed), error.
    """
    out = {"score": 50, "label": "Neutral", "error": None}
    try:
        ihsg = yf.download("^JKSE", period="1y", auto_adjust=True, progress=False, threads=False)
        idr = yf.download("IDR=X", period="3mo", auto_adjust=True, progress=False, threads=False)
        if ihsg is None or ihsg.empty or len(ihsg) < 200:
            out["error"] = "Data IHSG tidak cukup untuk Market Mood."
            return out
        score = 50.0
        close = ihsg["Close"]
        ihsg["MA200"] = close.rolling(200).mean()
        ihsg["RSI"] = _rsi(close, 14)
        atr = _atr_series(ihsg, 14)
        last = ihsg.iloc[-1]
        rsi = last.get("RSI")
        ma200 = last.get("MA200")
        price = float(last["Close"])
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
            idr_close = idr["Close"]
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
    except Exception as e:
        out["error"] = "Data Makro sedang offline."
        return out


def get_macro_indicators() -> dict:
    """
    Harga real-time: USD/IDR (IDR=X), Minyak WTI (CL=F), Emas (GC=F), BTC (BTC-USD).
    Return: dict dengan key idr, oil, gold, btc; masing-masing {price, pct_change, error}.
    """
    symbols = {"idr": "IDR=X", "oil": "CL=F", "gold": "GC=F", "btc": "BTC-USD"}
    result = {}
    for key, ticker in symbols.items():
        result[key] = {"price": None, "pct_change": 0.0, "error": None}
        try:
            df = yf.download(ticker, period="5d", auto_adjust=True, progress=False, threads=False)
            if df is None or df.empty or len(df) < 2:
                result[key]["error"] = "Data tidak tersedia"
                continue
            last = float(df["Close"].iloc[-1])
            prev = float(df["Close"].iloc[-2])
            pct = (last / prev - 1) * 100 if prev and prev > 0 else 0.0
            result[key]["price"] = last
            result[key]["pct_change"] = round(pct, 2)
        except Exception:
            result[key]["error"] = "Data Makro sedang offline."
    return result
