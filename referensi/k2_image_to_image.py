"""Kriteria 2 — Image-to-Image: inpainting, outpainting, zoom-out, refiner (F2.1 – F2.8).

Implementasi referensi untuk disalin ke sel yang bersesuaian pada template Pipeline.
Berkas ini tidak ikut ke dalam zip submission.

Konvensi mask di Stable Diffusion Inpainting:
    PUTIH (255) = area yang DIGANTI/diisi model
    HITAM  (0)  = area yang DIPERTAHANKAN
"""

import gc

import numpy as np
import torch
from PIL import Image, ImageDraw
from diffusers import StableDiffusionInpaintPipeline, StableDiffusionImg2ImgPipeline

# Diasumsikan sel Kriteria 1 sudah dijalankan sehingga tersedia:
#   pipe, DEVICE, DTYPE, PROMPT, NEGATIVE_PROMPT, buat_grid, tampilkan_baris

SEED_INPAINT = 9        # ketentuan rubrik untuk inpainting


# =============================================================================
# SETUP — checkpoint inpainting (instance TERPISAH, lihat §4.5 PRD)
# =============================================================================
# UNet inpainting punya 9 input channel (4 latent + 4 masked-latent + 1 mask),
# berbeda dari UNet text-to-image yang 4 channel. Karena arsitekturnya memang
# berbeda, instance terpisah di sini BUKAN pelanggaran tips "jangan reload model".

INPAINT_MODEL_CANDIDATES = [
    # Repo `runwayml/stable-diffusion-inpainting` sudah 404 sejak RunwayML
    # membubarkan organisasinya di Hugging Face. Kandidat mirror, diurutkan:
    "stable-diffusion-v1-5/stable-diffusion-inpainting",
    "botp/stable-diffusion-v1-5-inpainting",
]


def muat_inpaint_pipeline(kandidat=INPAINT_MODEL_CANDIDATES):
    """Mencoba beberapa mirror sampai ada yang berhasil dimuat."""
    galat = []
    for repo in kandidat:
        try:
            p = StableDiffusionInpaintPipeline.from_pretrained(
                repo, torch_dtype=DTYPE, safety_checker=None,      # noqa: F821
            ).to(DEVICE)                                            # noqa: F821
            p.enable_attention_slicing()
            print("checkpoint inpainting dimuat:", repo)
            return p, repo
        except Exception as e:                                      # noqa: BLE001
            galat.append(f"  - {repo}: {type(e).__name__}")
    raise RuntimeError("Tidak ada mirror inpainting yang bisa dimuat:\n"
                       + "\n".join(galat))


inpaint_pipe, INPAINT_MODEL_ID = muat_inpaint_pipeline()


# =============================================================================
# F2.1 — inpaint_engine()
# =============================================================================

def inpaint_engine(image, mask, prompt, negative_prompt="", seed=SEED_INPAINT,
                   guidance_scale=7.5, num_inference_steps=40):
    """Mengganti area putih pada `mask` sesuai `prompt`.

    image : PIL.Image  — gambar sumber
    mask  : PIL.Image  — mode "L", putih = area yang diganti
    prompt: str        — deskripsi objek yang ingin dimunculkan
    """
    w, h = image.size
    generator = torch.Generator(device=DEVICE).manual_seed(seed)     # noqa: F821
    hasil = inpaint_pipe(
        prompt=prompt,
        negative_prompt=negative_prompt,
        image=image,
        mask_image=mask,
        generator=generator,
        guidance_scale=guidance_scale,
        num_inference_steps=num_inference_steps,
        width=w,
        height=h,
    )
    return hasil.images[0]


# =============================================================================
# F2.2 — masking MANUAL (hardcode) via trial and error
# =============================================================================

def buat_mask_kotak(size, kotak):
    """Mask persegi panjang. `kotak` = (x0, y0, x1, y1) dalam piksel."""
    mask = Image.new("L", size, 0)          # default hitam = dipertahankan
    ImageDraw.Draw(mask).rectangle(kotak, fill=255)
    return mask


def pratinjau_mask(image, mask, alpha=0.5):
    """Menampilkan overlay merah di area mask — alat bantu trial and error."""
    overlay = Image.new("RGB", image.size, (255, 0, 0))
    return Image.composite(
        Image.blend(image.convert("RGB"), overlay, alpha),
        image.convert("RGB"),
        mask,
    )


# Koordinat di bawah adalah hasil trial and error: jalankan pratinjau_mask(),
# lihat posisinya, geser angkanya, ulangi sampai area yang dituju tepat.
KOTAK_SATELIT = (300, 60, 480, 220)         # <-- sesuaikan dengan gambar Anda

