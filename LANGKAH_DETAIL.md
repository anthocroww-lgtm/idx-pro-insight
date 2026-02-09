# Langkah Detail — Dari Lokal sampai Online

Panduan ini memecah setiap fase menjadi langkah sangat rinci (step-by-step). Gunakan bersama **DEPLOY.md** untuk referensi teknis (secrets, Firebase, format TOML).

---

## Fase A: Persiapan di komputer Anda

### A.1 Pastikan proyek siap di-push ke GitHub

1. Buka folder proyek di Cursor/VS Code: `C:\Users\user\idx-pro-insight`
2. Buka file **`.gitignore`**, pastikan ada baris:
   - `.streamlit/secrets.toml`
3. **Jangan** menambahkan `secrets.toml` ke Git. Cek dengan:
   - Buka terminal di folder proyek
   - Jalankan: `git status`
   - Pastikan **`.streamlit/secrets.toml`** tidak muncul di daftar "Changes to be committed" atau "Untracked files" yang akan di-commit. Jika muncul, pastikan `.gitignore` benar dan jangan `git add` file itu.

### A.2 Inisialisasi Git dan push ke GitHub (jika belum)

1. Jika belum ada Git:
   - Terminal: `git init`
   - Buat file `.gitignore` jika belum (isi minimal: `.streamlit/secrets.toml`, `__pycache__/`, `venv/`)
