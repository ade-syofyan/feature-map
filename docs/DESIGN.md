# Desain README

Diperbarui: 19 Oktober 2026.

## Arah visual

README Free menjadi halaman pengenalan produk: banner, manfaat, instalasi,
contoh, batas kemampuan, dokumentasi, dan penawaran Pro di bagian bawah.
English dan Indonesia memiliki halaman ringkasan sendiri. Panduan lengkap
sebelumnya dipertahankan di `GUIDE.md` pada root agar tautan relatif tetap valid.

Palet mengikuti aset lama: biru `#0f2851`, biru muda `#8fb8ec`, putih `#f3f8ff`,
serta amber `#ffb454`. Panel gelap `#0a1830` membantu hierarki dan kontras.
Font memakai sans-serif sistem; nama file memakai monospace. SVG mandiri,
tanpa JavaScript, font eksternal, atau gambar milik produk lain.

## Referensi ATM

Kedua referensi berikut benar-benar dibuka dan diperiksa visualnya pada
19 Oktober 2026:

- [Linear](https://linear.app/): judul besar, kalimat manfaat singkat, ruang lega,
  dan panel produk sebagai pusat perhatian. Prinsip tersebut diubah menjadi
  ilustrasi relasi file; Feature Map tidak memiliki dashboard SaaS.
- [Supabase README](https://github.com/supabase/supabase#readme): identitas produk
  di awal, manfaat yang mudah dipindai, serta tautan dokumentasi langsung.
  Warna, logo, aset, klaim pelanggan, dan tangkapan layar mereka tidak disalin.

Grid blueprint dan jalur hubungan file tetap mempertahankan identitas Feature
Map. Klaim angka token, jumlah flow, dan hasil audit yang tidak terikat bukti
dihapus dari ilustrasi. Label “Flow illustration” menjelaskan bahwa panel
merupakan gambar konsep, bukan tangkapan layar aplikasi.

## Keputusan

- Gunakan Markdown dan HTML sederhana yang didukung GitHub; tidak mengandalkan CSS kustom.
- Pertahankan fitur Free, cara instalasi, lisensi, dan kontak pembelian.
- Letakkan instruksi penting sebagai teks; gambar selalu punya deskripsi alternatif.
- Hindari badge berlebihan, animasi, angka penggunaan rekaan, serta kesan tool ini layanan cloud.
- Pindahkan detail panjang ke panduan, bukan menghapusnya.
- Perubahan ini hanya dokumen dan aset, tanpa perubahan perilaku program. Validasi memakai render SVG/README, tautan, registry, dan tes yang sudah ada.

Aset halaman depan memakai `hero.svg`, `banner-mobile.svg`, dan `workflow.svg`.
Aset lama dipertahankan untuk panduan lengkap; nama baru menghindari gambar
lama yang masih disimpan cache GitHub pada path gambar sebelumnya.

Promosi Pro ada pada navigasi, callout setelah manfaat Free, dan tabel perbandingan
di akhir README. Pembelian diarahkan ke email; status preview dan cakupan runtime
dinyatakan sesuai versi privat yang diperiksa, tanpa harga atau janji update rekaan.

## Logo Bersama

20 Oktober 2026: logo Alur Terjaga menggantikan simbol lama sebagai identitas produk.
Aset, makna dan referensi ada di [BRAND.md](BRAND.md). Palet serta layout yang sudah
ada dipertahankan. Ikon kunci pada tindakan pengelolaan kunci tetap sesuai konteks.
