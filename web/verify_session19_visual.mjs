import puppeteer from 'puppeteer-core';
import path from 'path';
import fs from 'fs';

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const SCREENSHOT_DIR = path.resolve('..', 'docs', 'screenshots', 'session19');
const ARTIFACT_DIR = 'C:\\Users\\SHIVANSH\\.gemini\\antigravity\\brain\\3cbb8772-3914-4bf5-9f8b-9626ccbe7152';
const WEB_BASE = 'http://localhost:5173';
const MOBILE_BASE = 'http://localhost:8081';

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
  console.log('=== STARTING SESSION 19 VISUAL VERIFICATION SUITE ===\n');

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--window-size=1440,900'],
  });

  try {
    // ---------------------------------------------------------
    // 1. WEB: ADMIN SIDEBAR REDESIGNED SECTION HEADINGS
    // ---------------------------------------------------------
    console.log('1. Verifying Web Admin Sidebar Redesigned Headings...');
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

    const adminSidebarBuf = await adminPage.screenshot({ fullPage: false });
    saveScreenshot('session19_web_admin_sidebar.png', adminSidebarBuf);
    await adminCtx.close();

    // ---------------------------------------------------------
    // 2. WEB: RECEPTIONIST SIDEBAR REDESIGNED SECTION HEADINGS
    // ---------------------------------------------------------
    console.log('2. Verifying Web Receptionist Sidebar Redesigned Headings...');
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

    const recSidebarBuf = await recPage.screenshot({ fullPage: false });
    saveScreenshot('session19_web_receptionist_sidebar.png', recSidebarBuf);
    await recCtx.close();

    // ---------------------------------------------------------
    // 3. MOBILE: STUDENT DASHBOARD & ALERTS & DRAWER PLACEHOLDER
    // ---------------------------------------------------------
    console.log('3. Verifying Mobile Student Dashboard Alerts & Drawer Placeholder...');
    const studentCtx = await browser.createBrowserContext();
    const studentPage = await studentCtx.newPage();
    await studentPage.setViewport({ width: 412, height: 915, isMobile: true, hasTouch: true });
    await studentPage.goto(MOBILE_BASE, { waitUntil: 'domcontentloaded', timeout: 35000 });
    await sleep(3000);

    // Student role is default, type password
    const pwdInput = await studentPage.$('input[type="password"]');
    if (pwdInput) {
      await pwdInput.click();
      await studentPage.keyboard.type('Student@123');
    }
    await sleep(500);

    // Click Sign In
    await studentPage.evaluate(() => {
      const el = Array.from(document.querySelectorAll('*')).find(
        (e) => (e.innerText || '').trim() === 'Sign in' && e.children.length === 0
      );
      if (el) (el.closest('[role="button"]') || el).click();
    });
    await sleep(4000);

    // Student Dashboard screenshot
    const studentDashBuf = await studentPage.screenshot();
    saveScreenshot('session19_mobile_student_dashboard.png', studentDashBuf);

    // Open Drawer to verify "Today's Class" Coming Soon pill
    await studentPage.evaluate(() => {
      const menuBtn = document.querySelector('[aria-label="Open Menu"]') ||
                      Array.from(document.querySelectorAll('*')).find(
                        el => (el.getAttribute('aria-label') || '').includes('Menu')
                      );
      if (menuBtn) menuBtn.click();
    });
    await sleep(1500);

    const studentDrawerBuf = await studentPage.screenshot();
    saveScreenshot('session19_mobile_student_drawer.png', studentDrawerBuf);
    await studentCtx.close();

    // ---------------------------------------------------------
    // 4. MOBILE: PARENT DASHBOARD & MULTI-CHILD ALERTS & DRAWER
    // ---------------------------------------------------------
    console.log('4. Verifying Mobile Parent Dashboard Alerts & Drawer Placeholders...');
    const parentCtx = await browser.createBrowserContext();
    const parentPage = await parentCtx.newPage();
    await parentPage.setViewport({ width: 412, height: 915, isMobile: true, hasTouch: true });
    await parentPage.goto(MOBILE_BASE, { waitUntil: 'domcontentloaded', timeout: 35000 });
    await sleep(3000);

    // Select Parent role tab
    await parentPage.evaluate(() => {
      const el = Array.from(document.querySelectorAll('*')).find(
        (e) => (e.innerText || '').trim().toLowerCase() === 'parent' && e.children.length === 0
      );
      if (el) (el.closest('[role="button"]') || el).click();
    });
    await sleep(800);

    const parentPwdInput = await parentPage.$('input[type="password"]');
    if (parentPwdInput) {
      await parentPwdInput.click();
      await parentPage.keyboard.type('Parent@123');
    }
    await sleep(500);

    await parentPage.evaluate(() => {
      const el = Array.from(document.querySelectorAll('*')).find(
        (e) => (e.innerText || '').trim() === 'Sign in' && e.children.length === 0
      );
      if (el) (el.closest('[role="button"]') || el).click();
    });
    await sleep(4000);

    // Parent Dashboard screenshot
    const parentDashBuf = await parentPage.screenshot();
    saveScreenshot('session19_mobile_parent_dashboard.png', parentDashBuf);

    // Open Parent Drawer to verify "Call Class Teacher" and "Message Class Teacher" Coming Soon pills
    await parentPage.evaluate(() => {
      const menuBtn = document.querySelector('[aria-label="Open Menu"]') ||
                      Array.from(document.querySelectorAll('*')).find(
                        el => (el.getAttribute('aria-label') || '').includes('Menu')
                      );
      if (menuBtn) menuBtn.click();
    });
    await sleep(1500);

    const parentDrawerBuf = await parentPage.screenshot();
    saveScreenshot('session19_mobile_parent_drawer.png', parentDrawerBuf);
    await parentCtx.close();

    // ---------------------------------------------------------
    // 5. MOBILE: TEACHER DRAWER PLACEHOLDERS
    // ---------------------------------------------------------
    console.log('5. Verifying Mobile Teacher Drawer Placeholders...');
    const teacherCtx = await browser.createBrowserContext();
    const teacherPage = await teacherCtx.newPage();
    await teacherPage.setViewport({ width: 412, height: 915, isMobile: true, hasTouch: true });
    await teacherPage.goto(MOBILE_BASE, { waitUntil: 'domcontentloaded', timeout: 35000 });
    await sleep(3000);

    // Select Teacher role tab
    await teacherPage.evaluate(() => {
      const el = Array.from(document.querySelectorAll('*')).find(
        (e) => (e.innerText || '').trim().toLowerCase() === 'teacher' && e.children.length === 0
      );
      if (el) (el.closest('[role="button"]') || el).click();
    });
    await sleep(800);

    const teacherPwdInput = await teacherPage.$('input[type="password"]');
    if (teacherPwdInput) {
      await teacherPwdInput.click();
      await teacherPage.keyboard.type('Teacher@123');
    }
    await sleep(500);

    await teacherPage.evaluate(() => {
      const el = Array.from(document.querySelectorAll('*')).find(
        (e) => (e.innerText || '').trim() === 'Sign in' && e.children.length === 0
      );
      if (el) (el.closest('[role="button"]') || el).click();
    });
    await sleep(4000);

    // Open Teacher Drawer to verify "Today's Class" and "Parent Messages" Coming Soon pills
    await teacherPage.evaluate(() => {
      const menuBtn = document.querySelector('[aria-label="Open Menu"]') ||
                      Array.from(document.querySelectorAll('*')).find(
                        el => (el.getAttribute('aria-label') || '').includes('Menu')
                      );
      if (menuBtn) menuBtn.click();
    });
    await sleep(1500);

    const teacherDrawerBuf = await teacherPage.screenshot();
    saveScreenshot('session19_mobile_teacher_drawer.png', teacherDrawerBuf);
    await teacherCtx.close();

    console.log('\n=== ALL SESSION 19 VISUAL VERIFICATION SCREENSHOTS CAPTURED SUCCESSFULLY ===');
  } finally {
    await browser.close();
  }
}

run().catch((err) => {
  console.error('Visual verification failed:', err);
  process.exit(1);
});
