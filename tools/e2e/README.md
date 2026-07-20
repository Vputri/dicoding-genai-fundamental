# Uji end-to-end aplikasi Streamlit

Menjalankan satu siklus penuh pada aplikasi yang sedang hidup di Colab (lewat tautan
ngrok) dan melaporkan komponen mana yang benar-benar bekerja — **dijalankan sebelum
merekam video**, supaya kerusakan tidak baru ketahuan di tengah rekaman.

Ini alat bantu pengembangan. Tidak ikut ke dalam zip submission.

## Kenapa perlu

Tiga kerusakan berikut ditemukan alat ini, dan ketiganya **gagal senyap** — tidak ada
pesan error di layar, tampilan terlihat normal:

| Masalah | Akibat |
|---|---|
| `image_to_url` dipindah Streamlit | `st_canvas` melempar AttributeError tersembunyi |
| Tanda tangan fungsinya ikut berubah | Shim penerus nama lama tetap gagal |
| iframe komponen dirender setinggi 0px | Kanvas ada di DOM tapi tak terlihat & tak bisa dicoret |

Tanpa uji ini, video demo akan tampak baik-baik saja sampai reviewer menyadari tidak
pernah ada mask yang dibuat — dan F3.9 gagal.

## Cara menjalankan

Sekali saja, pasang dependensinya:

```bash
cd "tools/e2e"
npm install
npx playwright install chromium
```

Lalu, dengan aplikasi Streamlit sedang berjalan di Colab:

```bash
node e2e.mjs https://xxxx-xxxx.ngrok-free.dev
```

Tautannya diambil dari output sel `ngrok.connect(8501)` di notebook Streamlit.

## Yang diuji

1. Aplikasi termuat
2. Text input prompt & negative prompt
3. Slider `num_inference_steps`, `guidance_scale`, `num_images`
4. Selectbox scheduler (dipilih DPM++)
5. Generate batch → 4 gambar dalam grid
6. Tombol Clear Memory
7. Tombol Select Img & pindah ke tab EDIT
8. Kanvas drawable-canvas muncul (dicari **di dalam iframe**)
9. Mencoret mask di kanvas
10. Menjalankan inpainting sampai selesai

## Membaca hasilnya

Setiap langkah dicetak `OK` atau `GAGAL`, ditutup ringkasan `n/m lolos`.
Screenshot tersimpan di direktori kerja untuk memudahkan penelusuran:

| Berkas | Isi |
|---|---|
| `e2e-1-generate.png` | Setelah batch generation |
| `e2e-2-edit.png` | Tab EDIT |
| `e2e-3-canvas.png` | Setelah kanvas dicoret |
| `e2e-4-inpaint.png` | Hasil inpainting |
| `e2e-error.png` | Bila uji berhenti mendadak |

## Catatan teknis

- **Header ngrok.** Akun gratis menampilkan halaman peringatan sebelum situs dibuka.
  Skrip mengirim header `ngrok-skip-browser-warning` agar langsung masuk.
- **Slider Streamlit.** Versi baru memakai react-aria — tidak ada `[role="slider"]`
  yang bisa di-`focus()`. Nilainya diatur dengan mengklik trek pada posisi relatif.
- **Kanvas ada di dalam iframe.** Komponen kustom Streamlit dirender terpisah, jadi
  `page.locator('canvas')` tidak akan menemukannya — harus lewat `frameLocator()`.
  Koordinat mouse tetap page-level, diambil dari kotak elemen iframe-nya.
- **Waktu tunggu panjang.** Generate batch di T4 bisa 1–3 menit, inpainting 1–2 menit;
  timeout sudah disetel longgar.

## Bukan pengganti rekaman manual

Playwright bisa merekam video (`record_video_dir`), tetapi hasilnya kurang cocok untuk
submission: tidak ada kursor yang terlihat, coretan kanvas tampak mekanis (garis
sempurna), dan Chromium headless tidak mewarisi tema gelap browser Anda.

Rekam sendiri layarnya. Alat ini hanya memastikan semuanya siap sebelum tombol rekam
ditekan.
