"""
Daily Opportunity Dashboard - Market Scanner.
Memindai saham likuid (LQ45 & IDX80) untuk rekomendasi Day Trade, Swing, dan Invest.
Tanpa pandas_ta: RSI, MACD, MA, VWAP dihitung manual (kompatibel Python 3.14).
"""
import pandas as pd
import numpy as np
import yfinance as yf
import streamlit as st
from datetime import datetime, timezone
import pytz

# Daftar saham likuid prioritas scan (LQ45 + IDX80, unik)
LQ45 = [
    "BBCA", "BBRI", "BMRI", "BNGA", "BBNI", "ASII", "GOTO", "TLKM", "ICBP", "UNVR",
    "GGRM", "HMSP", "INDF", "JPFA", "KLBF", "MNCN", "MRAT", "SIDO", "TOWR", "WIKA",
    "ADRO", "ANTM", "BRPT", "CPIN", "INCO", "ITMG", "MDKA", "PTBA", "PSSI", "SMGR",
    "AKRA", "BUKA", "EMTK", "EXCL", "BREN", "BUMI", "CTRA", "HRUM", "PGAS",
]
IDX80_EXTRA = [
    "BTPN", "BJBR", "BMTR", "BREN", "BSDE", "BUKA", "CPIN", "DKSH", "ELSA", "ERAA",
    "ESSA", "GEMS", "GGRM", "HDFA", "ICBP", "INCO", "INDF", "JPFA", "KLBF", "LPKR",
    "MAPI", "MBSS", "MDKA", "MKPI", "MNCN", "MPMX", "MRAT", "PGAS", "PTBA", "PTPP",
    "SCMA", "SIDO", "SMBR", "SMGR", "TINS", "TKIM", "TLKM", "TOWR", "TPIA", "UNTR",
    "WIKA", "WSBP", "WTON",
]
TICKERS_PRIORITAS = list(dict.fromkeys(LQ45 + IDX80_EXTRA))  # unik, urutan terjaga

# Saham defensif (Consumer Non-Cyclical dll.) untuk fallback saat tidak ada yang lolos Day/Swing/Invest
DEFENSIVE_TICKERS = ["ICBP", "UNVR", "KLBF", "SIDO", "INDF"]

# 5 saham terbesar per sektor utama untuk Sector Leaderboard (Leading vs Lagging)
SECTOR_STOCKS = {
    "Bank": ["BBCA", "BBRI", "BMRI", "BBNI", "BNGA"],
    "Energi": ["PTBA", "ITMG", "ADRO", "AKRA", "PGAS"],
    "Telko": ["TLKM", "GOTO", "EXCL"],
    "Consumer": ["UNVR", "ICBP", "GGRM", "HMSP", "INDF"],
}


def _ensure_jk(symbol: str) -> str:
    return f"{symbol}.JK" if not symbol.endswith(".JK") else symbol


def _jk_list(symbols: list) -> list:
    return [_ensure_jk(s) for s in symbols]


@st.cache_data(ttl=600)
def fetch_market_data():
    """
    Bulk download data 6 bulan untuk semua ticker prioritas.
    Mengembalikan dict ticker -> DataFrame (Open, High, Low, Close, Volume).
    """
    tickers = _jk_list(TICKERS_PRIORITAS)
    try:
        df = yf.download(
            tickers,
            period="6mo",
            group_by="ticker",
            auto_adjust=True,
            threads=True,
            progress=False,
        )
        if df.empty or len(df) < 20:
            return {}
        # MultiIndex columns (group_by='ticker'): level 0 = ticker symbol
        if isinstance(df.columns, pd.MultiIndex):
            out = {}
            for sym in df.columns.get_level_values(0).unique():
                try:
                    sub = df[sym].copy()
                    if sub is None or sub.empty:
                        continue
                    if isinstance(sub.columns, pd.MultiIndex):
                        sub.columns = sub.columns.get_level_values(0)
                    if "Close" not in sub.columns:
                        continue
                    out[sym] = sub
                except Exception:
                    continue
            return out
        # Satu ticker: DataFrame flat (Open, High, Low, Close, Volume)
        return {tickers[0]: df.copy()} if len(tickers) == 1 else {}
    except Exception:
        return {}


def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def _macd(close: pd.Series, fast=12, slow=26, signal=9):
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    return macd_line, signal_line


def _vwap_daily(row: pd.Series) -> float:
    """VWAP satu hari: Typical Price (H+L+C)/3 (proxy tanpa data intraday)."""
    h, l, c = row.get("High", row.get("Close")), row.get("Low", row.get("Close")), row["Close"]
    return (h + l + c) / 3 if pd.notna(h) and pd.notna(l) else float(c)


