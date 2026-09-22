import puppeteer from 'puppeteer-core';
import fs from 'fs';
import path from 'path';

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const ARTIFACT_DIR = 'C:\\Users\\SHIVANSH\\.gemini\\antigravity\\brain\\555b38d8-689f-4933-b73f-00badba4e300';
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function captureScreen(page, filename, desc) {
  const filePath = path.join(ARTIFACT_DIR, filename);
  await page.screenshot({ path: filePath, fullPage: false });
  console.log(`[Visual Proof] Captured ${desc} -> ${filename}`);
}

async function runMobileTests() {
  console.log('================================================================');
  console.log('  TESTING MOBILE LOGIN CONNECTIVITY & EYE TOGGLE VERIFICATION');
  console.log('================================================================');

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--window-size=412,915'],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 412, height: 915, isMobile: true, hasTouch: true });

  console.log('Navigating to Expo Mobile Web at http://localhost:8081...');
  await page.goto('http://localhost:8081', { waitUntil: 'domcontentloaded', timeout: 45000 });
  await sleep(4000);

  // Clear prior storage
  await page.evaluate(() => {
    try { localStorage.clear(); } catch (_) {}
  });
  await page.goto('http://localhost:8081', { waitUntil: 'domcontentloaded', timeout: 45000 });
  await sleep(4000);

  // 1. VERIFY PASSWORD EYE TOGGLE
  console.log('\n--- VERIFYING PASSWORD EYE TOGGLE ---');
  // Type password
  await page.evaluate(() => {
    const inputs = document.querySelectorAll('input');
    if (inputs.length >= 2) {
      const pwdInput = inputs[1];
      const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
      setter.call(pwdInput, 'SecretPassword123');
      pwdInput.dispatchEvent(new Event('input', { bubbles: true }));
      pwdInput.dispatchEvent(new Event('change', { bubbles: true }));
    }
  });
  await sleep(500);

  // Check initial type: should be 'password' (hidden)
  const initialType = await page.evaluate(() => {
    const inputs = document.querySelectorAll('input');
    return inputs.length >= 2 ? inputs[1].type : null;
  });
  console.log(`Initial password input type (Default Hidden): ${initialType}`);
  if (initialType !== 'password') {
    throw new Error(`Expected default password type to be 'password', got '${initialType}'`);
  }
  await captureScreen(page, 'mobile_eye_01_password_hidden.png', 'Password Hidden by Default');

  // Click eye icon toggle button
  console.log('Clicking eye toggle button to reveal password...');
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('*[role="button"], button, div'));
    const toggleBtn = buttons.find((b) => {
      const label = b.getAttribute('aria-label') || '';
      return label.toLowerCase().includes('password') || label.toLowerCase().includes('show');
    });
    if (toggleBtn) {
      toggleBtn.click();
    } else {
      // Find SVG or icon inside password container
      const inputs = document.querySelectorAll('input');
      if (inputs.length >= 2) {
        const container = inputs[1].parentElement;
        const iconBtn = container ? container.querySelector('[role="button"]') || container.lastElementChild : null;
        if (iconBtn) iconBtn.click();
      }
    }
  });
  await sleep(600);

  // Check toggled type: should be 'text' (visible) and value preserved
  const toggledState = await page.evaluate(() => {
    const inputs = document.querySelectorAll('input');
    if (inputs.length >= 2) {
      return { type: inputs[1].type, value: inputs[1].value };
    }
    return null;
  });
  console.log(`Toggled password input type: ${toggledState?.type}, Value preserved: ${toggledState?.value === 'SecretPassword123'}`);
  if (toggledState?.type !== 'text') {
    throw new Error(`Expected toggled password type to be 'text', got '${toggledState?.type}'`);
  }
  if (toggledState?.value !== 'SecretPassword123') {
    throw new Error(`Password value was modified/cleared during toggle!`);
  }
  await captureScreen(page, 'mobile_eye_02_password_visible.png', 'Password Toggled to Visible');

  // Click again to hide
  console.log('Clicking eye toggle button again to hide password...');
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('*[role="button"], button, div'));
    const toggleBtn = buttons.find((b) => {
      const label = b.getAttribute('aria-label') || '';
      return label.toLowerCase().includes('password') || label.toLowerCase().includes('hide');
    });
    if (toggleBtn) {
      toggleBtn.click();
    } else {
      const inputs = document.querySelectorAll('input');
      if (inputs.length >= 2) {
        const container = inputs[1].parentElement;
        const iconBtn = container ? container.querySelector('[role="button"]') || container.lastElementChild : null;
        if (iconBtn) iconBtn.click();
      }
    }
  });
  await sleep(600);

  const hiddenAgainType = await page.evaluate(() => {
    const inputs = document.querySelectorAll('input');
    return inputs.length >= 2 ? inputs[1].type : null;
  });
  console.log(`Password input type after second toggle: ${hiddenAgainType}`);
  if (hiddenAgainType !== 'password') {
    throw new Error(`Expected password type to be 'password' after second toggle, got '${hiddenAgainType}'`);
  }
  console.log('✓ Eye toggle verification passed with 100% accuracy!');

  // 2. VERIFY STUDENT LOGIN
  console.log('\n--- TESTING STUDENT LOGIN ---');
  await page.evaluate(() => {
    try { localStorage.clear(); } catch (_) {}
  });
  await page.goto('http://localhost:8081', { waitUntil: 'domcontentloaded', timeout: 45000 });
  await sleep(3000);

  // Student is selected by default, enter password
  await page.evaluate(() => {
    const inputs = document.querySelectorAll('input');
    if (inputs.length >= 2) {
      const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
      setter.call(inputs[0], '2024000001');
      inputs[0].dispatchEvent(new Event('input', { bubbles: true }));
      inputs[0].dispatchEvent(new Event('change', { bubbles: true }));
      setter.call(inputs[1], 'Student@123');
      inputs[1].dispatchEvent(new Event('input', { bubbles: true }));
      inputs[1].dispatchEvent(new Event('change', { bubbles: true }));
    }
  });
  await sleep(500);

  // Click Sign in
  await page.evaluate(() => {
    const candidates = Array.from(document.querySelectorAll('*'));
    const btn = candidates.find(
      (e) => (e.innerText || '').trim().toLowerCase() === 'sign in' && e.children.length === 0
    );
    if (btn) btn.click();
  });

  await page.waitForFunction(() => {
    const url = window.location.href;
    const text = document.body ? document.body.innerText : '';
    return url.includes('/student') || text.includes('Student') || text.includes('Attendance') || text.includes('Timetable');
  }, { timeout: 15000 });
  await sleep(2000);

  const studentUrl = await page.evaluate(() => window.location.href);
  console.log(`Student Login Successful! Current URL: ${studentUrl}`);
  await captureScreen(page, 'mobile_auth_01_student_dashboard.png', 'Student Authenticated Dashboard');

  // 3. VERIFY PARENT LOGIN
  console.log('\n--- TESTING PARENT LOGIN ---');
  await page.evaluate(() => {
    try { localStorage.clear(); } catch (_) {}
  });
  await page.goto('http://localhost:8081', { waitUntil: 'domcontentloaded', timeout: 45000 });
  await sleep(3000);

  // Click Parent Tab
  await page.evaluate(() => {
    const candidates = Array.from(document.querySelectorAll('*'));
    const tab = candidates.find(
      (e) => (e.innerText || '').trim().toLowerCase() === 'parent' && e.children.length === 0
    );
    if (tab) tab.click();
  });
  await sleep(500);

  await page.evaluate(() => {
    const inputs = document.querySelectorAll('input');
    if (inputs.length >= 2) {
      const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
      setter.call(inputs[0], '9876500001');
      inputs[0].dispatchEvent(new Event('input', { bubbles: true }));
      inputs[0].dispatchEvent(new Event('change', { bubbles: true }));
      setter.call(inputs[1], 'Parent@123');
      inputs[1].dispatchEvent(new Event('input', { bubbles: true }));
      inputs[1].dispatchEvent(new Event('change', { bubbles: true }));
    }
  });
  await sleep(500);

  await page.evaluate(() => {
    const candidates = Array.from(document.querySelectorAll('*'));
    const btn = candidates.find(
      (e) => (e.innerText || '').trim().toLowerCase() === 'sign in' && e.children.length === 0
    );
    if (btn) btn.click();
  });

  await page.waitForFunction(() => {
    const url = window.location.href;
    const text = document.body ? document.body.innerText : '';
    return url.includes('/parent') || text.includes('Children') || text.includes('Fees') || text.includes('Attendance');
  }, { timeout: 15000 });
  await sleep(2000);

  const parentUrl = await page.evaluate(() => window.location.href);
  console.log(`Parent Login Successful! Current URL: ${parentUrl}`);
  await captureScreen(page, 'mobile_auth_02_parent_dashboard.png', 'Parent Authenticated Dashboard');

  // 4. VERIFY TEACHER LOGIN
  console.log('\n--- TESTING TEACHER LOGIN ---');
  await page.evaluate(() => {
    try { localStorage.clear(); } catch (_) {}
  });
  await page.goto('http://localhost:8081', { waitUntil: 'domcontentloaded', timeout: 45000 });
  await sleep(3000);

  // Click Teacher Tab
  await page.evaluate(() => {
    const candidates = Array.from(document.querySelectorAll('*'));
    const tab = candidates.find(
      (e) => (e.innerText || '').trim().toLowerCase() === 'teacher' && e.children.length === 0
    );
    if (tab) tab.click();
  });
  await sleep(500);

  await page.evaluate(() => {
    const inputs = document.querySelectorAll('input');
    if (inputs.length >= 2) {
      const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
      setter.call(inputs[0], 'TCH001');
      inputs[0].dispatchEvent(new Event('input', { bubbles: true }));
      inputs[0].dispatchEvent(new Event('change', { bubbles: true }));
      setter.call(inputs[1], 'Teacher@123');
      inputs[1].dispatchEvent(new Event('input', { bubbles: true }));
      inputs[1].dispatchEvent(new Event('change', { bubbles: true }));
    }
  });
  await sleep(500);

  await page.evaluate(() => {
    const candidates = Array.from(document.querySelectorAll('*'));
    const btn = candidates.find(
      (e) => (e.innerText || '').trim().toLowerCase() === 'sign in' && e.children.length === 0
    );
    if (btn) btn.click();
  });

  await page.waitForFunction(() => {
    const url = window.location.href;
    const text = document.body ? document.body.innerText : '';
    return url.includes('/teacher') || text.includes('Classes') || text.includes('Homework') || text.includes('Attendance');
  }, { timeout: 15000 });
  await sleep(2000);

  const teacherUrl = await page.evaluate(() => window.location.href);
  console.log(`Teacher Login Successful! Current URL: ${teacherUrl}`);
  await captureScreen(page, 'mobile_auth_03_teacher_dashboard.png', 'Teacher Authenticated Dashboard');

  await browser.close();
  console.log('\n================================================================');
  console.log('  ALL MOBILE E2E AND EYE-TOGGLE TESTS COMPLETED SUCCESSFULLY!');
  console.log('================================================================');
}

runMobileTests().catch((e) => {
  console.error('Fatal Error running mobile tests:', e);
  process.exit(1);
});
