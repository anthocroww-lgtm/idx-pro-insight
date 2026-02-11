# IDX-Pro Insight

Aplikasi analisis saham IDX (Streamlit): Teknikal, Fundamental, Bandarmology, Korelasi Makro. Login & Portofolio Cloud via Firebase.

**Versi:** 1.3.0 (lihat [DEPLOY.md](DEPLOY.md) untuk deploy ke web; Android pakai WebView ke URL yang sama).

## Setup

1. **Virtual environment (opsional):**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

2. **Install dependensi:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Konfigurasi Firebase (opsional, untuk Login & Firestore):**
   - Copy `.streamlit/secrets.toml.example` ke `.streamlit/secrets.toml`
   - Isi `firebase_auth.api_key` (Web API Key dari Firebase Console)
   - Isi `[firebase]` dari JSON Service Account (Firestore)

4. **Gemini AI (opsional, untuk Tanya Gemini):**
   - Di `.streamlit/secrets.toml` isi `[gemini]` → `api_key` (dapatkan gratis di [Google AI Studio](https://aistudio.google.com/apikey)).

5. **Jalankan aplikasi:**
   ```bash
   python -m streamlit run app.py
   ```
   (Di Windows gunakan `python -m streamlit run app.py` jika perintah `streamlit` tidak dikenali.)

Tanpa Firebase, aplikasi tetap jalan; hanya fitur Login dan Portofolio Cloud yang tidak aktif. Tanpa Gemini API key, menu "Tanya Gemini" akan meminta Anda menambahkan key.

---

## Update ke web & Android

- **Web:** Setelah mengubah kode, push ke repo yang dipakai Streamlit Cloud (atau server Anda). Aplikasi web akan otomatis rebuild dan menampilkan versi terbaru (tab browser: "IDX-Pro Insight Terminal (v1.3.0)").
- **Android Studio:** Aplikasi Android hanya menampilkan URL web di WebView. Tidak perlu update APK untuk konten baru — cukup deploy web, lalu buka kembali app Android atau refresh; yang tampil adalah versi web terbaru. Jika Anda mengubah URL deploy, ganti `appUrl` di `MainActivity.kt` (lihat folder `android_webview_ref`).

---

## Sebelum online (deploy)

Panduan rinci: **[DEPLOY.md](DEPLOY.md)** (referensi teknis). **Langkah sangat detail (step-by-step):** **[LANGKAH_DETAIL.md](LANGKAH_DETAIL.md)** — dari persiapan Git, deploy Streamlit Cloud, atur Firebase, sampai verifikasi.

- **Secrets:** Buat `.streamlit/secrets.toml` dari `.streamlit/secrets.toml.example`, isi Firebase Auth `api_key`, Service Account `[firebase]`, dan opsional `[gemini].api_key`. Jangan commit `secrets.toml` ke Git.
- **Firebase:** Aktifkan Email/Password di Authentication; atur Firestore Rules; tambah domain deploy di Authorized domains.
- **Jalankan:** `py -m streamlit run app.py` (Windows) atau `python -m streamlit run app.py`.
- **Disclaimer:** Aplikasi untuk edukasi; rekomendasi bukan saran investasi—risiko ada di pemodal.
