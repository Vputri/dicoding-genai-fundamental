// Merekam demo aplikasi StudioAI menjadi video.
//
//   node e2e-video.mjs https://xxxx.ngrok-free.dev
//
// Menghasilkan rekaman .webm di ./video, lalu (bila ffmpeg tersedia)
// dikonversi menjadi video_demo_aplikasi_BFGAI.mp4.
//
// CATATAN: rekaman otomatis tidak menampilkan kursor asli sistem, jadi di sini
// disuntikkan kursor tiruan agar setiap klik terlihat. Tetap pertimbangkan
// merekam layar sendiri — lihat README.
import { chromium } from 'playwright';
import { execFileSync } from 'node:child_process';
import { existsSync, readdirSync, renameSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';

const URL = process.argv[2] || process.env.APP_URL;
if (!URL) {
  console.error('Pakai: node e2e-video.mjs <URL-ngrok>');
  process.exit(1);
}

const DIR_VIDEO = 'video';
const LEBAR = 1280, TINGGI = 800;
mkdirSync(DIR_VIDEO, { recursive: true });

// Kursor tiruan: mengikuti mousemove yang dikirim Playwright, di semua frame.
const SKRIP_KURSOR = `
(() => {
  if (window.__kursor) return;
  window.__kursor = true;
  const pasang = () => {
    const d = document.createElement('div');
    d.style.cssText = 'position:fixed;z-index:2147483647;width:22px;height:22px;' +
      'margin:-11px 0 0 -11px;border-radius:50%;pointer-events:none;' +
      'background:rgba(255,64,64,.45);border:2px solid #ff2d2d;' +
      'box-shadow:0 0 10px rgba(255,45,45,.8);transition:transform .08s;';
    document.body.appendChild(d);
    addEventListener('mousemove', e => {
      d.style.left = e.clientX + 'px';
      d.style.top = e.clientY + 'px';
    }, true);
    addEventListener('mousedown', () => { d.style.transform = 'scale(.6)'; }, true);
    addEventListener('mouseup',   () => { d.style.transform = 'scale(1)'; }, true);
  };
  document.readyState === 'loading'
    ? addEventListener('DOMContentLoaded', pasang)
    : pasang();
})();
`;

const browser = await chromium.launch();
const ctx = await browser.newContext({
  extraHTTPHeaders: { 'ngrok-skip-browser-warning': '1' },
  viewport: { width: LEBAR, height: TINGGI },
  recordVideo: { dir: DIR_VIDEO, size: { width: LEBAR, height: TINGGI } },
});
await ctx.addInitScript(SKRIP_KURSOR);
const page = await ctx.newPage();
page.setDefaultTimeout(60000);

const t0 = Date.now();
const detik = () => ((Date.now() - t0) / 1000).toFixed(0).padStart(3);

// Gerakkan kursor ke elemen lalu klik, supaya perpindahannya terlihat di video.
async function klik(locator, jeda = 900) {
  const b = await locator.boundingBox();
  if (!b) throw new Error('elemen tidak terukur');
  await page.mouse.move(b.x + b.width / 2, b.y + b.height / 2, { steps: 25 });
  await page.waitForTimeout(350);
  await page.mouse.down();
  await page.waitForTimeout(120);
  await page.mouse.up();
  await page.waitForTimeout(jeda);
}

async function ketik(locator, teks) {
  await klik(locator, 300);
  await locator.fill('');
  await locator.type(teks, { delay: 28 });
  await page.waitForTimeout(700);
}

try {
  console.log(`[${detik()}s] memuat aplikasi`);
  await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForSelector('button:has-text("Initialize Generation")', { timeout: 300000 });
  await page.waitForTimeout(2500);

  console.log(`[${detik()}s] mengisi prompt`);
  await ketik(page.locator('textarea').first(),
    'a cute cartoon astronaut floating in outer space, flat vector illustration');
  await ketik(page.locator('input[type="text"]').first(),
    'blurry, bad anatomy, worst quality');

  console.log(`[${detik()}s] mengatur slider & scheduler`);
  const sliders = page.locator('[data-testid="stSlider"]');
  const n = await sliders.count();
  async function geser(idx, frac) {
    const trek = sliders.nth(idx).locator('div[data-orientation="horizontal"]').last();
    const b = await trek.boundingBox();
    await page.mouse.move(b.x + b.width * frac, b.y + b.height / 2, { steps: 25 });
    await page.waitForTimeout(300);
    await page.mouse.down(); await page.waitForTimeout(120); await page.mouse.up();
    await page.waitForTimeout(1100);
  }
  await geser(0, 0.15);          // Quality Steps
  await geser(1, 0.45);          // Creativity (CFG)
  await geser(n - 1, 0.97);      // Batch Size -> 4

  await klik(page.locator('[data-testid="stSelectbox"]'));
  await page.waitForTimeout(600);
  await klik(page.locator('li:has-text("DPM++"), [role="option"]:has-text("DPM++")').first());

  console.log(`[${detik()}s] generate batch`);
  await klik(page.locator('button:has-text("Initialize Generation")'), 1500);
  await page.waitForSelector('[data-testid="stImage"] img', { timeout: 600000 });
  await page.waitForTimeout(3500);
  console.log(`[${detik()}s] ${await page.locator('[data-testid="stImage"] img').count()} gambar tampil`);
  await page.mouse.move(LEBAR * 0.75, TINGGI * 0.55, { steps: 30 });
  await page.waitForTimeout(2500);

  console.log(`[${detik()}s] Clear Memory`);
  await klik(page.locator('button:has-text("Flush RAM")'), 2500);

  console.log(`[${detik()}s] pindah ke tab EDIT`);
  const pilih = page.locator('button:has-text("Select Img")');
  if (await pilih.count()) await klik(pilih.first(), 2000);
  await klik(page.locator('[data-testid="stTab"]:has-text("EDIT")'), 3000);
  await page.waitForTimeout(6000);

  console.log(`[${detik()}s] mencoret mask`);
  const box = await page.locator('iframe[src*="st_canvas"]').boundingBox();
  if (box) {
    const cx = box.x + box.width / 2, cy = box.y + Math.min(box.height, 400) / 2;
    await page.mouse.move(cx - 70, cy, { steps: 20 });
    await page.mouse.down();
    for (let i = 0; i <= 28; i++) {
      await page.mouse.move(cx - 70 + i * 5, cy + Math.sin(i / 3) * 28, { steps: 2 });
      await page.waitForTimeout(35);
    }
    await page.mouse.up();
    await page.waitForTimeout(2500);
  }

  console.log(`[${detik()}s] menjalankan inpainting`);
  await ketik(page.locator('input[type="text"]').last(), 'a broken satellite');
  await klik(page.locator('button:has-text("Execute Inpainting")'), 2000);
  await page.waitForTimeout(300000).catch(() => {});

} catch (e) {
  console.log('BERHENTI:', e.message.split('\n')[0]);
} finally {
  console.log(`[${detik()}s] menutup & menyimpan rekaman`);
  await ctx.close();
  await browser.close();

  const webm = readdirSync(DIR_VIDEO).filter(f => f.endsWith('.webm'));
  if (!webm.length) { console.log('tidak ada rekaman'); process.exit(1); }
  const sumber = join(DIR_VIDEO, webm[webm.length - 1]);
  const tujuan = 'video_demo_aplikasi_BFGAI.mp4';
  try {
    execFileSync('ffmpeg', ['-y', '-i', sumber, '-c:v', 'libx264', '-crf', '23',
                            '-pix_fmt', 'yuv420p', '-movflags', '+faststart', tujuan],
                 { stdio: 'ignore' });
    console.log('video siap :', tujuan);
    const durasi = execFileSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration',
                                            '-of', 'csv=p=0', tujuan]).toString().trim();
    console.log('durasi     :', Number(durasi).toFixed(0), 'detik');
  } catch {
    console.log('ffmpeg tidak tersedia — rekaman mentah ada di', sumber);
  }
}
