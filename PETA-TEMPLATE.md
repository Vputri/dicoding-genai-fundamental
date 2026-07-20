# Peta Template Resmi → Implementasi Referensi

Hasil pembacaan langsung kedua template Dicoding (via Google Drive, 20 Juli 2026).

- Pipeline: `[Template]_Pipeline_submission_BFGAI_Nama-siswa.ipynb`
  (`1LrsNIPwbgM4bg2bLYNbvy9eX_AEgnX1U`, pemilik `raiz@dicoding.com`)
- Streamlit: `[Template]_Streamlit_submission_BFGAI_Nama-siswa.ipynb`
  (`13ULZSc8FA-zVoOUkcDFk7RCRIRgqWB6M`)

Buka tautan Colab-nya → **File → Save a copy in Drive** → hapus prefiks `[Template]_`,
ganti `Nama-siswa` menjadi `Vika-Putri-Ariyanti`.

---

## ⚠️ Tiga temuan penting

### 1. Mengubah struktur DIPERBOLEHKAN

Sel pertama template Streamlit menyatakan eksplisit:

> "Jika Anda memiliki preferensi lain atau ingin mengubah struktur code pada logic
> ataupun pada interface Streamlit, itu **DIPERSILAHKAN** saja, tetapi pastikan untuk
> memenuhi kriteria yang telah ditetapkan pada instruksi submission."
>
> "Jika Anda tidak ingin mengubah apapun dan ingin mengikuti template, tugas Anda
> hanyalah melengkapi code yang rumpang pada bagian yang sudah ditandai `________`."

Artinya larangan penolakan no. 2 dan no. 3 jauh lebih longgar dari dugaan awal.
Jalur teraman tetap: **isi bagian `________` saja**, jangan menata ulang tanpa alasan.

### 2. `app.py` SUDAH JADI — jangan ditulis ulang

Template Streamlit sudah memuat `app.py` lengkap, dan menyatakan:

> "Anda **TIDAK perlu mengubah atau menambahkan** apapun pada file **app.py** ini,
> cukup **jalankan** saja."

`app.py` bawaan sudah memenuhi seluruh komponen Kriteria 3: text input prompt &
negative prompt, slider `steps` dan `cfg`, `number_input` seed, selectbox scheduler,
slider batch size, tombol Flush RAM, dua tab (GENERATE & EDIT), `st_canvas`, dan
`st.image()` untuk menampilkan hasil termasuk grid 2 kolom.

**Tugas Anda hanya mengisi `logic.py`.**

### 3. Template memanggil model yang sudah 404

Sel `logic.py` bagian Basic berisi loader yang diberi komentar `# MODEL LOADER (JANGAN DIUBAH)`:

```python
pipe_txt2img = StableDiffusionPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5", torch_dtype=torch.float16
).to(device)

pipe_inpaint = StableDiffusionInpaintPipeline.from_pretrained(
    "runwayml/stable-diffusion-inpainting", torch_dtype=torch.float16
).to(device)
```

Kedua repo itu **sudah dihapus RunwayML dan mengembalikan 404**, sehingga aplikasi
akan gagal di `get_models()` dan `st.stop()` terpanggil. Ini harus diubah meskipun
ada komentar "JANGAN DIUBAH" — tanpa itu tidak ada yang bisa berjalan.

Tanyakan ke forum diskusi, lalu ganti ke mirror resmi dan **beri komentar penjelasan**
di sel tersebut agar reviewer paham alasannya.

---

## Peta Notebook Pipeline

Seluruh sel kode template ini **kosong** (tanpa penanda `________`), jadi isi penuh
sesuai judul bagiannya.

