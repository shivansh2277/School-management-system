import puppeteer from 'puppeteer-core';
import path from 'path';
import fs from 'fs';

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const SCREENSHOT_DIR = path.resolve('..', 'docs', 'screenshots', 'session20');
const ARTIFACT_DIR = 'C:\\Users\\SHIVANSH\\.gemini\\antigravity\\brain\\3cbb8772-3914-4bf5-9f8b-9626ccbe7152';
const WEB_BASE = 'http://localhost:5173';

if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

function saveScreenshot(filename, buffer) {
  const file1 = path.join(SCREENSHOT_DIR, filename);
  const file2 = path.join(ARTIFACT_DIR, filename);
  fs.writeFileSync(file1, buffer);
  try {
    fs.writeFileSync(file2, buffer);
  } catch (err) {
    console.warn(`[WARN] Could not save to artifact dir: ${err.message}`);
  }
  console.log(`[CAPTURED] ${filename}`);
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function run() {
  console.log('=== VERIFYING SIDEBAR WITHOUT HAMBURGER (DESKTOP, TABLET, MOBILE, MULTI-ROLE) ===\n');

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--window-size=1440,900'],
  });

  try {
    // -------------------------------------------------------------
    // 1. LAPTOP / DESKTOP (1440x900) - ADMIN ROLE
    // -------------------------------------------------------------
    console.log('1. Verifying Laptop/Desktop Admin Sidebar (Clean header, no hamburger in sidepanel)...');
    const adminCtx = await browser.createBrowserContext();
    const adminPage = await adminCtx.newPage();
    await adminPage.setViewport({ width: 1440, height: 900 });
    await adminPage.goto(`${WEB_BASE}/#/login`, { waitUntil: 'networkidle0' });
    await adminPage.waitForSelector('input[type="password"]');

    await adminPage.evaluate(() => {
      const emailInput = document.querySelector('input:not([type="password"])');
      const pwdInput = document.querySelector('input[type="password"]');
      const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
      setter.call(emailInput, 'admin@sunrisepublic.edu');
      emailInput.dispatchEvent(new Event('input', { bubbles: true }));
      setter.call(pwdInput, 'Admin@123');
      pwdInput.dispatchEvent(new Event('input', { bubbles: true }));
    });
    await adminPage.click('form button');
    await adminPage.waitForFunction(() => window.location.hash.includes('/dashboard'), { timeout: 12000 });
    await sleep(2000);

    const desktopBuf = await adminPage.screenshot({ fullPage: false });
    saveScreenshot('session20_clean_sidebar_laptop.png', desktopBuf);
    saveScreenshot('session20_sidebar_admin_expanded.png', desktopBuf);
    await adminCtx.close();

    // -------------------------------------------------------------
    // 2. TABLET (820x1180) - ADMIN ROLE
    // -------------------------------------------------------------
    console.log('2. Verifying Tablet View (820x1180 iPad Air size)...');
    const tabletCtx = await browser.createBrowserContext();
    const tabletPage = await tabletCtx.newPage();
    await tabletPage.setViewport({ width: 820, height: 1180 });
    await tabletPage.goto(`${WEB_BASE}/#/login`, { waitUntil: 'networkidle0' });
    await tabletPage.waitForSelector('input[type="password"]');

    await tabletPage.evaluate(() => {
      const emailInput = document.querySelector('input:not([type="password"])');
      const pwdInput = document.querySelector('input[type="password"]');
      const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
      setter.call(emailInput, 'admin@sunrisepublic.edu');
      emailInput.dispatchEvent(new Event('input', { bubbles: true }));
      setter.call(pwdInput, 'Admin@123');
      pwdInput.dispatchEvent(new Event('input', { bubbles: true }));
    });
    await tabletPage.click('form button');
    await tabletPage.waitForFunction(() => window.location.hash.includes('/dashboard'), { timeout: 12000 });
    await sleep(2000);

    const tabletBuf = await tabletPage.screenshot({ fullPage: false });
    saveScreenshot('session20_clean_sidebar_tablet.png', tabletBuf);
    await tabletCtx.close();

    // -------------------------------------------------------------
    // 3. MOBILE (390x844 iPhone 14 size) - OPEN DRAWER
    // -------------------------------------------------------------
    console.log('3. Verifying Mobile View (390x844 iPhone size) - Clean Sidepanel Drawer...');
    const mobCtx = await browser.createBrowserContext();
    const mobPage = await mobCtx.newPage();
    await mobPage.setViewport({ width: 390, height: 844, isMobile: true, hasTouch: true });
    await mobPage.goto(`${WEB_BASE}/#/login`, { waitUntil: 'networkidle0' });
    await mobPage.waitForSelector('input[type="password"]');

    await mobPage.evaluate(() => {
      const emailInput = document.querySelector('input:not([type="password"])');
      const pwdInput = document.querySelector('input[type="password"]');
      const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
      setter.call(emailInput, 'admin@sunrisepublic.edu');
      emailInput.dispatchEvent(new Event('input', { bubbles: true }));
      setter.call(pwdInput, 'Admin@123');
      pwdInput.dispatchEvent(new Event('input', { bubbles: true }));
    });
    await mobPage.click('form button');
    await mobPage.waitForFunction(() => window.location.hash.includes('/dashboard'), { timeout: 12000 });
    await sleep(2000);

    // Open drawer using top bar hamburger button
    await mobPage.evaluate(() => {
      const btn = document.querySelector('header button');
      if (btn) btn.click();
    });
    await sleep(1500);

    const mobileBuf = await mobPage.screenshot({ fullPage: false });
    saveScreenshot('session20_clean_sidebar_mobile.png', mobileBuf);
    saveScreenshot('session20_sidebar_mobile_drawer.png', mobileBuf);
    await mobCtx.close();

    // -------------------------------------------------------------
    // 4. RECEPTIONIST ROLE - CLEAN SIDEPANEL
    // -------------------------------------------------------------
    console.log('4. Verifying Receptionist Role (Clean sidepanel, no hamburger)...');
    const recCtx = await browser.createBrowserContext();
    const recPage = await recCtx.newPage();
    await recPage.setViewport({ width: 1440, height: 900 });
    await recPage.goto(`${WEB_BASE}/#/login`, { waitUntil: 'networkidle0' });
    await recPage.waitForSelector('input[type="password"]');

    await recPage.evaluate(() => {
      const emailInput = document.querySelector('input:not([type="password"])');
      const pwdInput = document.querySelector('input[type="password"]');
      const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
      setter.call(emailInput, 'receptionist@sunrisepublic.edu');
      emailInput.dispatchEvent(new Event('input', { bubbles: true }));
      setter.call(pwdInput, 'Admin@123');
      pwdInput.dispatchEvent(new Event('input', { bubbles: true }));
    });
    await recPage.click('form button');
    await recPage.waitForFunction(() => !window.location.hash.includes('/login'), { timeout: 12000 });
    await sleep(2000);

    const recBuf = await recPage.screenshot({ fullPage: false });
    saveScreenshot('session20_clean_sidebar_receptionist.png', recBuf);
    saveScreenshot('session20_sidebar_receptionist.png', recBuf);
    await recCtx.close();

    console.log('\n=== VISUAL VERIFICATION COMPLETE: ALL SCREENSHOTS CAPTURED ===');
  } catch (err) {
    console.error(`[ERROR] Verification failed: ${err.message}`);
    throw err;
  } finally {
    await browser.close();
  }
}

run();
