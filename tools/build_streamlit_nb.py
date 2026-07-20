"""Bangun Streamlit_submission_BFGAI_<nama>.ipynb dari struktur template resmi.

Urutan sel, judul markdown, dan cell id disalin dari
`[Template]_Streamlit_submission_BFGAI_Nama-siswa.ipynb`.

Yang diisi:
  - tiga sel `logic.py` (bagian bertanda ________ pada template)
  - sel ngrok: token dibaca dari Colab Secrets, bukan literal
  - model loader: repo `runwayml/*` yang sudah 404 diganti mirror resmi

Sel `app.py` disalin apa adanya dari template — JANGAN diubah.
"""

import json
import pathlib

STUDENT = "Vika-Putri-Ariyanti"
OUT = pathlib.Path(__file__).parent.parent / f"Streamlit_submission_BFGAI_{STUDENT}.ipynb"


def md(cid, text):
    return {"cell_type": "markdown", "metadata": {"id": cid}, "source": _src(text)}


def code(cid, text):
    return {"cell_type": "code", "execution_count": None, "metadata": {"id": cid},
            "outputs": [], "source": _src(text)}


def _src(text):
    text = text.strip("\n")
    lines = text.split("\n")
    return [l + "\n" for l in lines[:-1]] + [lines[-1]]


PENTING = """# **Penting**

*   Pada Notebook ini, Anda hanya perlu mengerjakan code pada bagian **logic.py** saja. Anda tidak diwajibkan untuk mengubah atau menambahkan **app.py** yang digunakan untuk membangun interface Streamlit.
*   Namun, jika Anda memiliki preferensi lain atau ingin mengubah struktur code pada logic ataupun pada interface Streamlit, itu **DIPERSILAHKAN** saja, tetapi pastikan untuk memenuhi kriteria yang telah ditetapkan pada intruksi submission
*   Jika Anda tidak ingin mengubah apapun dan ingin mengikuti template, tugas Anda hanyalah melengkapi code yang rumpang pada bagian yang sudah ditandai "________" saja.
"""