| Judul sel di template | Referensi | Fitur |
|---|---|---|
| **Preparing Dependancies** | — | `!pip install` |
| **Kriteria 1** → Load Base Pipeline Model | `k1` §SETUP | Muat SD1.5 satu instance |
| Generate Image | `k1` F1.1 | `generate_simple_image()` |
| Generate Image with Hyperparameter Configuration | `k1` F1.2 | `generate_advanced_image()` |
| Guidance Scale Comparison | `k1` F1.5 | Eksperimen CFG |
| *(markdown) Guidance Scale Explanation* | — | **Tulis observasi di sini** |
| Inference Steps Comparison | `k1` F1.6 | Step rendah vs tinggi |
| *(markdown) Inference Step Explanation* | — | **Tulis observasi di sini** |
| Batch Inference from One Prompt | `k1` F1.8 | Batch 4 + grid 2×2 |
| Load Scheduler | `k1` F1.9 | `load_scheduler()` |
| *(markdown) Scheduler Comparation* | — | **Tulis observasi di sini** |
| **Kriteria 2** → Inpainting → Load Model Inpainting | `k2` §SETUP | Checkpoint inpainting |
| Inpainting → Manual Masking | `k2` F2.2 | `buat_mask_kotak()` + `pratinjau_mask()` |
| Inpainting → Generate | `k2` F2.1/F2.3 | `inpaint_engine()`, seed 9 |
| Automasking → load Model Segmentation | `k2` F2.4 | Muat model segmentation |
| Automasking → Masking with Segmentation Model | `k2` F2.4 | `buat_mask_segmentasi()` |
| Automasking → Generate | `k2` F2.4 | Inpaint dengan mask otomatis |
| Outpainting → Prepare the Canvas | `k2` F2.5 | `prepare_outpainting()` satu arah |
| Outpainting → Generate | `k2` F2.6 | Outpaint dari hasil inpainting |
| Outpainting Zoom Out → Prepare Canvas for Zoom Out | `k2` F2.7 | `prepare_zoom_out()` |
| Outpainting Zoom Out → Generate | `k2` F2.7 | `zoom_out_bertahap()` |
| **Base + Refiner Image Generation** | `k2` F2.8 | `generate_two_stage()` |

Markdown observasi sudah disediakan template lengkap dengan kalimat pemandu —
**ganti kalimat dalam tanda kutip miring itu dengan observasi Anda sendiri.**

---

## Peta Notebook Streamlit — `logic.py`

Isi hanya bagian bertanda `________`. Signature fungsi **sudah ditentukan template**
dan dipanggil `app.py`, jadi jangan diubah.

| Sel template | Fungsi | Referensi |
|---|---|---|
| `logic.py` (**Basic**) | `generate_image(...)` versi sederhana | `k3` §Basic |
| `logic.py` (**Skilled**) | `flush_memory()`, `set_scheduler()`, `generate_image()` batch | `k3` §Skilled |
| `logic.py` (**Advanced**) | `run_inpainting()`, `prepare_outpainting()` | `k3` §Advanced |

### Catatan signature

- `generate_image(pipe, prompt, neg_prompt, seed, steps, cfg, num_images=1, scheduler_name="Euler A")`
  — versi Basic **wajib mengembalikan list** (`return [image]`) agar cocok dengan `app.py`.
- `run_inpainting(pipe, image, mask, prompt, strength)` — punya parameter `strength`,
  berbeda dari `inpaint_engine()` di notebook Pipeline.
- `prepare_outpainting(image, expand_pixels=128)` — **memperluas ke SEGALA ARAH**
  (`app.py` menyebut "diperluas 128px ke segala arah"), berbeda dari versi satu arah
  di notebook Pipeline. Template sudah menyediakan background blur dan `inner_box`;
  Anda hanya melengkapi perhitungan dimensi dan satu `mask.paste()`.

### Sel ngrok

```python
auth_token = "YOUR_AUTHENTICATION_KEY"
```

Jangan tulis token literal di situ. Ganti menjadi pembacaan dari Colab Secrets
(lihat §4.4 PRD) agar tidak melanggar larangan kebocoran kredensial.
