import puppeteer from 'puppeteer-core';
import path from 'path';
import fs from 'fs';

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const BASE_URL = 'http://localhost:5173';
const SCREENSHOT_DIR = path.resolve('..', 'docs', 'screenshots');
const ARTIFACT_DIR = 'C:\\Users\\SHIVANSH\\.gemini\\antigravity\\brain\\a3402699-c3b4-4fb3-b5cf-351024089387';

if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

const capturedScreenshots = [];

async function captureScreen(page, name, filename) {
  const filePath = path.join(SCREENSHOT_DIR, filename);
  await page.screenshot({ path: filePath, fullPage: false });
  const artifactPath = path.join(ARTIFACT_DIR, filename);
  fs.copyFileSync(filePath, artifactPath);
  console.log(`✓ Captured [${name}] -> ${filename}`);
  capturedScreenshots.push({ name, filename, path: filePath, artifactPath });
}

async function run() {
  console.log('=== STARTING BROWSER SCREENSHOT TEST & ANALYSIS ===');
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--window-size=1440,900'],
    defaultViewport: { width: 1440, height: 900 },
  });

  const errors = [];

  try {
    const page = await browser.newPage();
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(`[Console Error] ${msg.text()}`);
      }
    });
    page.on('pageerror', err => {
      errors.push(`[Page Error] ${err.toString()}`);
    });

    // 1. Login Page
    console.log('\n1. Navigating to Login Page...');
    await page.goto(`${BASE_URL}/#/login`, { waitUntil: 'networkidle0' });
    await captureScreen(page, 'Login Screen', 'live_01_login.png');

    // Perform Admin Login
    console.log('\n2. Logging in as Admin (admin@sunrisepublic.edu)...');
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
    await new Promise(r => setTimeout(r, 2000));

    // 2. Executive Dashboard
    console.log('\n3. Capturing Executive Dashboard...');
    await captureScreen(page, 'Executive Dashboard', 'live_02_dashboard.png');

    // 3. Click Defaulters Modal
    console.log('\n4. Opening Fees Defaulters Modal...');
    const clickedDefaulters = await page.evaluate(() => {
      const all = Array.from(document.querySelectorAll('*'));
      const el = all.find(e => e.children.length === 0 && e.textContent.trim() === 'Fees Remaining');
      if (el) {
        el.closest('.cursor-pointer')?.click();
        return true;
      }
      return false;
    });
    if (clickedDefaulters) {
      await page.waitForFunction(() => document.body.innerText.includes('Pending Fee Students'), { timeout: 10000 });
      await new Promise(r => setTimeout(r, 1000));
      await captureScreen(page, 'Fees Remaining Defaulters Modal', 'live_03_dashboard_defaulters_modal.png');
      await page.evaluate(() => {
        const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === 'Close');
        if (btn) btn.click();
      });
      await new Promise(r => setTimeout(r, 500));
    }

    // 4. Students Directory
    console.log('\n5. Navigating to Students Directory (/students)...');
    await page.goto(`${BASE_URL}/#/students`, { waitUntil: 'networkidle0' });
    await page.waitForFunction(() => document.body.innerText.includes('Students') || document.body.innerText.includes('Sharma'), { timeout: 10000 });
    await new Promise(r => setTimeout(r, 1500));
    await captureScreen(page, 'Students Directory', 'live_04_students.png');

    // 5. Teachers & Staff Directory
    console.log('\n6. Navigating to Teachers & Staff (/teachers)...');
    await page.goto(`${BASE_URL}/#/teachers`, { waitUntil: 'networkidle0' });
    await page.waitForFunction(() => document.body.innerText.includes('Staff') || document.body.innerText.includes('Teachers'), { timeout: 10000 });
    await new Promise(r => setTimeout(r, 1500));
    await captureScreen(page, 'Teachers & Staff Directory', 'live_05_teachers.png');

    // 6. Daily Attendance Matrix
    console.log('\n7. Navigating to Student Attendance (/attendance)...');
    await page.goto(`${BASE_URL}/#/attendance`, { waitUntil: 'networkidle0' });
    await page.waitForFunction(() => document.body.innerText.includes('Attendance'), { timeout: 10000 });
    await new Promise(r => setTimeout(r, 1500));
    await captureScreen(page, 'Student Attendance Matrix', 'live_06_attendance.png');

    // 7. Fees Ledger
    console.log('\n8. Navigating to Fee Ledger (/fees/ledger)...');
    await page.goto(`${BASE_URL}/#/fees/ledger`, { waitUntil: 'networkidle0' });
    await page.waitForFunction(() => document.body.innerText.includes('Ledger') || document.body.innerText.includes('fees'), { timeout: 10000 });
    await new Promise(r => setTimeout(r, 1500));
    await captureScreen(page, 'Fee Ledger', 'live_07_fees_ledger.png');

    // 8. Transport Routes
    console.log('\n9. Navigating to Transport (/transport)...');
    await page.goto(`${BASE_URL}/#/transport`, { waitUntil: 'networkidle0' });
    await page.waitForFunction(() => document.body.innerText.includes('Transport'), { timeout: 10000 });
    await new Promise(r => setTimeout(r, 1500));
    await captureScreen(page, 'Transport & Bus Fleet', 'live_08_transport.png');

    // 9. Stock & Inventory
    console.log('\n10. Navigating to Stock & Inventory (/inventory)...');
    await page.goto(`${BASE_URL}/#/inventory`, { waitUntil: 'networkidle0' });
    await page.waitForFunction(() => document.body.innerText.includes('Stock & Inventory'), { timeout: 10000 });
    await new Promise(r => setTimeout(r, 1500));
    await captureScreen(page, 'Stock & Inventory Management', 'live_09_inventory.png');

    // 10. Reports Library
    console.log('\n11. Navigating to Reports Library (/reports)...');
    await page.goto(`${BASE_URL}/#/reports`, { waitUntil: 'networkidle0' });
    await page.waitForFunction(() => document.body.innerText.includes('Reports library'), { timeout: 10000 });
    await new Promise(r => setTimeout(r, 1500));
    await captureScreen(page, 'Reports Library', 'live_10_reports.png');

    // 11. Configuration
    console.log('\n12. Navigating to System Configuration (/configuration)...');
    await page.goto(`${BASE_URL}/#/configuration`, { waitUntil: 'networkidle0' });
    await page.waitForFunction(() => document.body.innerText.includes('Configuration'), { timeout: 10000 });
    await new Promise(r => setTimeout(r, 1500));
    await captureScreen(page, 'System Configuration', 'live_11_configuration.png');

    // 12. Admission Overview
    console.log('\n13. Navigating to Admission Overview (/admission)...');
    await page.goto(`${BASE_URL}/#/admission`, { waitUntil: 'networkidle0' });
    await page.waitForFunction(() => document.body.innerText.includes('Admission') || document.body.innerText.includes('overview'), { timeout: 10000 });
    await new Promise(r => setTimeout(r, 1500));
    await captureScreen(page, 'Admission Executive Dashboard', 'live_12_admission_overview.png');

    console.log('\n=== BROWSER CAPTURE COMPLETED SUCCESSFULLY ===');
    console.log(`Captured ${capturedScreenshots.length} high-resolution screenshots.`);
    if (errors.length > 0) {
      console.log(`\n⚠️ Encountered ${errors.length} non-fatal browser console/page logs:`);
      errors.slice(0, 5).forEach(e => console.log('  ', e));
    } else {
      console.log('\n✓ Zero console errors or page errors encountered!');
    }

  } finally {
    await browser.close();
  }
}

run().catch(err => {
  console.error('❌ Browser screenshot script failed:', err);
  process.exit(1);
});