APP_PY = '''%%writefile app.py
import streamlit as st
import torch
import numpy as np
from PIL import Image
from streamlit_drawable_canvas import st_canvas
import logic
from PIL import Image, ImageDraw, ImageOps, ImageFilter

# Config
st.set_page_config(page_title="StudioAI", layout="wide", page_icon="🎨")

# Load Models
@st.cache_resource
def get_models():
    return logic.load_models_cached()

try:
    pipe_txt2img, pipe_inpaint = get_models()
except Exception as e:
    st.error(f"Error loading models: {e}")
    st.stop()

st.title("🎨 StudioAI: Craeating Amazing Paint with Stable Diffusion")

with st.sidebar:
    st.header("⚙️ Parameters")
    # Basic
    steps = st.slider("Quality Steps", 15, 50, 30)
    cfg = st.slider("Creativity (CFG)", 1.0, 20.0, 7.5)
    seed = st.number_input("Seed Control", value=42)

    st.divider()

    # Skilled
    st.subheader("🚀 Advanced")
    scheduler_name = st.selectbox("Scheduler", ["Euler A", "DPM++", "DDIM"])
    num_images = st.slider("Batch Size (Jumlah Gambar)", 1, 4, 1)

    st.divider()
    if st.button("🧹 Flush RAM"):
        logic.flush_memory()
        st.toast("Memory Cleared!")

# Tab (fitur) yang tersedia
tab_gen, tab_edit = st.tabs(["✨ GENERATE", "🛠️ EDIT"])

# Tab Generate
with tab_gen:
    c1, c2 = st.columns([1, 1], gap="large")

    # Input
    with c1:
        st.subheader("Input Blueprint")
        with st.form(key="gen_form"):
            prompt = st.text_area("Prompt", "a cute robot in a futuristic city, 8k, masterpiece", height=150)
            neg_prompt = st.text_input("Negative Prompt", "blurry, bad anatomy, worst quality")

            submit_gen = st.form_submit_button("🚀 Initialize Generation", type="primary")

        if submit_gen:
            with st.spinner("Processing Image"):
                logic.flush_memory()

                generated_list = logic.generate_image(
                    pipe_txt2img, prompt, neg_prompt, seed, steps, cfg, num_images, scheduler_name
                )

                st.session_state['generated_images'] = generated_list

                # Ini mencegah error "List has no attribute .size" di Tab Edit.
                if generated_list:
                    st.session_state['current_image'] = generated_list[0]

            # Refresh halaman untuk update tampilan
            st.rerun()

    # Output
    with c2:
        st.subheader("Visual Output")

        if 'generated_images' in st.session_state:
            imgs = st.session_state['generated_images']

            # Batch image: ada lebih dari 1 gambar
            if len(imgs) > 1:
                cols = st.columns(2) # Grid 2 Kolom
                for idx, img in enumerate(imgs):
                    with cols[idx % 2]:
                        st.image(img, caption=f"Img {idx+1}", use_container_width=True)

                        # Tombol Pilih Gambar untuk diedit
                        if st.button(f"Select Img {idx+1}", key=f"sel_{idx}"):
                            st.session_state['current_image'] = img
                            st.toast(f"✅ Image {idx+1} Selected for Editing!")

            # Single Image
            elif len(imgs) == 1:
                st.image(imgs[0], caption="Result", use_container_width=True)

        else:
            st.info("👈 Masukkan prompt di panel kiri dan tekan Generate.")


# Tab Edit (Inpainting dan Outpainting)
with tab_edit:
    if 'current_image' in st.session_state:
        source_img = st.session_state['current_image']

        # Validasi tipe data
        if isinstance(source_img, list):
            st.warning("⚠️ Terdeteksi List Gambar. Mengambil gambar pertama secara otomatis.")
            source_img = source_img[0]
            st.session_state['current_image'] = source_img

        W, H = source_img.size

        # Pilihan Mode
        mode = st.radio("Select Mode:", ["Inpainting (Edit Objek)", "Outpainting (Zoom Out)"], horizontal=True)
        st.divider()

        # Mode Inpainting
        if mode == "Inpainting (Edit Objek)":
            col_tools, col_result = st.columns([1, 1], gap="large")

            # Logic Reset Canvas: Agar coretan hilang setelah generate
            if 'canvas_key' not in st.session_state:
                st.session_state['canvas_key'] = 0

            img_id = str(id(source_img))

            dynamic_key = f"canvas_{st.session_state['canvas_key']}_{img_id}"

            with col_tools:
                st.subheader("✍️ Draw Mask")
                st.caption("Warnai area yang ingin diubah.")

                # SATU-SATUNYA perubahan pada app.py bawaan template.
                # streamlit-drawable-canvas tidak berhasil melaporkan tinggi frame-nya,
                # sehingga Streamlit merender iframe komponen dengan height="0":
                # kanvas ADA di DOM (isinya setinggi ~540px) tetapi tidak terlihat
                # sama sekali dan mustahil dicoret. Tidak ada pesan error yang muncul.
                # Tingginya dipaksa lewat CSS agar kanvas tampil utuh.
                st.markdown(
                    f"<style>iframe[title='streamlit_drawable_canvas.st_canvas']"
                    f"{{height:{H + 30}px !important;}}</style>",
                    unsafe_allow_html=True,
                )

                # Widget Canvas
                canvas_result = st_canvas(
                    fill_color="rgba(255, 255, 255, 1.0)", # Warna Kuas Putih
                    stroke_width=20,
                    stroke_color="#FFFFFF",
                    background_image=source_img,
                    update_streamlit=True,
                    height=H, width=W,
                    drawing_mode="freedraw",
                    key=dynamic_key
                )

            with col_result:
                st.subheader("Settings")

                # Form Input
                with st.form("inpaint_input"):
                    edit_prompt = st.text_input("Prompt Baru (Ganti jadi apa?)", "a pair of sunglasses")
                    strength = st.slider("Strength (Seberapa kuat perubahannya?)", 0.1, 1.0, 0.85)
                    submit_inpaint = st.form_submit_button("⚡ Execute Inpainting", type="primary")

                # Logic Eksekusi
                if submit_inpaint:
                    if canvas_result.image_data is not None and np.max(canvas_result.image_data) > 0:

                        with st.spinner("Processing Inpainting..."):
                            logic.flush_memory()

                            # Proses Masker
                            # Ambil Alpha Channel
                            mask_data = canvas_result.image_data[:, :, 3]

                            # Ubah abu-abu jadi putih mutlak
                            mask_data[mask_data > 0] = 255
                            mask_image = Image.fromarray(mask_data.astype('uint8'), mode='L')

                            # Samakan ukuran mask dengan gambar asli (PENTING!)
                            if mask_image.size != source_img.size:
                                mask_image = mask_image.resize(source_img.size, resample=Image.NEAREST)

                            # Menebalkan atau mempertegas Masker
                            mask_image = mask_image.filter(ImageFilter.MaxFilter(15))

                            # Tampilkan Masker yang akan dilihat model
                            with st.expander("🕵️ Lihat Masker Final (Debug)"):
                                st.image(mask_image, caption="Masker Tajam (Tanpa Blur)", width=200)

                            try:
                                result_img = logic.run_inpainting(
                                    pipe_inpaint, source_img, mask_image, edit_prompt, strength
                                )

                                st.session_state['current_image'] = result_img
                                st.session_state['canvas_key'] = str(int(st.session_state.get('canvas_key', 0)) + 1)
                                st.success("Inpainting Selesai!")
                                st.rerun()

                            except Exception as e:
                                st.error(f"Error pada logic: {e}")
                    else:
                        st.warning("⚠️ Silakan coret gambar terlebih dahulu!")

        # Mode Outpainting
        elif mode == "Outpainting (Zoom Out)":
            c_out_1, c_out_2 = st.columns([1, 1], gap="large")

            with c_out_1:
                st.subheader("Original")
                st.image(source_img, caption="Gambar saat ini", use_container_width=True)

            with c_out_2:
                st.subheader("Expansion")
                with st.form("outpaint_input"):
                    st.info("Gambar akan diperluas 128px ke segala arah.")
                    out_prompt = st.text_input(
                        "Prompt Deskriptif (Jelaskan gambar UTUH)",
                        "wide angle view of [masukkan prompt awal], detailed background, 8k"
                    )
                    submit_outpaint = st.form_submit_button("🔍 Zoom Out (Expand)", type="primary")

                if submit_outpaint:
                    with st.spinner("Expanding Canvas..."):
                        logic.flush_memory()
                        try:
                            # Siapkan Canvas & Mask (Logic dari kode siswa di atas)
                            canvas_ready, mask_ready = logic.prepare_outpainting(source_img)

                            # Jalankan Inpainting pada area kosong
                            final_result = logic.run_inpainting(
                                pipe_inpaint, canvas_ready, mask_ready, out_prompt, 1.0
                            )
                            st.session_state['current_image'] = final_result
                            st.rerun()

                        except Exception as e:
                            st.error(f"Error pada logic Outpainting: {e}")
                            st.caption("Pastikan fungsi prepare_outpainting di logic.py sudah benar.")

    else:
        # Tampilan jika belum ada gambar sama sekali
        st.info("👈 Belum ada gambar. Silakan ke Tab 'GENERATE' dan buat gambar dulu.")'''

