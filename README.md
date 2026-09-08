# TGI WMS (Python + CSV)

Aplikasi Warehouse Management System sederhana untuk gudang TGI, dibangun dengan
Python (Streamlit) dan menggunakan file CSV sebagai sumber data — tanpa database.

## Fitur

- **Dashboard** — Total Pesanan dan Stock Tersedia, pesanan terbaru, stock menipis.
- **Input Pesanan** — pilih customer (alamat otomatis terisi), tanggal pesanan,
  alamat kirim, dan detail item pesanan (multi-baris, validasi stock).
- **Daftar Pesanan** — cari & filter pesanan, lihat detail item, ubah status
  langsung: `Pesanan Masuk` → `Diproses` → `Dikirim` → `Selesai`.
- **Master Barang** — tambah barang baru, edit stock/harga langsung di tabel,
  hapus barang.

## Struktur folder

```
tgi_wms/
├── app.py                 # aplikasi Streamlit utama
├── requirements.txt
├── data/
│   ├── customers.csv      # master customer
│   ├── products.csv       # master barang & stock
│   ├── orders.csv         # header pesanan (id, customer, tanggal, alamat, status)
│   └── order_items.csv    # detail item tiap pesanan (order_id, product_id, qty)
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
