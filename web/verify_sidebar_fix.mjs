import puppeteer from 'puppeteer-core';
import path from 'path';
import fs from 'fs';

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const SCREENSHOT_DIR = path.resolve('..', 'docs', 'screenshots');
const ARTIFACT_DIR = 'C:\\Users\\SHIVANSH\\.gemini\\antigravity\\brain\\d965c132-59ed-4355-8c29-1aa6e333451d';

const sleep = ms => new Promise(r => setTimeout(r, ms));

async function run() {
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ['--no-sandbox'],
  });
  const ctx = await browser.createBrowserContext();
  const page = await ctx.newPage();
  await page.setViewport({ width: 1440, height: 900 });
  await page.goto('http://localhost:5173/#/login', { waitUntil: 'networkidle0', timeout: 20000 });
  await page.waitForSelector('input[type="password"]', { timeout: 10000 });
  await page.evaluate(({ loginId, password }) => {
    const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
    const emailInput = document.querySelector('input:not([type="password"])');
    const pwdInput = document.querySelector('input[type="password"]');
    setter.call(emailInput, loginId);
    emailInput.dispatchEvent(new Event('input', { bubbles: true }));
    setter.call(pwdInput, password);
    pwdInput.dispatchEvent(new Event('input', { bubbles: true }));
  }, { loginId: 'receptionist@sunrisepublic.edu', password: 'Admin@123' });
  await page.click('form button');
  await sleep(3000);
  await page.waitForSelector('#app-sidebar', { timeout: 10000 }).catch(() => {});
  await sleep(1000);

  const links = await page.$$eval('#app-sidebar nav a', els =>
    els.map(e => e.innerText.trim()).filter(Boolean)
  );
  console.log('Receptionist sidebar links:', JSON.stringify(links, null, 2));

  console.log('\n--- Forbidden links (must NOT appear) ---');
  const forbidden = ['Fees', 'Defaulters', 'Fee setup', 'Period close', 'Student fees', 'Payroll'];
  let allOk = true;
  for (const f of forbidden) {
    const found = links.some(l => l === f);
    if (found) { console.log(`  ✗ FAIL: "${f}" still visible!`); allOk = false; }
    else console.log(`  ✓ OK: "${f}" absent`);
  }

  console.log('\n--- Required links (must appear) ---');
  const required = ['Found & Lost', 'Student Passes', 'Meeting Slips', 'Important Directory', 'Fee Counter', 'Enquiries'];
  for (const r of required) {
    const found = links.some(l => l === r);
    if (!found) { console.log(`  ✗ FAIL: "${r}" missing!`); allOk = false; }
    else console.log(`  ✓ OK: "${r}" present`);
  }

  const buf = await page.screenshot({ fullPage: false });
  fs.writeFileSync(path.join(SCREENSHOT_DIR, 'rec_sidebar_clean.png'), buf);
  try { fs.writeFileSync(path.join(ARTIFACT_DIR, 'rec_sidebar_clean.png'), buf); } catch (e) {}
  console.log('\nScreenshot saved: rec_sidebar_clean.png');
  console.log(allOk ? '\n✅ ALL CHECKS PASSED' : '\n❌ SOME CHECKS FAILED');

  await browser.close();
}
run();