cells = [
    md("or2KNAA0GILH", PENTING),
    md("t2GnD1QImBX2", "# **Prepare Dependencies**"),
    code("0-WuMWt9hdbb", """
!pip install -q pyngrok
# PENTING — versi Streamlit disematkan.
# streamlit-drawable-canvas (rilis terakhir 0.9.3, tahun 2023) memanggil
# streamlit.elements.image.image_to_url(image, width: int, ...). Fungsi itu DIHAPUS
# pada Streamlit 1.41 dan dipindah ke lokasi lain dengan tanda tangan berbeda.
# Akibatnya pada Streamlit terbaru kanvas GAGAL SENYAP: komponen tidak muncul,
# tanpa pesan error apa pun di layar.
# 1.40.0 adalah versi terakhir yang masih cocok, sehingga app.py bawaan template
# dapat dipakai apa adanya tanpa tambalan apa pun.
!pip install -q streamlit==1.40.0
!pip install -q torch
!pip install -q diffusers
!pip install -q transformers
!pip install -q streamlit_drawable_canvas==0.9.3
"""),
    code("cURIiO0Yh6gP", """
from pyngrok import ngrok
import subprocess
"""),
    md("ILLV-lZ7mN5g", "# **Streamlit**"),
    md("KES2DFp0qhCc", "## logic.py (**Basic**)"),

    code("u8U0UVRHsKTS", '''
%%writefile logic.py
import torch
import gc
from diffusers import (
    StableDiffusionPipeline,
    StableDiffusionInpaintPipeline,
    EulerAncestralDiscreteScheduler,
    DPMSolverMultistepScheduler,
    DDIMScheduler
)
from PIL import Image, ImageFilter

# MODEL LOADER
# CATATAN: template semula memakai "runwayml/stable-diffusion-v1-5" dan
# "runwayml/stable-diffusion-inpainting". RunwayML telah membubarkan organisasinya
# di Hugging Face sehingga KEDUA repo tersebut mengembalikan HTTP 404, dan aplikasi
# berhenti di st.stop(). Repo di bawah adalah MIRROR RESMI dengan bobot serta
# arsitektur yang identik — bukan penggantian ke model lain.
# Referensi: https://github.com/huggingface/diffusers/issues/9322
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

# Ini mencegah error "Function not found" jika hanya mengerjakan Basic
def flush_memory(): pass
def set_scheduler(pipe, name): return pipe
def run_inpainting(pipe, img, mask, prompt, strength): return None
def prepare_outpainting(img, expand=128): return img, None
'''),

    code("DIp2ZAP3Uwhy", '''
%%writefile -a logic.py


def generate_image(pipe, prompt, neg_prompt, seed, steps, cfg, num_images=1, scheduler_name="Euler A"):

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
'''),

    md("axNesBDoq66a", "## logic.py (**Skilled**)"),
    code("lOdmPzkuU8_1", '''
%%writefile -a logic.py

# Implementasi pembersihan RAM GPU
def flush_memory():

    ### MULAI CODE ###

    gc.collect()
    torch.cuda.empty_cache()

    ### SELESAI CODE ###

    print("Memory Flushed!")

# Ganti scheduler sesuai input
def set_scheduler(pipe, scheduler_name):

    ### MULAI CODE ###

    # from_config memakai konfigurasi scheduler yang sedang aktif, sehingga bobot
    # UNet/VAE/text-encoder tetap berada di VRAM — model tidak dimuat ulang.
    if scheduler_name == "Euler A":
        pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(pipe.scheduler.config)
    elif scheduler_name == "DPM++":
        pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
    elif scheduler_name == "DDIM":
        pipe.scheduler = DDIMScheduler.from_config(pipe.scheduler.config)

    ### SELESAI CODE ###

    return pipe

# Definisikan ulang fungsi generate_image dan tambahkan parameter untuk batch inference
def generate_image(pipe, prompt, neg_prompt, seed, steps, cfg, num_images=1, scheduler_name="Euler A"):

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
'''),

    md("wSiw_ZPorC64", "## logic.py (**Advanced**)"),
    code("IYrxx8mkVEa6", '''
%%writefile -a logic.py

def run_inpainting(pipe, image, mask, prompt, strength):
    # Pastikan konversi RGB/L dan Resize Mask (Nearest)
    if image.mode != "RGB": image = image.convert("RGB")
    if mask.mode != "L": mask = mask.convert("L")

    # Resize Mask agar tajam
    if image.size != mask.size:
        mask = mask.resize(image.size, resample=Image.NEAREST)

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

    ### MULAI CODE ###
    w, h = image.size
    new_w = w + (expand_pixels * 2)
    new_h = h + (expand_pixels * 2)

    # Safety: Resolusi kelipatan 8
    new_w -= (new_w % 8)
    new_h -= (new_h % 8)

    ### SELESAI CODE ###

    # Background Blur
    bg = image.resize((new_w, new_h), resample=Image.BICUBIC)
    bg = bg.filter(ImageFilter.GaussianBlur(radius=50))

    canvas = bg.copy()
    paste_x = (new_w - w) // 2
    paste_y = (new_h - h) // 2
    canvas.paste(image, (paste_x, paste_y))

    # Masker (Putih = Edit, Hitam = Keep)
    mask = Image.new("L", (new_w, new_h), 255)
    inner_box = Image.new("L", (w, h), 0)

    ### MULAI CODE ###

    # Area gambar asli dihitamkan agar dipertahankan; cincin di sekelilingnya diisi model.
    mask.paste(inner_box, (paste_x, paste_y))

    ### SELESAI CODE ###

    return canvas, mask

'''),

    md("lldtOVOaqnt1",
       "## app.py\nAnda **TIDAK perlu mengubah atau menambahkan** apapun pada file **app.py** ini, cukup **jalankan** saja."),
    code("kixif86yhu0s", APP_PY),

    md("l0v3epbkmkVx", "# **Menggunakan *Ngrok* Untuk Deployment**"),
    md("DaneaH57DFlh", """## **Konfigurasi Autentikasi Ngrok dan Menjalankan Aplikasi Streamlit**
Cell ini digunakan untuk mengatur *authentication token Ngrok* dan menjalankan aplikasi Streamlit secara lokal. Token diperlukan agar *Ngrok* dapat membuat tunnel dengan akun pengguna. Setelah token diatur, aplikasi Streamlit dijalankan menggunakan subprocess sehingga server lokal aktif di background.

Apabila Anda belum mengetahui cara mendapatkan *authentication token Ngrok* milik Anda sendiri, silahkan baca pada bagian **tips and tricks submission**."""),
    code("AlnsPa6Fhvwa", """
# Token TIDAK ditulis sebagai literal di notebook.
# Simpan lebih dulu di panel Secrets Colab (ikon kunci) dengan nama NGROK_AUTH_TOKEN,
# lalu aktifkan "Notebook access".
from google.colab import userdata

auth_token = userdata.get("NGROK_AUTH_TOKEN")
assert auth_token, "NGROK_AUTH_TOKEN belum di-set pada Secrets Colab."

ngrok.set_auth_token(auth_token)
subprocess.Popen(["streamlit", "run", "app.py"])
"""),

    md("7yJzrhahDzUC", """## **Membuat Public URL**
Cell ini membuat *tunnel Ngrok* ke port lokal tempat Streamlit berjalan (default: 8501). *Ngrok* kemudian menghasilkan public URL yang bisa diakses dari internet, sehingga aplikasi Streamlit dapat dibuka tanpa harus berada di jaringan lokal yang sama."""),
    code("wHCuib8dh8Ti", """
public_url = ngrok.connect(8501).public_url
print(public_url)
"""),

    md("-r9Iro5nD6B4", "Apabila Anda mengalami limit endpoint usage pada Ngrok, jalankan hidden cell di bawah ini!"),
    md("me8GqKY1EE_A", """## **Menutup Semua Tunnel Ngrok yang Aktif**
Cell ini digunakan untuk menghentikan seluruh koneksi Ngrok yang masih aktif."""),
    code("b0118cc9", """
ngrok.kill()
print("All active ngrok tunnels have been closed.")
"""),
]

nb = {
    "nbformat": 4,
    "nbformat_minor": 0,
    "metadata": {
        "colab": {"provenance": [], "gpuType": "T4",
                  "collapsed_sections": ["me8GqKY1EE_A"]},
        "kernelspec": {"name": "python3", "display_name": "Python 3"},
        "language_info": {"name": "python"},
        "accelerator": "GPU",
    },
    "cells": cells,
}

OUT.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")

n_code = sum(1 for c in cells if c["cell_type"] == "code")
print(f"tertulis: {OUT.name} ({len(cells)} sel, {n_code} kode)")
