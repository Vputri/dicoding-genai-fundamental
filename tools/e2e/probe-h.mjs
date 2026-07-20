import { chromium } from 'playwright';
const browser = await chromium.launch();
const ctx = await browser.newContext({ extraHTTPHeaders:{'ngrok-skip-browser-warning':'1'}, viewport:{width:1500,height:1100} });
const page = await ctx.newPage();
await page.goto(process.argv[2], { waitUntil:'domcontentloaded', timeout:60000 });
await page.waitForSelector('button:has-text("Initialize Generation")', { timeout:300000 });
const th = page.locator('[data-testid="stSlider"]').first().locator('[role="slider"]').first();
await th.focus(); for (let i=0;i<15;i++) await page.keyboard.press('ArrowLeft');
await page.waitForTimeout(600);
await page.locator('button:has-text("Initialize Generation")').click();
await page.waitForSelector('[data-testid="stImage"] img', { timeout:600000 });
await page.waitForTimeout(3000);
await page.locator('[data-testid="stTab"]:has-text("EDIT")').click();
await page.waitForTimeout(12000);

const ifr = page.locator('iframe[src*="st_canvas"]');
console.log('jumlah iframe :', await ifr.count());
console.log('iframe box    :', JSON.stringify(await ifr.boundingBox()));
console.log('atribut       :', JSON.stringify(await ifr.evaluate(el => ({w:el.width,h:el.height,style:el.getAttribute('style')}))));
const fr = page.frames().find(f=>f.url().includes('st_canvas'));
console.log('body iframe   :', await fr.evaluate(()=>document.body.scrollHeight));
console.log('bg element    :', await fr.evaluate(()=>{
  const c=document.querySelector('.canvas-container');
  return c ? getComputedStyle(c).backgroundImage.slice(0,60) : 'tidak ada .canvas-container';
}));
await browser.close();
