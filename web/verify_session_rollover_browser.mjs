import puppeteer from 'puppeteer-core';
import path from 'path';
import fs from 'fs';

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const BASE_URL = 'http://localhost:5173';
const SCREENSHOT_DIR = path.resolve('..', 'docs', 'screenshots');
const ARTIFACT_DIR = 'C:\\Users\\SHIVANSH\\.gemini\\antigravity\\brain\\a3402699-c3b4-4fb3-b5cf-351024089387';

async function captureScreen(page, name, filename) {
  const filePath = path.join(SCREENSHOT_DIR, filename);
  await page.screenshot({ path: filePath, fullPage: false });
  const artifactPath = path.join(ARTIFACT_DIR, filename);
  fs.copyFileSync(filePath, artifactPath);
  console.log(`✓ Captured [${name}] -> ${filename}`);
}

async function run() {
  console.log('=== STARTING SESSION ROLLOVER SCREENSHOT & WORKFLOW VERIFICATION ===');
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--window-size=1440,900'],
    defaultViewport: { width: 1440, height: 900 },
  });

  try {
    const page = await browser.newPage();

    // Login as Admin / Principal
    console.log('Logging in as admin@sunrisepublic.edu...');
    await page.goto(`${BASE_URL}/#/login`, { waitUntil: 'networkidle0' });
    await page.waitForSelector('input[type="password"]');
    await page.evaluate(() => {
      const emailInput = document.querySelector('input:not([type="password"])');
      const pwdInput = document.querySelector('input[type="password"]');
      const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
      setter.call(emailInput, 'admin@sunrisepublic.edu');
      emailInput.dispatchEvent(new Event('input', { bubbles: true }));
      setter.call(pwdInput, 'Admin@123');
      pwdInput.dispatchEvent(new Event('input', { bubbles: true }));
    });
    await page.click('form button');
    await page.waitForFunction(() => window.location.hash.includes('/dashboard'), { timeout: 15000 });
    await new Promise(r => setTimeout(r, 1500));

    // 1. Navigate to /admin/session-rollover
    console.log('\n1. Navigating to /admin/session-rollover...');
    await page.goto(`${BASE_URL}/#/admin/session-rollover`, { waitUntil: 'networkidle0' });
    await new Promise(r => setTimeout(r, 2000));
    console.log('Current URL:', page.url());

    // Select class 9-A (which promotes to 10-A) to keep 10-A clean or test 9-A
    // Let's click on 9-A button
    await page.waitForSelector('button');
    await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const btn9a = btns.find(b => b.textContent.includes('9-A'));
      if (btn9a) btn9a.click();
    });
    await new Promise(r => setTimeout(r, 800));
    await captureScreen(page, 'Step 1: Session & Section Selection', 'live_19_rollover_step1_selection.png');

    // 2. Click "Inspect Roster & Next Steps →"
    console.log('\n2. Inspecting Roster (Advancing to Step 2)...');
    await page.evaluate(() => {
      const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Inspect Roster & Next Steps'));
      if (btn) btn.click();
    });
    await page.waitForFunction(() => document.body.innerText.includes('Roster Review for Class'), { timeout: 10000 });
    await new Promise(r => setTimeout(r, 1000));
    await captureScreen(page, 'Step 2: Roster Review & Outcomes', 'live_20_rollover_step2_roster.png');

    // 3. Override outcome for a student (e.g. detain)
    console.log('\n3. Overriding outcome to Detain for first student...');
    await page.evaluate(() => {
      const selects = document.querySelectorAll('tbody select');
      if (selects.length > 0) {
        selects[0].value = 'detain';
        selects[0].dispatchEvent(new Event('change', { bubbles: true }));
      }
    });
    await new Promise(r => setTimeout(r, 1500));
    await captureScreen(page, 'Step 2: Detention Override & Dynamic Roll Update', 'live_21_rollover_step2_detention_override.png');

    // 4. Click "Proceed to Safety Gate Verification →"
    console.log('\n4. Advancing to Step 3 (Safety Gate)...');
    await page.evaluate(() => {
      const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Proceed to Safety Gate Verification'));
      if (btn) btn.click();
    });
    await page.waitForFunction(() => document.body.innerText.includes('Critical Safety Gate'), { timeout: 10000 });
    await new Promise(r => setTimeout(r, 800));
    await captureScreen(page, 'Step 3: Safety Gate & Audit Verification', 'live_22_rollover_step3_safety_gate.png');

    // 5. Fill confirmation and reason, then commit
    console.log('\n5. Filling PROMOTE confirmation and committing...');
    await page.evaluate(() => {
      const inputs = document.querySelectorAll('input[type="text"]');
      const confirmInput = Array.from(inputs).find(i => i.getAttribute('placeholder') === 'PROMOTE');
      if (confirmInput) {
        const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        setter.call(confirmInput, 'PROMOTE');
        confirmInput.dispatchEvent(new Event('input', { bubbles: true }));
      }
    });
    await new Promise(r => setTimeout(r, 500));

    await page.evaluate(() => {
      const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Commit Promotion Now'));
      if (btn) btn.click();
    });

    await page.waitForFunction(() => document.body.innerText.includes('Promotion Successfully Completed!'), { timeout: 15000 });
    await new Promise(r => setTimeout(r, 1000));
    await captureScreen(page, 'Step 4: Promotion Rollover Completed', 'live_23_rollover_step4_completed.png');

    console.log('\n=== ALL BROWSER SCREENSHOTS CAPTURED SUCCESSFULLY! ===');
  } finally {
    await browser.close();
  }
}

run().catch(err => {
  console.error('FAILED:', err);
  process.exit(1);
});
