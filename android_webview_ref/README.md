# Referensi WebView Android (IDX-Pro Insight)

Salin isi file di folder ini ke project Android Studio Anda (`MyApplication`).  
**Versi aplikasi web yang direferensi:** 1.3.0 (grafik intraday 5m/15m, kesimpulan rinci, refresh data lebih cepat).

## 1. MainActivity.kt

- Buka `app/src/main/java/com/example/myapplication/MainActivity.kt`
- Ganti **seluruh isi** dengan isi file `MainActivity.kt` di folder ini.
- Ganti URL di baris `val appUrl = "..."` dengan URL Streamlit Anda jika belum.

## 2. activity_main.xml

- Buka `app/src/main/res/layout/activity_main.xml`
- Ganti **seluruh isi** dengan isi file `activity_main.xml` di folder ini.

## 3. AndroidManifest.xml

Tidak perlu diubah; pastikan sudah ada:

- `<uses-permission android:name="android.permission.INTERNET" />`
- Activity `MainActivity` dengan intent-filter MAIN + LAUNCHER.

## Fitur yang dipakai

- **OnBackPressedDispatcher**: tombol Back tanpa warning deprecation.
- **ProgressBar**: tampil di atas saat halaman loading, hilang saat selesai.
- **CookieManager**: cookie diaktifkan agar login/session Streamlit jalan.
- **WebViewClient**: redirect ditangani di dalam app (tidak buka browser luar).

## Login tetap (tidak hilang saat refresh)

- **Cookie** tetap dipakai (CookieManager).
- **Cache** diaktifkan (`LOAD_DEFAULT`) agar halaman dan session tidak hilang saat reload.
- **State WebView** disimpan/direstore saat activity di-recreate (rotate/background), jadi Anda tidak perlu login lagi setelah refresh atau buka lagi app.

## Logo / icon aplikasi

Lihat **ICON_SETUP.md** di folder ini: cara memasang logo profesional ke project Android (Image Asset Studio + file `idx_pro_insight_icon.png`).

## Setelah menyalin

1. File → Sync Project with Gradle Files
2. Build → Make Project
3. Run ▶ ke emulator atau perangkat

## Update perubahan ke web & Android

- **Web:** Deploy terbaru (push ke repo Streamlit Cloud). Versi tampil di judul tab (v1.3.0) dan di sidebar.
- **Android:** WebView memuat URL web yang sama. Setelah web di-update, buka lagi app Android atau tarik-refresh di dalam WebView — tampilan mengikuti web terbaru tanpa perlu update APK. Jika URL deploy berubah, edit `val appUrl = "..."` di `MainActivity.kt`.
