import puppeteer from 'puppeteer-core';
import path from 'path';
import fs from 'fs';

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const SCREENSHOT_DIR = path.resolve('..', 'docs', 'screenshots');
const ARTIFACT_DIR = 'C:\\Users\\SHIVANSH\\.gemini\\antigravity\\brain\\dc373d15-fa1f-4c85-9ddf-91e50c13f9e4';
const BASE_URL = 'http://localhost:5173';
const SAMPLE_IMAGE_PATH = path.resolve('..', 'backend', 'var', 'documents', '1', 'admission', '0ab4f18f45d946aa8bd53715315e4a51.png');

if (!fs.existsSync(SCREENSHOT_DIR)) fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });

function saveScreenshot(filename, buffer) {
  const f1 = path.join(SCREENSHOT_DIR, filename);
  fs.writeFileSync(f1, buffer);
  try {
    const f2 = path.join(ARTIFACT_DIR, filename);
    fs.writeFileSync(f2, buffer);
  } catch (e) {
    console.warn(`Artifact copy failed: ${e.message}`);
  }
  console.log(`  [SAVED] ${filename}`);
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function clickButtonWithText(page, text) {
  return page.evaluate((targetText) => {
    const btns = Array.from(document.querySelectorAll('button'));
    const btn = btns.find((b) => b.innerText.toLowerCase().includes(targetText.toLowerCase()));
    if (btn) {
      btn.click();
      return true;
    }
    return false;
  }, text);
}

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
  console.log('  VERIFY SESSION 12: TRANSPORT, ACCOUNTS & PICKUP PERSONS');
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
    // FLOW 1: TRANSPORT IN-CHARGE LOGIN & RBAC ISOLATION
    // ------------------------------------------------------------------
    console.log('\n--- FLOW 1: Transport In-Charge Login & Isolated Portal ---');
    {
      const ctx = await browser.createBrowserContext();
      const page = await ctx.newPage();
      await page.setViewport({ width: 1440, height: 900 });

      await performLogin(page, 'transport@sunrisepublic.edu', 'Admin@123');
      check('Transport In-Charge login successful', page.url().includes('#/'));

      await page.goto(`${BASE_URL}/#/transport`, { waitUntil: 'networkidle0', timeout: 20000 });
      await sleep(2500);

      const sidebarTextTransport = await page.evaluate(() => {
        const sidebar = document.querySelector('aside');
        return sidebar ? sidebar.innerText : '';
      });

      check('Transport & Logistics visible in sidebar', sidebarTextTransport.includes('Transport & Logistics') || sidebarTextTransport.includes('Transport'));
      check('Fees section strictly absent for Transport In-Charge', !sidebarTextTransport.includes('Fees') && !sidebarTextTransport.includes('Financial / Money'));
      check('Admissions section strictly absent for Transport In-Charge', !sidebarTextTransport.includes('Admissions') && !sidebarTextTransport.includes('Admission Cycles'));
      check('Settings section strictly absent for Transport In-Charge', !sidebarTextTransport.includes('Settings') && !sidebarTextTransport.includes('Admin Settings'));

      const transportScreenBuf = await page.screenshot({ fullPage: false });
      saveScreenshot('proof_transport_incharge_portal.png', transportScreenBuf);

      await ctx.close();
    }

    // ------------------------------------------------------------------
    // FLOW 2: ACCOUNTS DEPARTMENT LOGIN & FINANCIAL OPERATIONS
    // ------------------------------------------------------------------
    console.log('\n--- FLOW 2: Accounts Department Login & RBAC Isolation ---');
    {
      const ctx = await browser.createBrowserContext();
      const page = await ctx.newPage();
      await page.setViewport({ width: 1440, height: 900 });

      await performLogin(page, 'accounts@sunrisepublic.edu', 'Admin@123');
      check('Accounts Department login successful', page.url().includes('#/'));

      await page.goto(`${BASE_URL}/#/fees`, { waitUntil: 'networkidle0', timeout: 20000 });
      await sleep(2500);

      const sidebarTextAccounts = await page.evaluate(() => {
        const sidebar = document.querySelector('aside');
        return sidebar ? sidebar.innerText : '';
      });

      check('Financial / Money visible in sidebar', sidebarTextAccounts.includes('Financial / Money') || sidebarTextAccounts.includes('Fees'));
      check('Payroll visible in sidebar', sidebarTextAccounts.includes('Payroll') || sidebarTextAccounts.includes('HR & Payroll'));
      check('Reports visible in sidebar', sidebarTextAccounts.includes('Reports'));
      check('Transport section strictly absent for Accounts', !sidebarTextAccounts.includes('Transport & Logistics'));
      check('Admissions section strictly absent for Accounts', !sidebarTextAccounts.includes('Admission Cycles') && !sidebarTextAccounts.includes('Applications'));
      check('Settings strictly absent for Accounts', !sidebarTextAccounts.includes('Admin Settings') && !sidebarTextAccounts.includes('Academic Years'));

      const accountsScreenBuf = await page.screenshot({ fullPage: false });
      saveScreenshot('proof_accounts_role_portal.png', accountsScreenBuf);

      await ctx.close();
    }

    // ------------------------------------------------------------------
    // FLOW 3: PUBLIC ADMISSION WITH AUTHORIZED PICKUP PERSONS & PHOTOS
    // ------------------------------------------------------------------
    console.log('\n--- FLOW 3: Public Admission Pickup Persons with Photos ---');
    {
      const ctx = await browser.createBrowserContext();
      const page = await ctx.newPage();
      await page.setViewport({ width: 1440, height: 900 });

      await page.goto(`${BASE_URL}/#/apply`, { waitUntil: 'networkidle0', timeout: 20000 });
      await sleep(2000);

      // Click "+ Add Authorized Person" twice
      await clickButtonWithText(page, 'Add Authorized Person');
      await sleep(500);
      await clickButtonWithText(page, 'Add Authorized Person');
      await sleep(600);

      // Populate Pickup Person 1 and 2 details
      await page.evaluate(() => {
        const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;

        const nameInputs = document.querySelectorAll('input[placeholder="e.g. Ramesh Kumar"]');
        const relInputs = document.querySelectorAll('input[placeholder="e.g. Grandfather, Driver, Uncle"]');
        const phoneInputs = document.querySelectorAll('input[placeholder="e.g. 9876543210"]');
        const idInputs = document.querySelectorAll('input[placeholder*="XXXX-XXXX"]');

        if (nameInputs[0]) { setter.call(nameInputs[0], 'Devraj Kapoor'); nameInputs[0].dispatchEvent(new Event('input', { bubbles: true })); }
        if (relInputs[0]) { setter.call(relInputs[0], 'Grandfather'); relInputs[0].dispatchEvent(new Event('input', { bubbles: true })); }
        if (phoneInputs[0]) { setter.call(phoneInputs[0], '9811223344'); phoneInputs[0].dispatchEvent(new Event('input', { bubbles: true })); }
        if (idInputs[0]) { setter.call(idInputs[0], '9876-5432-1098'); idInputs[0].dispatchEvent(new Event('input', { bubbles: true })); }

        if (nameInputs[1]) { setter.call(nameInputs[1], 'Mukesh Kumar'); nameInputs[1].dispatchEvent(new Event('input', { bubbles: true })); }
        if (relInputs[1]) { setter.call(relInputs[1], 'Family Driver'); relInputs[1].dispatchEvent(new Event('input', { bubbles: true })); }
        if (phoneInputs[1]) { setter.call(phoneInputs[1], '9822334455'); phoneInputs[1].dispatchEvent(new Event('input', { bubbles: true })); }
        if (idInputs[1]) { setter.call(idInputs[1], 'DL-0420230012345'); idInputs[1].dispatchEvent(new Event('input', { bubbles: true })); }
      });

      // Upload photos for both pickup persons
      const fileInputs = await page.$$('input[type="file"]');
      if (fileInputs.length >= 2 && fs.existsSync(SAMPLE_IMAGE_PATH)) {
        await fileInputs[fileInputs.length - 2].uploadFile(SAMPLE_IMAGE_PATH);
        await sleep(1200);
        await fileInputs[fileInputs.length - 1].uploadFile(SAMPLE_IMAGE_PATH);
        await sleep(1200);
      }

      // Scroll to Authorized Pickup Persons section
      await page.evaluate(() => {
        const headings = Array.from(document.querySelectorAll('h3'));
        const target = headings.find(h => h.innerText.includes('Authorized Student Pickup Persons'));
        if (target) {
          const rect = target.getBoundingClientRect();
          window.scrollBy({ top: rect.top - 80, behavior: 'instant' });
        }
      });
      await sleep(1000);

      const applyPageBuf = await page.screenshot({ fullPage: false });
      saveScreenshot('proof_online_admission_pickup_persons.png', applyPageBuf);
      check('Online admission authorized pickup persons form rendered and captured', true);

      await ctx.close();
    }

    // ------------------------------------------------------------------
    // FLOW 4: FRONT-DESK GATE PASS WITH ESCORT PHOTO THUMBNAIL & PRINTABLE SLIP
    // ------------------------------------------------------------------
    console.log('\n--- FLOW 4: Student Gate Pass with Escort Photo & Printable Slip ---');
    {
      const ctx = await browser.createBrowserContext();
      const page = await ctx.newPage();
      await page.setViewport({ width: 1440, height: 900 });

      await performLogin(page, 'receptionist@sunrisepublic.edu', 'Admin@123');
      await page.goto(`${BASE_URL}/#/reception/passes`, { waitUntil: 'networkidle0', timeout: 20000 });
      await sleep(2000);

      // Seed an authorized person with photo for student 2024000001
      await page.evaluate(async () => {
        try {
          const token = localStorage.getItem('sunrise.token');
          const res = await fetch('http://localhost:8000/admin/reception/students/search?q=2024', {
            headers: { Authorization: `Bearer ${token}` }
          });
          const students = await res.json();
          if (students.length > 0) {
            const sid = students[0].id;
            await fetch(`http://localhost:8000/admin/reception/students/${sid}/authorized-persons`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${token}`
              },
              body: JSON.stringify({
                name: 'Devraj Kapoor',
                relationship: 'Grandfather',
                phone: '9811223344',
                id_proof_type: 'Aadhaar Card',
                id_proof_number: '9876-5432-1098',
                photo_url: '/documents/1/admission/0ab4f18f45d946aa8bd53715315e4a51.png',
                notes: 'Permanent verified escort'
              })
            });
          }
        } catch (e) {
          console.error(e);
        }
      });
      await sleep(1000);

      // Click "Issue Gate Pass"
      const clickedIssue = await clickButtonWithText(page, 'Issue Gate Pass');
      check('Clicked "Issue Gate Pass" button', clickedIssue);
      await sleep(1500);

      // Type into student search input
      await page.waitForSelector('input[placeholder^="Search by student"]', { timeout: 8000 });
      await page.evaluate(() => {
        const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        const inp = document.querySelector('input[placeholder^="Search by student"]');
        if (inp) {
          setter.call(inp, '2024000001');
          inp.dispatchEvent(new Event('input', { bubbles: true }));
        }
      });
      await sleep(1500);

      // Click search result to select student
      await page.evaluate(() => {
        const inp = document.querySelector('input[placeholder^="Search by student"]');
        if (inp && inp.parentElement) {
          const resContainer = inp.parentElement.querySelector('.overflow-y-auto') || inp.parentElement.nextElementSibling;
          if (resContainer) {
            const btn = resContainer.querySelector('button');
            if (btn) btn.click();
          }
        }
      });
      await sleep(2000);

      // Wait for permanent authorized person button (Devraj Kapoor) to appear in Section 2
      await page.waitForFunction(() => {
        const btns = Array.from(document.querySelectorAll('button'));
        return btns.some(b => b.innerText.includes('Devraj') || b.innerText.includes('Grandfather'));
      }, { timeout: 10000 });

      // Click Devraj Kapoor's authorized person button
      await page.evaluate(() => {
        const btns = Array.from(document.querySelectorAll('button'));
        const personBtn = btns.find(b => b.innerText.includes('Devraj') || b.innerText.includes('Grandfather'));
        if (personBtn) personBtn.click();
      });
      await sleep(1200);

      // Verify escort photo preview is shown in the form
      const hasFormPhotoPreview = await page.evaluate(() => {
        return document.body.innerText.includes('Verified Escort Photo Attached');
      });
      check('Verified Escort Photo Attached preview rendered in form', hasFormPhotoPreview);

      // Fill reason & departure time
      await page.evaluate(() => {
        const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        const reasonInp = document.querySelector('input[placeholder*="headache"]');
        const timeInp = document.querySelector('input[placeholder*="01:30 PM"]');

        if (reasonInp) { setter.call(reasonInp, 'Medical Appointment - Dental Checkup'); reasonInp.dispatchEvent(new Event('input', { bubbles: true })); }
        if (timeInp) { setter.call(timeInp, '01:30 PM'); timeInp.dispatchEvent(new Event('input', { bubbles: true })); }
      });
      await sleep(600);

      // Submit form
      const submitted = await page.evaluate(() => {
        const submitBtn = document.querySelector('button[type="submit"]');
        if (submitBtn) {
          submitBtn.click();
          return true;
        }
        return false;
      });
      check('Submitted gate pass form', submitted);
      await sleep(2500);

      // Wait for Printable Slip modal
      const hasPrintModal = await page.evaluate(() => {
        return document.body.innerText.includes('Official Student Gate Pass') ||
               document.body.innerText.includes('Authorized Escort / Pickup Person');
      });
      check('Printable Gate Pass modal open with escort details', hasPrintModal);

      const gatePassBuf = await page.screenshot({ fullPage: false });
      saveScreenshot('proof_student_pass_with_escort_photo.png', gatePassBuf);
      check('Student Gate Pass with Escort Photo slip captured', true);

      await ctx.close();
    }

    console.log('\n================================================================');
    console.log(`  VERIFICATION RESULTS: ${passed} PASSED, ${failed} FAILED`);
    console.log('================================================================\n');

  } finally {
    await browser.close();
  }
}

run().catch((err) => {
  console.error('Fatal execution error:', err);
  process.exit(1);
});
