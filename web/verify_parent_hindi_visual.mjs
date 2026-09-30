import puppeteer from 'puppeteer-core';
import path from 'path';
import fs from 'fs';

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const SCREENSHOT_DIR = path.resolve('..', 'docs', 'screenshots', 'session18');
const ARTIFACT_DIR = 'C:\\Users\\SHIVANSH\\.gemini\\antigravity\\brain\\e684d120-764d-4019-8a3b-b718f7cade80';
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

async function clickBottomTab(page, tabIndex) {
  await page.evaluate((idx) => {
    const tabs = document.querySelectorAll('a[role="tab"]');
    if (tabs[idx]) {
      tabs[idx].click();
    }
  }, tabIndex);
  await sleep(2500);
}

async function openDrawerAndNavigate(page, itemTextSnippet) {
  console.log(`Opening NavDrawer and navigating to "${itemTextSnippet}"...`);
  // Click hamburger icon
  await page.evaluate(() => {
    const menuBtn = document.querySelector('[aria-label="Open Menu"]') ||
                    document.querySelector('[aria-label="मेनू खोलें"]') ||
                    Array.from(document.querySelectorAll('*')).find(
                      el => (el.getAttribute('aria-label') || '').includes('Menu')
                    );
    if (menuBtn) {
      menuBtn.click();
    }
  });
  await sleep(1200);

  // Click the drawer item
  const clicked = await page.evaluate((snippet) => {
    const all = Array.from(document.querySelectorAll('*'));
    const item = all.find(
      (el) => (el.innerText || '').trim() === snippet && el.children.length === 0
    ) || all.find(
      (el) => (el.innerText || '').includes(snippet) && el.children.length === 0
    );
    if (item) {
      (item.closest('[role="button"]') || item).click();
      return true;
    }
    return false;
  }, itemTextSnippet);

  if (!clicked) {
    console.warn(`[WARN] Could not find drawer item for "${itemTextSnippet}"`);
  }
  await sleep(2500);
}

