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
  console.log('=== STARTING PAYROLL SCREENSHOT & WORKFLOW VERIFICATION ===');
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--window-size=1440,900'],
    defaultViewport: { width: 1440, height: 900 },
  });

  try {
    const page = await browser.newPage();

    // Login as Admin
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

    page.on('console', msg => console.log('BROWSER CONSOLE:', msg.type(), msg.text()));
    page.on('pageerror', err => console.log('BROWSER PAGE ERROR:', err.toString()));

    // 1. Navigate to /payroll
    console.log('\n1. Navigating to /payroll...');
    await page.goto(`${BASE_URL}/#/payroll`, { waitUntil: 'networkidle0' });
    await new Promise(r => setTimeout(r, 2000));
    console.log('Current URL:', page.url());
    const bodyText = await page.evaluate(() => document.body.innerText);
    console.log('Body snippet:', bodyText.substring(0, 300));
    await captureScreen(page, 'Payroll Runs Overview', 'live_13_payroll_runs.png');

    // 2. Click "+ Run Payroll" modal
    console.log('\n2. Opening Run Payroll Modal...');
    await page.evaluate(() => {
      const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('+ Run Payroll'));
      if (btn) btn.click();
    });
    await page.waitForFunction(() => document.body.innerText.includes('Open New Payroll Run'), { timeout: 10000 });
    await new Promise(r => setTimeout(r, 500));
    await captureScreen(page, 'Open New Payroll Run Modal', 'live_14_payroll_open_run_modal.png');

    // Submit Run Payroll (Month 4 / 2026)
    console.log('\n3. Creating Run for April 2026...');
    await page.click('div[role="dialog"] button[type="submit"], .fixed button[type="submit"]');
    await new Promise(r => setTimeout(r, 2000));

    // Calculate the Run if draft
    console.log('\n4. Calculating Payroll Run...');
    await page.evaluate(() => {
      const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === 'Calculate');
      if (btn) btn.click();
    });
    await new Promise(r => setTimeout(r, 2500));

    // 3. View Details of the Run
    console.log('\n5. Opening Run Details & Payslips...');
    await page.evaluate(() => {
      const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === 'View Details');
      if (btn) btn.click();
    });
    await page.waitForFunction(() => document.body.innerText.includes('Payslips Register'), { timeout: 10000 });
    await new Promise(r => setTimeout(r, 1500));
    await captureScreen(page, 'Payroll Run Details & Payslips', 'live_15_payroll_run_details.png');

    // 4. View / Print Payslip Modal
    console.log('\n6. Opening Payslip View & Print Modal...');
    await page.evaluate(() => {
      const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('View Slip & Print'));
      if (btn) btn.click();
    });
    await page.waitForFunction(() => document.body.innerText.includes('Teacher / Staff Payslip'), { timeout: 10000 });
    await new Promise(r => setTimeout(r, 1000));
    await captureScreen(page, 'CBSE Printable Payslip Modal', 'live_16_payroll_payslip_modal.png');

    // Close Payslip modal by clicking the backdrop or escape or close button
    await page.keyboard.press('Escape');
    await page.evaluate(() => {
      const closeBtns = Array.from(document.querySelectorAll('button')).filter(b => b.textContent.trim() === 'Close');
      closeBtns.forEach(b => b.click());
    });
    await new Promise(r => setTimeout(r, 1000));

    // 5. Back to tabs - Salary Components
    console.log('\n7. Navigating to Salary Components Tab...');
    await page.evaluate(() => {
      const tab = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Salary Components'));
      if (tab) tab.click();
    });
    await new Promise(r => setTimeout(r, 1500));
    await captureScreen(page, 'Salary Components Configuration', 'live_17_payroll_components.png');

    // 6. Staff Packages Tab
    console.log('\n8. Navigating to Staff Packages Tab...');
    await page.evaluate(() => {
      const tab = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Staff Packages'));
      if (tab) tab.click();
    });
    await new Promise(r => setTimeout(r, 1500));
    await captureScreen(page, 'Staff Packages & Structures', 'live_18_payroll_structures.png');

    console.log('\n=== PAYROLL BROWSER CAPTURE COMPLETED SUCCESSFULLY ===');
  } finally {
    await browser.close();
  }
}

run().catch(err => {
  console.error('❌ Payroll browser verification failed:', err);
  process.exit(1);
});
