"""
Data Engine: penarikan data harga saham dan indeks via yfinance.
Selalu menyertakan IHSG (^JKSE) sebagai benchmark untuk analisis komparatif.
"""
import pandas as pd
import yfinance as yf
import streamlit as st

# Ticker benchmark wajib untuk Mansfield RS dan analisis relatif
BENCHMARK_TICKER = "^JKSE"


def ensure_jk(ticker: str) -> str:
    """Pastikan kode saham IDX pakai suffix .JK."""
    t = (ticker or "").strip().upper()
    if not t:
        return ""
    if not t.endswith(".JK"):
        t = f"{t}.JK"
    return t


@st.cache_data(ttl=300)
def get_stock_data(ticker: str, period: str = "1y") -> pd.DataFrame:
    """
    Ambil data historis saham dari yfinance dengan caching (5 menit).
    Mengembalikan DataFrame dengan kolom Open, High, Low, Close, Volume.
    Mengembalikan DataFrame kosong jika ticker tidak ditemukan atau delisting.
    """
    t = ensure_jk(ticker)
    if not t:
        return pd.DataFrame()
    try:
        obj = yf.Ticker(t)
        df = obj.history(period=period, auto_adjust=True)
        if df is None or df.empty or len(df) < 5:
            return pd.DataFrame()
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300)
def get_benchmark(period: str = "1y") -> pd.DataFrame:
    """
    Ambil data Indeks Harga Saham Gabungan (IHSG) sebagai benchmark wajib
    untuk Mansfield Relative Strength dan analisis komparatif.
    """
    try:
        obj = yf.Ticker(BENCHMARK_TICKER)
        df = obj.history(period=period, auto_adjust=True)
        if df is None or df.empty:
            return pd.DataFrame()
        return df
    except Exception:
        return pd.DataFrame()


def get_stock_and_benchmark(ticker: str, period: str = "1y"):
    """
    Ambil data saham dan IHSG sekaligus. Berguna untuk Mansfield RS.
    Return (df_stock, df_benchmark). Jika saham tidak ditemukan, df_stock kosong.
    """
    df_stock = get_stock_data(ticker, period)
    df_bench = get_benchmark(period)
    return df_stock, df_bench
