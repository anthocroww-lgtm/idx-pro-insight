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
