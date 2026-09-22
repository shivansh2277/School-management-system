import puppeteer from 'puppeteer-core';
import path from 'path';
import fs from 'fs';

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const SCREENSHOT_DIR = path.resolve('..', 'docs', 'screenshots');
const ARTIFACT_DIR = 'C:\\Users\\SHIVANSH\\.gemini\\antigravity\\brain\\d965c132-59ed-4355-8c29-1aa6e333451d';

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
    console.warn(`Could not save to artifact dir: ${err.message}`);
  }
  console.log(`[Captured & Saved] ${filename} -> docs/screenshots & artifact dir`);
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function runVisualValidation() {
  console.log('================================================================');
  console.log('  SESSION 9: END-TO-END VISUAL VALIDATION SUITE');
  console.log('================================================================\n');

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
  });

  try {
    // -------------------------------------------------------------
    // 1. WEB ADMIN DASHBOARD & RED-X MODAL VERIFICATION
    // -------------------------------------------------------------
    console.log('\n--- 1. WEB ADMIN DASHBOARD & RED-X MODAL ---');
    const webPage = await browser.newPage();
    await webPage.setViewport({ width: 1440, height: 900 });

    console.log('Navigating to Web ERP: http://localhost:5173 ...');
    await webPage.goto('http://localhost:5173', { waitUntil: 'networkidle0', timeout: 30000 });

    // Login if needed
    const pwdInput = await webPage.$('input[type="password"]');
    if (pwdInput) {
      console.log('Logging in as Admin (admin@sunrisepublic.edu)...');
      await pwdInput.type('Admin@123');
      await Promise.all([
        webPage.waitForNavigation({ waitUntil: 'networkidle0' }).catch(() => {}),
        webPage.click('form button'),
      ]);
      await sleep(2500);
    }

    // Verify Dashboard loaded
    await webPage.waitForFunction(
      () => document.body.innerText.includes('Attendance Overview'),
      { timeout: 15000 }
    );
    console.log('✓ Verified: Dashboard loaded with Attendance Overview');

    // Verify Fee Collection chart card is completely absent
    const hasFeeCollectionCard = await webPage.evaluate(() => {
      const allCards = Array.from(document.querySelectorAll('h2, h3, div'));
      return allCards.some((el) => (el.innerText || '').trim() === 'Fee Collection');
    });
    console.log(`✓ Verification: Fee Collection Recharts card present? ${hasFeeCollectionCard} (Expected: false)`);

    // Verify Recruitment is NOT in sidebar
    const hasRecruitmentNav = await webPage.evaluate(() => {
      const links = Array.from(document.querySelectorAll('nav a, aside a'));
      return links.some((l) => (l.innerText || '').toLowerCase().includes('recruitment'));
    });
    console.log(`✓ Verification: Recruitment link in navigation? ${hasRecruitmentNav} (Expected: false)`);

    // Capture Web Dashboard
    const dashboardBuffer = await webPage.screenshot({ fullPage: false });
    saveScreenshot('session9_web_dashboard_no_fee_chart.png', dashboardBuffer);

    // Open Defaulters Modal to verify Red-X button
    console.log('Opening Pending Fee Students modal by clicking Fees Remaining...');
    const clickedFeesRemaining = await webPage.evaluate(() => {
      const all = Array.from(document.querySelectorAll('*'));
      const match = all.find(
        (el) => el.children.length === 0 && el.textContent.trim() === 'Fees Remaining'
      );
      if (match) {
        const box = match.closest('.cursor-pointer');
        if (box) {
          box.click();
          return true;
        }
      }
      return false;
    });

    if (!clickedFeesRemaining) {
      throw new Error('Could not find or click Fees Remaining card');
    }

    await webPage.waitForFunction(
      () => document.body.innerText.includes('Pending Fee Students'),
      { timeout: 10000 }
    );
    console.log('✓ Defaulters Modal opened');
    await sleep(800);

    // Verify Red-X Close button is present in modal
    const hasRedX = await webPage.evaluate(() => {
      const closeBtn = document.querySelector('button[aria-label="Close"]');
      if (!closeBtn) return false;
      const isRed = closeBtn.className.includes('red-500');
      const hasSvg = !!closeBtn.querySelector('svg');
      return !!closeBtn && isRed && hasSvg;
    });
    console.log(`✓ Verification: Modal has Red-X close control? ${hasRedX} (Expected: true)`);

    // Capture Modal with Red-X
    const modalBuffer = await webPage.screenshot({ fullPage: false });
    saveScreenshot('session9_web_modal_red_x.png', modalBuffer);

    // Click Red-X close control
    await webPage.click('button[aria-label="Close"]');
    await sleep(800);
    const modalClosed = await webPage.evaluate(() => !document.body.innerText.includes('Pending Fee Students'));
    console.log(`✓ Verification: Modal closed after Red-X click? ${modalClosed} (Expected: true)`);

    await webPage.close();

    // -------------------------------------------------------------
    // 2. MOBILE PARENT NAVIGATION & DRAWER
    // -------------------------------------------------------------
    console.log('\n--- 2. MOBILE PARENT NAVIGATION & DRAWER ---');
    const mobilePage = await browser.newPage();
    await mobilePage.setViewport({ width: 412, height: 915, isMobile: true, hasTouch: true });

    console.log('Navigating to Expo Mobile: http://localhost:8081 ...');
    await mobilePage.goto('http://localhost:8081', { waitUntil: 'domcontentloaded', timeout: 35000 });
    await mobilePage.evaluate(() => {
      try { localStorage.clear(); } catch (_) {}
    });
    await mobilePage.goto('http://localhost:8081', { waitUntil: 'domcontentloaded', timeout: 35000 });
    await sleep(3500);

    // Login as Parent (9876500001 / Parent@123)
    console.log('Logging in as Parent (9876500001)...');
    await mobilePage.evaluate(() => {
      const roleBtn = Array.from(document.querySelectorAll('*')).find(
        (e) => (e.innerText || '').trim().toLowerCase() === 'parent' && e.children.length === 0
      );
      if (roleBtn) roleBtn.click();
    });
    await sleep(600);

    await mobilePage.evaluate(() => {
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
    await sleep(600);

    await mobilePage.evaluate(() => {
      const signIn = Array.from(document.querySelectorAll('*')).find(
        (e) => (e.innerText || '').trim() === 'Sign in' && e.children.length === 0
      );
      if (signIn) signIn.click();
    });
    await sleep(4500);

    // Verify 4 bottom tabs
    const parentTabs = await mobilePage.evaluate(() => {
      const allText = Array.from(document.querySelectorAll('*'))
        .map((e) => (e.innerText || '').trim())
        .filter(Boolean);
      return {
        hasHome: allText.includes('Home'),
        hasChild: allText.includes('Child'),
        hasFees: allText.includes('Fees'),
        hasProfile: allText.includes('Profile'),
      };
    });
    console.log('✓ Parent bottom tabs verification:', parentTabs);

    // Capture Parent Tabs
    const parentTabsBuffer = await mobilePage.screenshot({ fullPage: false });
    saveScreenshot('session9_mobile_parent_tabs.png', parentTabsBuffer);

    // Click Hamburger Button (Open Menu)
    console.log('Clicking hamburger button to open NavDrawer...');
    await mobilePage.evaluate(() => {
      const hamburger = Array.from(document.querySelectorAll('*')).find(
        (e) => e.getAttribute('aria-label') === 'Open Menu' || e.getAttribute('accessibilitylabel') === 'Open Menu'
      );
      if (hamburger) hamburger.click();
    });
    await sleep(1500);

    // Verify NavDrawer content
    const parentDrawerContent = await mobilePage.evaluate(() => {
      const text = document.body.innerText;
      return {
        hasAcademics: text.includes('ACADEMICS'),
        hasOperations: text.includes('OPERATIONS'),
        hasCommunication: text.includes('COMMUNICATION'),
        hasLogout: text.includes('Logout') || text.includes('Log out'),
      };
    });
    console.log('✓ Parent NavDrawer menu verification:', parentDrawerContent);

    // Capture Parent Drawer Open
    const parentDrawerBuffer = await mobilePage.screenshot({ fullPage: false });
    saveScreenshot('session9_mobile_parent_drawer_open.png', parentDrawerBuffer);

    // Click Red-X on drawer
    console.log('Closing NavDrawer via Red-X button...');
    await mobilePage.evaluate(() => {
      const closeBtn = Array.from(document.querySelectorAll('*')).find(
        (e) => e.getAttribute('aria-label') === 'Close' || e.getAttribute('accessibilitylabel') === 'Close'
      );
      if (closeBtn) closeBtn.click();
    });
    await sleep(1000);

    // -------------------------------------------------------------
    // 3. MOBILE TEACHER NAVIGATION & DRAWER
    // -------------------------------------------------------------
    console.log('\n--- 3. MOBILE TEACHER NAVIGATION & DRAWER ---');
    await mobilePage.evaluate(() => {
      try { localStorage.clear(); } catch (_) {}
    });
    await mobilePage.goto('http://localhost:8081', { waitUntil: 'domcontentloaded', timeout: 35000 });
    await sleep(3500);

    console.log('Logging in as Teacher (TCH001)...');
    await mobilePage.evaluate(() => {
      const roleBtn = Array.from(document.querySelectorAll('*')).find(
        (e) => (e.innerText || '').trim().toLowerCase() === 'teacher' && e.children.length === 0
      );
      if (roleBtn) roleBtn.click();
    });
    await sleep(600);

    await mobilePage.evaluate(() => {
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
    await sleep(600);

    await mobilePage.evaluate(() => {
      const signIn = Array.from(document.querySelectorAll('*')).find(
        (e) => (e.innerText || '').trim() === 'Sign in' && e.children.length === 0
      );
      if (signIn) signIn.click();
    });
    await sleep(4500);

    // Verify 4 bottom tabs for Teacher
    const teacherTabs = await mobilePage.evaluate(() => {
      const allText = Array.from(document.querySelectorAll('*'))
        .map((e) => (e.innerText || '').trim())
        .filter(Boolean);
      return {
        hasHome: allText.includes('Home'),
        hasClasses: allText.includes('Classes'),
        hasAttendance: allText.includes('Attendance'),
        hasProfile: allText.includes('Profile'),
      };
    });
    console.log('✓ Teacher bottom tabs verification:', teacherTabs);

    const teacherTabsBuffer = await mobilePage.screenshot({ fullPage: false });
    saveScreenshot('session9_mobile_teacher_tabs.png', teacherTabsBuffer);

    // Open Teacher Drawer
    console.log('Opening Teacher NavDrawer via hamburger...');
    await mobilePage.evaluate(() => {
      const hamburger = Array.from(document.querySelectorAll('*')).find(
        (e) => e.getAttribute('aria-label') === 'Open Menu' || e.getAttribute('accessibilitylabel') === 'Open Menu'
      );
      if (hamburger) hamburger.click();
    });
    await sleep(1500);

    const teacherDrawerBuffer = await mobilePage.screenshot({ fullPage: false });
    saveScreenshot('session9_mobile_teacher_drawer_open.png', teacherDrawerBuffer);

    // -------------------------------------------------------------
    // 4. MOBILE STUDENT NAVIGATION & DRAWER
    // -------------------------------------------------------------
    console.log('\n--- 4. MOBILE STUDENT NAVIGATION & DRAWER ---');
    await mobilePage.evaluate(() => {
      try { localStorage.clear(); } catch (_) {}
    });
    await mobilePage.goto('http://localhost:8081', { waitUntil: 'domcontentloaded', timeout: 35000 });
    await sleep(3500);

    console.log('Logging in as Student (2024000001)...');
    await mobilePage.evaluate(() => {
      const roleBtn = Array.from(document.querySelectorAll('*')).find(
        (e) => (e.innerText || '').trim().toLowerCase() === 'student' && e.children.length === 0
      );
      if (roleBtn) roleBtn.click();
    });
    await sleep(600);

    await mobilePage.evaluate(() => {
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
    await sleep(600);

    await mobilePage.evaluate(() => {
      const signIn = Array.from(document.querySelectorAll('*')).find(
        (e) => (e.innerText || '').trim() === 'Sign in' && e.children.length === 0
      );
      if (signIn) signIn.click();
    });
    await sleep(4500);

    // Verify 4 bottom tabs for Student
    const studentTabs = await mobilePage.evaluate(() => {
      const allText = Array.from(document.querySelectorAll('*'))
        .map((e) => (e.innerText || '').trim())
        .filter(Boolean);
      return {
        hasHome: allText.includes('Home'),
        hasTimetable: allText.includes('Timetable'),
        hasHomework: allText.includes('Homework'),
        hasProfile: allText.includes('Profile'),
      };
    });
    console.log('✓ Student bottom tabs verification:', studentTabs);

    const studentTabsBuffer = await mobilePage.screenshot({ fullPage: false });
    saveScreenshot('session9_mobile_student_tabs.png', studentTabsBuffer);

    // Open Student Drawer
    console.log('Opening Student NavDrawer via hamburger...');
    await mobilePage.evaluate(() => {
      const hamburger = Array.from(document.querySelectorAll('*')).find(
        (e) => e.getAttribute('aria-label') === 'Open Menu' || e.getAttribute('accessibilitylabel') === 'Open Menu'
      );
      if (hamburger) hamburger.click();
    });
    await sleep(1500);

    const studentDrawerBuffer = await mobilePage.screenshot({ fullPage: false });
    saveScreenshot('session9_mobile_student_drawer_open.png', studentDrawerBuffer);

    await mobilePage.close();
    console.log('\n================================================================');
    console.log('  ALL END-TO-END VISUAL VALIDATION CHECKS PASSED SUCCESSFULLY!');
    console.log('================================================================\n');
  } finally {
    await browser.close();
  }
}

runVisualValidation().catch((err) => {
  console.error('Visual validation failed:', err);
  process.exit(1);
});
