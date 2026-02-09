"""
Mesin analisis saham IDX: Teknikal, Fundamental, Bandarmology, Korelasi Makro.
Menggunakan yfinance + pandas (tanpa pandas_ta agar kompatibel Python 3.14).
"""
import pandas as pd
import yfinance as yf
import numpy as np

# Saham LQ45 (contoh) untuk Big Caps / Foreign Flow proxy
LQ45_TICKERS = {
    "BBCA", "BBRI", "BMRI", "BNGA", "BBNI", "ASII", "GOTO", "TLKM", "ICBP", "UNVR",
    "GGRM", "HMSP", "INDF", "JPFA", "KLBF", "MNCN", "MRAT", "SIDO", "TOWR", "WIKA",
    "ADRO", "ANTM", "BRPT", "CPIN", "INCO", "ITMG", "MDKA", "PTBA", "PSSI", "SMGR",
    "AKRA", "BUKA", "EMTK", "EXCL", "GOTO", "BREN", "BUMI", "CTRA", "HRUM", "PGAS",
}

# Mapping sektor -> simbol komoditas/makro untuk korelasi
SECTOR_MACRO = {
    "energi": ["ADRO", "PTBA", "ITMG", "ARII", "BUMI", "BYAN", "DOID", "HRUM", "PGAS", "AKRA"],
    "tambang": ["ANTM", "MDKA", "INCO", "BRMS", "TINS", "SMMT", "TOPS"],
    "bank": ["BBCA", "BBRI", "BMRI", "BNGA", "BBNI", "BTPN", "BJBR", "CIMB", "NISP", "MAYA"],
}


def ensure_jk(ticker: str) -> str:
    """Pastikan kode saham pakai suffix .JK untuk IDX."""
    t = ticker.strip().upper()
    if not t.endswith(".JK"):
        t = f"{t}.JK"
    return t


def get_history(ticker: str, period: str = "1y") -> pd.DataFrame:
    """Ambil historis harga dari yfinance. Tangani ketika yfinance mengembalikan None atau error."""
    t = ensure_jk(ticker)
    try:
        obj = yf.Ticker(t)
        df = obj.history(period=period, auto_adjust=True)
        if df is None or df.empty or len(df) < 30:
            return pd.DataFrame()
        return df
    except (TypeError, AttributeError, KeyError, Exception):
        return pd.DataFrame()


