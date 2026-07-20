"""Kriteria 1 — Text-to-Image (F1.1 – F1.10).

Implementasi referensi. Setiap blok ditandai kode fitur PRD dan dimaksudkan untuk
DISALIN ke sel yang bersesuaian pada template
`[Template]_Pipeline_submission_BFGAI_<nama>.ipynb`.

Jangan menambah fungsi di luar yang diminta rubrik (larangan no. 3).
Berkas ini tidak ikut ke dalam zip submission.
"""

import torch
from PIL import Image
from diffusers import (
    StableDiffusionPipeline,
    EulerAncestralDiscreteScheduler,
    DPMSolverMultistepScheduler,
    DDIMScheduler,
)

# =============================================================================
# SETUP — model dimuat SATU KALI, dibagi ke seluruh task Kriteria 1 (§4.5 PRD)
# =============================================================================

# CATATAN (tulis juga sebagai sel markdown tepat di atas sel ini):
# repo `runwayml/stable-diffusion-v1-5` sudah dihapus RunwayML dari Hugging Face dan
# mengembalikan 404. Repo di bawah adalah mirror resmi dengan bobot dan arsitektur
# identik — bukan pergantian model.
MODEL_ID = "stable-diffusion-v1-5/stable-diffusion-v1-5"

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
DTYPE = torch.float16 if DEVICE == "cuda" else torch.float32

pipe = StableDiffusionPipeline.from_pretrained(
    MODEL_ID,
    torch_dtype=DTYPE,
    safety_checker=None,
).to(DEVICE)
pipe.enable_attention_slicing()          # hemat VRAM

print("model dimuat:", MODEL_ID, "| device:", DEVICE)


# =============================================================================
# KONSTANTA — negative prompt & seed WAJIB persis seperti rubrik
# =============================================================================

# Disalin persis dari rubrik — jangan diketik ulang agar tidak ada selisih karakter.
NEGATIVE_PROMPT = (
    "photorealistic, realistic, photograph, 3d render, messy, blurry, "
    "low quality, bad art, ugly, sketch, grainy, unfinished, chromatic aberration"
)

SEED = 222

# Prompt yang SAMA dipakai kedua fungsi agar perbandingan objektif (F1.4).
# Sesuaikan dengan gambar acuan di template — ini titik awal, bukan jawaban final.
PROMPT = (
    "a cute cartoon astronaut floating in outer space, flat vector illustration, "
    "pastel color palette, clean lines, minimalist, children book style"
)


# =============================================================================
# F1.1 — generate_simple_image()
# =============================================================================

def generate_simple_image(prompt, negative_prompt, seed):
    """Generasi standar: hanya prompt, negative_prompt, dan seed."""
    generator = torch.Generator(device=DEVICE).manual_seed(seed)
    hasil = pipe(
        prompt=prompt,
        negative_prompt=negative_prompt,
        generator=generator,
    )
    return hasil.images[0]


# =============================================================================
# F1.2 — generate_advanced_image()
# =============================================================================

def generate_advanced_image(prompt, negative_prompt, seed,
                            guidance_scale, num_inference_steps):
    """Generasi lanjutan: menambah kontrol guidance_scale & num_inference_steps."""
    generator = torch.Generator(device=DEVICE).manual_seed(seed)
    hasil = pipe(
        prompt=prompt,
        negative_prompt=negative_prompt,
        generator=generator,
        guidance_scale=guidance_scale,
        num_inference_steps=num_inference_steps,
    )
    return hasil.images[0]


# =============================================================================
# F1.3 / F1.4 — jalankan kedua fungsi dengan prompt identik
# =============================================================================

img_simple = generate_simple_image(PROMPT, NEGATIVE_PROMPT, SEED)
img_advanced = generate_advanced_image(
    PROMPT, NEGATIVE_PROMPT, SEED,
    guidance_scale=7.5,
    num_inference_steps=50,
)

display(img_simple)      # noqa: F821 — `display` tersedia di notebook
display(img_advanced)    # noqa: F821


