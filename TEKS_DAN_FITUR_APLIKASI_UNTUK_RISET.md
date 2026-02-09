# Teks dan Fitur Aplikasi IDX-Pro Insight Terminal — Bahan Riset untuk Gemini AI

Dokumen ini memuat **semua teks dan fitur** yang ada di aplikasi IDX-Pro Insight Terminal agar Gemini AI dapat melakukan riset tentang fitur-fitur ini.

---

## 1. Ringkasan Aplikasi

- **Nama aplikasi:** IDX-Pro Insight Terminal  
- **Deskripsi:** Sistem Pendukung Keputusan Saham IDX. Empat pilar: ATR (Risiko), Mansfield RS (Momentum), Seasonality, Sentimen Leksikon.  
- **Bahasa antarmuka:** Indonesia  
- **Teknologi:** Streamlit, data harga dari Yahoo Finance, login & data cloud via Firebase Auth dan Firestore.  
- **Tujuan:** Pembelajaran agar pengguna dapat membuat kesimpulan secara mandiri; analisis disajikan secara mendalam sebagai bahan pengambilan keputusan. Bukan saran investasi dari pihak lain; keputusan dan risiko sepenuhnya di tangan pemodal.

---

## 2. Menu dan Halaman

### Menu (Sidebar)
- **Jika sudah login:** Peluang Hari Ini | Analisis Mendalam | Tanya Gemini | Portofolio Saya | Logout  
- **Jika belum login:** Peluang Hari Ini | Market Overview | Tanya Gemini  

### Input di Sidebar
- **Kode Saham:** placeholder "Contoh: BBCA, GOTO"  
- **Simbol:** ditampilkan dengan format ticker (mis. BBCA.JK)

### Autentikasi (belum login)
- Tab: **Masuk** | **Daftar**  
- Form Masuk: Email, Kata sandi, checkbox "Ingat email", "Ingat kata sandi", tombol **Masuk**  
- Form Daftar: Nama lengkap, Email, Kata sandi (placeholder "Min. 6 karakter"), tombol **Daftar**  
- Caption: "Akses fitur Pro & Portofolio Cloud"  
- Caption: "Opsi penyimpanan (sesi ini)"  
- Pesan error validasi: "Email harus diisi.", "Kata sandi harus diisi."  
- Pesan sukses/error dari Firebase (login/register)

---

## 3. Halaman: Peluang Hari Ini

- **Header:** Peluang Hari Ini  
- **Caption:** Saham apa yang bagus untuk dibeli hari ini? Hasil pemindaian otomatis saham likuid (LQ45 & IDX80).  

### IHSG
- **Subheader:** IHSG (^JKSE)  
- **Metric:** Harga, perubahan %  
- Label warna: **Hijau** / **Merah**  
- **Peringatan:** Data IHSG hari ini tidak tersedia (pasar mungkin tutup).  

### Hasil Scan (3 kolom)
- **Day Trade Picks** — Caption: Saham dengan lonjakan volume tinggi hari ini.  
- **Swing Trade Picks** — Caption: Saham uptrend yang potensial lanjut naik.  
- **Invest Picks** — Caption: Saham bluechip yang sedang koreksi wajar.  

Untuk setiap pick ditampilkan: nomor urut, kode saham, harga/diskonto/jarak ke MA20, dan persen.  

- **Info jika kosong:** Tidak ada saham yang memenuhi kriteria pemindaian hari ini. Coba lagi saat pasar buka atau besok.  
- **Peringatan jika error:** Pesan error dari scanner (mis. Data pasar tidak tersedia).  

### Grafik Intraday
- **Subheader:** Grafik Intraday 15m · [kode saham]  
- Chart: Candlestick + VWAP  
- **Caption:** Data intraday: terakhir sebelum pasar tutup — [tanggal/waktu] WIB.  
- **Info:** Data intraday tidak tersedia (pasar tutup atau ticker tidak aktif).  
- **Peringatan:** Grafik intraday tidak dapat dimuat: [error]  

### Tombol
- **Analisa Mendalam Saham Ini** — pindah ke menu Analisis Mendalam dengan ticker dari chart.  

---

## 4. Halaman: Market Overview (tanpa login)

- **Header:** Market Overview  
- **Info:** Login untuk mengakses analisis lengkap, Portofolio, dan Trading Plan.  
- Chart IHSG 1 tahun  
- **Peringatan:** Data IHSG tidak dapat dimuat: [error]  