mask_manual = buat_mask_kotak(img_advanced.size, KOTAK_SATELIT)      # noqa: F821
display(pratinjau_mask(img_advanced, mask_manual))                   # noqa: F821

PROMPT_SATELIT = (
    "a broken damaged satellite with cracked solar panels floating in space, "
    "flat vector illustration, same pastel color palette, clean lines"
)

img_inpaint = inpaint_engine(
    image=img_advanced,                                              # noqa: F821
    mask=mask_manual,
    prompt=PROMPT_SATELIT,
    negative_prompt=NEGATIVE_PROMPT,                                 # noqa: F821
    seed=SEED_INPAINT,
)
display(img_inpaint)                                                 # noqa: F821


# =============================================================================
# F2.4 — masking OTOMATIS dengan model segmentation
# =============================================================================

def buat_mask_segmentasi(image, label_target, model_id="nvidia/segformer-b0-finetuned-ade-512-512"):
    """Membentuk mask otomatis dari hasil model segmentation.

    label_target : nama kelas yang ingin di-mask, mis. "sky".
    Mengembalikan (mask, daftar_label_tersedia) agar mudah ditelusuri bila meleset.
    """
    from transformers import pipeline as hf_pipeline

    segmenter = hf_pipeline("image-segmentation", model=model_id,
                            device=0 if DEVICE == "cuda" else -1)     # noqa: F821
    segmen = segmenter(image)
    tersedia = [s["label"] for s in segmen]

    terpilih = [s for s in segmen if s["label"].lower() == label_target.lower()]
    if not terpilih:
        return None, tersedia

    gabungan = np.zeros((image.size[1], image.size[0]), dtype=np.uint8)
    for s in terpilih:
        gabungan = np.maximum(gabungan, np.array(s["mask"].convert("L")))
    return Image.fromarray(gabungan).resize(image.size), tersedia


mask_auto, label_tersedia = buat_mask_segmentasi(img_advanced, "sky")  # noqa: F821
print("label terdeteksi:", label_tersedia)
if mask_auto is not None:
    display(pratinjau_mask(img_advanced, mask_auto))                   # noqa: F821


# =============================================================================
# F2.5 — prepare_outpainting(): memperluas kanvas ke SATU arah
# =============================================================================

def prepare_outpainting(image, direction, expand_px=192):
    """Memperluas kanvas ke satu arah dan menyiapkan mask area baru.

    direction : "kiri" | "kanan" | "atas" | "bawah"
    return    : (kanvas, mask) — mask putih menandai area kosong yang harus diisi.
    """
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

    # Seluruh kanvas putih (diisi), lalu area gambar asli dihitamkan (dipertahankan).
    mask = Image.new("L", ukuran_baru, 255)
    ImageDraw.Draw(mask).rectangle(
        [posisi[0], posisi[1], posisi[0] + w - 1, posisi[1] + h - 1], fill=0
    )
    return kanvas, mask


# =============================================================================
# F2.6 — outpainting satu sisi, memakai HASIL INPAINTING sebagai input
# =============================================================================

kanvas_out, mask_out = prepare_outpainting(img_inpaint, "kanan", expand_px=192)
display(pratinjau_mask(kanvas_out, mask_out))                          # noqa: F821

PROMPT_OUTPAINT = (
    "continuation of outer space scene with distant stars and nebula, "
    "flat vector illustration, same pastel color palette, clean lines"
)

img_outpaint = inpaint_engine(
    image=kanvas_out,
    mask=mask_out,
    prompt=PROMPT_OUTPAINT,
    negative_prompt=NEGATIVE_PROMPT,                                   # noqa: F821
    seed=SEED_INPAINT,
)
display(img_outpaint)                                                  # noqa: F821


# =============================================================================
# F2.7 — Zoom Out: perluasan bertahap ke berbagai arah
# =============================================================================

def prepare_zoom_out(image, zoom_factor=1.5):
    """Mengecilkan gambar ke tengah kanvas yang lebih besar.

    Area cincin di sekeliling gambar menjadi mask putih, sehingga hasil inpainting
    terasa seperti kamera mundur — bukan sekadar tempelan di satu sisi.
    """
    w, h = image.size
    kanvas_w, kanvas_h = int(w * zoom_factor), int(h * zoom_factor)
    kanvas_w -= kanvas_w % 8            # dimensi harus kelipatan 8 untuk VAE
    kanvas_h -= kanvas_h % 8

    kanvas = Image.new("RGB", (kanvas_w, kanvas_h), (255, 255, 255))
    kiri, atas = (kanvas_w - w) // 2, (kanvas_h - h) // 2
    kanvas.paste(image, (kiri, atas))

    mask = Image.new("L", (kanvas_w, kanvas_h), 255)
    ImageDraw.Draw(mask).rectangle([kiri, atas, kiri + w - 1, atas + h - 1], fill=0)
    return kanvas, mask


