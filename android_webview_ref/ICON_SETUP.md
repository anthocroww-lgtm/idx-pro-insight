# Logo / Icon Aplikasi Android — IDX-Pro Insight

Agar aplikasi terlihat profesional, gunakan icon yang sudah disediakan atau buat dari Image Asset Studio.

## Opsi 1: Icon yang sudah dibuat

Di folder **`android_webview_ref`** ini ada file **`idx_pro_insight_icon.png`** (grafik naik hijau, background gelap, tampilan profesional). Pakai file itu langsung di Android Studio (langkah Opsi 2).

## Opsi 2: Memasang icon di Android Studio

1. Buka project **MyApplication** di Android Studio.
2. Klik kanan folder **`app`** → **New** → **Image Asset**.
3. Di jendela **Asset Studio**:
   - **Icon Type:** Launcher Icons (Adaptive and Legacy).
   - **Name:** `ic_launcher` (atau biarkan default).
   - **Foreground Layer:** pilih **Image** → klik **Path** → pilih file `idx_pro_insight_icon.png` (atau gambar logo 512x512 lain).
   - Sesuaikan **Trim** dan **Resize** jika perlu.
4. Klik **Next** → **Finish**.

Android Studio akan membuat semua ukuran (mdpi, hdpi, xhdpi, xxhdpi, xxxhdpi) dan mengisi `mipmap-*`.

## Opsi 3: Icon manual (tanpa Asset Studio)

Jika Anda punya satu file PNG 512x512:

- Salin ke `app/src/main/res/mipmap-hdpi/`, `mipmap-mdpi/`, dll. dengan nama `ic_launcher.png`.
- Atau tetap pakai **Image Asset** (Opsi 2) dan pilih file PNG itu sebagai Foreground Image.

## Hasil

Setelah selesai, icon aplikasi di launcher dan di pengaturan akan menampilkan logo IDX-Pro Insight yang rapi dan profesional.
