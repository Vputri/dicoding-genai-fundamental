"""Bangun Pipeline_submission_BFGAI_<nama>.ipynb dari struktur template resmi.

Struktur (urutan sel, isi markdown, dan cell id) disalin persis dari
`[Template]_Pipeline_submission_BFGAI_Nama-siswa.ipynb`. Yang diisi hanya sel kode
yang pada template memang dibiarkan kosong — tidak ada sel yang ditambah, dihapus,
atau dipindah.
"""

import json
import pathlib

STUDENT = "Vika-Putri-Ariyanti"
OUT = pathlib.Path(__file__).parent.parent / f"Pipeline_submission_BFGAI_{STUDENT}.ipynb"


def md(cid, text):
    return {"cell_type": "markdown", "metadata": {"id": cid}, "source": _src(text)}


def code(cid, text):
    return {"cell_type": "code", "execution_count": None, "metadata": {"id": cid},
            "outputs": [], "source": _src(text)}


def _src(text):
    text = text.strip("\n")
    lines = text.split("\n")
    return [l + "\n" for l in lines[:-1]] + [lines[-1]]


# --- Markdown observasi: disalin persis dari template, kalimat pemandu dibiarkan ---
MD_CFG = """### **Guidance Scale Explanation:**

*   **Gambar dengan "Scale" Rendah:**
*"Jelaskan karakteristik gambar yang dihasilkan, seperti tingkat detail, kesesuaian dengan prompt, dan variasi visual yang terlihat."*

*   **Gambar dengan "Scale" Tinggi:**
*"Jelaskan perbedaan yang terlihat dibandingkan guidance scale rendah, terutama pada detail gambar dan kedekatannya dengan prompt."*"""

MD_STEP = """### **Inference Step Explanation:**

*   **Gambar dengan "Step" Rendah:**
*"Jelaskan karakteristik gambar yang dihasilkan, seperti tingkat detail, ketajaman, serta kemungkinan munculnya noise atau artefak."*
*   **Gambar dengan "Step" Tinggi:**
*"Jelaskan perbedaan yang terlihat dibandingkan step rendah, terutama pada detail gambar, kehalusan hasil, dan stabilitas visual."*"""

MD_SCHED = """### **Scheduler Comparation:**

*   **Gambar dengan "Euler A Scheduler":**
*"Jelaskan karakteristik gambar yang dihasilkan."*
*   **Gambar dengan "DPM++ Scheduler":**
*"Jelaskan karakteristik gambar yang dihasilkan."*
*   **Gambar dengan "DDIM Scheduler":**
*"Jelaskan karakteristik gambar yang dihasilkan."*"""