def zoom_out_bertahap(image, prompt, tahap=2, zoom_factor=1.4, ukuran_maks=768):
    """Menjalankan zoom-out beberapa kali secara berurutan."""
    hasil = [image]
    saat_ini = image
    for i in range(tahap):
        if max(saat_ini.size) * zoom_factor > ukuran_maks:
            print(f"tahap {i + 1} dilewati — melebihi batas {ukuran_maks}px")
            break
        kanvas, mask = prepare_zoom_out(saat_ini, zoom_factor)
        saat_ini = inpaint_engine(
            image=kanvas, mask=mask, prompt=prompt,
            negative_prompt=NEGATIVE_PROMPT,                           # noqa: F821
            seed=SEED_INPAINT,
        )
        hasil.append(saat_ini)
        print(f"tahap {i + 1}: {kanvas.size}")
    return hasil


tahapan_zoom = zoom_out_bertahap(img_inpaint, PROMPT_OUTPAINT, tahap=2)
tampilkan_baris(tahapan_zoom,                                          # noqa: F821
                [f"tahap {i}" for i in range(len(tahapan_zoom))])


# =============================================================================
# F2.8 — Refiner Pattern: Two-Stage Generation (Base + Refiner)
# =============================================================================
# Rubrik menyebut `denoising_end=0.8` dan `denoising_start=0.8`. Kedua parameter itu
# hanya ada pada pipeline SDXL base+refiner, sedangkan SDXL DILARANG oleh tips rubrik.
# Pada SD 1.5, porsi denoising sisa dikendalikan lewat parameter `strength`:
#
#     denoising_end   = 0.8  ->  base menjalankan 80% langkah
#     denoising_start = 0.8  ->  refiner melanjutkan 20% sisanya  ->  strength = 0.2
#
# Stage 1 tetap menghasilkan LATENT (output_type="latent") sesuai bunyi rubrik,
# lalu latent didekode dan dioper ke pipeline Img2Img sebagai Stage 2.

DENOISING_SPLIT = 0.8
TOTAL_STEPS = 50

# Img2Img berbagi seluruh komponen dengan `pipe` — tidak ada bobot baru yang dimuat.
refiner_pipe = StableDiffusionImg2ImgPipeline(**pipe.components)        # noqa: F821
refiner_pipe.enable_attention_slicing()
print("refiner berbagi UNet dengan base:", refiner_pipe.unet is pipe.unet)  # noqa: F821


def generate_two_stage(prompt, negative_prompt, seed,
                       denoising_split=DENOISING_SPLIT, total_steps=TOTAL_STEPS):
    """Base menghasilkan latent pada 80% langkah, refiner menuntaskan 20% sisanya."""
    # ---- Stage 1: Base -> latent ----
    generator = torch.Generator(device=DEVICE).manual_seed(seed)        # noqa: F821
    latent = pipe(                                                      # noqa: F821
        prompt=prompt,
        negative_prompt=negative_prompt,
        generator=generator,
        guidance_scale=7.5,
        num_inference_steps=int(total_steps * denoising_split),
        output_type="latent",
    ).images

    # Latent didekode menjadi gambar agar dapat dioper ke pipeline Img2Img.
    with torch.no_grad():
        decoded = pipe.vae.decode(                                      # noqa: F821
            latent / pipe.vae.config.scaling_factor                     # noqa: F821
        ).sample
    gambar_stage1 = pipe.image_processor.postprocess(                   # noqa: F821
        decoded, output_type="pil"
    )[0]

    # ---- Stage 2: Refiner (Img2Img) ----
    generator = torch.Generator(device=DEVICE).manual_seed(seed)        # noqa: F821
    hasil = refiner_pipe(
        prompt=prompt,
        negative_prompt=negative_prompt,
        image=gambar_stage1,
        generator=generator,
        guidance_scale=7.5,
        strength=round(1.0 - denoising_split, 2),      # 0.2 = sisa 20% denoising
        num_inference_steps=total_steps,
    ).images[0]

    return gambar_stage1, hasil


stage1, stage2 = generate_two_stage(PROMPT, NEGATIVE_PROMPT, SEED)      # noqa: F821
tampilkan_baris([stage1, stage2],                                       # noqa: F821
                ["Stage 1 (base, 80%)", "Stage 2 (refiner, 20%)"])

gc.collect()
torch.cuda.empty_cache()