def screen_day_trade(data: dict) -> list:
    """
    Day Trading: Volume spike > 1.2x avg vol 20d, candle hijau (Close > Open), Harga > VWAP.
    Output: Top 3 dengan % kenaikan hari ini tertinggi.
    """
    results = []
    for sym, df in data.items():
        if df is None or len(df) < 21:
            continue
        try:
            df = df.copy()
            last = df.iloc[-1]
            prev = df.iloc[-21:-1]
            vol_today = last.get("Volume") or 0
            avg_vol_20 = prev["Volume"].mean() if "Volume" in prev else 0
            if avg_vol_20 <= 0 or vol_today < 1.2 * avg_vol_20:
                continue
            open_ = last.get("Open", last["Close"])
            close = last["Close"]
            if close <= open_:
                continue
            vwap_today = _vwap_daily(last)
            if close <= vwap_today:
                continue
            pct = (close / open_ - 1) * 100 if open_ and open_ > 0 else 0
            results.append({"ticker": sym, "close": close, "pct_change": pct, "volume_ratio": vol_today / avg_vol_20})
        except Exception:
            continue
    results.sort(key=lambda x: x["pct_change"], reverse=True)
    return results[:3]


def screen_swing(data: dict) -> list:
    """
    Swing: Harga > MA20, RSI(14) antara 40-65, MACD > Signal.
    Output: Top 3 dengan RSI paling dekat 50-60 (seimbang).
    """
    results = []
    for sym, df in data.items():
        if df is None or len(df) < 35:
            continue
        try:
            df = df.copy()
            close = df["Close"]
            df["MA20"] = close.rolling(20).mean()
            df["RSI"] = _rsi(close, 14)
            macd_line, signal_line = _macd(close)
            df["MACD"], df["MACD_signal"] = macd_line, signal_line
            last = df.iloc[-1]
            ma20 = last.get("MA20")
            rsi = last.get("RSI")
            macd_val = last.get("MACD")
            sig_val = last.get("MACD_signal")
            if pd.isna(ma20) or last["Close"] <= ma20:
                continue
            if pd.isna(rsi) or rsi < 40 or rsi > 65:
                continue
            if pd.isna(macd_val) or pd.isna(sig_val) or macd_val <= sig_val:
                continue
            dist = min(abs(rsi - 50), abs(rsi - 60))
            support_dist = (last["Close"] - ma20) / ma20 * 100 if ma20 and ma20 > 0 else 0
            results.append({
                "ticker": sym, "close": last["Close"], "rsi": rsi, "ma20": ma20,
                "dist_support_pct": support_dist, "score_balance": -dist,
            })
        except Exception:
            continue
    results.sort(key=lambda x: x["score_balance"], reverse=True)
    return results[:3]


def screen_invest(data: dict) -> list:
    """
    Invest: Harga > MA200, koreksi 5-15% dari high 52 minggu (buy on dip).
    Output: Top 3 yang memenuhi.
    """
    results = []
    for sym, df in data.items():
        if df is None or len(df) < 200:
            continue
        try:
            df = df.copy()
            close = df["Close"]
            df["MA200"] = close.rolling(200).mean()
            last = df.iloc[-1]
            ma200 = last.get("MA200")
            if pd.isna(ma200) or last["Close"] <= ma200:
                continue
            high_52w = close.iloc[-252:].max() if len(close) >= 252 else close.max()
            if high_52w <= 0:
                continue
            discount = (1 - last["Close"] / high_52w) * 100
            if discount < 5 or discount > 15:
                continue
            results.append({
                "ticker": sym, "close": last["Close"], "ma200": ma200,
                "high_52w": high_52w, "discount_pct": discount,
            })
        except Exception:
            continue
    results.sort(key=lambda x: x["discount_pct"], reverse=True)  # diskon lebih dalam = lebih "murah"
    return results[:3]


def get_top_sectors(data: dict) -> list:
    """
    Rata-rata perubahan % hari ini dari 5 saham terbesar per sektor (Bank, Energi, Telko, Consumer).
    Output: daftar sektor terurut dari paling hijau (Leading) ke paling merah (Lagging).
    Setiap item: {"sector": nama, "pct_change": rata-rata %}.
    """
    results = []
    for sector_name, tickers in SECTOR_STOCKS.items():
        pcts = []
        for sym in tickers:
            jk = _ensure_jk(sym)
            if jk not in data:
                continue
            df = data[jk]
            if df is None or len(df) < 2:
                continue
            try:
                last = float(df["Close"].iloc[-1])
                prev = float(df["Close"].iloc[-2])
                if prev and prev > 0:
                    pcts.append((last / prev - 1) * 100)
            except Exception:
                continue
        if pcts:
            avg = sum(pcts) / len(pcts)
            results.append({"sector": sector_name, "pct_change": round(avg, 2)})
    results.sort(key=lambda x: x["pct_change"], reverse=True)
    return results


