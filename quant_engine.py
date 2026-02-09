"""
Quant Engine: logika kuantitatif untuk IDX-Pro Insight Terminal.
- ATR (Average True Range) untuk manajemen risiko dan position sizing.
- Mansfield Relative Strength vs IHSG (momentum komparatif).
- Seasonality Matrix (probabilitas bulanan, win rate).
Semua perhitungan murni pandas/numpy (tanpa pandas_ta) agar kompatibel Python 3.14+.
"""
import pandas as pd
import numpy as np


# --- ATR: Manajemen Risiko Berbasis Volatilitas ---
def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Average True Range (ATR) periode 14.
    TR = max(High - Low, |High - PrevClose|, |Low - PrevClose|).
    ATR = Wilder's smoothing (RMA) dari TR.
    Digunakan untuk mengukur volatilitas dan menetapkan jarak Stop Loss.
    """
    if df is None or df.empty or len(df) < 2:
        return pd.Series(dtype=float)
    high = df["High"]
    low = df["Low"]
    close = df["Close"]
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    # Wilder's RMA: ATR(period) pertama = SMA(TR, period), lalu ATR_t = (ATR_{t-1}*(period-1) + TR_t) / period
    atr_rma = tr.copy().astype(float)
    atr_rma.iloc[: period - 1] = np.nan
    atr_rma.iloc[period - 1] = tr.iloc[:period].mean()
    for i in range(period, len(tr)):
        atr_rma.iloc[i] = (atr_rma.iloc[i - 1] * (period - 1) + tr.iloc[i]) / period
    return atr_rma


def safe_entry_calculator(
    close_price: float,
    atr_value: float,
    modal_rp: float = 100_000_000,
    risk_pct: float = 1.0,
    stop_multiplier: float = 2.0,
) -> dict:
    """
    Kalkulator Safe Entry: Position Sizing berbasis ATR.
    - Jarak Stop Loss = ATR x Multiplier (skenario Long: SL di bawah harga).
    - Risk Amount (Rp) = Modal x (Risiko% / 100).
    - Max Position Size (lembar) = Risk Amount / Jarak Stop Loss.
    - Max Lot = floor(Position Size / 100) (1 lot = 100 lembar di IDX).
    """
    if atr_value is None or atr_value <= 0 or close_price is None or close_price <= 0:
        return {
            "jarak_sl": 0.0,
            "harga_sl": 0.0,
            "risk_amount": 0.0,
            "max_lembar": 0,
            "max_lot": 0,
        }
    jarak_sl = atr_value * stop_multiplier
    harga_sl = close_price - jarak_sl  # Long: SL di bawah
    risk_amount = modal_rp * (risk_pct / 100.0)
    max_lembar = int(risk_amount / jarak_sl) if jarak_sl > 0 else 0
    max_lot = max_lembar // 100
    return {
        "jarak_sl": jarak_sl,
        "harga_sl": harga_sl,
        "risk_amount": risk_amount,
        "max_lembar": max_lembar,
        "max_lot": max_lot,
    }


# --- Mansfield Relative Strength: Momentum Komparatif vs IHSG ---
def compute_mansfield_rs(
    df_stock: pd.DataFrame, df_bench: pd.DataFrame, period_sma: int = 52
) -> pd.DataFrame:
    """
    Mansfield Relative Strength vs benchmark (IHSG).
    Rasio = Harga Saham / Harga IHSG (align by date).
    Rata-rata Rasio = SMA(Rasio, period_sma).
    Mansfield RS = ((Rasio / Rata-rata Rasio) - 1) * 10.
    Nilai > 0 = saham mengalahkan pasar (Stronger than Market), < 0 = Underperforming.
    """
    if df_stock is None or df_stock.empty or df_bench is None or df_bench.empty:
        return pd.DataFrame()
    # Gabung Close saham dan Close benchmark by date
    s = df_stock[["Close"]].rename(columns={"Close": "Price"})
    b = df_bench[["Close"]].rename(columns={"Close": "Bench"})
    j = s.join(b, how="inner")
    if j.empty or len(j) < period_sma:
        return pd.DataFrame()
    j["Ratio"] = j["Price"] / j["Bench"].replace(0, np.nan)
    j = j.dropna(subset=["Ratio"])
    j["Ratio_SMA"] = j["Ratio"].rolling(period_sma).mean()
    j["Mansfield_RS"] = ((j["Ratio"] / j["Ratio_SMA"]) - 1) * 10
    return j[["Price", "Bench", "Ratio", "Ratio_SMA", "Mansfield_RS"]].dropna(how="all")


# --- Seasonality: Probabilitas Bulanan (Win Rate & Rata-rata Return) ---
def compute_seasonality(df: pd.DataFrame, min_years: int = 5) -> dict:
    """
    Analisis musiman: monthly returns, rata-rata return per bulan (Jan-Des),
    win rate (% bulan positif) per bulan. Data minimal min_years tahun.
    Untuk heatmap: matrix (tahun x bulan) dengan nilai return per bulan.
    """
    if df is None or df.empty or len(df) < 252 * min_years:  # ~1 tahun trading days
        return {
            "monthly_returns": None,
            "avg_return_by_month": None,
            "win_rate_by_month": None,
            "heatmap_df": None,
            "years": [],
        }
    # Resample ke bulanan: ambil Close terakhir tiap bulan
    close = df["Close"].resample("ME").last().dropna()
    monthly_ret = close.pct_change().dropna()
    if monthly_ret.empty:
        return {
            "monthly_returns": None,
            "avg_return_by_month": None,
            "win_rate_by_month": None,
            "heatmap_df": None,
            "years": [],
        }
    # Rata-rata return per bulan (1-12)
    by_month = monthly_ret.groupby(monthly_ret.index.month)
    avg_return_by_month = by_month.mean()
    win_rate_by_month = by_month.apply(lambda x: (x > 0).mean() * 100)
    # Heatmap: baris = tahun, kolom = bulan (1-12), nilai = return bulan itu
    monthly_ret_flat = monthly_ret.reset_index()
    monthly_ret_flat.columns = ["Date", "Return"]
    monthly_ret_flat["year"] = monthly_ret_flat["Date"].dt.year
    monthly_ret_flat["month"] = monthly_ret_flat["Date"].dt.month
    pivot = monthly_ret_flat.pivot_table(index="year", columns="month", values="Return", aggfunc="first")
    heatmap_df = pivot.reindex(columns=range(1, 13))
    return {
        "monthly_returns": monthly_ret,
        "avg_return_by_month": avg_return_by_month,
        "win_rate_by_month": win_rate_by_month,
        "heatmap_df": heatmap_df,
        "years": sorted(monthly_ret.index.year.unique().tolist()),
    }