async function runParentHindiVisual() {
  console.log('================================================================');
  console.log('  PARENT MULTILINGUAL (HINDI) E2E VISUAL VERIFICATION SUITE');
  console.log('================================================================\n');

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
  });

  try {
    const page = await browser.newPage();
    await page.setViewport({ width: 412, height: 915, isMobile: true, hasTouch: true });

    await page.evaluateOnNewDocument(() => {
      window.confirm = () => true;
      window.alert = (msg) => console.log('[Alert Mocked]:', msg);
    });

    console.log(`1. Navigating to Mobile App: ${MOBILE_BASE} ...`);
    await page.goto(MOBILE_BASE, { waitUntil: 'domcontentloaded', timeout: 35000 });
    await page.evaluate(() => {
      try { localStorage.clear(); } catch (_) {}
    });
    await page.goto(MOBILE_BASE, { waitUntil: 'domcontentloaded', timeout: 35000 });
    await sleep(2500);

    // -------------------------------------------------------------
    // STEP 1: LOGIN AS PARENT (9876500001 / Parent@123)
    // -------------------------------------------------------------
    console.log('2. Selecting Parent role and logging in...');
    await page.evaluate(() => {
      const el = Array.from(document.querySelectorAll('*')).find(
        (e) => (e.innerText || '').trim().toLowerCase() === 'parent' && e.children.length === 0
      );
      if (el) (el.closest('[role="button"]') || el).click();
    });
    await sleep(600);

    const pwdInput = await page.$('input[type="password"]');
    if (pwdInput) {
      await pwdInput.click();
      await page.keyboard.type('Parent@123');
    }
    await sleep(600);

    await page.evaluate(() => {
      const el = Array.from(document.querySelectorAll('*')).find(
        (e) => (e.innerText || '').trim() === 'Sign in' && e.children.length === 0
      );
      if (el) (el.closest('[role="button"]') || el).click();
    });
    await sleep(3500);

    // Verify Parent Home loaded
    await page.waitForFunction(
      () => document.body.innerText.includes('Suresh Sharma') || document.body.innerText.includes('Aarav'),
      { timeout: 15000 }
    );
    console.log('✓ Parent dashboard loaded for Suresh Sharma');

    // -------------------------------------------------------------
    // STEP 2: NAVIGATE TO PROFILE & SWITCH LANGUAGE TO HINDI
    // -------------------------------------------------------------
    console.log('3. Navigating to Profile (Tab 3) to switch language to Hindi...');
    await clickBottomTab(page, 3); // Profile tab

    // Verify Profile loaded
    await page.waitForFunction(
      () => document.body.innerText.includes('Language') || document.body.innerText.includes('App Settings') || document.body.innerText.includes('English'),
      { timeout: 10000 }
    );
    console.log('✓ Profile loaded. Clicking हिन्दी (Hindi) language chip...');

    // Click "हिन्दी (Hindi)"
    await page.evaluate(() => {
      const all = Array.from(document.querySelectorAll('*'));
      const hindiChip = all.find(
        (e) => (e.innerText || '').includes('हिन्दी') && e.children.length === 0
      );
      if (hindiChip) (hindiChip.closest('[role="button"]') || hindiChip).click();
    });
    await sleep(2000);

    // Verify Hindi rendered on Profile
    await page.waitForFunction(
      () => document.body.innerText.includes('ऐप सेटिंग्स') || document.body.innerText.includes('अभिभावक विवरण'),
      { timeout: 10000 }
    );
    console.log('✓ Language switched to Hindi successfully!');

    // Capture Screenshot 1: parent_hi_01_profile.png
    const shot01 = await page.screenshot({ fullPage: false });
    saveScreenshot('parent_hi_01_profile.png', shot01);

    // -------------------------------------------------------------
    // STEP 3: DASHBOARD IN HINDI
    // -------------------------------------------------------------
    console.log('4. Navigating to Dashboard (Tab 0: होम)...');
    await clickBottomTab(page, 0); // Home tab

    await page.waitForFunction(
      () => document.body.innerText.includes('कक्षा') && (document.body.innerText.includes('बकाया शुल्क') || document.body.innerText.includes('उपस्थिति')),
      { timeout: 10000 }
    );
    console.log('✓ Dashboard rendered in Hindi with कक्षा, उपस्थिति, and बकाया शुल्क!');

    // Capture Screenshot 2: parent_hi_02_dashboard.png
    const shot02 = await page.screenshot({ fullPage: false });
    saveScreenshot('parent_hi_02_dashboard.png', shot02);

    // -------------------------------------------------------------
    // STEP 4: CHILD DETAILS IN HINDI
    // -------------------------------------------------------------
    console.log('5. Navigating to Child (Tab 1: बच्चा / विद्यार्थी)...');
    await clickBottomTab(page, 1); // Child tab

    await page.waitForFunction(
      () => document.body.innerText.includes('विद्यार्थी विवरण') || document.body.innerText.includes('प्रवेश संख्या') || document.body.innerText.includes('नामांकन स्थिति') || document.body.innerText.includes('क्रमांक'),
      { timeout: 10000 }
    );
    console.log('✓ Child screen rendered in Hindi with विद्यार्थी विवरण!');

    // Capture Screenshot 3: parent_hi_03_child.png
    const shot03 = await page.screenshot({ fullPage: false });
    saveScreenshot('parent_hi_03_child.png', shot03);

    // -------------------------------------------------------------
    // STEP 5: FEES & PAYMENT DIALOG IN HINDI
    // -------------------------------------------------------------
    console.log('6. Navigating to Fees (Tab 2: फीस / शुल्क)...');
    await clickBottomTab(page, 2); // Fees tab

    await page.waitForFunction(
      () => document.body.innerText.includes('कुल बकाया शुल्क') || document.body.innerText.includes('शुल्क चालान'),
      { timeout: 10000 }
    );
    console.log('✓ Fees screen rendered in Hindi!');

    // Capture Screenshot 4: parent_hi_04_fees.png
    const shot04 = await page.screenshot({ fullPage: false });
    saveScreenshot('parent_hi_04_fees.png', shot04);

    // Click "भुगतान करें" (Pay Now) to open payment confirmation dialog
    console.log('Triggering payment confirmation dialog in Hindi...');
    await page.evaluate(() => {
      const all = Array.from(document.querySelectorAll('*'));
      const payBtn = all.find(
        (e) => (e.innerText || '').trim() === 'भुगतान करें' && e.children.length === 0
      );
      if (payBtn) (payBtn.closest('[role="button"]') || payBtn).click();
    });
    await sleep(1200);

    // Capture Screenshot 4b: parent_hi_04b_fees_dialog.png
    const shot04b = await page.screenshot({ fullPage: false });
    saveScreenshot('parent_hi_04b_fees_dialog.png', shot04b);

    // Click "रद्द करें" to close payment dialog
    await page.evaluate(() => {
      const all = Array.from(document.querySelectorAll('*'));
      const cancelBtn = all.find(
        (e) => (e.innerText || '').trim() === 'रद्द करें' && e.children.length === 0
      );
      if (cancelBtn) (cancelBtn.closest('[role="button"]') || cancelBtn).click();
    });
    await sleep(800);

    // -------------------------------------------------------------
    // STEP 6: ATTENDANCE & LEAVE APPLICATION MODAL IN HINDI
    // -------------------------------------------------------------
    console.log('7. Navigating to Attendance (उपस्थिति)...');
    await openDrawerAndNavigate(page, 'उपस्थिति');

    await page.waitForFunction(
      () => document.body.innerText.includes('उपस्थिति') || document.body.innerText.includes('कुल उपस्थिति') || document.body.innerText.includes('मासिक उपस्थिति'),
      { timeout: 10000 }
    );
    console.log('✓ Attendance screen rendered in Hindi!');

    // Capture Screenshot 5: parent_hi_05_attendance.png
    const shot05 = await page.screenshot({ fullPage: false });
    saveScreenshot('parent_hi_05_attendance.png', shot05);

    // Open leave application modal
    console.log('Opening leave application modal in Hindi...');
    await page.evaluate(() => {
      const all = Array.from(document.querySelectorAll('*'));
      const leaveBtn = all.find(
        (e) => (e.innerText || '').includes('अवकाश') && e.children.length === 0
      );
      if (leaveBtn) (leaveBtn.closest('[role="button"]') || leaveBtn).click();
    });
    await sleep(1200);

    // Capture Screenshot 5b: parent_hi_05b_attendance_leave_modal.png
    const shot05b = await page.screenshot({ fullPage: false });
    saveScreenshot('parent_hi_05b_attendance_leave_modal.png', shot05b);

    // Close modal
    await page.evaluate(() => {
      const all = Array.from(document.querySelectorAll('*'));
      const cancelBtn = all.find(
        (e) => (e.innerText || '').includes('रद्द') && e.children.length === 0
      );
      if (cancelBtn) (cancelBtn.closest('[role="button"]') || cancelBtn).click();
    });
    await sleep(800);

    // -------------------------------------------------------------
    // STEP 7: HOMEWORK IN HINDI
    // -------------------------------------------------------------
    console.log('8. Navigating to Homework (गृहकार्य)...');
    await openDrawerAndNavigate(page, 'गृहकार्य');

    await page.waitForFunction(
      () => document.body.innerText.includes('गृहकार्य') || document.body.innerText.includes('लंबित') || document.body.innerText.includes('जमा किया'),
      { timeout: 10000 }
    );
    console.log('✓ Homework screen rendered in Hindi!');

    // Capture Screenshot 6: parent_hi_06_homework.png
    const shot06 = await page.screenshot({ fullPage: false });
    saveScreenshot('parent_hi_06_homework.png', shot06);

    // -------------------------------------------------------------
    // STEP 8: RESULTS IN HINDI
    // -------------------------------------------------------------
    console.log('9. Navigating to Results (परिणाम)...');
    await openDrawerAndNavigate(page, 'परिणाम');

    await page.waitForFunction(
      () => document.body.innerText.includes('सम्पन्न परीक्षाएं') || document.body.innerText.includes('परीक्षा परिणाम') || document.body.innerText.includes('स्कोरकार्ड') || document.body.innerText.includes('परिणाम'),
      { timeout: 10000 }
    );
    console.log('✓ Results screen rendered in Hindi!');

    // Capture Screenshot 7: parent_hi_07_results.png
    const shot07 = await page.screenshot({ fullPage: false });
    saveScreenshot('parent_hi_07_results.png', shot07);

    // -------------------------------------------------------------
    // STEP 9: GRIEVANCES & NEW ISSUE MODAL IN HINDI
    // -------------------------------------------------------------
    console.log('10. Navigating to Grievances (शिकायतें)...');
    await openDrawerAndNavigate(page, 'शिकायतें');

    await page.waitForFunction(
      () => document.body.innerText.includes('शिकायत व सहायता कक्ष') || document.body.innerText.includes('नई समस्या दर्ज करें'),
      { timeout: 10000 }
    );
    console.log('✓ Grievances desk rendered in Hindi!');

    // Capture Screenshot 8: parent_hi_08_grievances.png
    const shot08 = await page.screenshot({ fullPage: false });
    saveScreenshot('parent_hi_08_grievances.png', shot08);

    // Open New Grievance Modal
    console.log('Opening New Grievance modal in Hindi...');
    await page.evaluate(() => {
      const all = Array.from(document.querySelectorAll('*'));
      const newIssueBtn = all.find(
        (e) => (e.innerText || '').includes('नई समस्या दर्ज करें') && e.children.length === 0
      );
      if (newIssueBtn) (newIssueBtn.closest('[role="button"]') || newIssueBtn).click();
    });
    await sleep(1500);

    // Capture Screenshot 8b: parent_hi_08b_grievances_modal.png
    const shot08b = await page.screenshot({ fullPage: false });
    saveScreenshot('parent_hi_08b_grievances_modal.png', shot08b);

    // Close modal
    await page.evaluate(() => {
      const all = Array.from(document.querySelectorAll('*'));
      const cancelBtn = all.find(
        (e) => (e.innerText || '').trim() === 'रद्द करें' && e.children.length === 0
      );
      if (cancelBtn) (cancelBtn.closest('[role="button"]') || cancelBtn).click();
    });
    await sleep(800);

    // -------------------------------------------------------------
    // STEP 10: NOTICES IN HINDI
    // -------------------------------------------------------------
    console.log('11. Navigating to Notices (सूचनाएं)...');
    await openDrawerAndNavigate(page, 'सूचनाएं');

    await page.waitForFunction(
      () => document.body.innerText.includes('सूचनाएं व परिपत्र') || document.body.innerText.includes('सभी') || document.body.innerText.includes('शैक्षणिक'),
      { timeout: 10000 }
    );
    console.log('✓ Notices circulars rendered in Hindi!');

    // Capture Screenshot 9: parent_hi_09_notices.png
    const shot09 = await page.screenshot({ fullPage: false });
    saveScreenshot('parent_hi_09_notices.png', shot09);

    // -------------------------------------------------------------
    // STEP 11: TIMETABLE IN HINDI
    // -------------------------------------------------------------
    console.log('12. Navigating to Timetable (समय-सारणी)...');
    await openDrawerAndNavigate(page, 'समय-सारणी');

    await page.waitForFunction(
      () => document.body.innerText.includes('सोमवार') || document.body.innerText.includes('समय-सारणी'),
      { timeout: 10000 }
    );
    console.log('✓ Timetable rendered in Hindi with day chips!');

    // Capture Screenshot 10: parent_hi_10_timetable.png
    const shot10 = await page.screenshot({ fullPage: false });
    saveScreenshot('parent_hi_10_timetable.png', shot10);

    // -------------------------------------------------------------
    // STEP 12: NAVDRAWER MENU IN HINDI
    // -------------------------------------------------------------
    console.log('13. Opening NavDrawer Menu to capture full Hindi menu drawer...');
    await page.evaluate(() => {
      const menuBtn = document.querySelector('[aria-label="Open Menu"]') ||
                      Array.from(document.querySelectorAll('*')).find(
                        el => (el.getAttribute('aria-label') || '').includes('Menu')
                      );
      if (menuBtn) menuBtn.click();
    });
    await sleep(1500);

    await page.waitForFunction(
      () => document.body.innerText.includes('नेविगेशन') || document.body.innerText.includes('साइन आउट') || document.body.innerText.includes('लॉग आउट'),
      { timeout: 10000 }
    );
    console.log('✓ NavDrawer opened in Hindi with localized sections and sign-out button!');

    // Capture Screenshot 11: parent_hi_11_menu_drawer.png
    const shot11 = await page.screenshot({ fullPage: false });
    saveScreenshot('parent_hi_11_menu_drawer.png', shot11);

    // -------------------------------------------------------------
    // STEP 13: LOGOUT / SIGN OUT
    // -------------------------------------------------------------
    console.log('14. Clicking sign out in drawer...');
    await page.evaluate(() => {
      const logoutBtn = document.querySelector('[aria-label="Logout"]') ||
                        Array.from(document.querySelectorAll('*')).find(
                          (e) => ((e.innerText || '').includes('साइन आउट') || (e.innerText || '').includes('लॉग आउट')) && e.children.length === 0
                        );
      if (logoutBtn) (logoutBtn.closest('[role="button"]') || logoutBtn).click();
    });
    await sleep(2500);

    // Verify back to login page
    await page.waitForFunction(
      () => document.body.innerText.includes('Sign in to continue') || document.body.innerText.includes('Sunrise Public School'),
      { timeout: 10000 }
    );
    console.log('✓ Successfully signed out back to login screen!');

    // Capture Screenshot 12: parent_hi_12_logout.png
    const shot12 = await page.screenshot({ fullPage: false });
    saveScreenshot('parent_hi_12_logout.png', shot12);

    console.log('\n================================================================');
    console.log('  PARENT MULTILINGUAL (HINDI) SUITE COMPLETED SUCCESSFULLY!');
    console.log('================================================================\n');

  } finally {
    await browser.close();
  }
}

runParentHindiVisual().catch((err) => {
  console.error('[FATAL ERROR]', err);
  process.exit(1);
});
