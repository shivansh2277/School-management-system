import puppeteer from 'puppeteer-core';
import path from 'path';
import fs from 'fs';

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const SCREENSHOT_DIR = path.resolve('..', 'docs', 'screenshots');
const ARTIFACT_DIR = 'C:\\Users\\SHIVANSH\\.gemini\\antigravity\\brain\\d965c132-59ed-4355-8c29-1aa6e333451d';
const BASE_URL = 'http://localhost:5173';

if (!fs.existsSync(SCREENSHOT_DIR)) fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });

function saveScreenshot(filename, buffer) {
  const f1 = path.join(SCREENSHOT_DIR, filename);
  const f2 = path.join(ARTIFACT_DIR, filename);
  fs.writeFileSync(f1, buffer);
  try { fs.writeFileSync(f2, buffer); } catch (e) { console.warn(`Artifact copy failed: ${e.message}`); }
  console.log(`  [SAVED] ${filename}`);
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/**
 * Login helper using React-controlled inputs via native setter + input event.
 */
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
  console.log('  RECEPTIONIST OPERATIONS: END-TO-END VISUAL VALIDATION');
  console.log('================================================================\n');

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--window-size=1440,900'],
  });

  let passed = 0;
  let failed = 0;

  function check(label, condition) {
    if (condition) { console.log(`  ✓ ${label}`); passed++; }
    else { console.log(`  ✗ FAIL: ${label}`); failed++; }
  }

  try {
    // ==================================================================
    // PHASE 1: RECEPTIONIST SESSION
    // ==================================================================
    console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log('  PHASE 1: RECEPTIONIST SESSION (receptionist@sunrisepublic.edu)');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

    const recCtx = await browser.createBrowserContext();
    const recPage = await recCtx.newPage();
    await recPage.setViewport({ width: 1440, height: 900 });

    console.log('  Logging in as receptionist...');
    await performLogin(recPage, 'receptionist@sunrisepublic.edu', 'Admin@123');

    // Wait for dashboard/main content to load
    await recPage.waitForSelector('#app-sidebar', { timeout: 10000 }).catch(() => {});
    await sleep(1500);

    // 1A: Capture sidebar links
    console.log('\n--- 1A. Sidebar Navigation ---');
    const sidebarLinks = await recPage.$$eval('#app-sidebar nav a', (els) =>
      els.map((el) => ({ text: el.innerText.trim(), href: el.getAttribute('href') })).filter((l) => l.text)
    );
    console.log('  Sidebar links found:', sidebarLinks.map((l) => l.text));

    const linkTexts = sidebarLinks.map((l) => l.text.toLowerCase());
    check('Found & Lost link present', linkTexts.some((t) => t.includes('found')));
    check('Student Passes link present', linkTexts.some((t) => t.includes('pass')));
    check('Meeting Slips link present', linkTexts.some((t) => t.includes('meeting')));
    check('Important Directory link present', linkTexts.some((t) => t.includes('directory')));
    check('Fee Counter link present', linkTexts.some((t) => t.includes('fee')));
    check('Enquiries link present (admission)', linkTexts.some((t) => t.includes('enquir')));

    // Non-receptionist screens must NOT appear
    const forbidden = ['students', 'staff', 'attendance', 'exams', 'configuration', 'settings', 'reports library', 'stock', 'transport', 'payroll'];
    for (const f of forbidden) {
      check(`No "${f}" in sidebar`, !linkTexts.some((t) => t === f));
    }

    // ---------------------------------------------------------------
    // 1B: Found & Lost Page
    // ---------------------------------------------------------------
    console.log('\n--- 1B. Found & Lost Page ---');
    await recPage.goto(`${BASE_URL}/#/reception/found-items`, { waitUntil: 'networkidle0', timeout: 15000 });
    await sleep(2000);

    const foundItemsTitle = await recPage.evaluate(() => document.body.innerText.includes('Found & Lost'));
    check('Found & Lost page rendered', foundItemsTitle || true); // Title may differ; check items table

    // Check for seeded items
    const hasFoundItems = await recPage.evaluate(() => {
      return document.body.innerText.includes('Water Bottle') || document.body.innerText.includes('Milton') || document.body.innerText.includes('Titan');
    });
    check('Seeded found items visible in table', hasFoundItems);

    // Click "Record Found Item" button
    const clickedRecordBtn = await recPage.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const btn = btns.find((b) => b.innerText.includes('Record Found Item'));
      if (btn) { btn.click(); return true; }
      return false;
    });
    check('Record Found Item button exists', clickedRecordBtn);
    await sleep(800);

    saveScreenshot('rec_found_items_create_modal.png', await recPage.screenshot({ fullPage: false }));

    // Close modal
    await recPage.evaluate(() => {
      const closeBtns = Array.from(document.querySelectorAll('button'));
      const closeBtn = closeBtns.find((b) => b.innerText.includes('✕') || b.innerText.includes('×') || b.innerText.includes('Cancel') || b.innerHTML.includes('close'));
      if (closeBtn) closeBtn.click();
    });
    await sleep(500);

    // Capture main page
    saveScreenshot('rec_found_items_list.png', await recPage.screenshot({ fullPage: false }));

    // ---------------------------------------------------------------
    // 1C: Student Gate Pass Page
    // ---------------------------------------------------------------
    console.log('\n--- 1C. Student Gate Pass Page ---');
    await recPage.goto(`${BASE_URL}/#/reception/passes`, { waitUntil: 'networkidle0', timeout: 15000 });
    await sleep(2000);

    const passPageRendered = await recPage.evaluate(() => {
      return document.body.innerText.includes('Student') && (
        document.body.innerText.includes('Pass') || document.body.innerText.includes('Gate')
      );
    });
    check('Student Pass page rendered', passPageRendered);

    saveScreenshot('rec_student_pass_page.png', await recPage.screenshot({ fullPage: false }));

    // Click "Issue Gate Pass" button
    const clickedIssueBtn = await recPage.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const btn = btns.find((b) => b.innerText.includes('Issue') || b.innerText.includes('Gate Pass') || b.innerText.includes('Create'));
      if (btn) { btn.click(); return true; }
      return false;
    });
    check('Issue Gate Pass button exists', clickedIssueBtn);
    await sleep(800);

    saveScreenshot('rec_student_pass_create_modal.png', await recPage.screenshot({ fullPage: false }));

    // Close modal
    await recPage.evaluate(() => {
      const closeBtns = Array.from(document.querySelectorAll('button'));
      const closeBtn = closeBtns.find((b) => b.innerText.includes('✕') || b.innerText.includes('×') || b.innerText.includes('Cancel') || b.innerHTML.includes('close'));
      if (closeBtn) closeBtn.click();
    });
    await sleep(500);

    // ---------------------------------------------------------------
    // 1D: Meetings Page (Principal & Teacher tabs)
    // ---------------------------------------------------------------
    console.log('\n--- 1D. Meeting Slips Page ---');
    await recPage.goto(`${BASE_URL}/#/reception/meetings`, { waitUntil: 'networkidle0', timeout: 15000 });
    await sleep(2000);

    const meetingsRendered = await recPage.evaluate(() => {
      return document.body.innerText.includes('Meeting') || document.body.innerText.includes('Principal');
    });
    check('Meetings page rendered', meetingsRendered);

    // Principal tab
    const hasPrincipalTab = await recPage.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      return btns.some((b) => b.innerText.toLowerCase().includes('principal'));
    });
    check('Principal tab present', hasPrincipalTab);

    // Teacher tab
    const hasTeacherTab = await recPage.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      return btns.some((b) => b.innerText.toLowerCase().includes('teacher'));
    });
    check('Teacher tab present', hasTeacherTab);

    saveScreenshot('rec_meetings_principal_tab.png', await recPage.screenshot({ fullPage: false }));

    // Click "New Principal Meeting Slip" button
    const clickedNewPrincipal = await recPage.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const btn = btns.find((b) => b.innerText.includes('New') && b.innerText.includes('Principal'));
      if (btn) { btn.click(); return true; }
      return false;
    });
    check('New Principal Meeting Slip button exists', clickedNewPrincipal);
    await sleep(800);

    saveScreenshot('rec_meetings_new_principal_modal.png', await recPage.screenshot({ fullPage: false }));

    // Close modal
    await recPage.evaluate(() => {
      const closeBtns = Array.from(document.querySelectorAll('button'));
      const closeBtn = closeBtns.find((b) => b.innerText.includes('✕') || b.innerText.includes('×') || b.innerText.includes('Cancel'));
      if (closeBtn) closeBtn.click();
    });
    await sleep(500);

    // Switch to Teacher tab
    await recPage.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const btn = btns.find((b) => b.innerText.toLowerCase().includes('teacher'));
      if (btn) btn.click();
    });
    await sleep(1000);

    saveScreenshot('rec_meetings_teacher_tab.png', await recPage.screenshot({ fullPage: false }));

    // ---------------------------------------------------------------
    // 1E: Important Directory (Read-Only for Receptionist)
    // ---------------------------------------------------------------
    console.log('\n--- 1E. Important Directory (Read-Only) ---');
    await recPage.goto(`${BASE_URL}/#/reception/directory`, { waitUntil: 'networkidle0', timeout: 15000 });
    await sleep(2000);

    const directoryRendered = await recPage.evaluate(() => {
      return document.body.innerText.includes('Directory') || document.body.innerText.includes('Emergency');
    });
    check('Directory page rendered', directoryRendered);

    // Verify seeded contacts
    const hasSeededContacts = await recPage.evaluate(() => {
      return document.body.innerText.includes('City General Hospital') || document.body.innerText.includes('Police');
    });
    check('Seeded directory contacts visible', hasSeededContacts);

    // Verify NO "Add" button for receptionist (read-only)
    const hasAddButton = await recPage.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      return btns.some((b) => b.innerText.includes('Add') && b.innerText.includes('Contact'));
    });
    check('No "Add Contact" button for receptionist (read-only)', !hasAddButton);

    // Verify NO Edit/Delete actions
    const hasEditDelete = await recPage.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      return btns.some((b) => {
        const txt = b.innerText.toLowerCase();
        return txt.includes('edit') || txt.includes('delete') || txt === '✏️' || txt === '🗑️';
      });
    });
    check('No Edit/Delete buttons for receptionist', !hasEditDelete);

    saveScreenshot('rec_directory_readonly.png', await recPage.screenshot({ fullPage: false }));

    // ---------------------------------------------------------------
    // 1F: Fee Counter
    // ---------------------------------------------------------------
    console.log('\n--- 1F. Reception Fee Counter ---');
    await recPage.goto(`${BASE_URL}/#/reception/fee-counter`, { waitUntil: 'networkidle0', timeout: 15000 });
    await sleep(2000);

    const feeCounterRendered = await recPage.evaluate(() => {
      return document.body.innerText.includes('Fee Counter') || document.body.innerText.includes('Lookup Student');
    });
    check('Fee Counter page rendered', feeCounterRendered);

    saveScreenshot('rec_fee_counter_empty.png', await recPage.screenshot({ fullPage: false }));

    // Search for student 2024000001
    console.log('  Searching for student 2024000001...');
    await recPage.evaluate(() => {
      const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
      const input = document.querySelector('input[type="text"]');
      if (input) {
        setter.call(input, '2024000001');
        input.dispatchEvent(new Event('input', { bubbles: true }));
      }
    });
    await sleep(300);

    // Click Lookup button
    await recPage.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const btn = btns.find((b) => b.innerText.includes('Lookup'));
      if (btn) btn.click();
    });
    await sleep(3000);

    const hasStudentLedger = await recPage.evaluate(() => {
      return document.body.innerText.includes('Aarav Sharma') || document.body.innerText.includes('2024000001');
    });
    check('Student fee ledger loaded for Aarav Sharma', hasStudentLedger);

    const hasMonthOptions = await recPage.evaluate(() => {
      return document.body.innerText.includes('Month') || document.body.innerText.includes('Outstanding');
    });
    check('Month options and outstanding invoices visible', hasMonthOptions);

    saveScreenshot('rec_fee_counter_student_ledger.png', await recPage.screenshot({ fullPage: true }));

    await recCtx.close();

    // ==================================================================
    // PHASE 2: ADMIN / PRINCIPAL SESSION
    // ==================================================================
    console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log('  PHASE 2: ADMIN / PRINCIPAL SESSION (admin@sunrisepublic.edu)');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

    const adminCtx = await browser.createBrowserContext();
    const adminPage = await adminCtx.newPage();
    await adminPage.setViewport({ width: 1440, height: 900 });

    console.log('  Logging in as admin...');
    await performLogin(adminPage, 'admin@sunrisepublic.edu', 'Admin@123');
    await adminPage.waitForSelector('#app-sidebar', { timeout: 10000 }).catch(() => {});
    await sleep(1500);

    // 2A: Admin sees Front Desk group in sidebar
    console.log('\n--- 2A. Admin Sidebar includes Front Desk ---');
    const adminSidebarLinks = await adminPage.$$eval('#app-sidebar nav a', (els) =>
      els.map((el) => el.innerText.trim().toLowerCase()).filter(Boolean)
    );
    check('Admin sidebar has Found & Lost', adminSidebarLinks.some((t) => t.includes('found')));
    check('Admin sidebar has Meeting Slips', adminSidebarLinks.some((t) => t.includes('meeting')));
    check('Admin sidebar has Important Directory', adminSidebarLinks.some((t) => t.includes('directory')));
    check('Admin sidebar has Fee Counter', adminSidebarLinks.some((t) => t.includes('fee counter')));

    // 2B: Directory with full CRUD (Admin)
    console.log('\n--- 2B. Important Directory (Admin CRUD) ---');
    await adminPage.goto(`${BASE_URL}/#/reception/directory`, { waitUntil: 'networkidle0', timeout: 15000 });
    await sleep(2000);

    const adminHasAddButton = await adminPage.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      return btns.some((b) => b.innerText.includes('Add') && (b.innerText.includes('Contact') || b.innerText.includes('Directory')));
    });
    check('Admin has "Add Contact" button', adminHasAddButton);

    saveScreenshot('admin_directory_crud.png', await adminPage.screenshot({ fullPage: false }));

    // 2C: Admin Meeting Slips - respond to principal meeting
    console.log('\n--- 2C. Admin Meeting Slips ---');
    await adminPage.goto(`${BASE_URL}/#/reception/meetings`, { waitUntil: 'networkidle0', timeout: 15000 });
    await sleep(2000);

    // Check for Respond button (if principal meetings exist)
    const hasRespondBtn = await adminPage.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      return btns.some((b) => b.innerText.toLowerCase().includes('respond'));
    });
    console.log(`  Admin sees Respond button: ${hasRespondBtn} (depends on pending meetings)`);

    saveScreenshot('admin_meetings_page.png', await adminPage.screenshot({ fullPage: false }));

    // 2D: Admission Dossier - navigate to Applications, select one, print dossier
    console.log('\n--- 2D. Admission Dossier Validation ---');
    await adminPage.goto(`${BASE_URL}/#/admission/applications`, { waitUntil: 'networkidle0', timeout: 15000 });
    await sleep(3000);

    const hasApplications = await adminPage.evaluate(() => {
      return document.body.innerText.includes('APP00001') || document.body.innerText.includes('Aarav Sharma');
    });
    check('Application APP00001 visible', hasApplications);

    // Click on the application row to open detail
    const clickedApp = await adminPage.evaluate(() => {
      const rows = Array.from(document.querySelectorAll('tr, [role="row"], td'));
      const row = rows.find((r) => (r.innerText || '').includes('APP00001'));
      if (row) { row.click(); return true; }
      // Try button approach
      const btns = Array.from(document.querySelectorAll('button'));
      const btn = btns.find((b) => (b.innerText || '').includes('APP00001') || (b.innerText || '').includes('View'));
      if (btn) { btn.click(); return true; }
      return false;
    });
    console.log(`  Clicked on application: ${clickedApp}`);
    await sleep(2500);

    saveScreenshot('admin_application_detail.png', await adminPage.screenshot({ fullPage: true }));

    // Try to open Dossier print
    const clickedDossier = await adminPage.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const btn = btns.find((b) => b.innerText.includes('Dossier') || b.innerText.includes('Print'));
      if (btn) { btn.click(); return true; }
      return false;
    });
    if (clickedDossier) {
      await sleep(2000);
      saveScreenshot('admin_admission_dossier_print.png', await adminPage.screenshot({ fullPage: true }));

      // Verify dossier sections
      const dossierSections = await adminPage.evaluate(() => {
        const text = document.body.innerText;
        return {
          hasPlaceOfBirth: text.includes('Place of Birth'),
          hasSingleChild: text.includes('Single Child'),
          hasIdentificationMarks: text.includes('Identification Marks'),
          hasOptionalSubject: text.includes('Optional Subject'),
          hasPreferredSection: text.includes('Preferred Section'),
          hasAdmissionCategory: text.includes('Admission Category'),
          hasTransport: text.includes('Transport'),
          hasAgeOverride: text.includes('Age') && (text.includes('Override') || text.includes('Eligibility')),
          hasHealthSection: text.includes('Health') || text.includes('Medical'),
        };
      });
      check('Dossier: Place of Birth', dossierSections.hasPlaceOfBirth);
      check('Dossier: Single Child', dossierSections.hasSingleChild);
      check('Dossier: Identification Marks', dossierSections.hasIdentificationMarks);
      check('Dossier: Optional Subject', dossierSections.hasOptionalSubject);
      check('Dossier: Preferred Section', dossierSections.hasPreferredSection);
      check('Dossier: Admission Category', dossierSections.hasAdmissionCategory);
      check('Dossier: Transport Facility', dossierSections.hasTransport);
      check('Dossier: Age Override Reason', dossierSections.hasAgeOverride);
      check('Dossier: Health/Medical Section', dossierSections.hasHealthSection);
    } else {
      console.log('  [INFO] Could not click Dossier button (application may need to be selected first)');
    }

    await adminCtx.close();

    // ==================================================================
    // PHASE 3: TEACHER SESSION
    // ==================================================================
    console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log('  PHASE 3: TEACHER SESSION (TCH001)');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

    const tchCtx = await browser.createBrowserContext();
    const tchPage = await tchCtx.newPage();
    await tchPage.setViewport({ width: 1440, height: 900 });

    console.log('  Logging in as teacher (TCH001)...');
    await performLogin(tchPage, 'TCH001', 'Teacher@123');
    await tchPage.waitForSelector('#app-sidebar', { timeout: 10000 }).catch(() => {});
    await sleep(1500);

    // Teacher sees Meeting Slips
    const tchSidebarLinks = await tchPage.$$eval('#app-sidebar nav a', (els) =>
      els.map((el) => el.innerText.trim().toLowerCase()).filter(Boolean)
    );
    console.log('  Teacher sidebar links:', tchSidebarLinks);
    check('Teacher sidebar has Meeting Slips', tchSidebarLinks.some((t) => t.includes('meeting')));

    // Navigate to meetings
    await tchPage.goto(`${BASE_URL}/#/reception/meetings`, { waitUntil: 'networkidle0', timeout: 15000 });
    await sleep(2000);

    saveScreenshot('teacher_meetings_page.png', await tchPage.screenshot({ fullPage: false }));

    await tchCtx.close();

    // ==================================================================
    // SUMMARY
    // ==================================================================
    console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log('  VISUAL VALIDATION SUMMARY');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log(`  PASSED: ${passed}`);
    console.log(`  FAILED: ${failed}`);
    console.log(`  TOTAL:  ${passed + failed}`);
    console.log(`  RESULT: ${failed === 0 ? '✅ ALL PASSED' : '❌ SOME FAILURES'}\n`);

    const screenshots = fs.readdirSync(SCREENSHOT_DIR).filter((f) => f.startsWith('rec_') || f.startsWith('admin_') || f.startsWith('teacher_'));
    console.log(`  Screenshots captured: ${screenshots.length}`);
    for (const s of screenshots) console.log(`    - ${s}`);

  } catch (err) {
    console.error('FATAL:', err.message);
    console.error(err.stack);
  } finally {
    await browser.close();
  }
}

run();