# =============================================================================
# Utilitas tampilan — dipakai beberapa eksperimen di bawah
# =============================================================================

def tampilkan_baris(gambar, judul, lebar=320):
    """Menempel beberapa gambar berdampingan agar mudah dibandingkan."""
    kecil = [g.resize((lebar, lebar)) for g in gambar]
    kanvas = Image.new("RGB", (lebar * len(kecil), lebar), "white")
    for i, g in enumerate(kecil):
        kanvas.paste(g, (i * lebar, 0))
    print(" | ".join(judul))
    return kanvas


def buat_grid(gambar, baris=2, kolom=2):
    """Menyusun gambar menjadi grid baris x kolom."""
    w, h = gambar[0].size
    grid = Image.new("RGB", (kolom * w, baris * h), "white")
    for i, g in enumerate(gambar[: baris * kolom]):
        grid.paste(g, ((i % kolom) * w, (i // kolom) * h))
    return grid


# =============================================================================
# F1.5 — eksperimen guidance scale (tulis observasinya di sel markdown template)
# =============================================================================

CFG_VALUES = [1.5, 7.5, 15.0]
hasil_cfg = [
    generate_advanced_image(PROMPT, NEGATIVE_PROMPT, SEED,
                            guidance_scale=cfg, num_inference_steps=30)
    for cfg in CFG_VALUES
]
tampilkan_baris(hasil_cfg, [f"CFG {c}" for c in CFG_VALUES])


# =============================================================================
# F1.6 — eksperimen inference steps: rendah (5-15) vs tinggi (30-50)
# =============================================================================

STEP_VALUES = [10, 40]
hasil_step = [
    generate_advanced_image(PROMPT, NEGATIVE_PROMPT, SEED,
                            guidance_scale=7.5, num_inference_steps=s)
    for s in STEP_VALUES
]
tampilkan_baris(hasil_step, [f"{s} steps" for s in STEP_VALUES])


# =============================================================================
# F1.8 — batch inference 4 gambar, ditampilkan sebagai grid 2x2
# =============================================================================

generator = torch.Generator(device=DEVICE).manual_seed(SEED)
batch = pipe(
    prompt=PROMPT,
    negative_prompt=NEGATIVE_PROMPT,
    generator=generator,
    guidance_scale=7.5,
    num_inference_steps=30,
    num_images_per_prompt=4,          # batch inference: 4 gambar sekaligus
).images

grid_2x2 = buat_grid(batch, baris=2, kolom=2)
display(grid_2x2)    # noqa: F821


# =============================================================================
# F1.9 — load_scheduler() mengganti sampling TANPA memuat ulang model
# =============================================================================

SCHEDULERS = {
    "Euler A": EulerAncestralDiscreteScheduler,
    "DPM++": DPMSolverMultistepScheduler,
    "DDIM": DDIMScheduler,
}


def load_scheduler(pipe, scheduler_name):
    """Mengganti algoritma sampling tanpa memuat ulang model.

    Scheduler baru dibangun dari config scheduler yang sedang aktif, sehingga bobot
    UNet/VAE/text-encoder tetap di VRAM dan tidak perlu di-load ulang.
    """
    if scheduler_name not in SCHEDULERS:
        raise ValueError(f"scheduler tidak dikenal: {scheduler_name}. "
                         f"Pilihan: {list(SCHEDULERS)}")
    pipe.scheduler = SCHEDULERS[scheduler_name].from_config(pipe.scheduler.config)
    return pipe


# Bukti model tidak dimuat ulang: id objek UNet tetap sama sebelum & sesudah.
print("UNet id sebelum :", id(pipe.unet))

hasil_scheduler = {}
for nama in SCHEDULERS:
    load_scheduler(pipe, nama)
    hasil_scheduler[nama] = generate_advanced_image(
        PROMPT, NEGATIVE_PROMPT, SEED,
        guidance_scale=7.5, num_inference_steps=30,
    )

print("UNet id sesudah :", id(pipe.unet))
tampilkan_baris(list(hasil_scheduler.values()), list(hasil_scheduler.keys()))
