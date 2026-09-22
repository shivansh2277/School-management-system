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

async function performLogin(page, loginId, password) {
  await page.goto('http://localhost:5173/#/login', { waitUntil: 'networkidle0', timeout: 30000 });
  await page.waitForSelector('input[type="password"]', { timeout: 10000 });

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

  await page.waitForFunction(() => {
    const token = localStorage.getItem('sunrise.token');
    return !!token && !window.location.hash.includes('/login');
  }, { timeout: 15000 });

  await sleep(1500);
}

async function runRBACTest() {
  console.log('================================================================');
  console.log('  STARTING RBAC E2E NAVIGATION & ROUTE PROTECTION VALIDATION');
  console.log('================================================================');

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--window-size=1366,768'],
  });

  try {
    // -------------------------------------------------------------
    // TEST 1: ADMISSION OFFICER
    // -------------------------------------------------------------
    console.log('\n[TEST 1] Verifying ADMISSION OFFICER navigation & route protection...');
    const aoContext = await browser.createBrowserContext();
    const aoPage = await aoContext.newPage();
    await aoPage.setViewport({ width: 1366, height: 768 });

    await performLogin(aoPage, 'admission@sunrisepublic.edu', 'Admin@123');

    const aoLinks = await aoPage.$$eval('aside nav a', els => els.map(e => e.innerText.trim()).filter(Boolean));
    console.log('Admission Officer Sidebar Screens:', aoLinks);

    // Assertions for Admission Officer:
    // 1. MUST NOT have Students, Classes, Notices
    if (aoLinks.includes('Students')) {
      throw new Error('FAIL: "Students" is present in Admission Officer sidebar!');
    }
    if (aoLinks.includes('Classes')) {
      throw new Error('FAIL: "Classes" is present in Admission Officer sidebar!');
    }
    if (aoLinks.includes('Notices')) {
      throw new Error('FAIL: "Notices" is present in Admission Officer sidebar!');
    }
    console.log('✓ Verified: "Students", "Classes", and "Notices" are completely absent from Admission Officer sidebar.');

    // 2. MUST have admission sections intact
    const expectedAOLinks = ['Enquiries', 'Applications', 'Merit & selection', 'Waitlist', 'Admission reports'];
    for (const exp of expectedAOLinks) {
      if (!aoLinks.includes(exp)) {
        throw new Error(`FAIL: Expected admission link "${exp}" missing from Admission Officer sidebar!`);
      }
    }
    console.log('✓ Verified: All 5 Admission pipeline sections are intact in Admission Officer sidebar.');

    await captureScreen(aoPage, 'e2e_web_03_admission_officer.png', 'Admission Officer Navigation Sidebar');

    // 3. Test direct URL access protection: #/students
    console.log('Navigating Admission Officer directly to protected URL: #/students ...');
    await aoPage.goto('http://localhost:5173/#/students', { waitUntil: 'networkidle0' });
    await sleep(1000);

    const studentsBlockedText = await aoPage.evaluate(() => document.body.innerText);
    if (!studentsBlockedText.includes('You do not have permission') || !studentsBlockedText.includes('students.profile.read')) {
      throw new Error(`FAIL: Direct URL access to #/students was not properly blocked! Page text: ${studentsBlockedText.slice(0, 200)}`);
    }
    console.log('✓ Verified: Direct URL navigation to #/students correctly blocked with "You do not have permission" (needs students.profile.read).');
    await captureScreen(aoPage, 'e2e_web_15_admission_officer_blocked_students.png', 'Admission Officer Blocked from Students');

    // 4. Test direct URL access protection: #/classes
    console.log('Navigating Admission Officer directly to protected URL: #/classes ...');
    await aoPage.goto('http://localhost:5173/#/classes', { waitUntil: 'networkidle0' });
    await sleep(1000);
    const classesBlockedText = await aoPage.evaluate(() => document.body.innerText);
    if (!classesBlockedText.includes('You do not have permission') || !classesBlockedText.includes('academics.class.read')) {
      throw new Error(`FAIL: Direct URL access to #/classes was not properly blocked! Page text: ${classesBlockedText.slice(0, 200)}`);
    }
    console.log('✓ Verified: Direct URL navigation to #/classes correctly blocked with "You do not have permission" (needs academics.class.read).');

    await aoContext.close();

    // -------------------------------------------------------------
    // TEST 2: FRONT DESK RECEPTIONIST
    // -------------------------------------------------------------
    console.log('\n[TEST 2] Verifying FRONT DESK RECEPTIONIST navigation & route protection...');
    const recContext = await browser.createBrowserContext();
    const recPage = await recContext.newPage();
    await recPage.setViewport({ width: 1366, height: 768 });

    await performLogin(recPage, 'receptionist@sunrisepublic.edu', 'Admin@123');

    const recLinks = await recPage.$$eval('aside nav a', els => els.map(e => e.innerText.trim()).filter(Boolean));
    console.log('Receptionist Sidebar Screens:', recLinks);

    // Assertions for Receptionist:
    // 1. MUST NOT have Applications, Merit & selection, Waitlist, Admission reports
    if (recLinks.includes('Applications')) {
      throw new Error('FAIL: "Applications" is present in Receptionist sidebar!');
    }
    if (recLinks.includes('Merit & selection')) {
      throw new Error('FAIL: "Merit & selection" is present in Receptionist sidebar!');
    }
    if (recLinks.includes('Waitlist')) {
      throw new Error('FAIL: "Waitlist" is present in Receptionist sidebar!');
    }
    if (recLinks.includes('Admission reports')) {
      throw new Error('FAIL: "Admission reports" is present in Receptionist sidebar!');
    }
    console.log('✓ Verified: "Applications" and application-processing links are completely absent from Receptionist sidebar.');

    // 2. MUST have Enquiries intact
    if (!recLinks.includes('Enquiries')) {
      throw new Error('FAIL: Expected front-desk link "Enquiries" missing from Receptionist sidebar!');
    }
    console.log('✓ Verified: Receptionist remains focused on "Enquiries" workflow.');

    await captureScreen(recPage, 'e2e_web_02_receptionist.png', 'Receptionist Navigation Sidebar (No Applications)');

    // 3. Test direct URL access protection: #/admission/applications
    console.log('Navigating Receptionist directly to protected URL: #/admission/applications ...');
    await recPage.goto('http://localhost:5173/#/admission/applications', { waitUntil: 'networkidle0' });
    await sleep(1000);

    const appsBlockedText = await recPage.evaluate(() => document.body.innerText);
    if (!appsBlockedText.includes('You do not have permission') || !appsBlockedText.includes('admission.application.read')) {
      throw new Error(`FAIL: Direct URL access to #/admission/applications was not properly blocked! Page text: ${appsBlockedText.slice(0, 200)}`);
    }
    console.log('✓ Verified: Direct URL navigation to #/admission/applications correctly blocked with "You do not have permission" (needs admission.application.read).');
    await captureScreen(recPage, 'e2e_web_16_receptionist_blocked_applications.png', 'Receptionist Blocked from Applications');

    await recContext.close();

    // -------------------------------------------------------------
    // TEST 3: SUPER ADMIN & PRINCIPAL REGRESSION CHECK
    // -------------------------------------------------------------
    console.log('\n[TEST 3] Verifying Super Admin and Principal navigation intact...');
    const adminContext = await browser.createBrowserContext();
    const adminPage = await adminContext.newPage();
    await adminPage.setViewport({ width: 1366, height: 768 });

    await performLogin(adminPage, 'admin@sunrisepublic.edu', 'Admin@123');
    const adminLinks = await adminPage.$$eval('aside nav a', els => els.map(e => e.innerText.trim()).filter(Boolean));
    console.log(`Super Admin Sidebar Screens (${adminLinks.length}):`, adminLinks.slice(0, 10).join(', ') + '...');
    if (!adminLinks.includes('Students') || !adminLinks.includes('Classes') || !adminLinks.includes('Applications')) {
      throw new Error('FAIL: Super Admin lost essential navigation links!');
    }
    console.log('✓ Verified: Super Admin navigation is intact.');
    await captureScreen(adminPage, 'e2e_web_01_super_admin.png', 'Super Admin Authenticated View');
    await adminContext.close();

    const princContext = await browser.createBrowserContext();
    const princPage = await princContext.newPage();
    await princPage.setViewport({ width: 1366, height: 768 });

    await performLogin(princPage, 'principal@sunrisepublic.edu', 'Admin@123');
    const princLinks = await princPage.$$eval('aside nav a', els => els.map(e => e.innerText.trim()).filter(Boolean));
    console.log(`Principal Sidebar Screens (${princLinks.length}):`, princLinks.slice(0, 10).join(', ') + '...');
    if (!princLinks.includes('Students') || !princLinks.includes('Classes')) {
      throw new Error('FAIL: Principal lost essential navigation links!');
    }
    console.log('✓ Verified: Principal navigation is intact.');
    await captureScreen(princPage, 'e2e_web_05_principal.png', 'Principal Authenticated View');
    await princContext.close();

    console.log('\n================================================================');
    console.log('  ALL RBAC AND ROUTE PROTECTION TESTS PASSED SUCCESSFULLY!');
    console.log('================================================================');
  } finally {
    await browser.close();
  }
}

runRBACTest().catch((err) => {
  console.error('Fatal Test Error:', err);
  process.exit(1);
});