# --- A. TEKNIKAL & TREN (tanpa pandas_ta: murni pandas/numpy) ---
def _rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """RSI(14) dari harga penutupan."""
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    avg_gain = gain.rolling(period, min_periods=period).mean()
    avg_loss = loss.rolling(period, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Tambahkan Bollinger Bands (20,2), MA20, MA50, MA200, RSI(14)."""
    if df.empty or len(df) < 50:
        return df
    df = df.copy()
    close = df["Close"]
    # Moving Averages
    df["MA20"] = close.rolling(20).mean()
    df["MA50"] = close.rolling(50).mean()
    df["MA200"] = close.rolling(200).mean()
    # Bollinger Bands (20, 2)
    df["BB_mid"] = close.rolling(20).mean()
    std20 = close.rolling(20).std()
    df["BB_upper"] = df["BB_mid"] + 2 * std20
    df["BB_lower"] = df["BB_mid"] - 2 * std20
    # RSI(14)
    df["RSI"] = _rsi(close, 14)
    return df


def get_technical_summary(df: pd.DataFrame) -> dict:
    """
    Ringkasan teknikal: tren (Strong Uptrend / Downtrend), RSI (Oversold/Overbought),
    Bollinger Squeeze (lebar pita mengecil).
    """
    if df.empty or len(df) < 50:
        return {"trend": "-", "rsi_label": "-", "squeeze": False, "details": []}

    row = df.iloc[-1]
    close = row["Close"]
    details = []

    # Trend
    ma20 = row.get("MA20")
    ma50 = row.get("MA50")
    ma200 = row.get("MA200")
    if pd.notna(ma20) and pd.notna(ma50) and pd.notna(ma200):
        if close > ma20 > ma50 > ma200:
            trend = "Strong Uptrend (Cocok trend following)"
            details.append("Harga > MA20 > MA50 > MA200")
        elif close < ma200:
            trend = "Downtrend / Bearish (Hati-hati)"
            details.append("Harga di bawah MA200")
        else:
            trend = "Sideways / Consolidation"
            details.append("Tren tidak jelas")
    else:
        trend = "Data MA belum cukup"
        details.append("Perlu lebih banyak data historis")

    # RSI
    rsi = row.get("RSI")
    if pd.notna(rsi):
        if rsi < 30:
            rsi_label = "Oversold / Diskon (Potensi Rebound)"
            details.append(f"RSI {rsi:.1f} - zona oversold")
        elif rsi > 70:
            rsi_label = "Overbought / Mahal (Rawan Profit Taking)"
            details.append(f"RSI {rsi:.1f} - zona overbought")
        else:
            rsi_label = f"Netral (RSI {rsi:.1f})"
            details.append(f"RSI {rsi:.1f}")
    else:
        rsi_label = "-"
        details.append("RSI belum dihitung")

    # Bollinger Squeeze: bandwidth mengecil (standar deviasi 20 hari terakhir dari lebar pita)
    squeeze = False
    if "BB_upper" in df.columns and "BB_lower" in df.columns:
        df["BB_width"] = (df["BB_upper"] - df["BB_lower"]) / df["BB_mid"].replace(0, np.nan)
        if len(df) >= 20:
            recent_width = df["BB_width"].iloc[-5:].mean()
            older_width = df["BB_width"].iloc[-20:-5].mean()
            if older_width > 0 and recent_width < older_width * 0.9:
                squeeze = True
                details.append("Bollinger Squeeze terdeteksi - pita menyempit, siap potensi breakout")

    return {
        "trend": trend,
        "rsi_label": rsi_label,
        "squeeze": squeeze,
        "details": details,
        "last_rsi": float(rsi) if pd.notna(rsi) else None,
        "last_close": float(close),
    }


# --- B. BANDARMOLOGY (VPA) ---
def get_bandarmology_signal(df: pd.DataFrame, ticker: str) -> dict:
    """
    Volume Price Analysis: Akumulasi (harga naik + volume > 2x rata-rata),
    Distribusi (harga turun/stagnan + volume tinggi). LQ45 = proksi aliran dana besar.
    """
    if df.empty or len(df) < 25:
        return {"signal": "-", "big_cap_flow": False, "description": "Data belum cukup"}

    sym = ticker.replace(".JK", "").upper()
    df = df.copy()
    df["Vol_Avg20"] = df["Volume"].rolling(20).mean()
    df["Price_Change"] = df["Close"].pct_change()
    row = df.iloc[-1]
    vol = row["Volume"]
    avg_vol = row["Vol_Avg20"]
    price_chg = row["Price_Change"]

    signal = "-"
    desc = []

    if pd.notna(avg_vol) and avg_vol > 0:
        if vol >= 2 * avg_vol:
            if pd.notna(price_chg) and price_chg > 0:
                signal = "Akumulasi Bandar Kuat"
                desc.append("Harga naik dengan volume > 2x rata-rata 20 hari - indikasi buying pressure institusi.")
            elif pd.notna(price_chg) and price_chg <= 0:
                signal = "Distribusi / Buangan Bandar"
                desc.append("Harga turun/stagnan dengan volume tinggi - waspada selling pressure.")
            else:
                signal = "Volume Tinggi"
                desc.append("Volume sangat tinggi; perhatikan arah harga berikutnya.")
        else:
            signal = "Volume Normal"
            desc.append("Volume dalam batas rata-rata.")
    else:
        desc.append("Rata-rata volume belum tersedia.")

    big_cap = sym in LQ45_TICKERS
    if big_cap:
        desc.append("Saham LQ45 - volume dapat menjadi proksi aliran dana institusi/asing.")

    # Volume Z-Score: (Volume Hari Ini - Rata2 Volume 20d) / Std Dev Volume 20d
    volume_zscore = None
    volume_spike_extreme = False
    if "Volume" in df.columns and len(df) >= 20:
        vol_series = df["Volume"].iloc[-21:-1]  # 20 hari sebelum hari ini
        mean_vol = vol_series.mean()
        std_vol = vol_series.std()
        if pd.notna(mean_vol) and pd.notna(std_vol) and std_vol > 0:
            volume_zscore = float((vol - mean_vol) / std_vol)
            if volume_zscore > 3:
                volume_spike_extreme = True

    return {
        "signal": signal,
        "big_cap_flow": big_cap,
        "description": " ".join(desc),
        "volume_ratio": float(vol / avg_vol) if pd.notna(avg_vol) and avg_vol > 0 else None,
        "volume_zscore": volume_zscore,
        "volume_spike_extreme": volume_spike_extreme,
    }


# --- C. FUNDAMENTAL & VALUASI ---
def get_fundamental_summary(ticker: str) -> dict:
    """
    Dari yfinance ticker.info: PER, PBV, ROE, DER.
    Hidden Gem: PER < 10 dan ROE > 15%.
    High Debt Risk: DER > 1.5 (kecuali bank).
    """
    t = ensure_jk(ticker)
    obj = yf.Ticker(t)
    info = obj.info
    if not info or info.get("regularMarketPrice") is None:
        return {"error": "Data fundamental tidak tersedia", "per": None, "pbv": None, "roe": None, "der": None}

    per = info.get("trailingPE") or info.get("forwardPE")
    pbv = info.get("priceToBook")
    roe = info.get("returnOnEquity")
    if roe is not None and roe <= 1:
        roe = roe * 100  # kadang dalam desimal
    total_debt = info.get("totalDebt") or 0
    equity = info.get("totalStockholderEquity") or 1
    der = total_debt / equity if equity and equity != 0 else None

    sector = (info.get("sector") or "").lower()
    industry = (info.get("industry") or "").lower()
    is_bank = "bank" in sector or "bank" in industry or "financial" in sector

    labels = []
    if per is not None and roe is not None:
        if per < 10 and roe > 15:
            labels.append("Hidden Gem (Murah & Bagus)")
    if der is not None and not is_bank and der > 1.5:
        labels.append("High Debt Risk (DER > 1.5)")
    if per is not None and per > 25 and not labels:
        labels.append("Valuasi tinggi (PER > 25)")

    return {
        "error": None,
        "per": per,
        "pbv": pbv,
        "roe": roe,
        "der": der,
        "labels": labels,
        "company_name": info.get("shortName") or info.get("longName") or ticker,
        "sector": info.get("sector") or "-",
        "industry": info.get("industry") or "-",
    }


# --- D. KORELASI MAKRO ---
def get_macro_symbol(ticker: str) -> tuple:
    """Return (symbol_yfinance, label) untuk korelasi makro berdasarkan sektor."""
    sym = ticker.replace(".JK", "").upper()
    for sector, tickers in SECTOR_MACRO.items():
        if sym in tickers:
            if sector == "energi":
                return "CL=F", "Minyak (CL=F)"
            if sector == "tambang":
                return "GC=F", "Emas (GC=F)"
            if sector == "bank":
                return "IDR=X", "Kurs USD/IDR (IDR=X)"
    return None, None


def get_macro_correlation_data(ticker: str, period: str = "6mo") -> pd.DataFrame:
    """Ambil data harga komoditas/makro untuk perbandingan."""
    macro_sym, _ = get_macro_symbol(ticker)
    if not macro_sym:
        return pd.DataFrame()
    try:
        return yf.Ticker(macro_sym).history(period=period, auto_adjust=True)
    except Exception:
        return pd.DataFrame()


def get_macro_narrative(ticker: str, stock_df: pd.DataFrame, macro_df: pd.DataFrame) -> str:
    """
    Narasi korelasi: misal "Harga ANTM turun, tapi Emas Global naik. Divergensi Positif (Peluang)."
    """
    if macro_df.empty or stock_df.empty or len(stock_df) < 5 or len(macro_df) < 5:
        return ""

    _, macro_label = get_macro_symbol(ticker)
    if not macro_label:
        return ""

    # Sederhana: perubahan 1 bulan terakhir
    stock_recent = stock_df["Close"].iloc[-1] / stock_df["Close"].iloc[-min(22, len(stock_df))] - 1
    macro_recent = macro_df["Close"].iloc[-1] / macro_df["Close"].iloc[-min(22, len(macro_df))] - 1

    stock_dir = "naik" if stock_recent > 0.02 else ("turun" if stock_recent < -0.02 else "stagnan")
    macro_dir = "naik" if macro_recent > 0.02 else ("turun" if macro_recent < -0.02 else "stagnan")

    sym = ticker.replace(".JK", "")
    if stock_dir == "turun" and macro_dir == "naik":
        return f"Harga {sym} turun, tapi {macro_label} sedang naik. Ada Divergensi Positif (peluang koreksi ke atas)."
    if stock_dir == "naik" and macro_dir == "turun":
        return f"Harga {sym} naik sementara {macro_label} turun. Waspada divergensi negatif."
    if stock_dir == macro_dir and macro_dir != "stagnan":
        return f"Harga {sym} dan {macro_label} bergerak searah ({macro_dir}) - korelasi positif."
    return f"Konteks makro: {macro_label}. Saham {sym} ({stock_dir}), komoditas ({macro_dir})."


# --- KEY LEVELS (52w, 20d - untuk telaah mendalam) ---
def get_key_levels(df: pd.DataFrame) -> dict:
    """
    Level penting: 52 minggu High/Low, 20 hari High/Low.
    Jarak saat ini ke masing-masing (%). Berguna untuk support/resistance dan buy on dip.
    """
    if df is None or df.empty or "Close" not in df.columns:
        return {}
    close = df["Close"].iloc[-1]
    high_52 = df["High"].iloc[-252:].max() if len(df) >= 252 else df["High"].max()
    low_52 = df["Low"].iloc[-252:].min() if len(df) >= 252 else df["Low"].min()
    high_20 = df["High"].iloc[-20:].max() if len(df) >= 20 else df["High"].max()
    low_20 = df["Low"].iloc[-20:].min() if len(df) >= 20 else df["Low"].min()
    def pct(a, b):
        return (close / b - 1) * 100 if b and b > 0 else None
    return {
        "high_52w": high_52, "low_52w": low_52,
        "high_20d": high_20, "low_20d": low_20,
        "close": close,
        "pct_from_52w_high": pct(close, high_52),
        "pct_from_52w_low": pct(close, low_52),
        "pct_from_20d_high": pct(close, high_20),
        "pct_from_20d_low": pct(close, low_20),
    }


# --- ON-BALANCE VOLUME (konfirmasi volume) ---
def get_obv(df: pd.DataFrame) -> pd.Series:
    """On-Balance Volume: kumulatif +Volume jika Close naik, -Volume jika Close turun."""
    if df is None or df.empty or "Volume" not in df.columns or "Close" not in df.columns:
        return pd.Series(dtype=float)
    close = df["Close"]
    vol = df["Volume"].fillna(0)
    direction = np.where(close > close.shift(1), 1, np.where(close < close.shift(1), -1, 0))
    obv = (vol * direction).cumsum()
    return obv


# --- SUPPORT & RESISTANCE (swing high/low sederhana) ---
def get_support_resistance(df: pd.DataFrame, lookback: int = 20) -> dict:
    """
    Support/Resistance dari swing high dan swing low (local max/min) dalam lookback.
    Berguna untuk area entry dan target.
    """
    if df is None or len(df) < lookback:
        return {"support": [], "resistance": []}
    high = df["High"].iloc[-lookback:]
    low = df["Low"].iloc[-lookback:]
    res = high.nlargest(3).tolist()
    sup = low.nsmallest(3).tolist()
    return {"support": sorted(set(sup)), "resistance": sorted(set(res), reverse=True)}


# --- RINGKASAN TELAAH (narasi singkat) ---
def get_insight_summary(technical: dict, bandar: dict, fundamental: dict, plan: dict, key_levels: dict) -> str:
    """
    Gabungkan sinyal teknikal, bandar, fundamental jadi 1–2 kalimat ringkasan.
    Membantu user menelaah saham secara mendalam dengan cepat.
    """
    parts = []
    if technical.get("trend"):
        parts.append(technical["trend"].split("(")[0].strip())
    if technical.get("last_rsi") is not None:
        r = technical["last_rsi"]
        if r < 30:
            parts.append("RSI oversold, potensi rebound.")
        elif r > 70:
            parts.append("RSI overbought, hati-hati profit taking.")
    if bandar.get("signal") and "Akumulasi" in str(bandar["signal"]):
        parts.append("Volume mengindikasikan akumulasi.")
    elif bandar.get("signal") and "Distribusi" in str(bandar["signal"]):
        parts.append("Volume mengindikasikan distribusi.")
    if fundamental.get("labels"):
        for lbl in fundamental["labels"]:
            if "Hidden Gem" in lbl:
                parts.append("Valuasi menarik (Hidden Gem).")
            elif "High Debt" in lbl:
                parts.append("Perhatikan utang tinggi.")
    if key_levels.get("pct_from_52w_high") is not None:
        d = key_levels["pct_from_52w_high"]
        if -15 <= d <= -5:
            parts.append("Saham dalam zona koreksi wajar dari ATH 52w.")
    if not parts:
        return "Gunakan indikator di atas untuk keputusan."
    return " ".join(parts[:4])


# --- KESIMPULAN & REKOMENDASI (saran beli/tidak + range harga) ---
def get_recommendation(
    ticker: str,
    df: pd.DataFrame,
    technical: dict,
    bandar: dict,
    fundamental: dict,
    plan: dict,
    key_levels: dict,
) -> dict:
    """
    Beri saran: cocok untuk Day Trading / Swing / Invest jangka panjang atau tidak disarankan,
    beserta range harga beli (misal 1000–1080) dan target, atau alasan tunggu koreksi.
    Mengurangi risiko beli di harga terlalu tinggi dan mengarahkan ke area support.
    """
    out = {
        "style": "not_recommended",
        "style_label": "Tidak disarankan beli saat ini",
        "buy_range_low": None,
        "buy_range_high": None,
        "target_low": None,
        "target_high": None,
        "avoid_reason": None,
        "summary": "",
    }
    if df is None or df.empty or not plan.get("support") or not plan.get("resistance"):
        out["summary"] = "Data tidak cukup untuk rekomendasi."
        return out

    close = float(df["Close"].iloc[-1])
    support = plan["support"]
    resistance = plan["resistance"]
    rsi = technical.get("last_rsi")
    high_52 = key_levels.get("high_52w")
    low_52 = key_levels.get("low_52w")
    pct_from_52w_high = key_levels.get("pct_from_52w_high")
    per = fundamental.get("per")
    ma20 = df["MA20"].iloc[-1] if "MA20" in df.columns and len(df) >= 20 else None
    ma200 = df["MA200"].iloc[-1] if "MA200" in df.columns and len(df) >= 200 else None

    # Range beli wajar: sekitar support sampai +2–3% (area akumulasi)
    buy_low = round(support * 0.98, 0)
    buy_high = round(support * 1.03, 0) if support else round(close * 0.98, 0)
    target_low = round(resistance * 0.98, 0)
    target_high = round(resistance * 1.02, 0)

    # --- Cek kondisi "tidak disarankan" / harga terlalu tinggi ---
    if rsi is not None and rsi > 70:
        out["avoid_reason"] = f"RSI overbought ({rsi:.0f}). Harga rawan koreksi."
        out["summary"] = f"Tidak disarankan beli di harga saat ini (Rp {close:,.0f}). Tunggu koreksi ke area Rp {buy_low:,.0f} – Rp {buy_high:,.0f}."
        out["buy_range_low"], out["buy_range_high"] = buy_low, buy_high
        out["target_low"], out["target_high"] = target_low, target_high
        return out
    if close >= resistance * 0.98:
        out["avoid_reason"] = "Harga mendekati resistance. Risk/reward tidak menguntungkan."
        out["summary"] = f"Tunggu koreksi ke zona beli Rp {buy_low:,.0f} – Rp {buy_high:,.0f}. Target area: Rp {target_low:,.0f} – Rp {target_high:,.0f}."
        out["buy_range_low"], out["buy_range_high"] = buy_low, buy_high
        out["target_low"], out["target_high"] = target_low, target_high
        return out
    if per is not None and per > 25 and pct_from_52w_high is not None and pct_from_52w_high > -5:
        out["avoid_reason"] = f"Valuasi tinggi (PER {per:.0f}) dan harga dekat 52w high."
        out["summary"] = f"Lebih aman tunggu koreksi ke Rp {buy_low:,.0f} – Rp {buy_high:,.0f} untuk entry jangka panjang."
        out["buy_range_low"], out["buy_range_high"] = buy_low, buy_high
        out["target_low"], out["target_high"] = target_low, target_high
        return out

    # --- Cocok Day Trading: volatil, volume spike, dekat support ---
    vol_ratio = bandar.get("volume_ratio") or 0
    if vol_ratio >= 1.2 and rsi is not None and 35 < rsi < 70 and support and close <= support * 1.05:
        out["style"] = "day_trade"
        out["style_label"] = "Cocok untuk Day Trading (scalping)"
        out["buy_range_low"], out["buy_range_high"] = buy_low, buy_high
        out["target_low"], out["target_high"] = target_low, target_high
        out["summary"] = f"Volume mendukung. Area beli: Rp {buy_low:,.0f} – Rp {buy_high:,.0f}. Target: Rp {target_low:,.0f} – Rp {target_high:,.0f}. Gunakan stop loss ketat."
        return out

    # --- Cocok Swing: uptrend, RSI netral, harga di atas MA20 ---
    if ma20 and close > ma20 and rsi is not None and 40 <= rsi <= 65:
        out["style"] = "swing"
        out["style_label"] = "Cocok untuk Swing Trading (1–2 minggu)"
        out["buy_range_low"] = round(support, 0)
        out["buy_range_high"] = round(ma20 * 1.02, 0) if ma20 else buy_high
        out["target_low"], out["target_high"] = target_low, target_high
        out["summary"] = f"Uptrend jangka pendek. Area beli: Rp {out['buy_range_low']:,.0f} – Rp {out['buy_range_high']:,.0f}. Target: Rp {target_low:,.0f} – Rp {target_high:,.0f}."
        return out

    # --- Cocok Invest jangka panjang: di atas MA200, koreksi 5–15% dari 52w high ---
    if ma200 and close > ma200 and pct_from_52w_high is not None and -15 <= pct_from_52w_high <= -3:
        out["style"] = "invest"
        out["style_label"] = "Cocok untuk Investasi Jangka Panjang"
        out["buy_range_low"] = round(support, 0)
        out["buy_range_high"] = round(close * 1.02, 0)
        out["target_low"] = round(high_52 * 0.95, 0) if high_52 else target_low
        out["target_high"] = round(high_52 * 1.05, 0) if high_52 else target_high
        out["summary"] = f"Buy on dip dari 52w high. Area akumulasi: Rp {out['buy_range_low']:,.0f} – Rp {out['buy_range_high']:,.0f}. Target jangka panjang mendekati 52w high."
        return out

    # --- Default: saran hati-hati dengan range ---
    out["style"] = "neutral"
    out["style_label"] = "Netral – perhatikan area support sebelum beli"
    out["buy_range_low"], out["buy_range_high"] = buy_low, buy_high
    out["target_low"], out["target_high"] = target_low, target_high
    out["summary"] = f"Disarankan entry di area Rp {buy_low:,.0f} – Rp {buy_high:,.0f}. Target: Rp {target_low:,.0f} – Rp {target_high:,.0f}. Pastikan stop loss."
    return out


# --- TRADING PLAN (Support / Resistance / SL) ---
def get_trading_plan(df: pd.DataFrame) -> dict:
    """
    Rencana trading: Buy Area (support / lower BB), Target (resistance / upper BB),
    Stop Loss 3-5% di bawah support.
    """
    if df.empty or len(df) < 20:
        return {"buy_area": "-", "target_profit": "-", "stop_loss": "-", "support": None, "resistance": None, "stop_loss_value": None, "current_price": None}
    row = df.iloc[-1]
    close = float(row["Close"])
    if close <= 0:
        return {"buy_area": "-", "target_profit": "-", "stop_loss": "-", "support": None, "resistance": None, "stop_loss_value": None, "current_price": close}

    support = float(row["BB_lower"]) if "BB_lower" in df.columns and pd.notna(row.get("BB_lower")) else (close * 0.97 if close > 0 else 0)
    resistance = float(row["BB_upper"]) if "BB_upper" in df.columns and pd.notna(row.get("BB_upper")) else close * 1.03

    # Stop loss 3-5% di bawah support
    sl_pct = 0.04
    stop_loss = support * (1 - sl_pct)

    return {
        "buy_area": f"Rp {support:,.0f} (Support / Lower Bollinger)",
        "target_profit": f"Rp {resistance:,.0f} (Resistance / Upper Bollinger)",
        "stop_loss": f"Rp {stop_loss:,.0f} (≈4% di bawah support)",
        "support": support,
        "resistance": resistance,
        "stop_loss_value": stop_loss,
        "current_price": close,
    }


# --- FULL ANALYSIS ---
def run_full_analysis(ticker: str, period: str = "1y") -> dict:
    """
    Jalankan semua analisis dan return satu dict untuk UI.
    """
    t = ensure_jk(ticker)
    df = get_history(t, period)
    if df.empty:
        return {
            "success": False,
            "error": "Data historis tidak tersedia. Cek kode saham dan koneksi.",
            "ticker": t,
        }

    df = add_technical_indicators(df)
    technical = get_technical_summary(df)
    bandar = get_bandarmology_signal(df, t)
    fundamental = get_fundamental_summary(t)
    plan = get_trading_plan(df)

    macro_df = get_macro_correlation_data(t, "6mo")
    macro_narrative = get_macro_narrative(t, df, macro_df)
    key_levels = get_key_levels(df)
    obv = get_obv(df)
    support_resistance = get_support_resistance(df, 20)
    insight_summary = get_insight_summary(technical, bandar, fundamental, plan, key_levels)
    recommendation = get_recommendation(t, df, technical, bandar, fundamental, plan, key_levels)

    # Stempel tanggal data terakhir (untuk transparansi bahan keputusan)
    last_date = df.index[-1] if len(df) else None
    data_as_of = last_date.strftime("%d/%m/%Y") if hasattr(last_date, "strftime") else (str(last_date)[:10] if last_date else None)
    return {
        "success": True,
        "ticker": t,
        "df": df,
        "technical": technical,
        "bandarmology": bandar,
        "fundamental": fundamental,
        "trading_plan": plan,
        "macro_df": macro_df,
        "macro_narrative": macro_narrative,
        "key_levels": key_levels,
        "obv": obv,
        "support_resistance": support_resistance,
        "insight_summary": insight_summary,
        "recommendation": recommendation,
        "data_as_of": data_as_of,
        "trading_days_count": len(df),
    }
