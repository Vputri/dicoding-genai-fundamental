# PRD — Generative Image Suite (Proyek Image Generation)

**Submission — Dicoding: Belajar Fundamental Generative AI (BFGAI)**
Penulis: Vika Putri Ariyanti
Tanggal: 20 Juli 2026
Target nilai: **Bintang 5 / A / Advanced (4 pts)**

---

## 1. Latar Belakang

Dari sisi pengguna, layanan seperti Gemini atau DALL·E terasa instan: ketik prompt,
gambar muncul. Proyek ini menempatkan kita di sisi sebaliknya — sebagai *engineer* yang
memahami pipeline difusi di balik layar: kontrol seed agar hasil dapat diulang,
pengaruh guidance scale dan inference steps, pergantian algoritma sampling, serta
manipulasi kanvas dan masker untuk inpainting dan outpainting.

Hasil akhirnya bukan kode statis di notebook, melainkan **Generative Image Suite** —
aplikasi web Streamlit yang menyatukan text-to-image, inpainting, dan outpainting
dalam satu antarmuka.

## 2. Tujuan Produk

Membangun aplikasi generative image **end-to-end** yang dapat dijalankan orang lain,
sekaligus mendemonstrasikan pemahaman atas parameter-parameter yang mengendalikan
kualitas keluaran model difusi.

### Sasaran terukur

| # | Sasaran | Indikator keberhasilan |
|---|---------|------------------------|
| G1 | Hasil generasi dapat direproduksi | Seed 222 menghasilkan gambar yang konsisten antar-run |
| G2 | Keluaran mendekati gambar acuan rubrik | Perbandingan visual side-by-side dengan gambar contoh |
| G3 | Pengaruh parameter terdokumentasi | Observasi tertulis untuk CFG, steps, dan 3 scheduler |
| G4 | Inpainting menambahkan objek sesuai target | Muncul *broken satellite* pada seed 9 |
| G5 | Aplikasi terbukti pernah berjalan | Video demo `.mp4` 1–5 menit |

### Non-Goals

- Tidak memakai SDXL (dilarang tips rubrik — rawan OOM).
- Tidak memakai arsitektur non-difusi (GAN, dsb.) — menyebabkan penolakan.
- Tidak menambah fitur di luar instruksi rubrik (lihat §4.1 no. 3).
- Tidak melakukan training atau fine-tuning model — proyek ini murni inferensi.

### 2.1 Ketentuan sebelum memulai

Submission ini terdiri atas dua tahapan: **eksperimen** (notebook Pipeline) dan
**pembuatan interface** (notebook Streamlit). Empat hal yang mengikat sejak awal:

1. **Notebook wajib jalan penuh tanpa error** sebelum dikirim, agar hasilnya dapat diverifikasi.
2. **Kerjakan berurutan: Basic → Skilled → Advanced.** Level atas hanya dinilai bila level
   di bawahnya sudah terpenuhi — melompat ke Advanced tanpa Basic tetap dihitung gagal.
3. **Keterbatasan komputasi → pakai GPU free tier** Google Colab atau Kaggle.
4. **Prompt bebas**, asalkan tidak mengandung unsur SARA atau hal negatif lainnya.
   Untuk keperluan perbandingan, **gunakan prompt yang sama** di seluruh eksperimen —
   ini bukan sekadar anjuran untuk F1.4, tetapi juga membuat perbandingan CFG, steps,
   dan scheduler menjadi apple-to-apple.

## 3. Ruang Lingkup Fungsional

### 3.1 Kriteria 1 — Text-to-Image

**Basic (2 pts)**
- **F1.1** `generate_simple_image()` memakai Stable Diffusion Pipeline dari `diffusers`,
  parameter: `prompt`, `negative_prompt`, `seed`.
- **F1.2** `generate_advanced_image()` dengan model & pipeline sama, parameter tambahan:
  `guidance_scale`, `num_inference_steps`.
- **F1.3** Generasi memakai **seed 222** dan negative prompt wajib:
  `"photorealistic, realistic, photograph, 3d render, messy, blurry, low quality, bad art, ugly, sketch, grainy, unfinished, chromatic aberration"`.
  Hasil dibandingkan dengan gambar acuan di template.
- **F1.4** Prompt pada kedua fungsi **wajib identik** agar perbandingan objektif.

