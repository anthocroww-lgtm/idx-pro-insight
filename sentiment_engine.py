"""
Sentimen Engine: analisis sentimen berbasis leksikon bahasa Indonesia.
Menggunakan kamus kata kunci pasar modal untuk skor Bullish/Bearish dari teks berita.
Tanpa API berita berbayar: user paste judul/teks berita, skor dihitung dari kata kunci.
"""
import re

# Kamus kata kunci pasar modal Indonesia (positif vs negatif)
POS_WORDS = [
    "laba", "naik", "untung", "cuan", "dividen", "melonjak", "meroket",
    "ekspansi", "akuisisi", "buyback", "tertinggi", "positif", "tumbuh",
    "kerjasama", "proyek", "rekor", "optimis", "kuat", "rally", "surge",
]

NEG_WORDS = [
    "rugi", "turun", "anjlok", "longsor", "boncos", "utang", "pailit",
    "suspensi", "gagal", "negatif", "koreksi", "melemah", "gugatan", "phk",
    "resesi", "bangkrut", "sanksi", "tuntutan", "turun", "jeblok",
]


def normalize_text(text: str) -> str:
    """Lowercase dan hapus karakter non-alfanumerik untuk matching kata."""
    if not text or not isinstance(text, str):
        return ""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return " ".join(text.split())


def count_words(text: str, word_list: list) -> int:
    """Hitung berapa banyak kata dari word_list yang muncul di text."""
    norm = normalize_text(text)
    if not norm:
        return 0
    words = set(norm.split())
    return sum(1 for w in word_list if w in words or w in norm)


def sentiment_score(text: str) -> dict:
    """
    Hitung skor sentimen: (Jumlah Kata Positif - Jumlah Kata Negatif).
    Return dict: score (-N sampai +N), pos_count, neg_count, label (Bearish/Netral/Bullish).
    """
    pos_count = count_words(text, POS_WORDS)
    neg_count = count_words(text, NEG_WORDS)
    score = pos_count - neg_count
    if score > 0:
        label = "Bullish"
    elif score < 0:
        label = "Bearish"
    else:
        label = "Netral"
    return {
        "score": score,
        "pos_count": pos_count,
        "neg_count": neg_count,
        "label": label,
    }


def gauge_value(score: int, min_score: int = -5, max_score: int = 5) -> float:
    """
    Normalisasi skor ke rentang 0–1 untuk Gauge Meter.
    0 = Bearish (merah), 0.5 = Netral, 1 = Bullish (hijau).
    """
    if max_score <= min_score:
        return 0.5
    x = max(min_score, min(max_score, score))
    return (x - min_score) / (max_score - min_score)
