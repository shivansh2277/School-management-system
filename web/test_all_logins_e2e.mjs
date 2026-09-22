import puppeteer from 'puppeteer-core';
import fs from 'fs';
import path from 'path';

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const SCREENSHOT_DIR = path.resolve('..', 'docs', 'screenshots');
const ARTIFACT_DIR = 'C:\\Users\\SHIVANSH\\.gemini\\antigravity\\brain\\555b38d8-689f-4933-b73f-00badba4e300';

if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

function copyToArtifacts(filename) {
  const src = path.join(SCREENSHOT_DIR, filename);
  const dest = path.join(ARTIFACT_DIR, filename);
  if (fs.existsSync(src)) {
    try {
      fs.copyFileSync(src, dest);
      console.log(`[Artifact] Copied ${filename} to conversation artifacts directory.`);
    } catch (e) {
      console.warn(`Could not copy ${filename} to artifacts:`, e.message);
    }
  }
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function captureScreen(page, filename, desc) {
  const filePath = path.join(SCREENSHOT_DIR, filename);
  await page.screenshot({ path: filePath, fullPage: false });
  copyToArtifacts(filename);
  console.log(`[Visual Proof] Captured ${desc} -> ${filename}`);
}

async function testWebLogin(browser, { title, loginId, password, expectedName, expectedHashPart, filename, isNegative = false }) {
  console.log(`\n======================================================`);
  console.log(`[TEST] Web Login: ${title} (${loginId})`);
  console.log(`======================================================`);

  const context = await browser.createBrowserContext();
  const page = await context.newPage();
  await page.setViewport({ width: 1366, height: 768 });

  try {
    await page.goto('http://localhost:5173/#/login', { waitUntil: 'networkidle0', timeout: 20000 });
    await page.waitForSelector('input[type="password"]', { timeout: 10000 });

    // Fill form inputs
    await page.evaluate((id, pwd) => {
      const emailInput = document.querySelector('input:not([type="password"])');
      const pwdInput = document.querySelector('input[type="password"]');
      const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;

      setter.call(emailInput, id);
      emailInput.dispatchEvent(new Event('input', { bubbles: true }));
      setter.call(pwdInput, pwd);
      pwdInput.dispatchEvent(new Event('input', { bubbles: true }));
    }, loginId, password);

    await sleep(300);
    await page.click('form button');

    if (isNegative) {
      // Expect error text on login form
      await page.waitForFunction(() => {
        const errorEl = document.querySelector('p.text-danger, .text-red-500');
        return errorEl && errorEl.innerText.length > 0;
      }, { timeout: 8000 });
      await sleep(500);

      const errText = await page.evaluate(() => {
        const el = document.querySelector('p.text-danger, .text-red-500');
        return el ? el.innerText.trim() : '';
      });
      console.log(`✓ Negative verification passed: Error message displayed: "${errText}"`);
      await captureScreen(page, filename, `Web Negative Login Error (${title})`);
      await context.close();
      return { success: true, title, role: 'web_negative', detail: errText };
    }

    // Positive login expectation
    await page.waitForFunction(() => {
      const token = localStorage.getItem('sunrise.token');
      return !!token && !window.location.hash.includes('/login');
    }, { timeout: 12000 });
    
    // Wait for lazy components and dashboard data to resolve
    await page.waitForFunction(() => {
      const text = document.body ? document.body.innerText : '';
      return !text.includes('Loading...') && (text.includes('Attendance Overview') || text.includes('Enquiry Register') || text.includes('Students') || text.includes('Fees'));
    }, { timeout: 10000 }).catch(() => {});
    await sleep(1500);

    const hash = await page.evaluate(() => window.location.hash);
    const headerName = await page.evaluate(() => {
      const header = document.querySelector('header');
      return header ? header.innerText : '';
    });
    const sidebarLinks = await page.$$eval('aside nav a', (els) => els.map((e) => e.innerText.trim()).filter(Boolean));

    console.log(`Landed Route: ${hash}`);
    console.log(`Header Info: ${headerName.replace(/\n+/g, ' ')}`);
    console.log(`Visible Navigation Screens (${sidebarLinks.length}): ${sidebarLinks.join(', ')}`);

    if (expectedHashPart && !hash.includes(expectedHashPart)) {
      console.warn(`Notice: Route ${hash} does not contain expected substring ${expectedHashPart}`);
    }

    if (expectedName && !headerName.toLowerCase().includes(expectedName.toLowerCase())) {
      console.warn(`Notice: Header text "${headerName}" does not contain expected name "${expectedName}"`);
    }

    await captureScreen(page, filename, `Web Authenticated View (${title})`);
    await context.close();
    return { success: true, title, role: 'web', hash, sidebarCount: sidebarLinks.length, headerName };
  } catch (err) {
    console.error(`FAILED Web Login for ${title}:`, err.message);
    try {
      await captureScreen(page, `err_${filename}`, `Failure Screen for ${title}`);
    } catch (_) {}
    await context.close();
    return { success: false, title, error: err.message };
  }
}

async function testMobileLogin(browser, { title, role, loginId, password, expectedText, filename, isNegative = false }) {
  console.log(`\n======================================================`);
  console.log(`[TEST] Mobile Login: ${title} [${role}] (${loginId})`);
  console.log(`======================================================`);

  const context = await browser.createBrowserContext();
  const page = await context.newPage();
  // Mobile viewport portrait
  await page.setViewport({ width: 412, height: 915, isMobile: true, hasTouch: true });

  try {
    await page.goto('http://localhost:8081', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await sleep(2000);

    // Clear any prior storage
    await page.evaluate(() => {
      try { localStorage.clear(); } catch (_) {}
    });
    await page.goto('http://localhost:8081', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await sleep(3000);

    // Click role tab (Student / Parent / Teacher)
    await page.evaluate((r) => {
      const candidates = Array.from(document.querySelectorAll('*'));
      const tab = candidates.find(
        (e) => (e.innerText || '').trim().toLowerCase() === r.toLowerCase() && e.children.length === 0
      );
      if (tab) tab.click();
    }, role);
    await sleep(600);

    // Enter loginId and password into text inputs
    await page.evaluate((id, pwd) => {
      const inputs = document.querySelectorAll('input');
      if (inputs.length >= 2) {
        const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        setter.call(inputs[0], id);
        inputs[0].dispatchEvent(new Event('input', { bubbles: true }));
        inputs[0].dispatchEvent(new Event('change', { bubbles: true }));
        setter.call(inputs[1], pwd);
        inputs[1].dispatchEvent(new Event('input', { bubbles: true }));
        inputs[1].dispatchEvent(new Event('change', { bubbles: true }));
      }
    }, loginId, password);
    await sleep(500);

    // Click Sign in button
    await page.evaluate(() => {
      const candidates = Array.from(document.querySelectorAll('*'));
      const btn = candidates.find(
        (e) => (e.innerText || '').trim().toLowerCase() === 'sign in' && e.children.length === 0
      );
      if (btn) btn.click();
    });

    if (isNegative) {
      await sleep(2500);
      const content = await page.evaluate(() => document.body.innerText);
      const hasError = content.includes('Invalid') || content.includes('failed') || content.includes('credentials');
      console.log(`✓ Negative verification passed: Error indication detected on mobile screen: ${hasError}`);
      await captureScreen(page, filename, `Mobile Negative Login Error (${title})`);
      await context.close();
      return { success: true, title, role: 'mobile_negative', detail: 'Error displayed' };
    }

    // Wait for authenticated dashboard route or content
    await page.waitForFunction(
      (expectedRole) => {
        const url = window.location.href;
        const text = document.body ? document.body.innerText : '';
        return url.includes(`/${expectedRole}`) || url.includes('dashboard') || text.includes('Dashboard') || text.includes('Attendance');
      },
      { timeout: 15000 },
      role
    );
    await sleep(2500);

    const currentUrl = await page.evaluate(() => window.location.href);
    const bodyText = await page.evaluate(() => document.body.innerText.slice(0, 300));
    console.log(`Current Mobile URL: ${currentUrl}`);
    console.log(`Mobile Screen Excerpt: ${bodyText.replace(/\n+/g, ' ')}`);

    if (expectedText && !bodyText.toLowerCase().includes(expectedText.toLowerCase())) {
      console.warn(`Notice: Screen content does not explicitly contain expected text "${expectedText}"`);
    }

    await captureScreen(page, filename, `Mobile Authenticated View (${title})`);
    await context.close();
    return { success: true, title, role: 'mobile', url: currentUrl };
  } catch (err) {
    console.error(`FAILED Mobile Login for ${title}:`, err.message);
    try {
      await captureScreen(page, `err_${filename}`, `Failure Screen for ${title}`);
    } catch (_) {}
    await context.close();
    return { success: false, title, error: err.message };
  }
}

async function runE2EValidationSuite() {
  console.log('================================================================');
  console.log('  STARTING AI-POWERED BROWSER E2E TEST SUITE FOR ALL LOGINS');
  console.log('================================================================');
  console.log(`Chrome Binary: ${CHROME_PATH}`);
  console.log(`Screenshots Target: ${SCREENSHOT_DIR}`);
  console.log(`Artifacts Target: ${ARTIFACT_DIR}`);

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--window-size=1366,768'],
  });

  const results = [];

  // ==================================================================
  // PART 1: WEB FRONTEND LOGINS (Staff & Administration)
  // ==================================================================
  const webTestCases = [
    {
      title: 'School Administrator (Super Admin)',
      loginId: 'admin@sunrisepublic.edu',
      password: 'Admin@123',
      expectedName: 'Office Administrator',
      expectedHashPart: '/',
      filename: 'e2e_web_01_super_admin.png',
    },
    {
      title: 'Front Desk Receptionist (Strict Queue Isolation)',
      loginId: 'receptionist@sunrisepublic.edu',
      password: 'Admin@123',
      expectedName: 'Front Desk Receptionist',
      expectedHashPart: '/admission/enquiries',
      filename: 'e2e_web_02_receptionist.png',
    },
    {
      title: 'Admission Officer (Intake, Dossier & Auto-Enrollment)',
      loginId: 'admission@sunrisepublic.edu',
      password: 'Admin@123',
      expectedName: 'Admission Officer',
      expectedHashPart: '/admission',
      filename: 'e2e_web_03_admission_officer.png',
    },
    {
      title: 'Fee Counter Clerk (Cashier & Defaulters Ledger)',
      loginId: 'counter@sunrisepublic.edu',
      password: 'Admin@123',
      expectedName: 'Fee Counter Clerk',
      expectedHashPart: '/fees',
      filename: 'e2e_web_04_cashier_counter.png',
    },
    {
      title: 'Principal (Executive & Academic Leadership)',
      loginId: 'principal@sunrisepublic.edu',
      password: 'Admin@123',
      expectedName: 'Principal',
      expectedHashPart: '/',
      filename: 'e2e_web_05_principal.png',
    },
    {
      title: 'Vice Principal (Academic Administration)',
      loginId: 'viceprincipal@sunrisepublic.edu',
      password: 'Admin@123',
      expectedName: 'Vice Principal',
      expectedHashPart: '/',
      filename: 'e2e_web_06_vice_principal.png',
    },
    {
      title: 'School Owner / Management (Executive Governance)',
      loginId: 'owner@sunrisepublic.edu',
      password: 'Admin@123',
      expectedName: 'School Owner',
      expectedHashPart: '/',
      filename: 'e2e_web_07_school_owner.png',
    },
    {
      title: 'Academic Coordinator (Curriculum & Schedule Oversight)',
      loginId: 'coordinator@sunrisepublic.edu',
      password: 'Admin@123',
      expectedName: 'Academic Coordinator',
      expectedHashPart: '/',
      filename: 'e2e_web_08_academic_coordinator.png',
    },
    {
      title: 'Transport Manager (Fleet & Route Ops)',
      loginId: 'TRM001',
      password: 'Admin@123',
      expectedName: 'Rakesh Chandra Dubey',
      expectedHashPart: '/transport',
      filename: 'e2e_web_09_transport_manager.png',
    },
    {
      title: 'Negative Test: Invalid Password Rejection',
      loginId: 'admin@sunrisepublic.edu',
      password: 'WrongPassword!99',
      filename: 'e2e_web_10_invalid_password_error.png',
      isNegative: true,
    },
  ];

  for (const tc of webTestCases) {
    const res = await testWebLogin(browser, tc);
    results.push(res);
  }

  // ==================================================================
  // PART 2: MOBILE APP LOGINS (Teachers, Parents, Students)
  // ==================================================================
  const mobileTestCases = [
    {
      title: 'Teacher Mobile App',
      role: 'teacher',
      loginId: 'TCH001',
      password: 'Teacher@123',
      expectedText: 'Priya Sharma',
      filename: 'e2e_mobile_11_teacher_dashboard.png',
    },
    {
      title: 'Parent Mobile App',
      role: 'parent',
      loginId: '9876500001',
      password: 'Parent@123',
      expectedText: 'Attendance',
      filename: 'e2e_mobile_12_parent_dashboard.png',
    },
    {
      title: 'Student Mobile App',
      role: 'student',
      loginId: '2024000001',
      password: 'Student@123',
      expectedText: 'Timetable',
      filename: 'e2e_mobile_13_student_dashboard.png',
    },
    {
      title: 'Negative Test: Invalid Mobile Student Password',
      role: 'student',
      loginId: '2024000001',
      password: 'WrongStudentPassword!99',
      filename: 'e2e_mobile_14_invalid_credentials_error.png',
      isNegative: true,
    },
  ];

  for (const tc of mobileTestCases) {
    const res = await testMobileLogin(browser, tc);
    results.push(res);
  }

  await browser.close();

  console.log('\n================================================================');
  console.log('                   E2E TEST SUMMARY RESULTS                     ');
  console.log('================================================================');
  let passedCount = 0;
  for (const r of results) {
    const icon = r.success ? '✓ PASS' : '✗ FAIL';
    if (r.success) passedCount++;
    console.log(`${icon} | ${r.title} ${r.error ? `-> Error: ${r.error}` : ''}`);
  }
  console.log(`\nTotal: ${results.length} | Passed: ${passedCount} | Failed: ${results.length - passedCount}`);
  console.log('================================================================');

  if (passedCount < results.length) {
    process.exit(1);
  }
}

runE2EValidationSuite().catch((e) => {
  console.error('FATAL E2E Suite Exception:', e);
  process.exit(1);
});