**Skilled (3 pts)** — semua Basic terpenuhi, ditambah:
- **F1.5** Eksperimen beberapa nilai **guidance scale** (mis. 1.5 / 7.5 / 15) + observasi tertulis:
  tingkat detail, kesesuaian dengan prompt, variasi visual.
- **F1.6** Eksperimen **inference steps**: step rendah (5–15) vs step tinggi (30–50) + observasi
  tertulis: ketajaman, noise/artefak, kehalusan, stabilitas visual.
- **F1.7** Seluruh observasi ditulis di **bagian notebook yang sudah disediakan**, bukan sel baru.

**Advanced (4 pts)** — semua Skilled terpenuhi, ditambah:
- **F1.8** **Batch inference** 4 gambar sekaligus, ditampilkan sebagai **grid 2×2**.
- **F1.9** `load_scheduler(pipe, scheduler_name)` — mengganti algoritma sampling
  **tanpa memuat ulang model**, mendukung: **Euler A**, **DPM++**, **DDIM**.
- **F1.10** Observasi tertulis karakteristik hasil ketiga scheduler.

### 3.2 Kriteria 2 — Image-to-Image

**Basic (2 pts)**
- **F2.1** `inpaint_engine(image, mask, prompt)` memakai model khusus inpainting
  (lihat §4.2 — ID resmi rubrik sudah tidak tersedia).
- **F2.2** Masking **manual/hardcode** melalui pendekatan *trial and error*.
- **F2.3** Hasil menambahkan **broken satellite** menyerupai gambar acuan, **seed 9**.

**Skilled (3 pts)** — semua Basic terpenuhi, ditambah:
- **F2.4** Masking otomatis memakai **model segmentation**.
- **F2.5** `prepare_outpainting()` — memperluas kanvas ke **satu arah** (kiri/kanan/atas/bawah).
- **F2.6** Outpainting satu sisi, memakai **gambar hasil inpainting** sebagai input.

**Advanced (4 pts)** — semua Skilled terpenuhi, ditambah:
- **F2.7** Logika outpainting bertahap ke berbagai arah untuk fitur **"Zoom Out"**.
- **F2.8** **Refiner Pattern** dua tahap:
  - Stage 1: pipeline Base dengan `denoising_end=0.8` menghasilkan latent.
  - Stage 2: latent dioper ke pipeline **Img2Img** dengan `denoising_start=0.8`.
  *(Lihat §4.3 — ada pertentangan antara ketentuan ini dan larangan SDXL.)*

### 3.3 Kriteria 3 — Interface Streamlit

**Basic (2 pts)**
- **F3.1** Melengkapi logic generate pada **template Streamlit yang disediakan**.
- **F3.2** Komponen wajib: text input `prompt` & `negative_prompt`; slider `guidance_scale`
  dan `num_inference_steps`; tombol **Generate**.
- **F3.3** Gambar hasil **tampil langsung di layar** setelah proses selesai.
- **F3.4** **Screen record 1–5 menit** memperlihatkan antarmuka, disimpan `.mp4`.

**Skilled (3 pts)** — semua Basic terpenuhi, ditambah:
- **F3.5** Input `num_images` → batch generation ditampilkan **grid 2×2**.
- **F3.6** **Selectbox** scheduler: Euler A / DPM++ / DDIM.
- **F3.7** Tombol **"Clear Memory"** memanggil `gc.collect()` dan `torch.cuda.empty_cache()`.

**Advanced (4 pts)** — semua Skilled terpenuhi, ditambah:
- **F3.8** **Tab baru** khusus Inpainting & Outpainting (zoom-out) atas gambar hasil generasi.
- **F3.9** Integrasi **`streamlit-drawable-canvas`** — pengguna mencoret langsung di browser
  untuk membentuk mask, lalu dikirim ke fungsi inpainting.

## 4. Batasan Wajib (Constraints)

| Aspek | Ketentuan |
|-------|-----------|
| Bahasa | Python |
| Library | `diffusers` — Stable Diffusion Pipeline |
| Model T2I | Stable Diffusion v1.5 (lihat §4.2) |
| Model inpainting | Stable Diffusion Inpainting (lihat §4.2) |
| Dilarang | **SDXL** — kata kunci `sdxl`, `stable-diffusion-xl`, `sd-xl` pada nama repo |
| Dilarang | Arsitektur non-difusi (GAN, dsb.) |
| Seed | **222** untuk Kriteria 1, **9** untuk inpainting |
| Negative prompt | String wajib persis seperti pada F1.3 |
| Template | Struktur template **tidak boleh diubah**; observasi ditulis di bagian yang disediakan |
| Efisiensi | **Jangan memuat ulang model** untuk task yang bisa berbagi checkpoint |
| Notebook | Semua sel sudah dijalankan, output tersimpan, bebas error |
| Secret | Authtoken ngrok lewat environment variable, bukan literal di sel |

