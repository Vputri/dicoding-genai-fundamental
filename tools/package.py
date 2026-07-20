"""Susun berkas submission menjadi BFGAI_<nama>.zip sesuai ketentuan berkas.

Menolak membuat zip bila ada syarat yang belum terpenuhi, agar tidak tersubmit
dalam kondisi yang pasti ditolak reviewer.
"""

import json
import pathlib
import re
import zipfile

STUDENT = "Vika-Putri-Ariyanti"

root = pathlib.Path(__file__).parent.parent
zip_path = root / f"BFGAI_{STUDENT}.zip"

# Perhatikan: nama video TIDAK memakai nama siswa — jangan "dirapikan".
WAJIB = [
    f"Pipeline_submission_BFGAI_{STUDENT}.ipynb",
    f"Streamlit_submission_BFGAI_{STUDENT}.ipynb",
    "video_demo_aplikasi_BFGAI.mp4",
    "requirements.txt",
]

TOKEN_RE = re.compile(r"\b[0-9a-zA-Z_]{20,}_[0-9a-zA-Z]{20,}\b")   # pola authtoken ngrok
SDXL_RE = re.compile(r"sdxl|stable-diffusion-xl|sd-xl", re.IGNORECASE)

masalah = []

for nama in WAJIB:
    p = root / nama
    if not p.exists():
        masalah.append(f"berkas hilang: {nama}")
        continue

    if p.suffix == ".ipynb":
        nb = json.loads(p.read_text(encoding="utf-8"))
        kode = [c for c in nb["cells"] if c["cell_type"] == "code"]

        # Penanda "sudah dijalankan" adalah execution_count, bukan ada-tidaknya
        # output: sel berisi import atau %%writefile memang tidak menghasilkan
        # output apa pun meski sudah dieksekusi.
        belum = [c for c in kode if c.get("execution_count") is None]
        if belum:
            masalah.append(
                f"{nama}: {len(belum)}/{len(kode)} sel kode belum dijalankan "
                "— jalankan di Colab lalu unduh ulang"
            )

        ada_error = [
            c for c in kode
            for o in c.get("outputs", [])
            if o.get("output_type") == "error"
        ]
        if ada_error:
            masalah.append(f"{nama}: {len(ada_error)} sel berakhir dengan error")

        # Baris komentar dilewati: menyebut SDXL untuk menjelaskan mengapa TIDAK
        # dipakai bukan pelanggaran — yang dilarang adalah benar-benar memuatnya.
        baris_kode = [
            l for c in nb["cells"] if c["cell_type"] == "code"
            for l in "".join(c["source"]).split("\n")
            if not l.lstrip().startswith("#")
        ]
        if any(SDXL_RE.search(l) for l in baris_kode):
            masalah.append(f"{nama}: SDXL dipakai di kode aktif — dilarang tips rubrik")

        if TOKEN_RE.search(p.read_text(encoding="utf-8")):
            masalah.append(f"{nama}: kemungkinan authtoken ngrok tertulis literal")

    if p.suffix == ".mp4" and p.stat().st_size < 100_000:
        masalah.append(f"{nama}: ukurannya mencurigakan kecil "
                       f"({p.stat().st_size} byte) — pastikan rekaman benar tersimpan")

if masalah:
    print("Zip TIDAK dibuat. Perbaiki dulu:")
    for m in masalah:
        print("  -", m)
    raise SystemExit(1)

with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    for nama in WAJIB:
        z.write(root / nama, f"BFGAI_{STUDENT}/{nama}")

print(f"Zip dibuat: {zip_path.name} ({zip_path.stat().st_size / 1e6:.2f} MB)")
for n in zipfile.ZipFile(zip_path).namelist():
    print("  ", n)