2. Buat repo baru di GitHub:
   - Buka [github.com](https://github.com) → Login → **New repository**
   - Repository name: misalnya `idx-pro-insight`
   - **Jangan** centang "Add a README" jika Anda sudah punya file di folder
   - Klik **Create repository**
3. Di terminal (di folder proyek):
   ```bash
   git remote add origin https://github.com/USERNAME/idx-pro-insight.git
   ```
   Ganti `USERNAME` dengan username GitHub Anda.
4. Tambahkan dan push:
   ```bash
   git add .
   git status
   ```
   Pastikan **tidak ada** `.streamlit/secrets.toml` di daftar. Jika ada, jalankan:
   ```bash
   git reset HEAD .streamlit/secrets.toml
   ```
   Lalu:
   ```bash
   git commit -m "IDX-Pro Insight - siap deploy"
   git branch -M main
   git push -u origin main
   ```

---

## Fase B: Streamlit Cloud — Deploy aplikasi

### B.1 Daftar / login Streamlit Cloud

1. Buka browser, ke: **https://share.streamlit.io**
2. Klik **Sign up** atau **Log in**
3. Pilih **Continue with GitHub**
4. Autorisasi jika diminta (Grant access), sampai Anda masuk ke dashboard Streamlit Cloud

### B.2 Buat app baru

1. Di dashboard, klik tombol **"New app"**
2. Isi form:
   - **Repository:** pilih `USERNAME/idx-pro-insight` (atau nama repo Anda). Jika tidak muncul, klik **"Configure GitHub account"** dan beri akses ke repo.
   - **Branch:** pilih `main` (atau branch yang Anda pakai)
   - **Main file path:** ketik `app.py`
   - **App URL (opsional):** bisa dikosongkan; Streamlit akan buat URL otomatis, misalnya `https://idx-pro-insight-xxx.streamlit.app`
3. **Jangan** klik Deploy dulu. Klik **"Advanced settings..."** (atau "Secrets" / tombol serupa di bawah)

### B.3 Isi Secrets di Streamlit Cloud

1. Di **Advanced settings**, cari bagian **"Secrets"** (kotak teks besar)
2. Buka di komputer Anda file: **`C:\Users\user\idx-pro-insight\.streamlit\secrets.toml`**
3. Buka dengan Notepad/Cursor, **select all** (Ctrl+A), **copy** (Ctrl+C)
4. Kembali ke browser, klik di dalam kotak **Secrets**
5. **Paste** (Ctrl+V) isi `secrets.toml` ke kotak tersebut
6. Format harus tetap TOML, contoh:
   ```toml
   [firebase_auth]
   api_key = "AIzaSy..."

   [firebase]
   type = "service_account"
   project_id = "idx-pro-insight"
   ...
   [gemini]
   api_key = "AIzaSy..."
   ```
7. Jangan hapus tanda petik atau nama key. Simpan (tombol **Save** jika ada).

### B.4 Deploy

1. Klik **"Deploy!"** (atau **Deploy**)
2. Tunggu proses build (bisa 2–5 menit). Anda akan melihat log "Building...", "Starting...".
3. Setelah selesai, akan muncul link aplikasi, misalnya:
   - **https://idx-pro-insight-abc123.streamlit.app**
4. **Salin URL ini** (tanpa path tambahan). Anda butuh untuk Fase C (Firebase Authorized domains).
5. Klik link untuk buka app. Cek:
   - Halaman utama terbuka
   - Jika ada error "Firebase tidak dikonfigurasi", artinya Secrets belum terbaca — ulangi B.3 dan redeploy (menu app → Settings → Secrets → Edit → Save → Redeploy).

---

## Fase C: Firebase — Agar login jalan di URL deploy

### C.1 Aktifkan Email/Password (jika belum)

1. Buka **https://console.firebase.google.com**
2. Pilih **project** Anda (misalnya "idx-pro-insight")
3. Di menu kiri: **Build** → **Authentication**
4. Klik tab **"Sign-in method"**
5. Di daftar "Sign-in providers", cari **"Email/Password"**
6. Klik **Email/Password**
7. Nyalakan **"Enable"** (toggle jadi biru)
8. Klik **Save**

### C.2 Tambah domain deploy ke Authorized domains

1. Di Firebase Console, klik **ikon roda gigi** di samping "Project Overview" → **Project settings**
2. Di tab **General**, scroll ke bawah sampai bagian **"Authorized domains"**
3. Anda akan lihat daftar domain (biasanya `localhost` sudah ada)
4. Klik **"Add domain"**
5. Masukkan **hanya subdomain** dari URL Streamlit Anda:
   - Jika URL app Anda: `https://idx-pro-insight-abc123.streamlit.app`
   - Yang Anda masukkan: **`idx-pro-insight-abc123.streamlit.app`** (tanpa `https://`)
6. Klik **Add**
7. Domain akan muncul di daftar. Tidak perlu "Simpan" lagi; langsung tersimpan.

### C.3 Firestore Rules (jika belum)

1. Di Firebase Console: **Build** → **Firestore Database**
2. Klik tab **"Rules"**
3. Ganti isi editor dengan rules berikut (copy-paste):

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /users/{userId}/{document=**} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
  }
}
```

4. Klik **"Publish"**
5. Jika ada peringatan, konfirmasi **Publish**

---

## Fase D: Verifikasi — Tes setelah online

### D.1 Tes akses aplikasi

1. Buka URL app Streamlit (dari B.4) di browser **mode incognito/private** (agar seperti user baru)
2. Pastikan halaman **Dashboard** atau **Peluang Hari Ini** terbuka tanpa error

### D.2 Tes Daftar & Login

1. Di sidebar, klik **"Daftar"** (atau tab Daftar)
2. Isi:
   - Email: alamat email yang valid (belum terdaftar di project ini)
   - Kata sandi: minimal 6 karakter
3. Klik tombol **Daftar**
4. Harus muncul pesan sukses dan Anda "masuk" (nama/email tampil di sidebar)
5. Klik **Logout**
6. Klik **Login**, masukkan email & kata sandi yang sama → harus bisa masuk lagi

Jika error "Firebase Auth tidak dikonfigurasi" → cek Secrets di Streamlit Cloud (B.3).  
Jika error "invalid API key" atau "domain not authorized" → cek C.2 (Authorized domains).

### D.3 Tes Firestore (Watchlist / Jurnal)

1. Setelah login, buka **"Analisis Mendalam"**
2. Input kode saham (mis. BBCA), jalankan analisis
3. Scroll ke **"Kesimpulan & Rekomendasi"**, klik **"Simpan rekomendasi ke Jurnal"**
4. Buka **"Portofolio Saya"** → tab **"Trading Jurnal"**
5. Harus ada entri rekomendasi yang baru disimpan

Jika simpan gagal → cek blok `[firebase]` di Secrets (Service Account) dan C.3 (Firestore Rules).

### D.4 Tes Tanya Gemini (jika API key Gemini diisi)

1. Di sidebar pilih **"Tanya Gemini"**
2. Ketik: "Apa itu RSI?"
3. Klik kirim / Enter
4. Harus ada jawaban dari Gemini (tanpa error 404 atau "model not found")

---

## Fase E: Opsional — Update kode dan redeploy

Setelah Anda mengubah kode di komputer:

1. Simpan semua file
2. Terminal di folder proyek:
   ```bash
   git add .
   git status
   ```
   Pastikan lagi **tidak ada** `secrets.toml`.
3. `git commit -m "Deskripsi perubahan"`
4. `git push origin main`
5. Streamlit Cloud biasanya **auto-redeploy** dalam 1–2 menit. Atau di dashboard Streamlit Cloud: buka app → **"Reboot app"** atau **"Redeploy"**.

---

## Ringkasan urutan (quick reference)

| Urutan | Fase | Yang dilakukan |
|--------|------|----------------|
| 1 | A | Pastikan `.gitignore` ada `secrets.toml`, push kode ke GitHub tanpa secrets |
| 2 | B | Streamlit Cloud: New app → isi repo, branch, `app.py` → Advanced settings → paste Secrets → Deploy |
| 3 | C.1 | Firebase: Authentication → Sign-in method → Email/Password → Enable |
| 4 | C.2 | Firebase: Project settings → Authorized domains → Add domain (xxx.streamlit.app) |
| 5 | C.3 | Firebase: Firestore → Rules → paste rules → Publish |
| 6 | D | Buka URL app → tes Daftar/Login → tes Simpan ke Jurnal → tes Tanya Gemini |

Setelah Fase D lolos, aplikasi Anda sudah online dan siap dipakai.
