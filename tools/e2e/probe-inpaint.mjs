// Probe: kenapa "Execute Inpainting" tidak memicu proses apa pun.
import { chromium } from 'playwright';

const URL = process.argv[2];
const browser = await chromium.launch();
const ctx = await browser.newContext({
  extraHTTPHeaders: { 'ngrok-skip-browser-warning': '1' },
  viewport: { width: 1400, height: 950 },
});
const page = await ctx.newPage();
page.setDefaultTimeout(60000);
page.on('console', m => { if (m.type() === 'error') console.log('  [console]', m.text().slice(0, 160)); });

await page.goto(URL, { waitUntil: 'domcontentloaded' });
await page.waitForSelector('button:has-text("Initialize Generation")', { timeout: 300000 });

// Gambar mungkin masih ada di session_state dari uji sebelumnya.
const adaTab = await page.locator('[data-testid="stTab"]:has-text("EDIT")').count();
console.log('tab EDIT ada:', adaTab > 0);
await page.locator('[data-testid="stTab"]:has-text("EDIT")').click();
await page.waitForTimeout(6000);

// Apakah gambar sumber tersedia di tab EDIT?
const infoKosong = await page.locator('text=Belum ada gambar').count();
console.log('session kosong:', infoKosong > 0);
if (infoKosong > 0) {
  await page.locator('[data-testid="stTab"]:has-text("GENERATE")').click();
  await page.waitForTimeout(1000);
  await page.locator('button:has-text("Initialize Generation")').click();
  await page.waitForSelector('[data-testid="stImage"] img', { timeout: 600000 });
  await page.waitForTimeout(3000);
  await page.locator('[data-testid="stTab"]:has-text("EDIT")').click();
  await page.waitForTimeout(6000);
}

// Isi kanvas di dalam iframe: berapa canvas, ukuran, dan apakah latar tergambar.
const frame = page.frames().find(f => f.url().includes('st_canvas'));
console.log('iframe st_canvas ditemukan:', !!frame);
if (frame) {
  const info = await frame.evaluate(() => Array.from(document.querySelectorAll('canvas')).map(c => {
    const d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data;
    let n = 0;
    for (let i = 3; i < d.length; i += 4) if (d[i] > 0) n++;
    return { w: c.width, h: c.height, opaque: n, cls: c.className };
  }));
  console.log('canvas sebelum dicoret:', JSON.stringify(info));
}

const box = await page.locator('iframe[src*="st_canvas"]').boundingBox();
console.log('kotak iframe:', JSON.stringify(box));

// Coret tebal di tengah kanvas.
const cx = box.x + box.width / 2, cy = box.y + 150;
await page.mouse.move(cx - 90, cy, { steps: 10 });
await page.mouse.down();
for (let i = 0; i <= 36; i++) {
  await page.mouse.move(cx - 90 + i * 5, cy + Math.sin(i / 3) * 30, { steps: 2 });
  await page.waitForTimeout(25);
}
await page.mouse.up();
await page.waitForTimeout(3000);

if (frame) {
  const info = await frame.evaluate(() => Array.from(document.querySelectorAll('canvas')).map(c => {
    const d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data;
    let n = 0;
    for (let i = 3; i < d.length; i += 4) if (d[i] > 0) n++;
    return n;
  }));
  console.log('opaque per canvas sesudah dicoret:', JSON.stringify(info));
}

console.log('--- klik Execute Inpainting ---');
await page.locator('button:has-text("Execute Inpainting")').click();

for (let i = 1; i <= 12; i++) {
  await page.waitForTimeout(5000);
  const spinner = await page.locator('[data-testid="stSpinner"]').count();
  const alerts = await page.locator('[data-testid="stAlert"]').allTextContents();
  const exc = await page.locator('[data-testid="stException"]').allTextContents();
  const expander = await page.locator('text=Lihat Masker Final').count();
  const imgs = await page.locator('[data-testid="stImage"] img').count();
  console.log(`t+${i * 5}s spinner=${spinner} expander=${expander} img=${imgs}` +
    ` alert=${JSON.stringify(alerts.map(a => a.replace(/\s+/g, ' ').slice(0, 90)))}` +
    (exc.length ? ` EXC=${JSON.stringify(exc.map(e => e.slice(0, 200)))}` : ''));
  if (exc.length || expander) break;
}

await page.screenshot({ path: 'probe-akhir.png', fullPage: true });
await ctx.close();
await browser.close();
