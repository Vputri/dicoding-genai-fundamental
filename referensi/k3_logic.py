"""Kriteria 3 — isian `logic.py` pada template Streamlit (F3.1 – F3.9).

PENTING: `app.py` sudah disediakan LENGKAP oleh template dan tidak perlu diubah.
Seluruh komponen Kriteria 3 (text input, slider, selectbox scheduler, tombol Flush RAM,
dua tab, st_canvas, st.image) sudah ada di sana. Tugas Anda hanya mengisi bagian
bertanda `________` di `logic.py`.

Signature fungsi di bawah MENGIKUTI template karena dipanggil langsung oleh `app.py` —
jangan diubah namanya maupun urutan parameternya.
"""

import gc

import torch
from PIL import Image, ImageFilter
from diffusers import (
    StableDiffusionPipeline,
    StableDiffusionInpaintPipeline,
    EulerAncestralDiscreteScheduler,
    DPMSolverMultistepScheduler,
    DDIMScheduler,
)


# =============================================================================
# MODEL LOADER — template menandainya "JANGAN DIUBAH", TETAPI wajib diubah
# =============================================================================
# Template memakai `runwayml/stable-diffusion-v1-5` dan
# `runwayml/stable-diffusion-inpainting`. RunwayML sudah membubarkan organisasinya
# di Hugging Face dan kedua repo itu mengembalikan 404, sehingga `get_models()` di
# app.py akan gagal dan aplikasi berhenti di `st.stop()`.
#
# Repo di bawah adalah mirror resmi dengan bobot dan arsitektur identik — bukan
# pergantian model. Konfirmasikan dulu ke forum diskusi, lalu biarkan komentar ini
# agar reviewer memahami alasannya.

def load_models_cached():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading models to {device}")

    pipe_txt2img = StableDiffusionPipeline.from_pretrained(
        "stable-diffusion-v1-5/stable-diffusion-v1-5", torch_dtype=torch.float16
    ).to(device)

    pipe_inpaint = StableDiffusionInpaintPipeline.from_pretrained(
        "stable-diffusion-v1-5/stable-diffusion-inpainting", torch_dtype=torch.float16
    ).to(device)

    return pipe_txt2img, pipe_inpaint


# =============================================================================
# BASIC — generate_image() versi sederhana
# =============================================================================
# Template menyediakan kerangka berikut; isi dua baris `________`.
# Perhatikan: nilai kembalian WAJIB berupa list agar cocok dengan app.py.

def generate_image_basic(pipe, prompt, neg_prompt, seed, steps, cfg,
                         num_images=1, scheduler_name="Euler A"):
    ### MULAI CODE ###

    # Setup Generator (Seed)
    generator = torch.Generator(device=pipe.device).manual_seed(int(seed))

    # Generate gambar standard
    image = pipe(
        prompt=prompt,
        negative_prompt=neg_prompt,
        generator=generator,
        num_inference_steps=int(steps),
        guidance_scale=float(cfg),
    ).images[0]

    ### SELESAI CODE ###

    # Kembalikan dalam bentuk List agar kompatibel dengan UI (List isi 1 gambar)
    return [image]


# =============================================================================
# SKILLED — flush_memory(), set_scheduler(), generate_image() dengan batch
# =============================================================================

def flush_memory():
    ### MULAI CODE ###

    gc.collect()
    torch.cuda.empty_cache()

    ### SELESAI CODE ###

    print("Memory Flushed!")


def set_scheduler(pipe, scheduler_name):
    ### MULAI CODE ###

    # `from_config` memakai config scheduler yang sedang aktif, sehingga bobot
    # UNet/VAE/text-encoder tetap di VRAM — model tidak dimuat ulang.
    if scheduler_name == "Euler A":
        pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(pipe.scheduler.config)
    elif scheduler_name == "DPM++":
        pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
    elif scheduler_name == "DDIM":
        pipe.scheduler = DDIMScheduler.from_config(pipe.scheduler.config)

    ### SELESAI CODE ###

    return pipe


def generate_image(pipe, prompt, neg_prompt, seed, steps, cfg,
                   num_images=1, scheduler_name="Euler A"):
    ### MULAI CODE ###

    # Set Scheduler
    pipe = set_scheduler(pipe, scheduler_name)

    generator = torch.Generator(device=pipe.device).manual_seed(int(seed))

    # Generate Batch
    result = pipe(
        prompt=prompt,
        negative_prompt=neg_prompt,
        generator=generator,
        num_inference_steps=int(steps),
        guidance_scale=float(cfg),
        num_images_per_prompt=int(num_images),
    ).images

    ### SELESAI CODE ###

    return result


# =============================================================================
# ADVANCED — run_inpainting(), prepare_outpainting()
# =============================================================================

def run_inpainting(pipe, image, mask, prompt, strength):
    # --- bagian ini sudah disediakan template ---
    if image.mode != "RGB":
        image = image.convert("RGB")
    if mask.mode != "L":
        mask = mask.convert("L")

    if image.size != mask.size:
        mask = mask.resize(image.size, resample=Image.NEAREST)
    # --- akhir bagian bawaan template ---

    result = pipe(
        prompt=prompt,
        image=image,
        mask_image=mask,
        strength=float(strength),
        num_inference_steps=30,
        guidance_scale=7.5,
        width=image.size[0],
        height=image.size[1],
    ).images[0]

    return result


def prepare_outpainting(image, expand_pixels=128):
    """Memperluas kanvas ke SEGALA ARAH — app.py menyebut '128px ke segala arah'.

    Berbeda dari `prepare_outpainting()` di notebook Pipeline yang satu arah saja.
    """
    ### MULAI CODE ###
    w, h = image.size
    new_w = w + (expand_pixels * 2)
    new_h = h + (expand_pixels * 2)

    # Safety: Resolusi kelipatan 8
    new_w -= (new_w % 8)
    new_h -= (new_h % 8)

    ### SELESAI CODE ###

    # --- bagian ini sudah disediakan template ---
    bg = image.resize((new_w, new_h), resample=Image.BICUBIC)
    bg = bg.filter(ImageFilter.GaussianBlur(radius=50))

    canvas = bg.copy()
    paste_x = (new_w - w) // 2
    paste_y = (new_h - h) // 2
    canvas.paste(image, (paste_x, paste_y))

    # Masker (Putih = Edit, Hitam = Keep)
    mask = Image.new("L", (new_w, new_h), 255)
    inner_box = Image.new("L", (w, h), 0)
    # --- akhir bagian bawaan template ---

    ### MULAI CODE ###

    # Area gambar asli dihitamkan agar dipertahankan; sisanya (cincin luar) diisi model.
    mask.paste(inner_box, (paste_x, paste_y))

    ### SELESAI CODE ###

    return canvas, mask


# =============================================================================
# SEL NGROK — jangan tulis token sebagai literal
# =============================================================================
# Template menulis:  auth_token = "YOUR_AUTHENTICATION_KEY"
# Ganti menjadi:
#
#     from google.colab import userdata
#     from pyngrok import ngrok
#     import subprocess
#
#     auth_token = userdata.get("NGROK_AUTH_TOKEN")
#     ngrok.set_auth_token(auth_token)
#     subprocess.Popen(["streamlit", "run", "app.py"])
