import puppeteer from 'puppeteer-core';
import path from 'path';
import fs from 'fs';

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const SCREENSHOT_DIR = path.resolve('..', 'docs', 'screenshots', 'local_e2e_verification');
const ARTIFACT_DIR = 'C:\\Users\\SHIVANSH\\.gemini\\antigravity\\brain\\6f889fba-503e-46ca-b3b6-b0b91d35c2f9';
const WEB_BASE = 'http://127.0.0.1:5173';
const API_BASE = 'http://127.0.0.1:8000';

if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

function saveScreenshot(filename, buffer) {
  const f1 = path.join(SCREENSHOT_DIR, filename);
  const f2 = path.join(ARTIFACT_DIR, filename);
  fs.writeFileSync(f1, buffer);
  try {
    fs.writeFileSync(f2, buffer);
  } catch (e) {
    console.warn(`[WARN] Artifact copy failed: ${e.message}`);
  }
  console.log(`  [SCREENSHOT] Saved: ${filename}`);
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const results = [];
function record(scenario, status, details = '') {
  results.push({ scenario, status, details });
  const icon = status === 'PASS' ? '✓' : status === 'FAIL' ? '✗' : '⚠';
  console.log(`  ${icon} [${status}] ${scenario}${details ? ` - ${details}` : ''}`);
}

async function loginUser(page, loginId, password) {
  await page.goto(`${WEB_BASE}/#/login`, { waitUntil: 'networkidle0', timeout: 15000 });
  await sleep(1000);
  await page.click('input:not([type="password"])');
  await page.keyboard.down('Control');
  await page.keyboard.press('KeyA');
  await page.keyboard.up('Control');
  await page.keyboard.press('Backspace');
  await page.type('input:not([type="password"])', loginId);
  await page.type('input[type="password"]', password);
  await sleep(400);
  await page.click('form button');
  await sleep(2500);
}

async function getAuthToken(loginId, password, role = 'admin') {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ login_id: loginId, password, role }),
  });
  if (!res.ok) {
    throw new Error(`Login failed for ${loginId}: ${res.status} ${await res.text()}`);
  }
  const data = await res.json();
  return data.access_token;
}

async function setInputValue(page, selector, value) {
  await page.$eval(selector, (el, val) => {
    const setter = Object.getOwnPropertyDescriptor(
      el instanceof HTMLTextAreaElement ? window.HTMLTextAreaElement.prototype : window.HTMLInputElement.prototype,
      'value'
    ).set;
    setter.call(el, val);
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
  }, value);
}