---

## 5. Halaman: Analisis Mendalam (IDX-Pro Insight Terminal)

- **Header:** IDX-Pro Insight Terminal  
- **Peringatan:** Masukkan kode saham di sidebar.  
- **Error:** Data tidak ditemukan atau ticker delisting. Cek kode saham.  

### Empat Tab
1. **Dashboard Utama**  
2. **Manajemen Risiko (ATR)**  
3. **Analisis Musiman**  
4. **Sentimen Berita**  

---

### Tab 1: Dashboard Utama

**Stempel data**
- **Caption:** Data harga per [tanggal] · Berdasarkan [N] hari perdagangan. Sumber: Yahoo Finance. Data dapat tertunda.  

**Ringkasan Telaah**
- **Info:** Ringkasan Telaah: [teks ringkasan dari mesin analisis]  

**Kesimpulan & Rekomendasi**
- **Subheader:** Kesimpulan & Rekomendasi  
- **Label rekomendasi (dari mesin):**  
  - Cocok untuk Day Trading (scalping)  
  - Cocok untuk Swing Trading (1–2 minggu)  
  - Cocok untuk Investasi Jangka Panjang  
  - Tidak disarankan beli saat ini  
  - Netral – perhatikan area support sebelum beli  
- **Teks:** Area beli disarankan: Rp [low] – Rp [high]  
- **Teks:** Target / resistance: Rp [low] – Rp [high]  
- **Metric:** Risk/Reward (R:R) — "1 : [nilai]" — Delta: Semakin tinggi semakin menguntungkan  
- **Caption:** [summary dari rekomendasi]  
- **Tombol (jika login):** Simpan rekomendasi ke Jurnal  
- **Disclaimer (caption):**  
  Aplikasi ini untuk **pembelajaran** agar Anda dapat membuat **kesimpulan secara mandiri**. Analisis disajikan secara mendalam sebagai **bahan pengambilan keputusan**—dengan bantuan aplikasi ini Anda dapat mengambil keputusan sendiri. Ini bukan saran atau rekomendasi investasi dari pihak lain; keputusan dan risiko sepenuhnya ada di tangan pemodal. Gunakan hasil analisis dengan bijak, lakukan riset tambahan bila perlu.  

**Chart Teknikal**
- **Subheader:** Chart Teknikal · [ticker]  
- Grafik: Harga, BB Upper/Mid/Lower, MA20, MA50, MA200  
- Sumbu Y: Harga (Rp)  

**RSI**
- Grafik RSI(14), garis Overbought (70), Oversold (30)  

**Momentum Komparatif**
- **Subheader:** Momentum Komparatif · Mansfield RS vs IHSG  
- **Caption:** Stronger than Market / Weaker than Market  

**Key Levels**
- **Subheader:** Key Levels · 52 Minggu & 20 Hari  
- **Metric:** 52w High, 52w Low, 20d High, 20d Low (dengan jarak % dari sekarang)  
- **Caption:** Jarak harga saat ini ke level-level penting. Buy on dip sering di area 52w low atau koreksi 5–15% dari 52w high.  

**On-Balance Volume (OBV)**
- **Subheader:** On-Balance Volume (OBV)  
- **Caption:** Konfirmasi volume: OBV naik = volume mengikuti kenaikan harga.  

**Expander: Support & Resistance (20 hari)**
- **Resistance (area jual):** [daftar harga]  
- **Support (area beli):** [daftar harga]  

**Expander: Ringkasan Teknikal & Tren**
- **Tren:** [nilai dari mesin, contoh:] Strong Uptrend (Cocok trend following), Downtrend / Bearish (Hati-hati), Sideways / Consolidation, Data MA belum cukup  
- **RSI:** [nilai dari mesin, contoh:] Oversold / Diskon (Potensi Rebound), Overbought / Mahal (Rawan Profit Taking), Netral (RSI xx), -  
- **Bollinger:** Squeeze terdeteksi (potensi breakout)  
- **Caption:** RSI = momentum (<30 oversold, >70 overbought). MA = Moving Average tren.  

