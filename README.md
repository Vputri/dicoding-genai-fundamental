# Proyek Image Generation — Generative Image Suite (BFGAI)

Implementasi dari [PRD-Image-Generation.md](../PRD-Image-Generation.md).
Target: **Advanced (4 pts)** pada ketiga kriteria.

## ⚠️ Baca ini dulu

Kedua template resmi sudah dibaca isinya — pemetaan sel-per-sel ada di
**[PETA-TEMPLATE.md](PETA-TEMPLATE.md)**. Tiga hal yang mengubah cara kerja:

1. **Mengubah struktur DIPERBOLEHKAN.** Template menyatakannya eksplisit. Jalur teraman
   tetap mengisi bagian bertanda `________` saja, tapi tidak seketat dugaan awal.
2. **`app.py` sudah jadi** — jangan ditulis ulang. Seluruh komponen Kriteria 3 sudah ada
   di sana. Tugas Anda hanya mengisi `logic.py`.
3. **Template memanggil model yang sudah 404** — `runwayml/*` di `load_models_cached()`
   harus diganti walau diberi komentar "JANGAN DIUBAH", kalau tidak aplikasi mati total.

Notebook tetap **tidak dibuat dari nol**; isi folder ini adalah implementasi referensi
untuk disalin ke sel yang bersesuaian.

## Isi

| Berkas | Untuk | Isi |
|---|---|---|
| `PETA-TEMPLATE.md` | Panduan | Pemetaan setiap sel template → blok referensi |
| `referensi/k1_text_to_image.py` | Notebook Pipeline | F1.1–F1.10: kedua fungsi generate, eksperimen CFG & steps, batch grid 2×2, `load_scheduler()` |
| `referensi/k2_image_to_image.py` | Notebook Pipeline | F2.1–F2.8: `inpaint_engine()`, mask manual & segmentasi, `prepare_outpainting()`, zoom-out, refiner dua tahap |
| `referensi/k3_logic.py` | Notebook Streamlit | Isian `logic.py`: `generate_image()` Basic & batch, `flush_memory()`, `set_scheduler()`, `run_inpainting()`, `prepare_outpainting()` |
| `requirements.txt` | Submission | Dependensi terkunci versinya |
| `tools/package.py` | Perkakas | Pengemas zip — menolak bila ada syarat belum terpenuhi |

Folder `referensi/`, `tools/`, dan `PETA-TEMPLATE.md` **tidak ikut ke dalam zip**.

## Cara pakai

1. Buka kedua tautan Colab template → **File → Save a copy in Drive**.
2. Hapus prefiks `[Template]_`, ganti `Nama-siswa` → `Vika-Putri-Ariyanti`.
3. Aktifkan GPU (**Runtime → Change runtime type → T4**).
4. Ikuti [PETA-TEMPLATE.md](PETA-TEMPLATE.md) — setiap sel template sudah dipetakan
   ke blok referensi yang sesuai.
5. Tulis observasi eksperimen di sel markdown yang sudah disiapkan template
   (ganti kalimat dalam kutip miring dengan observasi Anda sendiri).
6. Jalankan semua sel sampai selesai, lalu unduh `.ipynb`-nya.

## Keputusan desain

- **`stable-diffusion-v1-5/stable-diffusion-v1-5`** menggantikan `runwayml/...` yang
  sudah 404. Bobot dan arsitektur identik — bukan pergantian model. **Konfirmasi dulu
  ke forum diskusi**, dan sertakan sel markdown penjelasan di atas sel pemuatan model.
- **Checkpoint inpainting instance terpisah.** UNet inpainting punya 9 input channel
  (4 latent + 4 masked-latent + 1 mask), berbeda dari UNet t2i yang 4 channel. Jadi ini
  bukan pelanggaran tips "jangan muat ulang model" — arsitekturnya memang beda.
  `muat_inpaint_pipeline()` mencoba beberapa mirror karena repo aslinya juga 404.
- **Refiner dua tahap tanpa SDXL.** Rubrik meminta `denoising_end`/`denoising_start`,
  parameter yang hanya ada di pipeline SDXL — padahal SDXL dilarang. Pada SD1.5 porsi
  denoising dikendalikan `strength`, jadi pemetaannya: `denoising_end=0.8` → base
  menjalankan 80% langkah; `denoising_start=0.8` → refiner `strength=0.2`.
  Stage 1 tetap menghasilkan latent (`output_type="latent"`) sesuai bunyi rubrik.
- **Refiner berbagi komponen dengan base** (`StableDiffusionImg2ImgPipeline(**pipe.components)`)
  — tidak ada bobot baru yang dimuat ke VRAM.
- **Bukti `load_scheduler()` tidak memuat ulang model:** `id(pipe.unet)` dicetak sebelum
  dan sesudah pergantian, nilainya sama.

## Yang masih perlu dikerjakan sendiri

- [ ] Tanya forum diskusi: model 404 (§4.2 PRD) dan refiner-vs-SDXL (§4.3 PRD)
- [ ] Unduh kedua template resmi
- [ ] Sesuaikan `PROMPT` agar hasilnya mendekati gambar acuan di template
- [ ] Kalibrasi `KOTAK_SATELIT` lewat trial and error dengan `pratinjau_mask()`
- [ ] Sesuaikan `label_target` segmentasi dengan label yang benar-benar terdeteksi
- [ ] Jalankan kedua notebook sampai selesai di Colab GPU
- [ ] Rekam video demo 1–5 menit → `video_demo_aplikasi_BFGAI.mp4`
- [ ] `python3 tools/package.py` untuk membuat zip

## Sebelum submit

`tools/package.py` memeriksa otomatis: berkas lengkap, sel kode ber-output, tidak ada
rujukan SDXL, tidak ada authtoken yang bocor, dan ukuran video wajar. Zip hanya dibuat
bila semuanya lolos.