async function run() {
  console.log('================================================================');
  console.log('  TESTING HOLIDAY EDITING & MULTI-VIEW PROPAGATION (WEB & MOBILE)');
  console.log('================================================================\n');

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--window-size=1440,900'],
  });

  let holidayId = null;

  try {
    const adminCtx = await browser.createBrowserContext();
    const adminPage = await adminCtx.newPage();
    await adminPage.setViewport({ width: 1440, height: 900 });

    const adminToken = await getAuthToken('admin@sunrisepublic.edu', 'Admin@123', 'admin');
    const teacherToken = await getAuthToken('TCH001', 'Teacher@123', 'teacher');

    // 1. Declare an initial test holiday for 2026-10-01 (Yesterday): "Staff Professional Day", School-Wide
    const initHolidayRes = await fetch(`${API_BASE}/admin/attendance/holidays`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${adminToken}` },
      body: JSON.stringify({
        name: 'Staff Professional Day',
        start_date: '2026-10-01',
        end_date: '2026-10-01',
        description: 'Mandatory staff training workshop',
        is_school_wide: true,
        class_section_ids: [],
      }),
    });
    const initHoliday = await initHolidayRes.json();
    holidayId = initHoliday.id;
    record('H1.1: Declare initial test holiday on 2026-10-01 (School-Wide)', initHolidayRes.status === 201 ? 'PASS' : 'FAIL', `ID: ${holidayId}`);

    // Verify initial state: Teacher attendance on 2026-10-01 is BLOCKED by initial holiday
    const initCheckRes = await fetch(`${API_BASE}/teacher/attendance`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${teacherToken}` },
      body: JSON.stringify({
        class_section_id: 1,
        date: '2026-10-01',
        entries: [{ student_id: 1, status: 'present' }],
      }),
    });
    const initCheckData = await initCheckRes.json();
    const initBlocked = initCheckRes.status === 400 && initCheckData.detail?.includes('Staff Professional Day');
    record('H1.2: Initial holiday blocks attendance marking on 2026-10-01 as expected (400 Bad Request)', initBlocked ? 'PASS' : 'FAIL', initCheckData.detail);

    // 2. Log in as Super Admin
    await loginUser(adminPage, 'admin@sunrisepublic.edu', 'Admin@123');

    // 3. Open Holiday Management page in UI
    await adminPage.goto(`${WEB_BASE}/#/admin/holidays`, { waitUntil: 'networkidle0' });
    await adminPage.reload({ waitUntil: 'networkidle0' });
    await adminPage.waitForSelector('table tbody tr', { timeout: 10000 });
    await sleep(1500);

    // 4. Click Edit button for our declared holiday
    const editBtnFound = await adminPage.evaluate((targetId) => {
      const rows = Array.from(document.querySelectorAll('table tbody tr'));
      for (const row of rows) {
        if (row.innerText.includes('Staff Professional Day')) {
          const editBtn = Array.from(row.querySelectorAll('button')).find(b => b.textContent?.trim() === 'Edit');
          if (editBtn) {
            editBtn.click();
            return true;
          }
        }
      }
      return false;
    }, holidayId);
    record('H1.3: Admin UI renders Edit button and opens Edit Holiday Modal', editBtnFound ? 'PASS' : 'FAIL');
    await sleep(1000);
    saveScreenshot('01_holiday_edit_modal_open.png', await adminPage.screenshot());

    // 5. Fill out the Edit Modal with modifications:
    //    - Change Title to: "Gandhi Jayanti Observance"
    //    - Move Date to: 2026-10-02 (Today)
    //    - Change Description to: "School closed for Gandhi Jayanti celebrations"
    //    - Change Scope to: Section-Scoped (Select Class Section 1 only)
    await adminPage.waitForSelector('.bg-surface h2', { timeout: 5000 });
    await sleep(500);

    await adminPage.evaluate(() => {
      const textInput = document.querySelector('.bg-surface input[type="text"]');
      if (textInput) {
        const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        setter.call(textInput, 'Gandhi Jayanti Observance');
        textInput.dispatchEvent(new Event('input', { bubbles: true }));
        textInput.dispatchEvent(new Event('change', { bubbles: true }));
      }
      const descArea = document.querySelector('.bg-surface textarea');
      if (descArea) {
        const setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
        setter.call(descArea, 'School closed for Gandhi Jayanti celebrations');
        descArea.dispatchEvent(new Event('input', { bubbles: true }));
        descArea.dispatchEvent(new Event('change', { bubbles: true }));
      }
    });

    const dateInputs = await adminPage.$$('.bg-surface input[type="date"]');
    for (const dInput of dateInputs) {
      await adminPage.evaluate((el) => {
        const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        setter.call(el, '2026-10-02');
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
      }, dInput);
    }

    // Switch scope radio to Section-Scoped
    const radios = await adminPage.$$('.bg-surface input[type="radio"]');
    if (radios[1]) {
      await radios[1].click();
      await sleep(500);
    }

    // Select Section 1 (10-A) checkbox explicitly
    await adminPage.waitForSelector('.bg-surface input[type="checkbox"]', { timeout: 5000 });
    const checked = await adminPage.evaluate(() => {
      const cbs = Array.from(document.querySelectorAll('.bg-surface input[type="checkbox"]'));
      for (const cb of cbs) {
        const label = cb.closest('label');
        if (label && label.textContent && label.textContent.includes('10-A')) {
          if (!cb.checked) {
            cb.click();
            return true;
          }
        }
      }
      return false;
    });
    console.log(`    Checked 10-A checkbox: ${checked}`);
    await sleep(500);

    saveScreenshot('02_holiday_edit_modal_filled.png', await adminPage.screenshot());

    // Click "Save Changes"
    const clickedSave = await adminPage.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('.bg-surface button'));
      const saveBtn = btns.find(b => b.textContent?.includes('Save Changes'));
      if (saveBtn) {
        saveBtn.click();
        return true;
      }
      return false;
    });
    console.log(`    Clicked Save Changes: ${clickedSave}`);
    await sleep(2500);

    // 6. Verify table row reflects the edited values
    const tableText = await adminPage.evaluate(() => document.body.innerText);
    const hasUpdatedName = tableText.includes('Gandhi Jayanti Observance');
    const hasUpdatedDates = tableText.includes('2026-10-02');
    const hasUpdatedScope = tableText.includes('Specific Sections');
    record('H1.4: Holiday successfully edited in UI (Name, Date 2026-10-02, Specific Scope 1)', hasUpdatedName && hasUpdatedDates && hasUpdatedScope ? 'PASS' : 'FAIL');
    saveScreenshot('03_holiday_edited_in_admin_table.png', await adminPage.screenshot());

    // 7. Test Propagation to Web Attendance View (/#/attendance)
    console.log('\n--- VERIFY PROPAGATION: WEB ATTENDANCE VIEW (/#/attendance) ---');
    await adminPage.goto(`${WEB_BASE}/#/attendance`, { waitUntil: 'networkidle0' });
    await sleep(2000);

    // Test 7A: Check old date (2026-10-01) -> Banner MUST NOT be shown anymore!
    await adminPage.$eval('input[type="date"]', (el) => {
      el.value = '2026-10-01';
      el.dispatchEvent(new Event('change', { bubbles: true }));
    });
    await sleep(1000);
    const oldDateText = await adminPage.evaluate(() => document.body.innerText);
    const oldDateHasBanner = oldDateText.includes('Declared Holiday:');
    record('H2.1: Old holiday date (2026-10-01) no longer displays holiday banner', !oldDateHasBanner ? 'PASS' : 'FAIL');

    // Test 7B: Check edited date (2026-10-02) for Section 1 (affected section) -> Banner MUST be shown!
    await adminPage.select('select', '1');
    await adminPage.$eval('input[type="date"]', (el) => {
      el.value = '2026-10-02';
      el.dispatchEvent(new Event('change', { bubbles: true }));
    });
    await sleep(1000);
    const section1Text = await adminPage.evaluate(() => document.body.innerText);
    const section1HasBanner = section1Text.includes('Declared Holiday:') &&
      section1Text.includes('Gandhi Jayanti Observance') &&
      section1Text.includes('Normal attendance marking is blocked');
    record('H2.2: Edited date (2026-10-02) for affected Section 1 displays Declared Holiday banner with updated name', section1HasBanner ? 'PASS' : 'FAIL');
    saveScreenshot('04_holiday_propagation_attendance_affected.png', await adminPage.screenshot());

    // Test 7C: Check edited date (2026-10-02) for Section 2 (unaffected section) -> Banner MUST NOT be shown!
    await adminPage.select('select', '2');
    await sleep(1000);
    const section2Text = await adminPage.evaluate(() => document.body.innerText);
    const section2HasBanner = section2Text.includes('Declared Holiday:');
    record('H2.3: Edited date (2026-10-02) for unaffected Section 2 does NOT display holiday banner (scoped correctly)', !section2HasBanner ? 'PASS' : 'FAIL');
    saveScreenshot('05_holiday_propagation_attendance_unaffected.png', await adminPage.screenshot());

    // 8. Test Propagation to Web Dashboard Upcoming Events (/#/dashboard)
    console.log('\n--- VERIFY PROPAGATION: WEB DASHBOARD UPCOMING EVENTS ---');
    await adminPage.goto(`${WEB_BASE}/#/dashboard`, { waitUntil: 'networkidle0' });
    await adminPage.reload({ waitUntil: 'networkidle0' });
    await sleep(2500);
    const dashboardText = await adminPage.evaluate(() => document.body.innerText);
    const dashboardHasUpdatedEvent = dashboardText.includes('Gandhi Jayanti Observance');
    record('H3.1: Dashboard Upcoming Events card reflects edited holiday name and date', dashboardHasUpdatedEvent ? 'PASS' : 'FAIL');
    saveScreenshot('06_holiday_propagation_dashboard_events.png', await adminPage.screenshot());

    // 9. Test Propagation to Teacher Attendance API / Mobile App API (/teacher/attendance)
    console.log('\n--- VERIFY PROPAGATION: TEACHER / MOBILE ATTENDANCE API ---');

    // Test 9A: Teacher marks Section 1 on old date (2026-10-01) -> MUST SUCCEED (freed up by edit)!
    const markOldDateRes = await fetch(`${API_BASE}/teacher/attendance`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${teacherToken}` },
      body: JSON.stringify({
        class_section_id: 1,
        date: '2026-10-01',
        entries: [{ student_id: 1, status: 'present' }],
      }),
    });
    record('H4.1: Teacher attendance on previously scheduled date (2026-10-01) is now ALLOWED (200 OK)', markOldDateRes.status === 200 ? 'PASS' : 'FAIL', `Status: ${markOldDateRes.status}`);

    // Test 9B: Teacher marks Section 1 on edited date (2026-10-02) -> MUST BE BLOCKED with 400 Bad Request!
    const markAffectedRes = await fetch(`${API_BASE}/teacher/attendance`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${teacherToken}` },
      body: JSON.stringify({
        class_section_id: 1,
        date: '2026-10-02',
        entries: [{ student_id: 1, status: 'present' }],
      }),
    });
    const markAffectedData = await markAffectedRes.json();
    const markAffectedBlocked = markAffectedRes.status === 400 &&
      markAffectedData.detail?.includes('Gandhi Jayanti Observance') &&
      markAffectedData.detail?.includes('not a working day');
    record('H4.2: Teacher attendance on edited holiday date (2026-10-02) for Section 1 is BLOCKED (400 Bad Request)', markAffectedBlocked ? 'PASS' : 'FAIL', markAffectedData.detail);

    // 10. Test Second Edit: Re-expand holiday scope to School-Wide via PUT
    console.log('\n--- VERIFY SECOND EDIT: RE-EXPAND TO SCHOOL-WIDE ---');
    const reEditRes = await fetch(`${API_BASE}/admin/attendance/holidays/${holidayId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${adminToken}` },
      body: JSON.stringify({
        name: 'Gandhi Jayanti All-School Holiday',
        start_date: '2026-10-02',
        end_date: '2026-10-02',
        description: 'School-wide holiday for all sections',
        is_school_wide: true,
        class_section_ids: [],
      }),
    });
    record('H5.1: Second Edit: Re-expand holiday scope to School-Wide via PUT', reEditRes.status === 200 ? 'PASS' : 'FAIL');

    // Verify propagation of School-Wide edit to Web Attendance view:
    await adminPage.goto(`${WEB_BASE}/#/attendance`, { waitUntil: 'networkidle0' });
    await adminPage.reload({ waitUntil: 'networkidle0' });
    await sleep(2000);
    await adminPage.select('select', '2'); // Section 2
    await adminPage.$eval('input[type="date"]', (el) => {
      el.value = '2026-10-02';
      el.dispatchEvent(new Event('change', { bubbles: true }));
    });
    await sleep(1000);
    const sec2ReText = await adminPage.evaluate(() => document.body.innerText);
    const sec2NowHasBanner = sec2ReText.includes('Declared Holiday:') && sec2ReText.includes('Gandhi Jayanti All-School Holiday');
    record('H5.2: Section 2 now shows Declared Holiday banner in Web Attendance after school-wide re-expansion', sec2NowHasBanner ? 'PASS' : 'FAIL');
    saveScreenshot('07_holiday_reexpanded_school_wide.png', await adminPage.screenshot());

    // 11. Cleanup test holiday
    await fetch(`${API_BASE}/admin/attendance/holidays/${holidayId}/cancel`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${adminToken}` },
      body: JSON.stringify({ reason: 'E2E holiday editing verification complete' }),
    });

  } catch (err) {
    console.error('Fatal error during holiday editing verification:', err);
  } finally {
    await browser.close();
  }

  console.log('\n================================================================');
  console.log('  HOLIDAY EDITING & PROPAGATION SUMMARY RESULTS:');
  console.log('================================================================');
  const total = results.length;
  const passed = results.filter((r) => r.status === 'PASS').length;
  const failed = results.filter((r) => r.status === 'FAIL').length;
  console.log(`  Total Scenarios Tested : ${total}`);
  console.log(`  Passed                 : ${passed}`);
  console.log(`  Failed                 : ${failed}`);
  console.log('================================================================\n');
}

run();
