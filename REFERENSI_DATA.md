# Referensi Sumber Data Aplikasi

Aplikasi memakai beberapa sumber data. **Struktur dan tampilan tidak berubah**; hanya penarikan data yang punya fallback opsional.

---

## Sumber utama: Yahoo Finance (yfinance)

- **Digunakan untuk:** harga saham IDX (.JK), IHSG (^JKSE), USD/IDR (IDR=X), Minyak WTI (CL=F), Emas (GC=F), Bitcoin (BTC-USD), data fundamental, pemindaian pasar.
- **Tidak perlu API key.** Gratis, bisa rate limit atau gagal sementara.
- **Solusi di aplikasi:** retry + jeda antar request (lihat `macro_engine.py`, `data_engine.py`).

---

## Sumber fallback (opsional): Alpha Vantage

- **Digunakan hanya ketika Yahoo gagal** untuk:
  - **USD/IDR** (kurs)
  - **BTC** (harga Bitcoin)
- **Perlu API key** (gratis, 25 request/hari). Daftar: [Alpha Vantage – API Key](https://www.alphavantage.co/support/#api-key).

### Cara mengaktifkan

1. Dapatkan API key dari [alphavantage.co](https://www.alphavantage.co/support/#api-key).
2. Di **lokal**: tambah di `.streamlit/secrets.toml`:
   ```toml
   [alpha_vantage]
   api_key = "API_KEY_ANDA"
   ```
3. Di **Streamlit Cloud**: Settings → Secrets → tambah blok yang sama.
4. Simpan. Jika Yahoo untuk IDR atau BTC gagal, aplikasi akan mencoba Alpha Vantage otomatis (tanpa mengubah tampilan atau format data).

---

## Ringkas

| Data           | Sumber utama | Fallback (opsional)   |
|----------------|--------------|------------------------|
| Saham IDX, IHSG| Yahoo Finance | -                     |
| USD/IDR        | Yahoo (IDR=X) | Alpha Vantage (FX_DAILY) |
| Minyak, Emas   | Yahoo (CL=F, GC=F) | -                 |
| Bitcoin        | Yahoo (BTC-USD)   | Alpha Vantage (DIGITAL_CURRENCY_DAILY) |

Tanpa konfigurasi tambahan, aplikasi tetap jalan penuh dengan Yahoo Finance. Fallback hanya menambah ketersediaan saat Yahoo sementara gagal.

---

## Pembaruan data lebih cepat

- **TTL cache:** Data pasar (market mood, makro, sektor, saham, scanner) di-cache dengan TTL singkat (2–10 menit). **Grafik intraday 15m** di-cache 5 menit (sinkron dengan data saham). Setelah TTL lewat, data diambil ulang otomatis.
- **Tombol "Refresh data":** Di halaman Analisis Mendalam / Market Overview, gunakan tombol **Refresh data** untuk memaksa pembaruan segera (clear cache lalu muat ulang, termasuk grafik intraday di Peluang Hari Ini). Berguna saat ingin harga/analisis terbaru tanpa menunggu TTL.
- **Keterlambatan sumber:** Yahoo Finance (dan bursa) bisa punya delay 15–20 menit untuk data intraday. Untuk data benar-benar real-time, dibutuhkan sumber berbayar (mis. bursa/Reuters); aplikasi ini mengandalkan Yahoo agar gratis dan stabil.
