import puppeteer from 'puppeteer-core';
import path from 'path';
import fs from 'fs';

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const SCREENSHOT_DIR = path.resolve('..', 'docs', 'screenshots');
const ARTIFACT_DIR = 'C:\\Users\\SHIVANSH\\.gemini\\antigravity\\brain\\3ef88ed0-50dc-47a4-bc44-2809c7e8a404';
const BASE_URL = 'http://localhost:5173';

if (!fs.existsSync(SCREENSHOT_DIR)) fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });

function saveScreenshot(filename, buffer) {
  const f1 = path.join(SCREENSHOT_DIR, filename);
  fs.writeFileSync(f1, buffer);
  try {
    if (!fs.existsSync(ARTIFACT_DIR)) fs.mkdirSync(ARTIFACT_DIR, { recursive: true });
    const f2 = path.join(ARTIFACT_DIR, filename);
    fs.writeFileSync(f2, buffer);
  } catch (e) {
    console.warn(`Artifact copy failed: ${e.message}`);
  }
  console.log(`  [SAVED] ${filename}`);
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function performLogin(page, loginId, password) {
  await page.goto(`${BASE_URL}/#/login`, { waitUntil: 'networkidle0', timeout: 30000 });
  await page.waitForSelector('input[type="password"]', { timeout: 10000 });

  await page.evaluate(({ loginId, password }) => {
    const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
    const emailInput = document.querySelector('input:not([type="password"])');
    const pwdInput = document.querySelector('input[type="password"]');
    setter.call(emailInput, loginId);
    emailInput.dispatchEvent(new Event('input', { bubbles: true }));
    setter.call(pwdInput, password);
    pwdInput.dispatchEvent(new Event('input', { bubbles: true }));
  }, { loginId, password });

  await page.click('form button');
  await sleep(3000);
}

async function run() {
  console.log('================================================================');
  console.log('  VERIFY SESSION 13: ROLE-SPECIFIC SIDEBAR & RBAC HARDENING');
  console.log('================================================================\n');

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--window-size=1440,900'],
  });

  let passed = 0;
  let failed = 0;

  function check(label, condition) {
    if (condition) {
      console.log(`  ✓ ${label}`);
      passed++;
    } else {
      console.log(`  ✗ FAIL: ${label}`);
      failed++;
    }
  }

  try {
    // ------------------------------------------------------------------
    // FLOW 1: ADMIN ROLE SIDEBAR & DIRECT ROUTE GATING
    // ------------------------------------------------------------------
    console.log('\n--- FLOW 1: Admin Role Sidebar & Route Gating ---');
    {
      const ctx = await browser.createBrowserContext();
      const page = await ctx.newPage();
      await page.setViewport({ width: 1440, height: 900 });

      await performLogin(page, 'admin@sunrisepublic.edu', 'Admin@123');
      check('Admin login successful', page.url().includes('#/'));

      await page.goto(`${BASE_URL}/#/dashboard`, { waitUntil: 'networkidle0', timeout: 20000 });
      await sleep(2000);

      const sidebarText = await page.evaluate(() => {
        const sidebar = document.querySelector('aside');
        return sidebar ? sidebar.innerText : '';
      });

      // 1. Admission Module checks
      check('Admin sees Admission Dashboard in sidebar', sidebarText.includes('Admission dashboard'));
      check('Admin DOES NOT see Enquiries in sidebar', !sidebarText.includes('Enquiries'));
      check('Admin DOES NOT see Applications in sidebar', !sidebarText.includes('Applications'));
      check('Admin DOES NOT see Merit & selection in sidebar', !sidebarText.includes('Merit & selection'));
      check('Admin DOES NOT see Waitlist in sidebar', !sidebarText.includes('Waitlist'));
      check('Admin DOES NOT see Admission reports in sidebar', !sidebarText.includes('Admission reports'));

      // 2. Money Module checks
      check('Admin sees Fees in sidebar', sidebarText.includes('Fees'));
      check('Admin sees Fee setup in sidebar', sidebarText.includes('Fee setup'));
      check('Admin sees Period close in sidebar', sidebarText.includes('Period close'));
      check('Admin DOES NOT see Student fees in sidebar', !sidebarText.includes('Student fees'));
      check('Admin DOES NOT see Defaulters in sidebar', !sidebarText.includes('Defaulters'));

      // 3. Front Desk Module checks
      check('Admin sees Meeting Slips in sidebar', sidebarText.includes('Meeting Slips'));
      check('Admin sees Important Directory in sidebar', sidebarText.includes('Important Directory'));
      check('Admin DOES NOT see Found & Lost in sidebar', !sidebarText.includes('Found & Lost'));
      check('Admin DOES NOT see Student Passes in sidebar', !sidebarText.includes('Student Passes'));
      check('Admin DOES NOT see Fee Counter in sidebar', !sidebarText.includes('Fee Counter'));

      // Retained modules
      check('Admin sees Students in sidebar', sidebarText.includes('Students'));
      check('Admin sees Staff in sidebar', sidebarText.includes('Staff'));
      check('Admin sees Classes in sidebar', sidebarText.includes('Classes'));
      check('Admin sees Configuration in sidebar', sidebarText.includes('Configuration'));

      // Capture official screenshot proof for Admin
      const adminShot = await page.screenshot({ fullPage: false });
      saveScreenshot('proof_admin_sidebar_hardened.png', adminShot);

      // Direct URL Navigation Gating for Admin
      console.log('  Testing Admin direct URL restrictions...');
      const adminRestrictedUrls = [
        { url: '/admission/enquiries', name: 'Enquiries' },
        { url: '/admission/applications', name: 'Applications' },
        { url: '/admission/merit', name: 'Merit & selection' },
        { url: '/admission/selection', name: 'Selection (alias)' },
        { url: '/admission/waitlist', name: 'Waitlist' },
        { url: '/admission/reports', name: 'Admission reports' },
        { url: '/fees/ledger', name: 'Student fees' },
        { url: '/fees/defaulters', name: 'Defaulters' },
        { url: '/reception/found-items', name: 'Found & Lost' },
        { url: '/reception/found-lost', name: 'Found & Lost (alias)' },
        { url: '/reception/passes', name: 'Student Passes' },
        { url: '/reception/fee-counter', name: 'Fee Counter' },
      ];

      for (const item of adminRestrictedUrls) {
        await page.goto(`${BASE_URL}/#${item.url}`, { waitUntil: 'networkidle0', timeout: 15000 });
        await sleep(1000);
        const pageContent = await page.evaluate(() => document.body.innerText);
        const isBlocked = pageContent.includes('Access Restricted') || pageContent.includes('restricted for your role');
        check(`Admin direct URL ${item.url} is refused (${item.name})`, isBlocked);
      }

      await ctx.close();
    }

    // ------------------------------------------------------------------
    // FLOW 2: TRANSPORT IN-CHARGE ROLE SIDEBAR & DIRECT ROUTE GATING
    // ------------------------------------------------------------------
    console.log('\n--- FLOW 2: Transport In-Charge Role Sidebar & Route Gating ---');
    {
      const ctx = await browser.createBrowserContext();
      const page = await ctx.newPage();
      await page.setViewport({ width: 1440, height: 900 });

      await performLogin(page, 'transport@sunrisepublic.edu', 'Admin@123');
      check('Transport In-Charge login successful', page.url().includes('#/'));

      // Wait for navigation
      await sleep(2500);

      const sidebarText = await page.evaluate(() => {
        const sidebar = document.querySelector('aside');
        return sidebar ? sidebar.innerText : '';
      });

      // People module must be completely removed
      check('Transport In-Charge sidebar DOES NOT contain "PEOPLE"', !sidebarText.includes('PEOPLE'));
      check('Transport In-Charge sidebar DOES NOT contain "Students"', !sidebarText.includes('Students'));
      check('Transport In-Charge sidebar DOES NOT contain "Staff"', !sidebarText.includes('Staff'));
      check('Transport In-Charge sidebar DOES NOT contain "Staff leave"', !sidebarText.includes('Staff leave'));

      // Academics module must be completely removed
      check('Transport In-Charge sidebar DOES NOT contain "ACADEMICS"', !sidebarText.includes('ACADEMICS'));
      check('Transport In-Charge sidebar DOES NOT contain "Classes"', !sidebarText.includes('Classes'));
      check('Transport In-Charge sidebar DOES NOT contain "Attendance"', !sidebarText.includes('Attendance'));
      check('Transport In-Charge sidebar DOES NOT contain "Exams"', !sidebarText.includes('Exams'));
      check('Transport In-Charge sidebar DOES NOT contain "Session rollover"', !sidebarText.includes('Session rollover'));

      // Other non-transport modules must not appear
      check('Transport In-Charge sidebar DOES NOT contain "Fees"', !sidebarText.includes('Fees'));
      check('Transport In-Charge sidebar DOES NOT contain "Admission"', !sidebarText.includes('Admission'));
      check('Transport In-Charge sidebar DOES NOT contain "Front Desk"', !sidebarText.includes('Front Desk'));

      // Allowed screens: Transport and Notices
      check('Transport In-Charge sidebar contains "Transport"', sidebarText.includes('Transport'));
      check('Transport In-Charge sidebar contains "Notices"', sidebarText.includes('Notices'));

      // Navigate to transport page and capture screenshot proof
      await page.goto(`${BASE_URL}/#/transport`, { waitUntil: 'networkidle0', timeout: 20000 });
      await sleep(2500);

      const transportShot = await page.screenshot({ fullPage: false });
      saveScreenshot('proof_transport_sidebar_hardened.png', transportShot);

      // Verify Riders modal queries student/class data without standalone management screens
      console.log('  Testing Transport Riders modal student/class data...');
      const rowClicked = await page.evaluate(() => {
        const row = document.querySelector('table tbody tr');
        if (row) {
          row.click();
          return true;
        }
        return false;
      });
      if (rowClicked) {
        await sleep(2000);
        const modalText = await page.evaluate(() => {
          const modal = document.querySelector('[role="dialog"], .fixed');
          return modal ? modal.innerText : '';
        });
        check('Transport Riders modal displays student names and class labels', modalText.includes('Who rides this route') || modalText.includes('Child'));
      }

      // Direct URL Navigation Gating for Transport In-Charge
      console.log('  Testing Transport In-Charge direct URL restrictions...');
      const transportRestrictedUrls = [
        { url: '/students', name: 'Students' },
        { url: '/teachers', name: 'Staff' },
        { url: '/staff-leave', name: 'Staff leave' },
        { url: '/classes', name: 'Classes' },
        { url: '/attendance', name: 'Attendance' },
        { url: '/exams', name: 'Exams' },
        { url: '/admin/session-rollover', name: 'Session rollover' },
        { url: '/fees', name: 'Fees' },
      ];

      for (const item of transportRestrictedUrls) {
        await page.goto(`${BASE_URL}/#${item.url}`, { waitUntil: 'networkidle0', timeout: 15000 });
        await sleep(1000);
        const pageContent = await page.evaluate(() => document.body.innerText);
        const isBlocked = pageContent.includes('Access Restricted') || pageContent.includes('You do not have permission');
        check(`Transport In-Charge direct URL ${item.url} is refused (${item.name})`, isBlocked);
      }

      await ctx.close();
    }

    // ------------------------------------------------------------------
    // FLOW 3: PRESERVATION OF OTHER ROLES
    // ------------------------------------------------------------------
    console.log('\n--- FLOW 3: Preservation of Other Operational Roles ---');
    {
      // 1. Admission Officer
      const ctx1 = await browser.createBrowserContext();
      const page1 = await ctx1.newPage();
      await page1.setViewport({ width: 1440, height: 900 });

      await performLogin(page1, 'admission@sunrisepublic.edu', 'Admin@123');
      await page1.goto(`${BASE_URL}/#/admission/applications`, { waitUntil: 'networkidle0', timeout: 20000 });
      await sleep(2000);

      const admSidebar = await page1.evaluate(() => document.querySelector('aside')?.innerText || '');
      check('Admission Officer sees Enquiries', admSidebar.includes('Enquiries'));
      check('Admission Officer sees Applications', admSidebar.includes('Applications'));
      check('Admission Officer sees Merit & selection', admSidebar.includes('Merit & selection'));
      check('Admission Officer sees Waitlist', admSidebar.includes('Waitlist'));
      check('Admission Officer sees Admission reports', admSidebar.includes('Admission reports'));

      const admContent = await page1.evaluate(() => document.body.innerText);
      check('Admission Officer can open Applications page without refusal', !admContent.includes('Access Restricted'));
      await ctx1.close();

      // 2. Accounts Officer
      const ctx2 = await browser.createBrowserContext();
      const page2 = await ctx2.newPage();
      await page2.setViewport({ width: 1440, height: 900 });

      await performLogin(page2, 'accounts@sunrisepublic.edu', 'Admin@123');
      await page2.goto(`${BASE_URL}/#/fees/ledger`, { waitUntil: 'networkidle0', timeout: 20000 });
      await sleep(2000);

      const accSidebar = await page2.evaluate(() => document.querySelector('aside')?.innerText || '');
      check('Accounts Officer sees Fees', accSidebar.includes('Fees'));
      check('Accounts Officer sees Student fees', accSidebar.includes('Student fees'));
      check('Accounts Officer sees Defaulters', accSidebar.includes('Defaulters'));
      check('Accounts Officer sees Payroll', accSidebar.includes('Payroll'));

      const accContent = await page2.evaluate(() => document.body.innerText);
      check('Accounts Officer can open Student fees without refusal', !accContent.includes('Access Restricted'));
      await ctx2.close();

      // 3. Receptionist
      const ctx3 = await browser.createBrowserContext();
      const page3 = await ctx3.newPage();
      await page3.setViewport({ width: 1440, height: 900 });

      await performLogin(page3, 'receptionist@sunrisepublic.edu', 'Admin@123');
      await page3.goto(`${BASE_URL}/#/reception/passes`, { waitUntil: 'networkidle0', timeout: 20000 });
      await sleep(2000);

      const recSidebar = await page3.evaluate(() => document.querySelector('aside')?.innerText || '');
      check('Receptionist sees Found & Lost', recSidebar.includes('Found & Lost'));
      check('Receptionist sees Student Passes', recSidebar.includes('Student Passes'));
      check('Receptionist sees Meeting Slips', recSidebar.includes('Meeting Slips'));
      check('Receptionist sees Important Directory', recSidebar.includes('Important Directory'));
      check('Receptionist sees Fee Counter', recSidebar.includes('Fee Counter'));

      const recContent = await page3.evaluate(() => document.body.innerText);
      check('Receptionist can open Student Passes without refusal', !recContent.includes('Access Restricted'));
      await ctx3.close();
    }

  } catch (err) {
    console.error(`Verification aborted due to error: ${err.message}`);
    failed++;
  } finally {
    await browser.close();
  }

  console.log('\n================================================================');
  console.log(`  VERIFICATION RESULTS: ${passed} PASSED | ${failed} FAILED`);
  console.log('================================================================');
  if (failed > 0) process.exit(1);
}

run();