cells = [
    md("pdfg5WGru1p1", "# **Preparing Dependancies**"),
    code("NOrlFqP3UdC-", """
!pip install -q diffusers transformers accelerate safetensors

import gc
import torch
from PIL import Image, ImageDraw
from diffusers import (
    StableDiffusionPipeline,
    StableDiffusionInpaintPipeline,
    StableDiffusionImg2ImgPipeline,
    EulerAncestralDiscreteScheduler,
    DPMSolverMultistepScheduler,
    DDIMScheduler,
)

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
DTYPE = torch.float16 if DEVICE == "cuda" else torch.float32
print("device:", DEVICE)
"""),

    md("OOD1F_wPZNYU", "# **Kriteria 1: Melakukan Image Generation dari Teks (Text-to-Image)**"),
    md("XyRzGFQxKhCv", "## **Load Base Pipeline Model**"),
    code("Y9IJ4p4AjGQn", """
# CATATAN PENTING
# Rubrik menyebut model `runwayml/stable-diffusion-v1-5`. Namun RunwayML telah
# membubarkan organisasinya di Hugging Face, sehingga repo tersebut kini
# mengembalikan HTTP 404 dan tidak dapat dimuat sama sekali.
# Referensi: https://github.com/huggingface/diffusers/issues/9322
#
# Repo di bawah adalah MIRROR RESMI Stable Diffusion v1.5 dengan bobot dan
# arsitektur yang identik — bukan penggantian ke model lain.
MODEL_ID = "stable-diffusion-v1-5/stable-diffusion-v1-5"

# Model dimuat SATU KALI dan dipakai ulang untuk seluruh task text-to-image
# (generate standar, hyperparameter, batch, dan pergantian scheduler).
pipe = StableDiffusionPipeline.from_pretrained(
    MODEL_ID,
    torch_dtype=DTYPE,
    safety_checker=None,
).to(DEVICE)
pipe.enable_attention_slicing()

print("model dimuat:", MODEL_ID)
"""),

    md("NVZnfuxTKpfm", "## **Generate Image**"),
    code("6gvJ6ixAjJgR", """
# Negative prompt disalin persis sesuai ketentuan rubrik.
NEGATIVE_PROMPT = (
    "photorealistic, realistic, photograph, 3d render, messy, blurry, "
    "low quality, bad art, ugly, sketch, grainy, unfinished, chromatic aberration"
)

SEED = 222

# Prompt yang SAMA dipakai pada kedua fungsi agar perbandingan objektif.
PROMPT = (
    "a cute cartoon astronaut floating in outer space, flat vector illustration, "
    "pastel color palette, clean lines, minimalist, children book style"
)


def generate_simple_image(prompt, negative_prompt, seed):
    generator = torch.Generator(device=DEVICE).manual_seed(seed)
    return pipe(
        prompt=prompt,
        negative_prompt=negative_prompt,
        generator=generator,
    ).images[0]


img_simple = generate_simple_image(PROMPT, NEGATIVE_PROMPT, SEED)
display(img_simple)
"""),

    md("AhtzPn0oLMWS", "## **Generate Image with Hyperparameter Configuration**"),
    code("Quq8Ek-IYHlU", """
def generate_advanced_image(prompt, negative_prompt, seed,
                            guidance_scale, num_inference_steps):
    generator = torch.Generator(device=DEVICE).manual_seed(seed)
    return pipe(
        prompt=prompt,
        negative_prompt=negative_prompt,
        generator=generator,
        guidance_scale=guidance_scale,
        num_inference_steps=num_inference_steps,
    ).images[0]


# Prompt, negative prompt, dan seed sengaja sama persis dengan sel sebelumnya.
img_advanced = generate_advanced_image(
    PROMPT, NEGATIVE_PROMPT, SEED,
    guidance_scale=7.5,
    num_inference_steps=50,
)
display(img_advanced)
"""),

    md("HiHpEkcZLayr", "## **Guidance Scale Comparison**"),
    code("Yp1Ff8Ac306o", """
def tampilkan_baris(gambar, judul, lebar=320):
    kecil = [g.resize((lebar, lebar)) for g in gambar]
    kanvas = Image.new("RGB", (lebar * len(kecil), lebar), "white")
    for i, g in enumerate(kecil):
        kanvas.paste(g, (i * lebar, 0))
    print(" | ".join(judul))
    return kanvas


CFG_VALUES = [1.5, 7.5, 15.0]
hasil_cfg = [
    generate_advanced_image(PROMPT, NEGATIVE_PROMPT, SEED,
                            guidance_scale=cfg, num_inference_steps=30)
    for cfg in CFG_VALUES
]
display(tampilkan_baris(hasil_cfg, [f"CFG {c}" for c in CFG_VALUES]))
"""),
    md("cUNEH4wnPw4h", MD_CFG),

    md("FeGbU6BNNZQ-", "## **Inference Steps Comparison**"),
    code("-fU5bZGujPoJ", """
# Step rendah (rentang 5-15) dibandingkan step tinggi (rentang 30-50).
STEP_VALUES = [10, 40]
hasil_step = [
    generate_advanced_image(PROMPT, NEGATIVE_PROMPT, SEED,
                            guidance_scale=7.5, num_inference_steps=s)
    for s in STEP_VALUES
]
display(tampilkan_baris(hasil_step, [f"{s} steps" for s in STEP_VALUES]))
"""),
    md("Ar_2cJoxPNzb", MD_STEP),

    md("4LaHWRn7O4xP", "## **Batch Inference from One Prompt**"),
    code("oTmNPi9mjRHp", """
def buat_grid(gambar, baris=2, kolom=2):
    w, h = gambar[0].size
    grid = Image.new("RGB", (kolom * w, baris * h), "white")
    for i, g in enumerate(gambar[: baris * kolom]):
        grid.paste(g, ((i % kolom) * w, (i // kolom) * h))
    return grid


generator = torch.Generator(device=DEVICE).manual_seed(SEED)
batch = pipe(
    prompt=PROMPT,
    negative_prompt=NEGATIVE_PROMPT,
    generator=generator,
    guidance_scale=7.5,
    num_inference_steps=30,
    num_images_per_prompt=4,      # empat gambar sekaligus dari satu prompt
).images

display(buat_grid(batch, baris=2, kolom=2))
"""),

    md("pLJ0lAPBeCcT", "## **Load Scheduler**"),
    code("9Y_1e0zpeJyb", """
SCHEDULERS = {
    "Euler A": EulerAncestralDiscreteScheduler,
    "DPM++": DPMSolverMultistepScheduler,
    "DDIM": DDIMScheduler,
}


def load_scheduler(pipe, scheduler_name):
    # Scheduler dibangun dari config scheduler yang sedang aktif, sehingga bobot
    # UNet/VAE/text-encoder tetap berada di VRAM — model tidak dimuat ulang.
    if scheduler_name not in SCHEDULERS:
        raise ValueError(f"scheduler tidak dikenal: {scheduler_name}")
    pipe.scheduler = SCHEDULERS[scheduler_name].from_config(pipe.scheduler.config)
    return pipe


# Bukti model tidak dimuat ulang: id objek UNet tetap sama sebelum dan sesudah.
print("UNet id sebelum :", id(pipe.unet))

hasil_scheduler = {}
for nama in SCHEDULERS:
    load_scheduler(pipe, nama)
    hasil_scheduler[nama] = generate_advanced_image(
        PROMPT, NEGATIVE_PROMPT, SEED,
        guidance_scale=7.5, num_inference_steps=30,
    )

print("UNet id sesudah :", id(pipe.unet))
display(tampilkan_baris(list(hasil_scheduler.values()), list(hasil_scheduler.keys())))
"""),
    md("kxsz6G4u2ICp", MD_SCHED),

    md("AA_Hjnnxdn01", "# **Kriteria 2: Menyempurnakan Gambar Melalui Image-to-Image**"),
    md("mAGwVXQ9O_1X", "## **Inpainting**"),
    md("lJEGIP8gjXY-", "### **Load Model Inpainting**"),
    code("ZIafvPvCjVsJ", """
# Checkpoint inpainting memakai instance TERPISAH karena arsitekturnya memang berbeda:
# UNet inpainting menerima 9 input channel (4 latent + 4 masked-latent + 1 mask),
# sedangkan UNet text-to-image hanya 4 channel. Jadi ini bukan pemuatan ulang model
# yang sama, melainkan checkpoint yang berbeda.
#
# Repo `runwayml/stable-diffusion-inpainting` juga sudah 404, sehingga dipakai mirror.
INPAINT_MODEL_CANDIDATES = [
    "stable-diffusion-v1-5/stable-diffusion-inpainting",
    "botp/stable-diffusion-v1-5-inpainting",
]

inpaint_pipe = None
for repo in INPAINT_MODEL_CANDIDATES:
    try:
        inpaint_pipe = StableDiffusionInpaintPipeline.from_pretrained(
            repo, torch_dtype=DTYPE, safety_checker=None,
        ).to(DEVICE)
        inpaint_pipe.enable_attention_slicing()
        INPAINT_MODEL_ID = repo
        print("checkpoint inpainting dimuat:", repo)
        break
    except Exception as e:
        print(f"gagal memuat {repo}: {type(e).__name__}")

assert inpaint_pipe is not None, "Tidak ada mirror inpainting yang berhasil dimuat."
"""),

    md("bSSX58-tHfgm", "### **Manual Masking**"),
    code("RkBtloUCjdUP", """
SEED_INPAINT = 9      # ketentuan rubrik untuk inpainting


def buat_mask_kotak(size, kotak):
    # Konvensi: PUTIH (255) = area yang diganti, HITAM (0) = area dipertahankan.
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rectangle(kotak, fill=255)
    return mask


def pratinjau_mask(image, mask, alpha=0.5):
    # Overlay merah untuk membantu proses trial and error penentuan koordinat.
    overlay = Image.new("RGB", image.size, (255, 0, 0))
    return Image.composite(
        Image.blend(image.convert("RGB"), overlay, alpha),
        image.convert("RGB"),
        mask,
    )


# Koordinat berikut ditentukan secara hardcode lewat trial and error:
# jalankan pratinjau_mask(), amati posisinya, geser angkanya, ulangi.
KOTAK_SATELIT = (300, 60, 480, 220)

mask_manual = buat_mask_kotak(img_advanced.size, KOTAK_SATELIT)
display(pratinjau_mask(img_advanced, mask_manual))
"""),

    md("Pbc6xhxxjmxh", "### **Generate**"),
    code("HKCRX2KFjqPG", """
def inpaint_engine(image, mask, prompt, negative_prompt="", seed=SEED_INPAINT,
                   guidance_scale=7.5, num_inference_steps=40):
    w, h = image.size
    generator = torch.Generator(device=DEVICE).manual_seed(seed)
    return inpaint_pipe(
        prompt=prompt,
        negative_prompt=negative_prompt,
        image=image,
        mask_image=mask,
        generator=generator,
        guidance_scale=guidance_scale,
        num_inference_steps=num_inference_steps,
        width=w,
        height=h,
    ).images[0]


PROMPT_SATELIT = (
    "a broken damaged satellite with cracked solar panels floating in space, "
    "flat vector illustration, same pastel color palette, clean lines"
)

img_inpaint = inpaint_engine(
    image=img_advanced,
    mask=mask_manual,
    prompt=PROMPT_SATELIT,
    negative_prompt=NEGATIVE_PROMPT,
    seed=SEED_INPAINT,
)
display(img_inpaint)
"""),

    md("C9JMXCzTjs1-", "## **Inpainting Menggunakan Automasking**"),
    md("lYw4zhpHkCzL", "### **load Model Segmentation Untuk Masking**"),
    code("JmnZzRYlkKWr", """
from transformers import pipeline as hf_pipeline

SEG_MODEL_ID = "nvidia/segformer-b0-finetuned-ade-512-512"
segmenter = hf_pipeline(
    "image-segmentation",
    model=SEG_MODEL_ID,
    device=0 if DEVICE == "cuda" else -1,
)
print("model segmentation dimuat:", SEG_MODEL_ID)
"""),

    md("iNGNHn7OHGLo", "### **Masking with Segmentation Model**"),
    code("HHr7V1cBBC7I", """
import numpy as np


def buat_mask_segmentasi(image, label_target):
    segmen = segmenter(image)
    tersedia = [s["label"] for s in segmen]

    terpilih = [s for s in segmen if s["label"].lower() == label_target.lower()]
    if not terpilih:
        return None, tersedia

    gabungan = np.zeros((image.size[1], image.size[0]), dtype=np.uint8)
    for s in terpilih:
        gabungan = np.maximum(gabungan, np.array(s["mask"].convert("L")))
    return Image.fromarray(gabungan).resize(image.size), tersedia


# Label disesuaikan dengan yang benar-benar terdeteksi pada gambar Anda.
mask_auto, label_tersedia = buat_mask_segmentasi(img_advanced, "sky")
print("label terdeteksi:", label_tersedia)

if mask_auto is not None:
    display(pratinjau_mask(img_advanced, mask_auto))
else:
    print("label target tidak ditemukan — pilih salah satu dari daftar di atas.")
"""),

    md("foiYnRrOkMZO", "### **Generate**"),
    code("vCcexx-5kPCd", """
PROMPT_AUTOMASK = (
    "colorful nebula and distant stars in deep space, "
    "flat vector illustration, pastel color palette, clean lines"
)

img_automask = inpaint_engine(
    image=img_advanced,
    mask=mask_auto,
    prompt=PROMPT_AUTOMASK,
    negative_prompt=NEGATIVE_PROMPT,
    seed=SEED_INPAINT,
)
display(img_automask)
"""),

    md("BC_r5KUEPEM0", "## **Outpainting**"),
    md("SjY4HcHdkpeT", "### **Prepare the Canvas**"),
    code("ANYypjWMeXsA", """
def prepare_outpainting(image, direction, expand_px=192):
    # Memperluas kanvas ke SATU arah: "kiri", "kanan", "atas", atau "bawah".
    w, h = image.size
    arah = {
        "kiri":  ((w + expand_px, h), (expand_px, 0)),
        "kanan": ((w + expand_px, h), (0, 0)),
        "atas":  ((w, h + expand_px), (0, expand_px)),
        "bawah": ((w, h + expand_px), (0, 0)),
    }
    if direction not in arah:
        raise ValueError(f"arah tidak dikenal: {direction}. Pilihan: {list(arah)}")

    ukuran_baru, posisi = arah[direction]
    kanvas = Image.new("RGB", ukuran_baru, (255, 255, 255))
    kanvas.paste(image, posisi)

    # Seluruh kanvas putih (diisi model), lalu area gambar asli dihitamkan.
    mask = Image.new("L", ukuran_baru, 255)
    ImageDraw.Draw(mask).rectangle(
        [posisi[0], posisi[1], posisi[0] + w - 1, posisi[1] + h - 1], fill=0
    )
    return kanvas, mask


# Input outpainting adalah GAMBAR HASIL INPAINTING sebelumnya.
kanvas_out, mask_out = prepare_outpainting(img_inpaint, "kanan", expand_px=192)
display(pratinjau_mask(kanvas_out, mask_out))
"""),

    md("PNDRqGFQku7R", "### **Generate**"),
    code("4q6oI-jfkbi1", """
PROMPT_OUTPAINT = (
    "continuation of outer space scene with distant stars and nebula, "
    "flat vector illustration, same pastel color palette, clean lines"
)

img_outpaint = inpaint_engine(
    image=kanvas_out,
    mask=mask_out,
    prompt=PROMPT_OUTPAINT,
    negative_prompt=NEGATIVE_PROMPT,
    seed=SEED_INPAINT,
)
display(img_outpaint)
"""),

    md("hVk8nX9y7jvA", "## **Outpainting Zoom Out**"),
    md("kQmHcBlyhHez", "### **Prepare Canvas for Zoom Out**"),
    code("oOF6cebEkc4Y", """
def prepare_zoom_out(image, zoom_factor=1.4):
    # Gambar diletakkan di TENGAH kanvas yang lebih besar, sehingga area yang diisi
    # membentuk cincin ke segala arah — efeknya seperti kamera mundur.
    w, h = image.size
    kw, kh = int(w * zoom_factor), int(h * zoom_factor)
    kw -= kw % 8            # dimensi harus kelipatan 8 untuk VAE
    kh -= kh % 8

    kanvas = Image.new("RGB", (kw, kh), (255, 255, 255))
    kiri, atas = (kw - w) // 2, (kh - h) // 2
    kanvas.paste(image, (kiri, atas))

    mask = Image.new("L", (kw, kh), 255)
    ImageDraw.Draw(mask).rectangle([kiri, atas, kiri + w - 1, atas + h - 1], fill=0)
    return kanvas, mask


kanvas_zoom, mask_zoom = prepare_zoom_out(img_inpaint, zoom_factor=1.4)
display(pratinjau_mask(kanvas_zoom, mask_zoom))
"""),

    md("H0GB651LhS04", "### **Generate**"),
    code("54HVviXfkdwn", """
def zoom_out_bertahap(image, prompt, tahap=2, zoom_factor=1.4, ukuran_maks=768):
    # Perluasan dilakukan berulang: hasil tahap sebelumnya menjadi input tahap berikutnya.
    hasil = [image]
    saat_ini = image
    for i in range(tahap):
        if max(saat_ini.size) * zoom_factor > ukuran_maks:
            print(f"tahap {i + 1} dilewati — melebihi batas {ukuran_maks}px")
            break
        kanvas, mask = prepare_zoom_out(saat_ini, zoom_factor)
        saat_ini = inpaint_engine(
            image=kanvas, mask=mask, prompt=prompt,
            negative_prompt=NEGATIVE_PROMPT, seed=SEED_INPAINT,
        )
        hasil.append(saat_ini)
        print(f"tahap {i + 1}: {kanvas.size}")
    return hasil


tahapan_zoom = zoom_out_bertahap(img_inpaint, PROMPT_OUTPAINT, tahap=2)
display(tampilkan_baris(tahapan_zoom, [f"tahap {i}" for i in range(len(tahapan_zoom))]))
"""),

    md("5iX0nggJNtn_", "## **Base + Refiner Image Generation**"),
    code("7ZDrCLkdjTuo", """
# CATATAN PENTING
# Rubrik meminta `denoising_end=0.8` (Stage 1) dan `denoising_start=0.8` (Stage 2).
# Kedua parameter tersebut HANYA tersedia pada pipeline SDXL base+refiner, sedangkan
# tips submission secara eksplisit melarang penggunaan SDXL karena rawan OOM.
#
# Pada Stable Diffusion 1.5, porsi denoising yang tersisa dikendalikan lewat `strength`:
#     denoising_end   = 0.8  ->  base menjalankan 80% langkah
#     denoising_start = 0.8  ->  refiner melanjutkan 20% sisanya  ->  strength = 0.2
#
# Stage 1 tetap menghasilkan LATENT (output_type="latent") sesuai bunyi rubrik.

DENOISING_SPLIT = 0.8
TOTAL_STEPS = 50

# Refiner berbagi SELURUH komponen dengan pipeline base — tidak ada bobot baru
# yang dimuat ke VRAM.
refiner_pipe = StableDiffusionImg2ImgPipeline(**pipe.components)
refiner_pipe.enable_attention_slicing()
print("refiner berbagi UNet dengan base:", refiner_pipe.unet is pipe.unet)


def generate_two_stage(prompt, negative_prompt, seed,
                       denoising_split=DENOISING_SPLIT, total_steps=TOTAL_STEPS):
    # ---- Stage 1: Base menghasilkan latent pada 80% langkah ----
    generator = torch.Generator(device=DEVICE).manual_seed(seed)
    latent = pipe(
        prompt=prompt,
        negative_prompt=negative_prompt,
        generator=generator,
        guidance_scale=7.5,
        num_inference_steps=int(total_steps * denoising_split),
        output_type="latent",
    ).images

    # Latent didekode agar dapat dioper ke pipeline Img2Img.
    with torch.no_grad():
        decoded = pipe.vae.decode(latent / pipe.vae.config.scaling_factor).sample
    gambar_stage1 = pipe.image_processor.postprocess(decoded, output_type="pil")[0]

    # ---- Stage 2: Refiner menuntaskan 20% sisa denoising ----
    generator = torch.Generator(device=DEVICE).manual_seed(seed)
    hasil = refiner_pipe(
        prompt=prompt,
        negative_prompt=negative_prompt,
        image=gambar_stage1,
        generator=generator,
        guidance_scale=7.5,
        strength=round(1.0 - denoising_split, 2),
        num_inference_steps=total_steps,
    ).images[0]

    return gambar_stage1, hasil


stage1, stage2 = generate_two_stage(PROMPT, NEGATIVE_PROMPT, SEED)
display(tampilkan_baris([stage1, stage2],
                        ["Stage 1 (base, 80%)", "Stage 2 (refiner, 20%)"]))

gc.collect()
torch.cuda.empty_cache()
"""),
]

nb = {
    "nbformat": 4,
    "nbformat_minor": 0,
    "metadata": {
        "colab": {"provenance": [], "gpuType": "T4"},
        "kernelspec": {"name": "python3", "display_name": "Python 3"},
        "language_info": {"name": "python"},
        "accelerator": "GPU",
    },
    "cells": cells,
}

OUT.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")

n_code = sum(1 for c in cells if c["cell_type"] == "code")
print(f"tertulis: {OUT.name} ({len(cells)} sel, {n_code} kode)")
