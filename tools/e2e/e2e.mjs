// Uji end-to-end aplikasi StudioAI lewat ngrok, sebelum direkam manual.
// Menjalankan satu siklus penuh dan melaporkan komponen mana yang benar-benar bekerja.
import { chromium } from 'playwright';

// URL aplikasi Streamlit di Colab (tautan ngrok). Bisa lewat argumen atau env:
//   node e2e.mjs https://xxxx.ngrok-free.dev
//   APP_URL=https://xxxx.ngrok-free.dev node e2e.mjs
const URL = process.argv[2] || process.env.APP_URL;

if (!URL) {
  console.error('Pakai: node e2e.mjs <URL-ngrok>');
  process.exit(1);
}

const hasil = [];

function lapor(nama, ok, catatan = '') {
  hasil.push({ nama, ok, catatan });
  console.log(`  ${ok ? 'OK   ' : 'GAGAL'} ${nama}${catatan ? ' — ' + catatan : ''}`);
}

const browser = await chromium.launch();
const ctx = await browser.newContext({
  extraHTTPHeaders: { 'ngrok-skip-browser-warning': '1' },
  viewport: { width: 1500, height: 950 },
});
const page = await ctx.newPage();
page.setDefaultTimeout(30000);

try {
  console.log('\n[1] Memuat aplikasi');
  await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForSelector('button:has-text("Initialize Generation")', { timeout: 240000 });
  lapor('Aplikasi termuat', true, await page.title());

  console.log('\n[2] Mengisi input');
  const textareas = page.locator('textarea');
  await textareas.first().fill('a cute cartoon astronaut floating in outer space, flat vector illustration');
  lapor('Text input prompt', true);

  const negInput = page.locator('input[type="text"]').first();
  await negInput.fill('blurry, bad anatomy, worst quality, low quality');
  lapor('Text input negative prompt', true);

  console.log('\n[3] Mengatur slider & scheduler');
  const sliders = page.locator('[data-testid="stSlider"]');
  const nSlider = await sliders.count();

  // DOM slider berbeda antar versi Streamlit:
  //   <= 1.40 : baseweb, thumb punya [role="slider"] -> bisa di-focus + panah keyboard
  //   >= 1.41 : react-aria, tanpa [role="slider"]    -> harus klik pada trek
  // Keduanya ditangani agar uji ini tidak bergantung pada satu versi.
  async function setSlider(idx, frac, nama) {
    const slider = sliders.nth(idx);

    const thumb = slider.locator('[role="slider"]');
    if (await thumb.count() > 0) {
      const t = thumb.first();
      const info = await t.evaluate(el => ({
        now: Number(el.getAttribute('aria-valuenow')),
        min: Number(el.getAttribute('aria-valuemin')),
        max: Number(el.getAttribute('aria-valuemax')),
      }));
      const target = info.min + (info.max - info.min) * frac;
      await t.focus();
      // Langkah keyboard dibatasi agar tidak menekan panah ratusan kali.
      const langkah = Math.min(60, Math.round(Math.abs(target - info.now)));
      const tombol = target > info.now ? 'ArrowRight' : 'ArrowLeft';
      for (let i = 0; i < langkah; i++) await page.keyboard.press(tombol);
      await page.waitForTimeout(1200);
      const akhir = await t.getAttribute('aria-valuenow');
      lapor(nama, true, `nilai jadi ${akhir}`);
      return;
    }

    const trek = slider.locator('div[data-orientation="horizontal"]').last();
    const box = await trek.boundingBox().catch(() => null);
    if (!box) { lapor(nama, false, 'trek tidak terukur'); return; }
    await page.mouse.click(box.x + box.width * frac, box.y + box.height / 2);
    await page.waitForTimeout(1200);
    const nilai = await slider.locator('[data-testid="stSliderThumbValue"]').innerText().catch(() => '?');
    lapor(nama, true, `nilai jadi ${nilai.trim()}`);
  }

  await setSlider(0, 0.15, 'Slider num_inference_steps');   // Quality Steps -> rendah, biar cepat
  await setSlider(1, 0.45, 'Slider guidance_scale');        // Creativity (CFG)
  await setSlider(nSlider - 1, 0.97, 'Slider num_images');  // Batch Size -> 4

  // Selectbox scheduler -> DPM++
  try {
    const sb = page.locator('[data-testid="stSelectbox"]');
    await sb.scrollIntoViewIfNeeded();
    const box = await sb.boundingBox();
    await page.mouse.click(box.x + box.width / 2, box.y + box.height - 12);
    await page.waitForTimeout(1200);
    await page.locator('li:has-text("DPM++"), [role="option"]:has-text("DPM++")').first().click({ timeout: 8000 });
    await page.waitForTimeout(1500);
    lapor('Selectbox scheduler', true, 'dipilih DPM++');
  } catch (e) {
    lapor('Selectbox scheduler', false, e.message.split('\n')[0].slice(0, 90));
  }

  console.log('\n[4] Generate batch (bisa 1-3 menit)');
  await page.locator('button:has-text("Initialize Generation")').click();
  await page.waitForSelector('[data-testid="stImage"] img', { timeout: 600000 });
  await page.waitForTimeout(4000);
  const nGambar = await page.locator('[data-testid="stImage"] img').count();
  lapor('Gambar tampil di layar', nGambar > 0, `${nGambar} gambar`);
  lapor('Batch grid 2x2', nGambar >= 4, nGambar >= 4 ? 'empat gambar' : `hanya ${nGambar}`);
  await page.screenshot({ path: 'e2e-1-generate.png' });

  console.log('\n[5] Tombol Clear Memory');
  await page.locator('button:has-text("Flush RAM")').click();
  await page.waitForTimeout(2500);
  lapor('Tombol Clear Memory', true);

  console.log('\n[6] Pindah ke tab EDIT');
  const tombolSelect = page.locator('button:has-text("Select Img")');
  if (await tombolSelect.count() > 0) {
    await tombolSelect.first().click();
    await page.waitForTimeout(3000);
    lapor('Tombol Select Img', true);
  }
  await page.locator('[data-testid="stTab"]:has-text("EDIT")').click();
  await page.waitForTimeout(10000);

  // st_canvas adalah komponen kustom Streamlit -> dirender di dalam IFRAME.
  // locator biasa tidak menembus iframe, jadi hitung lewat frameLocator.
  const bingkai = page.frameLocator('iframe[src*="st_canvas"]');
  const adaKanvas = await bingkai.locator('canvas').count().catch(() => 0);
  lapor('Tab Inpaint/Outpaint', adaKanvas > 0, `${adaKanvas} canvas dalam iframe`);
  await page.screenshot({ path: 'e2e-2-edit.png' });

  console.log('\n[7] Mencoret kanvas (drawable-canvas)');
  // Koordinat mouse bersifat page-level, jadi kotak diambil dari elemen iframe-nya.
  const box = await page.locator('iframe[src*="st_canvas"]').boundingBox();
  if (box) {
    const cx = box.x + box.width / 2;
    const cy = box.y + box.height / 2;
    await page.mouse.move(cx - 60, cy - 40);
    await page.mouse.down();
    for (let i = 0; i <= 20; i++) {
      await page.mouse.move(cx - 60 + i * 6, cy - 40 + Math.sin(i / 2) * 25);
      await page.waitForTimeout(25);
    }
    await page.mouse.up();
    await page.waitForTimeout(3000);

    // Verifikasi lewat PIKSEL, bukan tampilan: hitung berapa piksel tidak transparan
    // pada tiap canvas di dalam iframe. Latar = gambar hasil generate,
    // lapisan atas = coretan mask.
    const frame = page.frames().find(f => f.url().includes('st_canvas'));
    const piksel = await frame.evaluate(() =>
      Array.from(document.querySelectorAll('canvas')).map(c => {
        try {
          const d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data;
          let n = 0;
          for (let i = 3; i < d.length; i += 4) if (d[i] > 0) n++;
          return n;
        } catch { return -1; }
      })
    );
    const terisi = piksel.filter(n => n > 0);
    lapor('Latar kanvas termuat', terisi.length > 0, `piksel per canvas: ${piksel.join(', ')}`);
    lapor('Coretan mask di kanvas', terisi.length >= 2,
          terisi.length >= 2 ? 'coretan terekam' : 'hanya latar, coretan tidak terekam');
    await page.screenshot({ path: 'e2e-3-canvas.png' });
  } else {
    lapor('Coretan mask di kanvas', false, 'canvas tidak terukur');
  }

  console.log('\n[8] Menjalankan inpainting (bisa 1-2 menit)');
  const tombolInpaint = page.locator('button:has-text("Execute Inpainting")');
  if (await tombolInpaint.count() > 0) {
    await tombolInpaint.click();

    // app.py memanggil st.rerun() TEPAT setelah st.success("Inpainting Selesai!"),
    // sehingga pesan sukses langsung terhapus dan tidak bisa dijadikan penanda.
    // Penanda yang dipakai: spinner muncul lalu hilang, dan tidak ada exception.
    try {
      await page.waitForSelector('[data-testid="stSpinner"]', { timeout: 30000 });
      console.log('     (proses berjalan...)');
      await page.waitForSelector('[data-testid="stSpinner"]', { state: 'detached', timeout: 600000 });
      await page.waitForTimeout(5000);

      const nErr = await page.locator('[data-testid="stException"]').count();
      if (nErr > 0) {
        const teks = (await page.locator('[data-testid="stException"]').first().innerText()).slice(0, 200);
        lapor('Inpainting berjalan', false, teks.replace(/\n/g, ' '));
      } else {
        const peringatan = await page.locator('[data-testid="stAlert"]').allTextContents();
        const bermasalah = peringatan.find(t => t.includes('coret') || t.includes('Error'));
        lapor('Inpainting berjalan', !bermasalah, bermasalah || 'selesai tanpa error');
      }
    } catch (e) {
      lapor('Inpainting berjalan', false, e.message.split('\n')[0].slice(0, 120));
    }
    await page.screenshot({ path: 'e2e-4-inpaint.png' });
  } else {
    lapor('Inpainting berjalan', false, 'tombol tidak ditemukan');
  }

} catch (e) {
  console.log('\nBERHENTI:', e.message.split('\n')[0]);
  await page.screenshot({ path: 'e2e-error.png' }).catch(() => {});
} finally {
  console.log('\n' + '='.repeat(60));
  const gagal = hasil.filter(h => !h.ok);
  console.log(`RINGKASAN: ${hasil.length - gagal.length}/${hasil.length} lolos`);
  if (gagal.length) gagal.forEach(g => console.log(`  perlu dicek: ${g.nama} — ${g.catatan}`));
  await browser.close();
}
