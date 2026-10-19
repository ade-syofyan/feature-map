# Reminder Perubahan

Reminder menunjukkan kemungkinan dampak pada flow, bukan bukti aturan berubah.
Perubahan tampilan murni tidak perlu mengubah `FEATURE-MAP.yaml`.

Hook Claude menyaring Edit/MultiEdit dengan teks old/new lengkap untuk gaya
statis yang dikenal: jarak, warna, ukuran teks normal, serta gaya sel Excel.
Penyaringan terjadi sebelum penandaan stale atau pending. Rumus pada konteks
yang tidak berubah tidak dianggap rumus baru; kondisi yang dihapus tetap dicek.

Struktur atau nama sheet, header, filter, visibilitas dan format data tetap
memerlukan review kontrak impor/ekspor. Perubahan tersebut bisa memengaruhi
konsumen meskipun rumus tidak berubah. Nilai data yang berisi teks seperti
`class="p-2"` tetap data, bukan gaya tampilan.

Write, Bash, input tanpa old/new lengkap, gaya dinamis dan perubahan yang tidak
dikenali tetap mengikuti reminder biasa. Ini penyaringan konservatif, bukan
pemahaman semantik otomatis untuk seluruh bahasa atau framework. Codex memakai
aturan review skill karena tidak menerima hook Claude. Adapter lain belum
memakai penyaring ini.

Pending lama tidak dihapus otomatis. Review dampaknya lalu sinkronkan aturan
atau tandai sebagai perubahan tanpa dampak bisnis melalui alur sync yang ada.
