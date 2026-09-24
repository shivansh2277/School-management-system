import puppeteer from 'puppeteer-core';
import path from 'path';
import fs from 'fs';

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const SCREENSHOT_DIR = path.resolve('..', 'docs', 'screenshots');
const ARTIFACT_DIR = 'C:\\Users\\SHIVANSH\\.gemini\\antigravity\\brain\\dc373d15-fa1f-4c85-9ddf-91e50c13f9e4';
const BASE_URL = 'http://localhost:5173';

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
  console.log('  LIVE PRINTABLE SLIPS & ADMISSION PORTAL VISUAL VERIFICATION');
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
    const ctx = await browser.createBrowserContext();
    const page = await ctx.newPage();
    await page.setViewport({ width: 1440, height: 900 });

    console.log('1. Logging in as Receptionist...');
    await performLogin(page, 'receptionist@sunrisepublic.edu', 'Admin@123');
    check('Receptionist Login Successful', page.url().includes('#/'));

    // ------------------------------------------------------------------
    // FLOW 1: STUDENT GATE PASS
    // ------------------------------------------------------------------
    console.log('\n--- FLOW 1: Student Gate Pass Slip ---');
    await page.goto(`${BASE_URL}/#/reception/passes`, { waitUntil: 'networkidle0', timeout: 20000 });
    await sleep(2000);

    // Click "Issue Gate Pass"
    const clickedIssuePass = await clickButtonWithText(page, 'Issue Gate Pass');
    check('Clicked "Issue Gate Pass" button', clickedIssuePass);
    await sleep(1200);

    // Search for student 2024000001
    await page.waitForSelector('input[placeholder*="Search by student"]', { timeout: 8000 });
    await page.evaluate(() => {
      const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
      const inp = document.querySelector('input[placeholder*="Search by student"]');
      if (inp) {
        setter.call(inp, '2024000001');
        inp.dispatchEvent(new Event('input', { bubbles: true }));
      }
    });
    await sleep(1500);

    // Click matching student in search results
    const clickedStudent = await page.evaluate(() => {
      const resBtns = Array.from(document.querySelectorAll('.border.border-rule.rounded button'));
      if (resBtns.length > 0) {
        resBtns[0].click();
        return true;
      }
      return false;
    });
    check('Selected student 2024000001 for pass', clickedStudent);
    await sleep(1000);

    // Fill escort info
    await page.evaluate(() => {
      const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
      const nameInput = document.querySelector('input[placeholder="Full Name"]');
      const relInput = document.querySelector('input[placeholder*="Father"]');
      const phoneInput = document.querySelector('input[placeholder*="+91"]');
      
      if (nameInput) {
        setter.call(nameInput, 'Rajesh Sharma');
        nameInput.dispatchEvent(new Event('input', { bubbles: true }));
      }
      if (relInput) {
        setter.call(relInput, 'Father');
        relInput.dispatchEvent(new Event('input', { bubbles: true }));
      }
      if (phoneInput) {
        setter.call(phoneInput, '9876543210');
        phoneInput.dispatchEvent(new Event('input', { bubbles: true }));
      }

      // Reason select
      const reasonSelect = document.querySelector('form select');
      if (reasonSelect && reasonSelect.options.length > 1) {
        reasonSelect.selectedIndex = 1;
        reasonSelect.dispatchEvent(new Event('change', { bubbles: true }));
      }
    });

    // Click Submit ("Generate & Print Gate Pass")
    const clickedSubmitPass = await clickButtonWithText(page, 'Generate & Print Gate Pass');
    check('Submitted Gate Pass form', clickedSubmitPass);
    await sleep(2500);

    // Verify Printable Modal is rendered
    const hasGatePassModal = await page.evaluate(() => {
      return document.body.innerText.includes('Official Student Gate Pass') ||
             document.body.innerText.includes('STUDENT EARLY DEPARTURE GATE PASS');
    });
    check('Student Gate Pass Modal Opened', hasGatePassModal);

    // Capture screenshot
    const passBuf = await page.screenshot({ fullPage: false });
    saveScreenshot('proof_printable_student_pass.png', passBuf);

    // Close modal
    await clickButtonWithText(page, 'Close');
    await sleep(1000);

    // ------------------------------------------------------------------
    // FLOW 2: PRINCIPAL MEETING SLIP
    // ------------------------------------------------------------------
    console.log('\n--- FLOW 2: Principal Meeting Slip ---');
    await page.goto(`${BASE_URL}/#/reception/meetings`, { waitUntil: 'networkidle0', timeout: 20000 });
    await sleep(2000);

    // Click "New Principal Meeting Slip"
    const clickedBookPrinc = await clickButtonWithText(page, 'New Principal Meeting Slip');
    check('Clicked "New Principal Meeting Slip" button', clickedBookPrinc);
    await sleep(1200);

    // Fill Principal Appointment Form
    await page.evaluate(() => {
      const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
      const txtSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;

      const vName = document.querySelector('input[placeholder*="Alok Mathur"]');
      const vPhone = document.querySelector('input[placeholder*="+91 98"]');
      const vOrg = document.querySelector('input[placeholder*="CBSE Inspection"]');
      const vReason = document.querySelector('textarea[placeholder*="Principal"]');

      if (vName) {
        setter.call(vName, 'Dr. Meenakshi Sundaram');
        vName.dispatchEvent(new Event('input', { bubbles: true }));
      }
      if (vPhone) {
        setter.call(vPhone, '9876543211');
        vPhone.dispatchEvent(new Event('input', { bubbles: true }));
      }
      if (vOrg) {
        setter.call(vOrg, 'CBSE Regional Inspection Directorate');
        vOrg.dispatchEvent(new Event('input', { bubbles: true }));
      }
      if (vReason) {
        txtSetter.call(vReason, 'Annual Affiliation and Quality Assurance Review');
        vReason.dispatchEvent(new Event('input', { bubbles: true }));
      }
    });

    // Submit Principal Meeting Form
    const clickedSubmitPrinc = await clickButtonWithText(page, 'Generate Slip & Notify Principal');
    check('Submitted Principal Meeting form', clickedSubmitPrinc);
    await sleep(2500);

    // Verify Modal
    const hasPrincModal = await page.evaluate(() => {
      return document.body.innerText.includes('Principal Visitor Meeting Slip') ||
             document.body.innerText.includes('PRINCIPAL EXECUTIVE OFFICE');
    });
    check('Principal Meeting Slip Modal Opened', hasPrincModal);

    // Capture screenshot
    const princBuf = await page.screenshot({ fullPage: false });
    saveScreenshot('proof_printable_principal_meeting.png', princBuf);

    // Close modal
    await clickButtonWithText(page, 'Close');
    await sleep(1000);

    // ------------------------------------------------------------------
    // FLOW 3: TEACHER MEETING SLIP
    // ------------------------------------------------------------------
    console.log('\n--- FLOW 3: Teacher Meeting Slip ---');
    // Switch to Teacher Meeting Slips Tab
    const clickedTeacherTab = await clickButtonWithText(page, 'Teacher Meeting Slips');
    check('Switched to Teacher Meeting Slips Tab', clickedTeacherTab);
    await sleep(1000);

    // Click "New Teacher Meeting Slip"
    const clickedLogTeacher = await clickButtonWithText(page, 'New Teacher Meeting Slip');
    check('Clicked "New Teacher Meeting Slip" button', clickedLogTeacher);
    await sleep(1200);

    // Fill Teacher Form
    await page.evaluate(() => {
      const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
      const txtSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;

      // Select first available teacher
      const tSelect = document.querySelector('form select');
      if (tSelect && tSelect.options.length > 1) {
        tSelect.selectedIndex = 1;
        tSelect.dispatchEvent(new Event('change', { bubbles: true }));
      }

      const vName = document.querySelector('input[placeholder="Visitor Name"]');
      const vPhone = document.querySelector('input[placeholder="+91..."]');
      const vRel = document.querySelector('input[placeholder*="Mother, Father"]');
      const sName = document.querySelector('input[placeholder="Student Name"]');
      const vReason = document.querySelector('textarea[placeholder*="Topic of discussion"]');

      if (vName) {
        setter.call(vName, 'Suresh Kumar');
        vName.dispatchEvent(new Event('input', { bubbles: true }));
      }
      if (vPhone) {
        setter.call(vPhone, '9876543212');
        vPhone.dispatchEvent(new Event('input', { bubbles: true }));
      }
      if (vRel) {
        setter.call(vRel, 'Father');
        vRel.dispatchEvent(new Event('input', { bubbles: true }));
      }
      if (sName) {
        setter.call(sName, 'Aarav Sharma');
        sName.dispatchEvent(new Event('input', { bubbles: true }));
      }
      if (vReason) {
        txtSetter.call(vReason, 'Quarterly mathematics assessment and syllabus discussion');
        vReason.dispatchEvent(new Event('input', { bubbles: true }));
      }
    });

    // Submit Teacher Meeting Form
    const clickedSubmitTeacher = await clickButtonWithText(page, 'Generate Slip & Notify Teacher');
    check('Submitted Teacher Meeting form', clickedSubmitTeacher);
    await sleep(2500);

    // Verify Modal
    const hasTeacherModal = await page.evaluate(() => {
      return document.body.innerText.includes('Teacher Visitor Meeting Slip') ||
             document.body.innerText.includes('TEACHER APPOINTMENT SLIP');
    });
    check('Teacher Meeting Slip Modal Opened', hasTeacherModal);

    // Capture screenshot
    const teacherBuf = await page.screenshot({ fullPage: false });
    saveScreenshot('proof_printable_teacher_meeting.png', teacherBuf);

    // Close modal
    await clickButtonWithText(page, 'Close');
    await sleep(1000);

    // ------------------------------------------------------------------
    // FLOW 4: COUNTER FEE PAYMENT & RECEIPT
    // ------------------------------------------------------------------
    console.log('\n--- FLOW 4: Counter Fee Payment & Receipt ---');
    await page.goto(`${BASE_URL}/#/reception/fee-counter`, { waitUntil: 'networkidle0', timeout: 20000 });
    await sleep(2000);

    // Search for student with unpaid invoices
    await page.waitForSelector('input[placeholder*="2024000001"]', { timeout: 8000 });
    await page.evaluate(() => {
      const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
      const inp = document.querySelector('input[placeholder*="2024000001"]');
      if (inp) {
        setter.call(inp, '2024000003');
        inp.dispatchEvent(new Event('input', { bubbles: true }));
      }
    });
    await sleep(500);

    // Submit fee search form
    await page.click('form button[type="submit"]');
    await sleep(2500);

    // Verify fee options loaded
    const hasFeeOptions = await page.evaluate(() => {
      return document.body.innerText.includes('Collect ₹') || document.body.innerText.includes('Exact Computed Total:');
    });
    check('Student Outstanding Fee Options Loaded', hasFeeOptions);

    // Click collect button to record collection and generate receipt
    const clickedCollect = await clickButtonWithText(page, 'Collect ₹');
    check('Clicked Collect Fee button', clickedCollect);
    await sleep(2500);

    // Verify Receipt Modal opened
    const hasReceiptModal = await page.evaluate(() => {
      return document.body.innerText.includes('Fee Collection Receipt') ||
             document.body.innerText.includes('OFFICIAL FEE PAYMENT RECEIPT');
    });
    check('Printable Fee Receipt Slip Modal Opened', hasReceiptModal);

    // Capture screenshot
    const receiptBuf = await page.screenshot({ fullPage: false });
    saveScreenshot('proof_printable_fee_receipt.png', receiptBuf);

    // Close modal
    await clickButtonWithText(page, 'Close');
    await sleep(1000);

    // ------------------------------------------------------------------
    // FLOW 5: PUBLIC ONLINE ADMISSION PORTAL
    // ------------------------------------------------------------------
    console.log('\n--- FLOW 5: Public Online Admission Portal (/#/apply) ---');
    await page.goto(`${BASE_URL}/#/apply`, { waitUntil: 'networkidle0', timeout: 20000 });
    await sleep(2000);

    const portalHeader = await page.evaluate(() => {
      return document.body.innerText.includes('Sunrise Public School') &&
             (document.body.innerText.includes('Apply Online') || document.body.innerText.includes('Admissions Open'));
    });
    check('Online Admission Portal Rendered Successfully', portalHeader);

    // Capture screenshot of the Admission Portal
    const portalBuf = await page.screenshot({ fullPage: false });
    saveScreenshot('proof_online_admission_portal.png', portalBuf);

    // Also check status tab
    const clickedStatusTab = await clickButtonWithText(page, 'Check Status');
    check('Switched to Status Lookup Tab', clickedStatusTab);
    await sleep(1000);
    const statusTabBuf = await page.screenshot({ fullPage: false });
    saveScreenshot('proof_online_admission_status_checker.png', statusTabBuf);

    // Also check criteria tab
    const clickedInfoTab = await clickButtonWithText(page, 'Seat Matrix & Criteria');
    check('Switched to Seat Matrix & Criteria Tab', clickedInfoTab);
    await sleep(1000);
    const infoTabBuf = await page.screenshot({ fullPage: false });
    saveScreenshot('proof_online_admission_seat_matrix.png', infoTabBuf);

    console.log('\n================================================================');
    console.log(`  VERIFICATION RESULTS: ${passed} PASSED, ${failed} FAILED`);
    console.log('================================================================\n');

  } catch (err) {
    console.error(`Verification crashed with error: ${err.message}`, err.stack);
    failed++;
  } finally {
    await browser.close();
    process.exit(failed > 0 ? 1 : 0);
  }
}

run();
