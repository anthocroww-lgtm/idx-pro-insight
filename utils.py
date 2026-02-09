"""
Helper functions: format angka IDR, tanggal, dan utilitas umum.
Digunakan di seluruh IDX-Pro Insight Terminal.
"""
from datetime import datetime
from typing import Union


def format_idr(value: Union[int, float], decimals: int = 0) -> str:
    """
    Format angka ke string Rupiah Indonesia.
    Contoh: 100000000 -> "Rp 100.000.000"
    """
    if value is None or (isinstance(value, float) and __import__("math").isnan(value)):
        return "-"
    try:
        n = float(value)
        if decimals == 0:
            s = f"{int(round(n)):,}".replace(",", ".")
        else:
            s = f"{n:,.{decimals}f}".replace(",", ".")
        return f"Rp {s}"
    except (TypeError, ValueError):
        return "-"


def format_date(dt, fmt: str = "%d %b %Y") -> str:
    """
    Format datetime/date ke string Indonesia-friendly.
    fmt default: 09 Feb 2025
    """
    if dt is None:
        return "-"
    if hasattr(dt, "strftime"):
        return dt.strftime(fmt)
    try:
        return datetime.fromisoformat(str(dt)).strftime(fmt)
    except Exception:
        return str(dt)


def format_pct(value: Union[int, float], decimals: int = 2) -> str:
    """Format persentase. Contoh: 0.015 -> "1.50%\" """
    if value is None or (isinstance(value, float) and __import__("math").isnan(value)):
        return "-"
    try:
        return f"{float(value) * 100:.{decimals}f}%"
    except (TypeError, ValueError):
        return "-"
