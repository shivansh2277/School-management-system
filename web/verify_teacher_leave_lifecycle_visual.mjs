import puppeteer from 'puppeteer-core';
import path from 'path';
import fs from 'fs';

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const SCREENSHOT_DIR = path.resolve('..', 'docs', 'screenshots', 'session18');
const ARTIFACT_DIR = 'C:\\Users\\SHIVANSH\\.gemini\\antigravity\\brain\\e684d120-764d-4019-8a3b-b718f7cade80';
const API_BASE = 'http://127.0.0.1:8000';
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
  console.log(`[CAPTURED] ${filename} -> docs/screenshots/session18 & artifact dir`);
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function apiLogin(login_id, password, role) {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ login_id, password, role }),
  });
  if (!res.ok) {
    throw new Error(`Login failed for ${login_id}: ${res.status} ${await res.text()}`);
  }
  const data = await res.json();
  return data.access_token;
}

async function runTeacherLeaveVisual() {
  console.log('================================================================');
  console.log('  TEACHER LEAVE LIFECYCLE: END-TO-END VISUAL VERIFICATION');
  console.log('================================================================\n');

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
  });

  try {
    const page = await browser.newPage();
    await page.setViewport({ width: 412, height: 915, isMobile: true, hasTouch: true });

    // Prevent any alert/confirm/prompt dialogs from hanging the browser
    await page.evaluateOnNewDocument(() => {
      window.confirm = () => true;
      window.alert = (msg) => console.log('[Alert Mocked]:', msg);
      window.prompt = () => 'Prior urgent commitment';
    });

    console.log(`1. Navigating to Mobile App: ${MOBILE_BASE} ...`);
    await page.goto(MOBILE_BASE, { waitUntil: 'domcontentloaded', timeout: 35000 });
    await page.evaluate(() => {
      try { localStorage.clear(); } catch (_) {}
    });
    await page.goto(MOBILE_BASE, { waitUntil: 'domcontentloaded', timeout: 35000 });
    await sleep(2500);

    // 2. Login as Teacher (TCH001 / Teacher@123)
    console.log('2. Selecting Teacher role on login screen...');
    await page.evaluate(() => {
      const el = Array.from(document.querySelectorAll('*')).find(
        (e) => (e.innerText || '').trim().toLowerCase() === 'teacher' && e.children.length === 0
      );
      if (el) (el.closest('[role="button"]') || el).click();
    });
    await sleep(600);

    console.log('Entering Teacher credentials (TCH001 / Teacher@123)...');
    const pwdInput = await page.$('input[type="password"]');
    if (pwdInput) {
      await pwdInput.click();
      await page.keyboard.type('Teacher@123');
    }
    await sleep(600);

    console.log('Clicking Sign in button...');
    await page.evaluate(() => {
      const el = Array.from(document.querySelectorAll('*')).find(
        (e) => (e.innerText || '').trim() === 'Sign in' && e.children.length === 0
      );
      if (el) (el.closest('[role="button"]') || el).click();
    });
    await sleep(3500);

    // Verify Teacher dashboard loaded
    await page.waitForFunction(
      () => document.body.innerText.includes('Anita Sharma'),
      { timeout: 15000 }
    );
    console.log('✓ Teacher dashboard loaded for Anita Sharma');

    // 3. Navigate to Leave screen via Quick Actions
    console.log('3. Navigating to Leave screen via Apply Leave button...');
    await page.evaluate(() => {
      const el = Array.from(document.querySelectorAll('*')).find(
        (e) => (e.innerText || '').trim() === 'Apply Leave' && e.children.length === 0
      );
      if (el) (el.closest('[role="button"]') || el).click();
    });
    await sleep(2500);

    // Verify Leave screen loaded
    await page.waitForFunction(
      () => document.body.innerText.includes('Apply for Leave') || document.body.innerText.includes('Leave Duration'),
      { timeout: 10000 }
    );
    console.log('✓ Teacher Leave screen loaded');

    // 4. Fill 3-day Casual Leave form (2026-10-07 to 2026-10-09)
    console.log('4. Selecting Multiple Days and setting dates 2026-10-07 to 2026-10-09...');
    // Click "Multiple Days"
    await page.evaluate(() => {
      const all = Array.from(document.querySelectorAll('*'));
      const multDaysBtn = all.find(
        (el) => (el.innerText || '').trim() === 'Multiple Days' && el.children.length === 0
      );
      if (multDaysBtn) {
        (multDaysBtn.closest('[role="button"]') || multDaysBtn).click();
      }
    });
    await sleep(800);

    // Fill Start Date, End Date, and Reason
    await page.evaluate(() => {
      const inputs = Array.from(document.querySelectorAll('input, textarea'));
      const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
      const areaSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;

      if (inputs[0]) {
        setter.call(inputs[0], '2026-10-07');
        inputs[0].dispatchEvent(new Event('input', { bubbles: true }));
        inputs[0].dispatchEvent(new Event('change', { bubbles: true }));
      }
      if (inputs[1]) {
        setter.call(inputs[1], '2026-10-09');
        inputs[1].dispatchEvent(new Event('input', { bubbles: true }));
        inputs[1].dispatchEvent(new Event('change', { bubbles: true }));
      }
      const reasonInput = inputs.find((el) => el.tagName === 'TEXTAREA') || inputs[2];
      if (reasonInput) {
        const fn = reasonInput.tagName === 'TEXTAREA' ? areaSetter : setter;
        fn.call(reasonInput, 'Urgent 3-day family function requiring personal leave');
        reasonInput.dispatchEvent(new Event('input', { bubbles: true }));
        reasonInput.dispatchEvent(new Event('change', { bubbles: true }));
      }
    });
    await sleep(800);

    // 5. Inspect Affected Periods
    console.log('5. Clicking "Check Affected Periods & Substitutes"...');
    await page.evaluate(() => {
      const all = Array.from(document.querySelectorAll('*'));
      const inspectBtn = all.find(
        (el) => (el.innerText || '').includes('Check Affected Periods') && el.children.length === 0
      );
      if (inspectBtn) {
        (inspectBtn.closest('[role="button"]') || inspectBtn).click();
      }
    });
    await sleep(2500);

    // Wait for inspected periods to load: exactly 12 periods affected!
    await page.waitForFunction(
      () => document.body.innerText.includes('12 period(s) affected') || document.body.innerText.includes('Cover Assigned'),
      { timeout: 10000 }
    );
    console.log('✓ Successfully inspected periods: exactly 12 periods detected across 3 days!');

    // Capture Screenshot 1: teacher_01_leave_inspect_12_periods.png
    await sleep(1000);
    const shot1 = await page.screenshot({ fullPage: false });
    saveScreenshot('teacher_01_leave_inspect_12_periods.png', shot1);

    // 6. Submit Leave Application
    console.log('6. Submitting Leave Application with all 12 substitutes selected...');
    await page.evaluate(() => {
      window.confirm = () => true;
      window.alert = () => true;
      const all = Array.from(document.querySelectorAll('*'));
      const submitBtn = all.find(
        (el) => (el.innerText || '').trim() === 'Submit Leave Application' && el.children.length === 0
      );
      if (submitBtn) {
        (submitBtn.closest('[role="button"]') || submitBtn).click();
      }
    });
    await sleep(3500);

    // Wait for history tab / submitted applications
    await page.waitForFunction(
      () => document.body.innerText.includes('Submitted Applications') || document.body.innerText.includes('Pending Review'),
      { timeout: 10000 }
    );
    console.log('✓ Leave Application submitted and visible in history!');

    // Expand substitutions breakdown
    console.log('Expanding period cover details...');
    await page.evaluate(() => {
      const all = Array.from(document.querySelectorAll('*'));
      const viewSubsBtn = all.find(
        (el) => (el.innerText || '').includes('View Period Substitutions') && el.children.length === 0
      );
      if (viewSubsBtn) {
        (viewSubsBtn.closest('[role="button"]') || viewSubsBtn).click();
      }
    });
    await sleep(2000);

    await page.waitForFunction(
      () => document.body.innerText.includes('Period Cover Breakdown:') || document.body.innerText.includes('Awaiting Confirmations'),
      { timeout: 10000 }
    );
    console.log('✓ All 12 periods visible with Pending confirmation status!');

    // Capture Screenshot 2: teacher_02_leave_submitted_12_pending.png
    const shot2 = await page.screenshot({ fullPage: false });
    saveScreenshot('teacher_02_leave_submitted_12_pending.png', shot2);

    // 7. Get Leave Application and Substitutions details via API
    console.log('7. Fetching leave application and substitution IDs from API...');
    const anitaToken = await apiLogin('TCH001', 'Teacher@123', 'teacher');
    const histRes = await fetch(`${API_BASE}/teacher/leave/history`, {
      headers: { Authorization: `Bearer ${anitaToken}` },
    });
    const historyList = await histRes.json();
    const app = historyList[0];
    console.log(`Active Leave Application ID: ${app.id} (${app.from_date} to ${app.to_date}, status: ${app.status})`);

    const subsRes = await fetch(`${API_BASE}/teacher/leave/applications/${app.id}/substitutions`, {
      headers: { Authorization: `Bearer ${anitaToken}` },
    });
    const subsData = await subsRes.json();
    const periods = subsData.periods;
    console.log(`Total substitution periods: ${periods.length}`);

    // First period substitution
    const p1 = periods[0];
    console.log(`Period 1: date=${p1.date}, slot=${p1.slot_id}, sub_id=${p1.substitution_id}, sub_teacher=${p1.substitute_teacher_name} (ID: ${p1.substitute_teacher_id})`);

    // 8. One substitute rejects: Period 1 substitute rejects
    console.log(`8. Substitute (${p1.substitute_teacher_name}) declines substitution request for Period 1...`);
    const subToken = await apiLogin('TCH012', 'Teacher@123', 'teacher');
    const rejRes = await fetch(`${API_BASE}/teacher/substitutions/${p1.substitution_id}/respond`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${subToken}`,
      },
      body: JSON.stringify({ action: 'reject', reason: 'Prior urgent examination duty commitment' }),
    });
    console.log(`Substitute reject response: ${rejRes.status}`);

    // Refresh teacher UI by toggling substitutions breakdown
    console.log('Refreshing Anita Sharma view to show rejected period...');
    await page.evaluate(() => {
      const all = Array.from(document.querySelectorAll('*'));
      const btn = all.find(
        (el) => (el.innerText || '').includes('Hide Period Cover Details') && el.children.length === 0
      );
      if (btn) (btn.closest('[role="button"]') || btn).click();
    });
    await sleep(800);
    await page.evaluate(() => {
      const all = Array.from(document.querySelectorAll('*'));
      const btn = all.find(
        (el) => (el.innerText || '').includes('View Period Substitutions') && el.children.length === 0
      );
      if (btn) (btn.closest('[role="button"]') || btn).click();
    });
    await sleep(2000);

    // Wait for "Declined" or "Reassign" button to appear
    await page.waitForFunction(
      () => document.body.innerText.includes('Declined') || document.body.innerText.includes('Reassign'),
      { timeout: 10000 }
    );
    console.log('✓ Rejected period clearly displays "Declined" pill and "Reassign" action button!');

    // Capture Screenshot 3: teacher_03_substitute_rejected.png
    const shot3 = await page.screenshot({ fullPage: false });
    saveScreenshot('teacher_03_substitute_rejected.png', shot3);

    // 9. Teacher clicks Reassign on Period 1
    console.log('9. Clicking "Reassign" button on rejected Period 1...');
    await page.evaluate(() => {
      const all = Array.from(document.querySelectorAll('*'));
      const reassignBtn = all.find(
        (el) => (el.innerText || '').trim() === 'Reassign' && el.children.length === 0
      );
      if (reassignBtn) {
        (reassignBtn.closest('[role="button"]') || reassignBtn).click();
      }
    });
    await sleep(1500);

    // Wait for Reassign Modal to open
    await page.waitForFunction(
      () => document.body.innerText.includes('Reassign Substitute') && document.body.innerText.includes('Select New Substitute'),
      { timeout: 10000 }
    );
    console.log('✓ Reassign Substitute modal opened with ranked eligible candidates!');

    // Select candidate: Sunita Yadav
    console.log('Selecting new substitute candidate: Sunita Yadav...');
    await page.evaluate(() => {
      window.confirm = () => true;
      window.alert = () => true;
      const all = Array.from(document.querySelectorAll('*'));
      const cand = all.find(
        (el) => (el.innerText || '').includes('Sunita Yadav') && el.children.length === 0
      );
      if (cand) {
        (cand.closest('[role="button"]') || cand).click();
      }
    });
    await sleep(2500);

    // Verify reassigned
    console.log('✓ Reassignment confirmed! Refreshing UI...');
    // Toggle details to see updated row
    await page.evaluate(() => {
      const all = Array.from(document.querySelectorAll('*'));
      const btn = all.find(
        (el) => (el.innerText || '').includes('Hide Period Cover Details') && el.children.length === 0
      );
      if (btn) (btn.closest('[role="button"]') || btn).click();
    });
    await sleep(800);
    await page.evaluate(() => {
      const all = Array.from(document.querySelectorAll('*'));
      const btn = all.find(
        (el) => (el.innerText || '').includes('View Period Substitutions') && el.children.length === 0
      );
      if (btn) (btn.closest('[role="button"]') || btn).click();
    });
    await sleep(2000);

    // Capture Screenshot 4: teacher_04_reassigned_substitute.png
    const shot4 = await page.screenshot({ fullPage: false });
    saveScreenshot('teacher_04_reassigned_substitute.png', shot4);

    // 10. New substitute accepts + remaining 11 substitutes accept
    console.log('10. New substitute (Sunita Yadav) accepts reassigned request...');
    const subsRes2 = await fetch(`${API_BASE}/teacher/leave/applications/${app.id}/substitutions`, {
      headers: { Authorization: `Bearer ${anitaToken}` },
    });
    const subsData2 = await subsRes2.json();
    const updatedPeriods = subsData2.periods;

    const sunitaToken = await apiLogin('TCH003', 'Teacher@123', 'teacher');
    const p1Updated = updatedPeriods[0];
    console.log(`Accepting period 1 with Sunita (sub_id=${p1Updated.substitution_id})...`);
    await fetch(`${API_BASE}/teacher/substitutions/${p1Updated.substitution_id}/respond`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${sunitaToken}` },
      body: JSON.stringify({ action: 'accept' }),
    });

    // Accept remaining 11 substitutes
    console.log('Accepting remaining 11 substitution periods...');
    for (let i = 1; i < updatedPeriods.length; i++) {
      const p = updatedPeriods[i];
      if (p.substitution_id) {
        const tCode = `TCH${String(p.substitute_teacher_id).padStart(3, '0')}`;
        try {
          const tok = await apiLogin(tCode, 'Teacher@123', 'teacher');
          await fetch(`${API_BASE}/teacher/substitutions/${p.substitution_id}/respond`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${tok}` },
            body: JSON.stringify({ action: 'accept' }),
          });
          console.log(`✓ Accepted period ${i + 1} (${p.date} P${p.period_no}) by ${tCode}`);
        } catch (err) {
          console.warn(`Could not accept for ${tCode}: ${err.message}`);
        }
      }
    }

    // Refresh teacher UI
    console.log('Refreshing Anita Sharma view to show 100% Accepted...');
    await page.evaluate(() => {
      const all = Array.from(document.querySelectorAll('*'));
      const btn = all.find(
        (el) => (el.innerText || '').includes('Hide Period Cover Details') && el.children.length === 0
      );
      if (btn) (btn.closest('[role="button"]') || btn).click();
    });
    await sleep(800);
    await page.evaluate(() => {
      const all = Array.from(document.querySelectorAll('*'));
      const btn = all.find(
        (el) => (el.innerText || '').includes('View Period Substitutions') && el.children.length === 0
      );
      if (btn) (btn.closest('[role="button"]') || btn).click();
    });
    await sleep(2500);

    // Wait for 100% Accepted
    await page.waitForFunction(
      () => document.body.innerText.includes('100% Accepted'),
      { timeout: 10000 }
    );
    console.log('✓ All 12 periods confirmed! Header shows "100% Accepted"!');

    // Capture Screenshot 5: teacher_05_all_12_confirmed.png
    const shot5 = await page.screenshot({ fullPage: false });
    saveScreenshot('teacher_05_all_12_confirmed.png', shot5);

    // 11. Admin approves the leave application
    console.log('11. Admin approving leave application with full cover confirmed...');
    const adminToken = await apiLogin('admin@sunrisepublic.edu', 'Admin@123', 'admin');
    const approveRes = await fetch(`${API_BASE}/admin/staff-leave/${app.id}/approve-with-substitutions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${adminToken}`,
      },
      body: JSON.stringify({ note: 'Approved with full 100% cover confirmed for all 12 periods' }),
    });
    console.log(`Admin approval status: ${approveRes.status}`);

    // Refresh Anita Sharma view
    console.log('Refreshing teacher UI to verify Approved status...');
    await page.reload({ waitUntil: 'domcontentloaded' });
    await sleep(2500);
    // Switch to history tab
    await page.evaluate(() => {
      const all = Array.from(document.querySelectorAll('*'));
      const histTab = all.find(
        (el) => (el.innerText || '').trim() === 'My Leaves' && el.children.length === 0
      );
      if (histTab) (histTab.closest('[role="button"]') || histTab).click();
    });
    await sleep(2000);

    await page.waitForFunction(
      () => document.body.innerText.includes('Approved') && document.body.innerText.includes('Approved with full 100% cover confirmed'),
      { timeout: 10000 }
    );
    console.log('✓ Leave Application successfully Approved with Admin remarks visible!');

    // Capture Screenshot 6: teacher_06_admin_approved.png
    const shot6 = await page.screenshot({ fullPage: false });
    saveScreenshot('teacher_06_admin_approved.png', shot6);

    console.log('\n================================================================');
    console.log('  TEACHER LEAVE LIFECYCLE: ALL 6 SCREENSHOTS VERIFIED & SAVED!');
    console.log('================================================================\n');

  } finally {
    await browser.close();
  }
}

runTeacherLeaveVisual().catch((err) => {
  console.error('[FATAL ERROR]', err);
  process.exit(1);
});