**Expander: Sinyal Bandarmology (VPA)**
- **Sinyal:** [nilai dari mesin, contoh:] Akumulasi Bandar Kuat, Distribusi / Buangan Bandar, Volume Tinggi, Volume Normal, -  
- **Caption:** [deskripsi], Rasio volume vs rata-rata 20 hari: [x]x  
- **Caption:** Proksi aliran uang besar lewat Volume Price Analysis.  

**Expander: Fundamental & Valuasi**
- **Metric:** PER, PBV, ROE (%), DER  
- **Label dari mesin:** Hidden Gem (Murah & Bagus), High Debt Risk (DER > 1.5), Valuasi tinggi (PER > 25)  
- **Caption:** PER, PBV, ROE, DER — metrik valuasi & kesehatan keuangan.  
- **Peringatan:** [jika error fundamental]  

**Expander: Korelasi Makro & Komoditas**
- **Info:** [narasi korelasi saham vs komoditas/makro, mis. Minyak, Emas, USD/IDR]  

**Rencana Trading**
- **Subheader:** Rencana Trading  
- **Buy Area** — Info: [Rp support] (Support / Lower BB) — Caption: Support / Lower BB  
- **Target** — Success: [Rp resistance] (Resistance / Upper BB) — Caption: Resistance / Upper BB  
- **Stop Loss** — Error: [Rp] (≈4% di bawah support) — Caption: ≈4% di bawah support  

**Tombol**
- **Simpan ke Jurnal** (jika login) — menyimpan rencana trading ke Firestore.  
- **Caption (tanpa login):** Login untuk menyimpan rencana ke Jurnal Cloud.  
- **Tambah ke Watchlist** (jika login) — menambah ticker ke watchlist.  

---

### Tab 2: Manajemen Risiko (ATR)

- **Subheader:** Safe Entry Calculator · Manajemen Risiko Berbasis ATR  
- **Caption:** Position sizing berdasarkan volatilitas (ATR 14). Stop Loss = ATR × multiplier (skenario Long).  
- **Input:** Modal Trading (Rp), Risiko Maksimal per Trade (%), Stop Loss Multiplier (× ATR)  
- **Subheader blok:** Rekomendasi Safe Entry  
- **Metric:** Jarak Stop Loss, Harga Stop Loss, Risk Amount (Rp), Max Lembar, Max Lot  
- **Peringatan:** Kerugian maksimal jika SL kena (per trade): [Rp]  
- **Info:** ATR 14 mengukur volatilitas harian. Posisi maksimal dihitung agar kerugian per trade tidak melebihi risiko yang Anda pilih.  

---

### Tab 3: Analisis Musiman

- **Subheader:** Probabilitas Musiman · Rata-rata Return & Win Rate per Bulan  
- **Caption:** Data historis minimal 10 tahun. Pola Window Dressing / January Effect.  
- **Peringatan:** Data historis belum cukup untuk analisis musiman (perlu minimal ~5 tahun).  
- **Judul heatmap:** Return Bulanan per Tahun  
- **Sumbu:** Bulan (Jan–Des), Tahun  
- **Subheader:** Rata-rata Return per Bulan  
- **Caption:** Win rate (% bulan positif): [per bulan]  

---

### Tab 4: Sentimen Berita

- **Subheader:** Analisis Sentimen Berita · Leksikon Pasar Modal Indonesia  
- **Caption:** Tempel judul/teks berita terkini tentang saham. Skor dari kata kunci positif vs negatif.  
- **Text area:** Teks berita (placeholder: Contoh: Emiten catat laba naik 20%, dividen melonjak...)  
- **Tombol:** Hitung Sentimen  
- **Peringatan:** Masukkan teks berita terlebih dahulu.  
- **Metric:** Skor Sentimen — [angka] ([label])  
- **Caption:** Kata positif: [n] · Kata negatif: [n]  
- **Gauge:** Sentimen — sumbu Bearish | Netral | Bullish  
- **Label sentimen dari mesin:** Bullish, Bearish, Netral  

---

## 6. Halaman: Tanya Gemini

