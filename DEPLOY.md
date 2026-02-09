# Panduan Go-Live IDX-Pro Insight

Panduan langkah demi langkah untuk menyiapkan aplikasi sebelum di-onlinekan: isi secrets, atur Firebase, dan cara menjalankan.

---

## 1. Isi `.streamlit/secrets.toml` di lingkungan deploy

File ini menyimpan **API key dan credential** yang tidak boleh di-commit ke Git. Di setiap lingkungan (komputer Anda atau server deploy), Anda harus membuat/mengisi file ini.

### 1.1 Membuat file secrets

- **Lokal:** Di folder proyek, pastikan ada folder `.streamlit`. Di dalamnya buat file bernama `secrets.toml`.
- **Copy dari contoh:**  
  Salin isi `.streamlit/secrets.toml.example` ke `.streamlit/secrets.toml`, lalu ganti nilai placeholder dengan nilai asli.

Struktur file (format TOML):

```toml
[firebase_auth]
api_key = "..."

[firebase]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "..."
# ... field lain dari JSON Service Account

[gemini]
api_key = "..."
```

---

### 1.2 Firebase Auth `api_key` (untuk Login & Register)

Digunakan oleh aplikasi untuk login/register lewat Firebase Authentication (REST API).

**Langkah:**

1. Buka [Firebase Console](https://console.firebase.google.com/).
2. Pilih project Anda (atau buat project baru).
3. Klik ikon **roda gigi** di samping "Project Overview" → **Project settings**.
4. Di tab **General**, scroll ke bagian **Your apps**.
5. Jika belum ada app web, klik **Add app** → pilih ikon **Web (</>)**. Isi nickname (misalnya "IDX-Pro Insight") → **Register app**. Anda bisa skip "Firebase Hosting" untuk sementara.
6. Di **Your apps** akan muncul konfigurasi seperti:
   - `apiKey: "AIzaSy..."`  
   Ini yang Anda butuhkan.
7. Salin nilai **apiKey** (tanpa tanda petik di dalam file).
8. Di `.streamlit/secrets.toml`, isi:

```toml
[firebase_auth]
api_key = "AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
```

Ganti `AIzaSy...` dengan apiKey yang Anda salin.

---

### 1.3 Firebase Service Account (untuk Firestore: Watchlist & Jurnal)

Digunakan agar aplikasi bisa baca/tulis Firestore (watchlist, trading journal, rekomendasi).

**Langkah:**

1. Di Firebase Console → **Project settings** (roda gigi) → tab **Service accounts**.
2. Klik **Generate new private key** → **Generate key**. File JSON akan terunduh.
3. Buka file JSON tersebut. Isinya mirip seperti berikut (nama key harus sama):

```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "xxx",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "firebase-adminsdk-xxx@your-project-id.iam.gserviceaccount.com",
  "client_id": "123456789",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://...",
  "universe_domain": "googleapis.com"
}
```

4. Konversi ke TOML di `.streamlit/secrets.toml`:

- Buat blok `[firebase]`.
- Setiap key di JSON jadi key TOML (gunakan underscore: `private_key_id`, `private_key`, `client_email`, dll.).
- Untuk **private_key**: nilai di JSON biasanya sudah berisi `\n`. Di TOML Anda bisa tulis dengan newline asli, atau tetap pakai `\n`; kode aplikasi akan mengganti `\\n` menjadi newline jika perlu.

**Contoh** (nilai disingkat):

```toml
[firebase]
type = "service_account"
project_id = "your-project-id"
private_key_id = "xxxxxxxxxxxxxxxx"
private_key = "-----BEGIN PRIVATE KEY-----\nMIIE...\n-----END PRIVATE KEY-----\n"
client_email = "firebase-adminsdk-xxxxx@your-project-id.iam.gserviceaccount.com"
client_id = "123456789"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
universe_domain = "googleapis.com"
```

**Penting:** Jangan ubah nama key (harus `project_id`, `private_key`, `client_email`, dll.) dan jangan commit file ini ke Git.

---

### 1.4 Gemini API key (opsional – untuk menu "Tanya Gemini")

Jika Anda ingin fitur asisten tanya jawab saham dengan Gemini:

1. Buka [Google AI Studio](https://aistudio.google.com/apikey).
2. Login, lalu buat API key (Create API key).
3. Salin key tersebut.
4. Di `.streamlit/secrets.toml`:

```toml
[gemini]
api_key = "AIzaSy..."
```

Jika tidak diisi, aplikasi tetap jalan; menu "Tanya Gemini" akan menampilkan pesan agar pengguna menambahkan key.

---

### 1.5 Di platform deploy (misalnya Streamlit Cloud)

- **Streamlit Cloud:** Setelah connect repo, buka **Settings** → **Secrets**. Tempel isi **seluruh** `.streamlit/secrets.toml` (blok `[firebase_auth]`, `[firebase]`, `[gemini]`) ke kotak Secrets. Format tetap TOML.
- **Server sendiri:** Buat file `.streamlit/secrets.toml` di direktori yang dipakai saat menjalankan `streamlit run app.py`, isi sama seperti di atas.

---

## 2. Atur Firebase: Auth, Firestore Rules, Authorized domains

Agar login dan Firestore aman serta bisa dipakai dari URL deploy Anda.

---

### 2.1 Firebase Authentication – aktifkan Email/Password

1. Firebase Console → **Build** → **Authentication**.
2. Tab **Sign-in method**.
3. Klik **Email/Password**.
4. Nyalakan **Enable**, lalu **Save**.

Tanpa ini, login/register dari aplikasi akan ditolak.

---

### 2.2 Firestore Rules (keamanan baca/tulis)

Aplikasi menyimpan data per user di:

- `users/{userId}/watchlist/...`
- `users/{userId}/trading_journal/...`

Aturan yang disarankan: hanya user yang login yang boleh baca/tulis dokumen miliknya sendiri.

1. Firebase Console → **Build** → **Firestore Database**.
2. Tab **Rules**.
3. Ganti rules dengan (sesuaikan jika Anda punya struktur lain):

```text
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /users/{userId}/{document=**} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
  }
}
```

4. Klik **Publish**.

Dengan ini, hanya pemilik `userId` yang bisa akses sub-koleksi di bawah `users/{userId}`.

---

### 2.3 Authorized domains (agar auth jalan di URL deploy)

Firebase Auth hanya menerima request dari domain yang didaftar.

1. Firebase Console → **Project settings** (roda gigi) → tab **General**.
2. Scroll ke **Authorized domains**.
3. Biasanya sudah ada `localhost` (untuk development).
4. Klik **Add domain**:
   - **Streamlit Cloud:** domain seperti `nama-app.streamlit.app`.
   - **Domain sendiri:** misalnya `app.domainanda.com`.

5. Simpan.

Tanpa menambah domain deploy, login dari browser di URL tersebut bisa diblokir.

---

## 3. Menjalankan aplikasi

### 3.1 Di komputer Anda (Windows)

1. Buka terminal di folder proyek (folder yang berisi `app.py`).
2. (Opsional) Aktifkan virtual environment:
   - `python -m venv venv`
   - `venv\Scripts\activate`
3. Install dependensi (sekali saja):
   - `py -m pip install -r requirements.txt`  
   atau  
   - `python -m pip install -r requirements.txt`
4. Pastikan `.streamlit/secrets.toml` sudah diisi (minimal `[firebase_auth]` dan `[firebase]` jika ingin login + Firestore).
5. Jalankan:
   - `py -m streamlit run app.py`  
   atau  
   - `python -m streamlit run app.py`
6. Buka di browser alamat yang muncul (biasanya `http://localhost:8501`).

---

### 3.2 Di Streamlit Cloud

1. Push kode ke GitHub (tanpa file `secrets.toml`; pastikan ada di `.gitignore`).
2. Buka [share.streamlit.io](https://share.streamlit.io), login dengan GitHub.
3. **New app** → pilih repo, branch, dan file `app.py`.
4. Di **Advanced settings** → **Secrets**, tempel isi lengkap `.streamlit/secrets.toml` (semua blok).
5. Deploy. Setelah selesai, buka URL app (misalnya `https://nama-app.streamlit.app`).
6. Tambahkan URL tersebut ke **Authorized domains** di Firebase (langkah 2.3 di atas).

---

### 3.3 Di server/VPS (Linux)

1. Clone repo ke server, masuk ke folder proyek.
2. Buat virtual environment dan install:  
   `python3 -m venv venv && source venv/bin/activate`  
   `pip install -r requirements.txt`
3. Buat `.streamlit/secrets.toml` di folder proyek, isi sama seperti di lokal.
4. Jalankan:
   - Langsung: `python -m streamlit run app.py --server.port 8501`
   - Atau dengan process manager (systemd/supervisor) agar jalan di belakang dan auto-restart. Pastikan perintah yang dijalankan adalah `streamlit run app.py` dengan environment yang sama (venv aktif).

---

## Ringkasan checklist go-live

| Langkah | Cek |
|--------|-----|
| 1 | File `.streamlit/secrets.toml` ada dan tidak di-commit ke Git |
| 2 | `[firebase_auth].api_key` = Web API Key dari Firebase Console |
| 3 | `[firebase]` = isi Service Account (dari JSON) dalam format TOML |
| 4 | (Opsional) `[gemini].api_key` untuk menu Tanya Gemini |
| 5 | Firebase Auth → Sign-in method: Email/Password diaktifkan |
| 6 | Firestore Rules di-publish (hanya user sendiri yang akses datanya) |
| 7 | Authorized domains termasuk URL deploy (Streamlit Cloud / domain Anda) |
| 8 | Menjalankan: `py -m streamlit run app.py` (Windows) atau `python -m streamlit run app.py` |

Setelah semua terisi dan Firebase diatur, aplikasi siap di-onlinekan.
