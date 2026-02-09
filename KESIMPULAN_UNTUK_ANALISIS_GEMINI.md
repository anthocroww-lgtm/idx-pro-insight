# Kesimpulan Aplikasi IDX-Pro Insight Terminal — Untuk Analisis oleh Gemini AI

Dokumen ini berisi **kesimpulan terstruktur** tentang aplikasi IDX-Pro Insight Terminal agar dapat dianalisis oleh Gemini AI (riset fitur, rekomendasi, atau tinjauan konsep).

---

## 1. Identitas dan Tujuan

| Aspek | Ringkasan |
|--------|------------|
| **Nama** | IDX-Pro Insight Terminal |
| **Jenis** | Aplikasi web (Streamlit) untuk analisis saham Bursa Efek Indonesia (IDX). |
| **Target pengguna** | Pemula hingga menengah; fokus edukasi dan bahan pengambilan keputusan mandiri. |
| **Tujuan utama** | Membantu pengguna **belajar** dan **membuat kesimpulan sendiri** dengan dukungan analisis mendalam; **bukan** pemberi saran investasi. Keputusan dan risiko sepenuhnya di tangan pemodal. |
| **Bahasa antarmuka** | Indonesia. |
| **Sumber data harga** | Yahoo Finance (dapat tertunda). |

---

## 2. Empat Pilar Analisis

1. **ATR (Average True Range)** — Manajemen risiko dan position sizing (Safe Entry Calculator).  
2. **Mansfield Relative Strength** — Momentum komparatif saham vs IHSG (^JKSE).  
3. **Seasonality** — Pola return bulanan dan win rate per bulan (min. ~5 tahun data).  
4. **Sentimen leksikon** — Skor teks berita dari kamus kata positif/negatif pasar modal Indonesia (tanpa API berita berbayar).  

Ditambah: analisis **teknikal** (RSI, MA, Bollinger Bands, OBV, support/resistance), **fundamental** (PER, PBV, ROE, DER), **bandarmology/VPA**, dan **korelasi makro** (komoditas/kurs sesuai sektor).

---

## 3. Fitur Utama (Menu)

- **Peluang Hari Ini** — Scanner saham likuid (LQ45 & IDX80) dalam 3 kategori: Day Trade (volume spike & VWAP), Swing (uptrend, RSI 40–65, MACD > signal), Invest (harga > MA200, koreksi 5–15% dari 52w high). Grafik intraday 15m dengan VWAP; jam istirahat bursa 11:30–13:30 WIB disembunyikan di chart. Fallback: jika tidak ada yang lolos ketiga kategori, ditampilkan Top 3 saham defensif (Consumer Non-Cyclical: ICBP, UNVR, KLBF, dll.).  
- **Analisis Mendalam** — Per saham: ringkasan telaah, kesimpulan & rekomendasi (area beli, target, risk/reward), chart teknikal, RSI, Mansfield RS, key levels 52w/20d, OBV, support & resistance, rencana trading (buy area, target, stop loss), tab Manajemen Risiko (ATR), tab Musiman, tab Sentimen berita. Simpan ke Jurnal/Simpan rekomendasi ke Jurnal dan Tambah ke Watchlist (perlu login).  
- **Tanya Gemini** — Chat dengan model Gemini untuk tanya jawab edukasi saham (teknikal, fundamental, istilah); konteks: pembelajaran dan bahan keputusan, bukan saran investasi.  
- **Portofolio Saya** — Watchlist dan Trading Jurnal (tersimpan di Firestore; perlu login).  

Data IHSG: jika data hari ini belum ada (NaN/telat update), aplikasi memakai data penutupan terakhir yang valid (fallback) agar tampilan dan perhitungan (mis. Mansfield RS) tidak error.

---

## 4. Batasan dan Disclaimer

- **Bukan saran investasi** — Semua rekomendasi dan analisis bersifat edukasi dan bahan pengambilan keputusan; keputusan dan risiko ada di pemodal.  
- **Data dapat tertunda** — Sumber: Yahoo Finance; stempel “Data harga per [tanggal]” dan “Berdasarkan N hari perdagangan” ditampilkan.  
- **AI (Gemini)** — Jawaban untuk pembelajaran; dapat tidak akurat; pengguna disarankan riset mandiri.  
- **Indeks ^JKSE** — Sering telat di-update dibanding saham; aplikasi memakai fallback ke data terakhir yang valid.

---

## 5. Validasi dan Penyempurnaan yang Sudah Diterapkan

- **Scanner Peluang Hari Ini** — Pemisahan Day/Swing/Invest sesuai struktur mikro pasar Indonesia; Day fokus volume spike & VWAP; Invest memakai filter koreksi wajar dari 52w high pada bluechip.  
- **Chart intraday** — Rangebreaks Plotly untuk menyembunyikan jam istirahat bursa 11:30–13:30 WIB.  
- **IHSG** — Fallback ke data penutupan terakhir yang valid jika hari ini NaN.  
- **Scanner kosong** — Fallback Top 3 saham defensif (ICBP, UNVR, KLBF, SIDO, INDF) saat tidak ada yang lolos Day/Swing/Invest; grafik intraday memakai ticker defensif #1 jika tidak ada Day Trade pick.  
- **Transparansi data** — Tampil “Data harga per [tanggal]”, jumlah hari perdagangan, dan sumber Yahoo Finance.  
- **Validasi input** — Kode saham disanitasi (huruf/angka, maks. 10 karakter).  
- **Struktur data** — Penambahan fitur (defensive, data_as_of, disclaimer, dll.) tidak mengubah format data lama (watchlist, jurnal, hasil analisis).

---

## 6. Konteks untuk Analisis Gemini

- Aplikasi ini **sudah berjalan** dengan fitur di atas; dokumen **TEKS_DAN_FITUR_APLIKASI_UNTUK_RISET.md** berisi inventaris lengkap teks dan fitur UI.  
- **Kesimpulan ini** memuat: identitas, tujuan, pilar analisis, fitur utama, batasan, dan validasi/penyempurnaan.  
- Gemini AI dapat menggunakan dokumen ini untuk: **meringkas** fitur, **menilai** kesesuaian dengan riset pasar Indonesia, **mengusulkan** peningkatan konsep atau teks (tanpa mengubah data yang ada), atau **menjawab** pertanyaan pengguna tentang cara kerja dan batasan aplikasi.

---

*Dokumen kesimpulan untuk analisis oleh Gemini AI. Tidak mengubah data atau kode aplikasi.*