def screen_defensive_fallback(data: dict) -> list:
    """
    Fallback saat tidak ada saham yang lolos Day/Swing/Invest (mis. pasar merah).
    Top 3 saham defensif (Consumer Non-Cyclical: ICBP, UNVR, KLBF, dll.) diurutkan
    oleh perubahan % terbaik (least negative first) agar halaman tidak terlihat sepi.
    """
    results = []
    for sym in DEFENSIVE_TICKERS:
        jk = _ensure_jk(sym)
        if jk not in data:
            continue
        df = data[jk]
        if df is None or len(df) < 2:
            continue
        try:
            last = df.iloc[-1]
            prev = df.iloc[-2]
            close = last.get("Close")
            prev_close = prev.get("Close")
            if pd.isna(close) or pd.isna(prev_close) or prev_close <= 0:
                continue
            close = float(close)
            prev_close = float(prev_close)
            pct = (close / prev_close - 1) * 100
            results.append({"ticker": jk, "close": close, "pct_change": pct})
        except Exception:
            continue
    # Urutkan: yang paling tidak turun (atau naik) di atas
    results.sort(key=lambda x: x["pct_change"], reverse=True)
    return results[:3]


def run_scan():
    """
    Jalankan pemindaian lengkap. Return dict day_trade, swing, invest, defensive (fallback).
    Jika tidak ada yang lolos ketiga kategori, isi defensive dengan Top 3 saham defensif
    agar halaman tidak terlihat sepi saat pasar crash.
    """
    try:
        data = fetch_market_data()
        if not data:
            return {"day_trade": [], "swing": [], "invest": [], "defensive": [], "error": "Data pasar tidak tersedia (pasar tutup atau gagal fetch)."}
        day_trade = screen_day_trade(data)
        swing = screen_swing(data)
        invest = screen_invest(data)
        defensive = screen_defensive_fallback(data) if (not day_trade and not swing and not invest) else []
        return {
            "day_trade": day_trade,
            "swing": swing,
            "invest": invest,
            "defensive": defensive,
            "error": None,
        }
    except Exception as e:
        return {"day_trade": [], "swing": [], "invest": [], "defensive": [], "error": str(e)}


def get_ihsg_today():
    """
    Ambil IHSG (^JKSE): harga terakhir dan perubahan %.
    Fallback: Jika data hari ini belum ada (Yahoo telat update indeks), pakai data penutupan
    terakhir yang valid (mis. kemarin) agar tampilan dan perhitungan (mis. Mansfield RS) tidak crash.
    """
    try:
        df = yf.download("^JKSE", period="5d", auto_adjust=True, progress=False, threads=False)
        if df is None or df.empty or len(df) < 1:
            return None, None, None
        # Ambil baris terakhir; jika Close NaN (indeks belum di-update), fallback ke baris sebelumnya
        last = df.iloc[-1]
        close = last.get("Close")
        if pd.isna(close) or (isinstance(close, (int, float)) and close <= 0):
            if len(df) < 2:
                return None, None, None
            last = df.iloc[-2]
            close = last.get("Close")
            if pd.isna(close) or (isinstance(close, (int, float)) and close <= 0):
                return None, None, None
        close = float(close)
        prev_close = None
        for i in range(len(df) - 2, -1, -1):
            pc = df.iloc[i].get("Close")
            if pd.notna(pc) and pc > 0:
                prev_close = float(pc)
                break
        pct = (close / prev_close - 1) * 100 if prev_close and prev_close > 0 else 0.0
        return close, pct, last.get("Volume")
    except Exception:
        return None, None, None


@st.cache_data(ttl=300)
def get_intraday_15m(ticker: str, interval: str = "15m"):
    """
    Data intraday untuk candlestick. WIB. Cache 5 menit (sinkron dengan data saham).
    interval: "5m" (lebih granular) atau "15m". Jika pasar tutup: pakai data akhir sebelum tutup.
    Return (DataFrame, last_timestamp) agar UI bisa tampilkan "Data terakhir: ...".
    """
    if interval not in ("5m", "15m"):
        interval = "15m"
    try:
        t = _ensure_jk(ticker) if not ticker.endswith(".JK") else ticker
        obj = yf.Ticker(t)
        df = obj.history(period="5d", interval=interval, auto_adjust=True)
        if df is None or df.empty:
            df = obj.history(period="1mo", interval=interval, auto_adjust=True)
        if df is None or df.empty:
            return None, None
        try:
            if df.index.tzinfo is None:
                df = df.tz_localize("UTC", ambiguous="infer")
            df = df.tz_convert("Asia/Jakarta")
        except Exception:
            pass
        last_ts = df.index[-1] if len(df) else None
        return df, last_ts
    except Exception:
        return None, None


def vwap_intraday(df: pd.DataFrame) -> pd.Series:
    """VWAP kumulatif intraday: cumulative( TypicalPrice * Volume ) / cumulative(Volume)."""
    if df is None or df.empty or "Volume" not in df.columns:
        return pd.Series(dtype=float)
    typical = (df["High"] + df["Low"] + df["Close"]) / 3
    tp_vol = typical * df["Volume"].replace(0, np.nan)
    return tp_vol.cumsum() / df["Volume"].cumsum()