### 4.1 Larangan — penyebab Submission Ditolak

1. Tidak melampirkan berkas yang diminta (§6).
2. **Tidak memakai, atau mengubah struktur, template yang disediakan.**
3. **Menambahkan kode atau fitur di luar instruksi.** → Tahan diri dari "kreativitas ekstra";
   kerjakan tepat sesuai rubrik.
4. Notebook tidak dijalankan lebih dulu sehingga output sel tidak terekam.
5. Tidak menampilkan hasil generate pada antarmuka Streamlit.
6. Tidak mengimplementasikan fitur wajib berurutan (Basic → Skilled → Advanced).
7. Memakai model/pipeline di luar anjuran (mis. GAN alih-alih Stable Diffusion).

### 4.2 ⚠️ Risiko kritis — model yang diwajibkan sudah dihapus

Rubrik mewajibkan `runwayml/stable-diffusion-v1-5` dan `runwayml/stable-diffusion-inpainting`.
**Kedua repositori itu sudah tidak ada.** RunwayML membubarkan organisasinya di Hugging Face,
dan ID tersebut kini mengembalikan **404**
([issue diffusers #9322](https://github.com/huggingface/diffusers/issues/9322),
[forum HF](https://discuss.huggingface.co/t/license-agreement-error-runwayml-stable-diffusion-v1-5-returns-404/161673)).

Artinya sel pertama notebook akan gagal apa pun yang dilakukan. Rencana penanganan:

| Kebutuhan | Repo pengganti |
|---|---|
| Text-to-image | [`stable-diffusion-v1-5/stable-diffusion-v1-5`](https://huggingface.co/stable-diffusion-v1-5/stable-diffusion-v1-5) |
| Inpainting | `stable-diffusion-v1-5/stable-diffusion-inpainting` (verifikasi ketersediaannya lebih dulu) |

Ini **bobot dan arsitektur yang identik** — hanya berpindah organisasi, bukan berganti model,
sehingga tidak melanggar larangan no. 7. Tindakan yang harus diambil:

1. **Tanyakan ke forum diskusi** sebelum mengerjakan, dan simpan tangkapan layar jawabannya.
2. Definisikan ID model sebagai **satu konstanta** di awal notebook agar mudah diganti.
3. Tulis **sel markdown penjelasan** tepat di atas sel pemuatan model, sertakan tautan bukti
   bahwa repo asli 404 — supaya reviewer memahami ini bukan penggantian model sepihak.

### 4.3 ⚠️ Pertentangan internal rubrik — Refiner Pattern vs larangan SDXL

**F2.8** meminta `denoising_end=0.8` dan `denoising_start=0.8`. Kedua parameter itu adalah
milik pipeline **SDXL base+refiner**; `StableDiffusionPipeline` v1.5 tidak menerimanya —
img2img SD1.5 memakai parameter `strength`. Padahal tips rubrik melarang SDXL.

Rencana penanganan: **tanyakan ke forum diskusi**, lalu ambil pendekatan yang menghormati
kedua ketentuan — mengemulasi pola dua tahap di SD1.5:

- Stage 1: base pipeline dijalankan sampai ~80% langkah dengan `output_type="latent"`.
- Stage 2: latent dioper ke `StableDiffusionImg2ImgPipeline` dengan `strength≈0.2`
  (setara melanjutkan 20% sisa denoising).

Sertakan sel markdown yang menjelaskan pemetaan `denoising_end/start` → `strength`, agar
terlihat bahwa ketentuan dipahami, bukan diabaikan.

### 4.4 Pengelolaan Secret (ngrok)

Streamlit di Colab diekspos ke publik lewat ngrok, jadi diperlukan authtoken pribadi.

**Cara memperolehnya:**
1. Buka ngrok.com, lalu **sign up / sign in** (akun Google bisa dipakai).
2. Setelah masuk ke homepage, buka bagian **"Your Authtoken"**.
3. Salin token yang tampil, kembali ke notebook.

Authtoken **tidak boleh** ditulis sebagai literal di sel:

```python
from google.colab import userdata
import os
os.environ["NGROK_AUTH_TOKEN"] = userdata.get("NGROK_AUTH_TOKEN")
```

Sebelum submit, telusuri notebook — token tidak boleh tersisa di source maupun output sel,
termasuk pada output `ngrok.connect()` atau traceback.

### 4.5 Efisiensi model — satu instance, banyak task

Tips rubrik: **hindari memuat ulang model berulang kali**. Selama perbedaan antar-task hanya
pada *parameter* atau *treatment*, tidak perlu inisialisasi model baru. Keuntungannya:
waktu loading lebih singkat, serta VRAM dan disk lebih hemat.

Penerapan pada proyek ini:

| Task | Instance |
|---|---|
| `generate_simple_image()` | ← SD v1.5, **satu instance** |
| `generate_advanced_image()` | ← instance yang sama |
| Eksperimen CFG & steps | ← instance yang sama |
| Batch 4 gambar & grid 2×2 | ← instance yang sama |
| Pergantian scheduler | ← instance yang sama (justru inti dari `load_scheduler()`) |
| Img2Img / refiner stage 2 | ← boleh berbagi komponen dari instance yang sama |
| `inpaint_engine()` | **instance terpisah** — checkpoint inpainting punya UNet 9-channel, arsitekturnya memang berbeda |

Praktik pendukung: `pipe.enable_attention_slicing()`, dan panggil `gc.collect()` +
`torch.cuda.empty_cache()` di antara tahap berat (fungsi yang sama dipakai tombol
**Clear Memory** pada F3.7).

### 4.6 Larangan SDXL — cara mengenalinya

SDXL punya parameter dan kebutuhan memori yang jauh lebih besar, rawan **OOM** terutama saat
memuat lebih dari satu model. Kenali dari nama repositorinya — hampir selalu mengandung:

- `sdxl`
- `stable-diffusion-xl`
- `sd-xl`

Contoh yang **harus dihindari**: `stabilityai/stable-diffusion-xl-base-1.0`,
`stabilityai/stable-diffusion-xl-refiner-1.0`.

Konsekuensinya untuk F2.8 dibahas di §4.3 — pola *refiner* wajib diemulasi di SD1.5,
bukan dengan memanggil pipeline SDXL.

## 5. Arsitektur Sistem

```
                    ┌──────────────────────────────────────────────┐
                    │  SD v1.5 checkpoint — DIMUAT SATU KALI       │
                    │  (dibagi ke semua task text-to-image)        │
                    └───────┬──────────────────────────────────────┘
                            │
   prompt + negative ──────▶│ generate_simple_image()    seed 222
                            │ generate_advanced_image()  + cfg, steps
                            │ load_scheduler()  Euler A / DPM++ / DDIM
                            │ batch 4 ──▶ grid 2×2
                            ▼
                      gambar hasil generasi
                            │
        ┌───────────────────┴────────────────────┐
        ▼                                        ▼
  mask manual (hardcode)                  mask otomatis (segmentation)
        └───────────────────┬────────────────────┘
                            ▼
        ┌──────────────────────────────────────────┐
        │  SD Inpainting checkpoint (terpisah)     │
        │  inpaint_engine(image, mask, prompt)     │  seed 9
        └───────────────────┬──────────────────────┘
                            ▼
                   prepare_outpainting()  ──▶  Zoom Out bertahap
                            ▼
              Refiner dua tahap: Base (80%) ──▶ Img2Img (20%)
                            ▼
   ┌────────────────────────────────────────────────────────────┐
   │  Streamlit — ngrok                                          │
   │  Tab 1: Text-to-Image (prompt, slider, scheduler, grid 2×2, │
   │          tombol Generate & Clear Memory)                    │
   │  Tab 2: Inpaint & Outpaint (drawable-canvas → mask)         │
   └────────────────────────────────────────────────────────────┘
                            ▼
                  Screen record .mp4 (1–5 menit)
```

## 6. Deliverable

```
BFGAI_Vika-Putri-Ariyanti.zip
├── Pipeline_submission_BFGAI_Vika-Putri-Ariyanti.ipynb
├── Streamlit_submission_BFGAI_Vika-Putri-Ariyanti.ipynb
├── video_demo_aplikasi_BFGAI.mp4
└── requirements.txt
```

Catatan berkas:
- Kedua notebook **dikerjakan di atas template yang disediakan** — awali dengan mengunduh
  `[Template]_Pipeline_...` dan `[Template]_Streamlit_...`, lalu hapus prefiks `[Template]_`.
- Semua sel **sudah dijalankan** dan menyimpan output.
- Video `.mp4` berdurasi 1–5 menit, memperlihatkan antarmuka benar-benar berjalan.

### 6.1 Menyiapkan `requirements.txt`

| Cara | Perilaku | Catatan |
|------|----------|---------|
| `pip freeze > requirements.txt` | Semua paket di environment + versinya | Lengkap tapi berisik di Colab |
| `pipreqs /path/to/project` | Hanya yang benar-benar di-`import` | Ringkas, bisa melewatkan dependensi tak langsung |

Rekomendasi: mulai dari `pipreqs`, lalu pin manual versi kritikal (`diffusers`, `transformers`,
`torch`, `accelerate`, `safetensors`, `streamlit`, `streamlit-drawable-canvas`, `pyngrok`,
`pillow`) dari hasil `pip freeze`.

### 6.2 Ekspor Notebook

Colab: **File → Download → Download .ipynb**, dilakukan **setelah** semua sel dijalankan.

### 6.3 Proses Review

- Review selambatnya **3 hari kerja** (di luar Sabtu, Minggu, libur nasional).
- Hindari submit berulang — memperlambat penilaian.
- Hasil dikirim via email atau dicek di status submission akun Dicoding.

## 7. Rencana Pengerjaan

| Tahap | Aktivitas | Output |
|-------|-----------|--------|
| T0 | Tanya forum diskusi soal model 404 (§4.2) & refiner-vs-SDXL (§4.3) | keputusan tertulis |
| T1 | Unduh template, setup Colab GPU, pin versi `diffusers` | environment stabil |
| T2 | Muat SD v1.5 **satu instance**, implementasi F1.1–F1.4 (seed 222) | Kriteria 1 Basic |
| T3 | Eksperimen CFG & steps + tulis observasi | F1.5–F1.7 |
| T4 | Batch 4 → grid 2×2, `load_scheduler()`, observasi 3 scheduler | F1.8–F1.10 |
| T5 | `inpaint_engine()` + mask hardcode trial-and-error, seed 9 | F2.1–F2.3 |
| T6 | Mask otomatis via segmentation, `prepare_outpainting()`, outpaint 1 sisi | F2.4–F2.6 |
| T7 | Zoom Out bertahap + refiner dua tahap | F2.7, F2.8 |
| T8 | Lengkapi template Streamlit: input, slider, generate, tampil gambar | F3.1–F3.4 |
| T9 | `num_images` grid 2×2, selectbox scheduler, Clear Memory | F3.5–F3.7 |
| T10 | Tab inpaint/outpaint + `streamlit-drawable-canvas` | F3.8, F3.9 |
| T11 | Jalankan via ngrok, rekam layar 1–5 menit → `.mp4` | video demo |
| T12 | Rerun kedua notebook end-to-end, susun berkas & zip | deliverable |

## 8. Definition of Done

- [ ] Kedua notebook jalan penuh tanpa error, output tersimpan
- [ ] Struktur template **tidak diubah**; observasi ditulis di bagian yang disediakan
- [ ] **Tidak ada fitur tambahan** di luar instruksi rubrik
- [ ] `generate_simple_image()` & `generate_advanced_image()` sesuai parameter yang diminta
- [ ] Prompt identik di kedua fungsi; seed 222; negative prompt persis
- [ ] Hasil generasi mendekati gambar acuan (bandingkan berdampingan)
- [ ] Observasi tertulis: guidance scale (rendah vs tinggi), steps (rendah vs tinggi)
- [ ] Batch 4 gambar tampil grid 2×2
- [ ] `load_scheduler()` mendukung Euler A / DPM++ / DDIM **tanpa reload model**
- [ ] Observasi tertulis ketiga scheduler
- [ ] `inpaint_engine()` memakai checkpoint inpainting; mask hardcode; seed 9; muncul broken satellite
- [ ] Mask otomatis via model segmentation
- [ ] `prepare_outpainting()` satu arah; outpaint memakai hasil inpainting
- [ ] Zoom Out bertahap multi-arah
- [ ] Refiner dua tahap (base → img2img) terimplementasi & dijelaskan
- [ ] Streamlit: text input, 2 slider, tombol Generate, gambar tampil di layar
- [ ] `num_images` + grid 2×2, selectbox scheduler, tombol Clear Memory berfungsi
- [ ] Tab inpaint/outpaint + drawable-canvas mengirim mask ke inpainting
- [ ] Video `.mp4` 1–5 menit memperlihatkan aplikasi berjalan
- [ ] Tidak memakai SDXL di titik mana pun
- [ ] Authtoken ngrok tidak terlihat di source maupun output sel
- [ ] Zip berisi tepat 4 berkas sesuai §6

## 9. Risiko & Mitigasi

| Risiko | Dampak | Mitigasi |
|--------|--------|----------|
| **Model `runwayml/*` 404** | Notebook gagal sejak sel pertama | Pakai mirror resmi, konfirmasi ke forum, dokumentasikan (§4.2) |
| **Refiner Pattern menuntut API SDXL** | Advanced K2 tak tercapai / melanggar larangan SDXL | Emulasi dua tahap di SD1.5 via `strength`, jelaskan pemetaannya (§4.3) |
| Menambah fitur "biar bagus" | **Ditolak** (larangan no. 3) | Kerjakan tepat sesuai rubrik; tahan diri dari improvisasi |
| Mengubah struktur template | **Ditolak** (larangan no. 2) | Isi sel yang disediakan; jangan menata ulang bagian |
| OOM saat memuat >1 model | Sesi mati | Satu instance SD1.5 dibagi lintas task; `enable_attention_slicing()`; Clear Memory antar-tahap |
| Hasil jauh dari gambar acuan | K1 Reject | Iterasi prompt dengan seed 222 dikunci; bandingkan berdampingan tiap percobaan |
| Mask hardcode meleset | K2 Reject | Trial-and-error dengan overlay mask divisualisasikan tiap percobaan |
| Sesi ngrok putus saat merekam | Tidak ada bukti video | Rekam segera setelah aplikasi hidup; simpan langsung ke Drive |
| Token ngrok bocor di output | Risiko keamanan | `userdata.get()`; audit output sebelum ekspor (§4.4) |
| Ketidakcocokan versi `diffusers` | Notebook error saat direview | Pin versi di `requirements.txt`, rerun penuh sebelum zip |

## 10. Metrik Evaluasi Kualitas

- **Reproduktibilitas:** dua run dengan seed sama → gambar identik.
- **Kesesuaian acuan:** perbandingan visual berdampingan dengan gambar contoh rubrik.
- **Kualitas observasi:** setiap eksperimen menyebutkan perubahan visual yang *terlihat*,
  bukan sekadar teori parameter.
- **Kelengkapan antarmuka:** setiap komponen wajib terlihat dan berfungsi di video demo.

## 11. Perhitungan & Tabel Penilaian

```
Nilai Akhir = Total Points / Jumlah Kriteria
```

Formula ini berlaku bila setiap kriteria memperoleh minimal 2 pts — **satu kriteria yang
ditolak menggugurkan perhitungan**, bukan sekadar menurunkan rata-rata.

| Nilai Akhir | Nilai Dicoding | Huruf | Level of Mastery | Makna |
|---|---|---|---|---|
| < 1 | Rejected | E | — | Tidak lulus |
| 1 – <2 | Bintang 2 | D | Below Basic | Kurang |
| 2 – <3 | Bintang 3 | C | Basic | Cukup |
| 3 – <4 | Bintang 4 | B | Skilled | Mahir |
| **4** | **Bintang 5** | **A** | **Advanced** | **Tingkat lanjut** |

**Simulasi target proyek ini:** (4 + 4 + 4) ÷ 3 = **4,0 → Bintang 5 / A / Advanced**

Konsekuensi penting dari pembagi 3: nilai 4,0 hanya tercapai bila **ketiganya** Advanced.
Satu kriteria yang berhenti di Skilled sudah menurunkan hasil ke (4+4+3)÷3 ≈ 3,67 →
Bintang 4. Jadi tidak ada kriteria yang boleh "dikorbankan" — termasuk Kriteria 3 yang
terlihat paling ringan.