- **Header:** Tanya Gemini · Asisten Belajar Saham  
- **Caption:** Ajukan pertanyaan seputar saham, teknikal, fundamental, atau istilah pasar. Untuk **pembelajaran** dan **bahan pengambilan keputusan** Anda—bukan saran investasi. Jawaban AI dapat tidak akurat; gunakan sebagai referensi dan lakukan riset mandiri.  
- **Info (jika API key kosong):** Untuk mengaktifkan asisten, tambahkan **Gemini API key** di `.streamlit/secrets.toml` (blok `[gemini]` → `api_key = "..."`). Dapatkan key gratis di Google AI Studio.  
- **Chat input placeholder:** Tanya tentang saham, RSI, support/resistance, dll.  
- **Spinner:** Gemini menjawab...  
- **Instruksi sistem ke model:** Asisten edukasi saham untuk pemula di Indonesia; jawab Bahasa Indonesia, singkat dan mudah dipahami; fokus penjelasan konsep (teknikal, fundamental, istilah pasar), bukan saran beli/jual; sebutkan untuk pembelajaran dan bukan saran investasi bila relevan.  

---

## 7. Halaman: Portofolio Saya

- **Peringatan (tanpa login):** Silakan login untuk melihat Portofolio.  
- **Header:** Portofolio Saya  
- **Tab:** Watchlist | Trading Jurnal  

**Watchlist**
- **Info:** Watchlist kosong. Gunakan 'Tambah ke Watchlist' di halaman analisis.  
- Per item: **Ticker** · **Company** — Caption: Tren: [nilai] · [tanggal]  

**Trading Jurnal**
- **Info:** Jurnal kosong. Simpan rencana trading dari halaman analisis.  
- **Entri tipe rekomendasi:** Ticker · Rekomendasi · [waktu] — Style, Area beli, Target, Summary, Catatan (avoid_reason)  
- **Entri tipe rencana:** Ticker · [waktu] — Buy, Target, SL — Trend, RSI, Bandar  

---

## 8. Konsep dan Indikator yang Dipakai

- **Teknikal:** Bollinger Bands (20,2), MA20, MA50, MA200, RSI(14), OBV, Support/Resistance (swing high/low 20 hari), Key Levels (52w high/low, 20d high/low).  
- **Bandarmology / VPA:** Volume Price Analysis; akumulasi vs distribusi; rasio volume vs rata-rata 20 hari; LQ45 sebagai proksi aliran institusi.  
- **Fundamental:** PER, PBV, ROE, DER; Hidden Gem (PER < 10, ROE > 15%); High Debt Risk (DER > 1.5); valuasi tinggi (PER > 25).  
- **Makro:** Korelasi sektor dengan Minyak (CL=F), Emas (GC=F), USD/IDR (IDR=X).  
- **Risiko:** ATR(14), Safe Entry (position sizing), Risk/Reward ratio, Stop Loss ≈4% di bawah support, kerugian maksimal per trade.  
- **Momentum:** Mansfield Relative Strength vs IHSG (^JKSE).  
- **Musiman:** Return bulanan, win rate per bulan, heatmap return per tahun.  
- **Sentimen:** Leksikon kata positif/negatif pasar modal Indonesia; skor = positif − negatif; label Bullish/Bearish/Netral.  
- **Scanner:** Day Trade (volume spike, candle hijau, harga > VWAP); Swing (harga > MA20, RSI 40–65, MACD > Signal); Invest (harga > MA200, koreksi 5–15% dari 52w high).  

---

## 9. Sumber Data dan Disclaimer

- **Sumber data:** Yahoo Finance. Data dapat tertunda.  
- **Stempel:** Data harga per [tanggal], berdasarkan [N] hari perdagangan.  
- **Disclaimer rekomendasi:** Pembelajaran, kesimpulan mandiri, bahan pengambilan keputusan; bukan saran investasi; keputusan dan risiko di pemodal; gunakan dengan bijak dan riset tambahan.  
- **Tanya Gemini:** Untuk pembelajaran dan bahan pengambilan keputusan; bukan saran investasi; jawaban AI dapat tidak akurat; gunakan sebagai referensi dan riset mandiri.  

---

## 10. Pesan Sukses / Error Umum

- Berhasil disimpan  
- Firebase tidak dikonfigurasi. Cek .streamlit/secrets.toml  
- [Pesan error dari Firebase/Firestore]  
- Data historis tidak tersedia. Cek kode saham dan koneksi.  
- Data fundamental tidak tersedia  

---

Dokumen ini memuat **seluruh teks dan fitur** yang tampil di aplikasi IDX-Pro Insight Terminal. Gunakan sebagai referensi untuk riset fitur (mis. oleh Gemini AI) tanpa perlu membuka kode sumber.
