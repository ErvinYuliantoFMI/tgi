# TGI WMS (Python + CSV)

Aplikasi Warehouse Management System sederhana untuk gudang TGI, dibangun dengan
Python (Streamlit) dan menggunakan file CSV sebagai sumber data — tanpa database.

## Fitur

- Menu navigasi di sidebar memakai [`streamlit-option-menu`](https://github.com/victoryhb/streamlit-option-menu)
  agar tampil sebagai daftar menu dengan ikon (bukan radio button bawaan
  Streamlit), dengan gaya warna navy & amber yang senada dengan brand.

- **Profil Perusahaan** — halaman landing berisi profil PT Tanaka Graha Indonesia
  (hero, tentang kami, statistik, Why Us, layanan) dengan tampilan yang selaras
  dengan [tanakagraha.id](https://tanakagraha.id/), memakai logo dan skema warna
  navy (`#1E2442`) + amber (`#FBAF43`) dari brand TGI.
- **Dashboard** — kartu Total Pesanan & Stock Tersedia dengan background
  gradient (navy & amber), serta grafik: donut Pesanan per Status, area chart
  Trend Pesanan Harian, lollipop chart Stock per Barang, dan bar gradient
  Item Terlaris.
- **Input Pesanan** — pilih customer (alamat otomatis terisi), tanggal pesanan,
  alamat kirim, dan detail item pesanan (multi-baris, validasi stock).
- **Daftar Pesanan** — cari & filter pesanan, lihat detail item, ubah status
  langsung: `Pesanan Masuk` → `Diproses` → `Dikirim` → `Selesai`.
- **Master Barang** — tambah barang baru, edit stock/harga langsung di tabel,
  hapus barang.

## Struktur folder

```
tgi_wms/
├── app.py                      # aplikasi Streamlit utama
├── requirements.txt
├── .streamlit/
│   └── config.toml             # tema warna (navy & amber sesuai brand TGI)
├── assets/
│   ├── logo-tgi.png            # logo berwarna (untuk latar terang)
│   ├── logo-tgi-putih.png      # logo putih (untuk latar navy — sidebar & hero)
│   └── logo-icon.png           # ikon asterisk saja (watermark dekoratif)
├── data/
│   ├── customers.csv           # master customer
│   ├── products.csv            # master barang & stock
│   ├── orders.csv              # header pesanan (id, customer, tanggal, alamat, status)
│   └── order_items.csv         # detail item tiap pesanan (order_id, product_id, qty)
```

Semua perubahan (pesanan baru, ubah status, ubah stock/harga, tambah/hapus barang)
langsung disimpan ke file CSV di folder `data/`, jadi datanya persisten setiap
kali aplikasi dijalankan ulang.

## Cara menjalankan

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
2. Jalankan aplikasi:
   ```
   streamlit run app.py
   ```
3. Buka browser ke alamat yang muncul di terminal (biasanya `http://localhost:8501`).

## Catatan

- ID pesanan baru dibuat otomatis dengan format `SO-xxxxx` (lanjutan dari nomor
  terakhir di `orders.csv`).
- ID barang baru dibuat otomatis dengan format `Pxx`.
- Kalau ingin reset data ke kondisi awal, tinggal kembalikan isi file CSV di
  folder `data/` seperti semula.
