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
  console.log('  VERIFY TRANSPORT UPGRADE: PLAN 1 & PLAN 2 VISUAL VERIFICATION');
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
      console.log(`  [PASS] ${label}`);
      passed++;
    } else {
      console.error(`  [FAIL] ${label}`);
      failed++;
    }
  }

  try {
    const page = await browser.newPage();
    await page.setViewport({ width: 1440, height: 900 });

    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        console.log('  [BROWSER CONSOLE ERROR]:', msg.text());
      }
    });
    page.on('pageerror', (err) => {
      console.error('  [PAGE RUNTIME ERROR]:', err.message);
    });

    console.log('[STEP 1] Login as Transport In-Charge (transport@sunrisepublic.edu)...');
    await performLogin(page, 'transport@sunrisepublic.edu', 'Admin@123');

    console.log('[STEP 2] Navigating to Transport Desk (/#/transport)...');
    await page.goto(`${BASE_URL}/#/transport`, { waitUntil: 'networkidle0', timeout: 30000 });
    await sleep(2000);

    // Verify header and elements
    const pageText = await page.evaluate(() => document.body.innerText);
    check('Transport & Fleet Management Desk heading rendered', pageText.includes('Transport & Fleet Management Desk'));
    check('Student Allocation Desk action button present', pageText.includes('Student Allocation Desk'));
    check('Distance Fee Slabs action button present', pageText.includes('Distance Fee Slabs'));
    check('+ Add Vehicle button present', pageText.includes('+ Add Vehicle'));
    check('+ New Route button present', pageText.includes('+ New Route'));
    check('Routes running stat card present', pageText.includes('Routes running'));
    check('Fleet capacity stat card present', pageText.includes('Fleet capacity'));
    check('Gomti Nagar route present', pageText.includes('Gomti Nagar'));
    check('Fleet vehicle UP32AB1234 present', pageText.includes('UP32AB1234'));

    const shot1 = await page.screenshot({ fullPage: true });
    saveScreenshot('proof_transport_upgrade_main_desk.png', shot1);

    // Step 3: Open Printable Route Manifest & Roster
    console.log('[STEP 3] Opening Printable Route Manifest & Roster modal...');
    await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const rosterBtn = btns.find(b => b.innerText.includes('Roster'));
      if (rosterBtn) rosterBtn.click();
    });
    await sleep(2500);

    const rosterText = await page.evaluate(() => document.body.innerText);
    check('Roster header "SUNRISE PUBLIC SCHOOL" displayed', rosterText.includes('SUNRISE PUBLIC SCHOOL'));
    check('Roster subtitle "Daily Transport Manifest & Student Route Roster" displayed', rosterText.toUpperCase().includes('DAILY TRANSPORT MANIFEST & STUDENT ROUTE ROSTER'));
    check('Driver and Attendant details displayed on Roster', rosterText.includes('Driver') && rosterText.includes('Attendant'));
    check('Authorized Pickup Escorts or standard parent pickup displayed', rosterText.includes('Emergency Contact') || rosterText.includes('Authorized Pickup Escorts'));

    const shot2 = await page.screenshot({ fullPage: false });
    saveScreenshot('proof_transport_printable_roster.png', shot2);

    // Close Roster modal
    await page.evaluate(() => {
      const closeBtn = document.querySelector('button[aria-label="Close"]');
      if (closeBtn) closeBtn.click();
    });
    await sleep(1000);

    // Step 4: Open Crew & Vehicle Dispatch modal
    console.log('[STEP 4] Opening Crew & Vehicle Dispatch modal...');
    await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const crewBtn = btns.find(b => b.innerText.trim() === 'Crew');
      if (crewBtn) crewBtn.click();
    });
    await sleep(2000);

    const crewText = await page.evaluate(() => document.body.innerText);
    check('Crew Dispatch modal opened', crewText.includes('Crew & Vehicle Dispatch'));
    check('Designated Driver dropdown and compliance displayed', crewText.includes('Designated Driver'));
    check('Driving Licence / Police Verification indicators displayed', crewText.includes('Driving Licence') || crewText.includes('Police Verification'));

    const shot3 = await page.screenshot({ fullPage: false });
    saveScreenshot('proof_transport_crew_dispatch.png', shot3);

    // Close Crew modal
    await page.evaluate(() => {
      const closeBtn = document.querySelector('button[aria-label="Close"]');
      if (closeBtn) closeBtn.click();
    });
    await sleep(1000);

    // Step 5: Open Route & Stop Builder modal
    console.log('[STEP 5] Opening Route & Stop Builder modal...');
    await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const stopsBtn = btns.find(b => b.innerText.trim() === 'Stops');
      if (stopsBtn) stopsBtn.click();
    });
    await sleep(2000);

    const builderText = await page.evaluate(() => document.body.innerText);
    check('Route & Stop Builder modal opened', builderText.includes('Route & Stop Builder'));
    check('Address-First location instruction displayed', builderText.includes('Address-First'));
    check('Stops list with pickup and drop timings displayed', builderText.includes('Route Stops & Timings'));

    const shot4 = await page.screenshot({ fullPage: false });
    saveScreenshot('proof_transport_route_stop_builder.png', shot4);

    // Close Builder modal
    await page.evaluate(() => {
      const closeBtn = document.querySelector('button[aria-label="Close"]');
      if (closeBtn) closeBtn.click();
    });
    await sleep(1000);

    // Step 6: Open Student Transport Allocation Desk
    console.log('[STEP 6] Opening Student Transport Allocation Desk modal...');
    await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const deskBtn = btns.find(b => b.innerText.includes('Student Allocation Desk'));
      if (deskBtn) deskBtn.click();
    });
    await sleep(2000);

    const deskText = await page.evaluate(() => document.body.innerText);
    check('Student Transport Allocation & Dispatch Desk opened', deskText.includes('Student Transport Allocation & Dispatch Desk'));
    check('Admission Queue tab present', deskText.includes('Admission Queue'));
    check('Student Search & Allocation tab present', deskText.includes('Student Search & Allocation'));
    check('Active Riders & Transfers tab present', deskText.includes('Active Riders & Transfers'));

    const shot5 = await page.screenshot({ fullPage: false });
    saveScreenshot('proof_transport_student_allocation_desk.png', shot5);

    // Switch to Search tab
    await page.evaluate(() => {
      const tabs = Array.from(document.querySelectorAll('button'));
      const searchTab = tabs.find(b => b.innerText.includes('Student Search & Allocation'));
      if (searchTab) searchTab.click();
    });
    await sleep(1000);

    const shot5b = await page.screenshot({ fullPage: false });
    saveScreenshot('proof_transport_student_search_tab.png', shot5b);

    // Close Allocation Desk modal
    console.log('[STEP 6b] Closing Student Transport Allocation Desk modal...');
    await page.evaluate(() => {
      const closeBtns = Array.from(document.querySelectorAll('button[aria-label="Close"]'));
      console.log('Found close buttons:', closeBtns.length);
      if (closeBtns.length > 0) {
        closeBtns[closeBtns.length - 1].click();
      }
    });
    await sleep(1500);

    // Step 7: Open Fee Slabs modal
    console.log('[STEP 7] Opening Distance Fee Slabs modal...');
    const clickedSlabs = await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const slabsBtn = btns.find(b => b.innerText.includes('Distance Fee Slabs'));
      if (slabsBtn) {
        slabsBtn.click();
        return true;
      }
      return false;
    });
    console.log('Clicked Distance Fee Slabs button:', clickedSlabs);
    await sleep(2500);

    const slabsText = await page.evaluate(() => document.body.innerText);
    check('Distance Fee Slabs modal opened', slabsText.includes('Transport Distance Fee Slabs'));
    check('Slabs table with monthly fees rendered', slabsText.includes('0-5 km') || slabsText.includes('Monthly Fee'));

    const shot6 = await page.screenshot({ fullPage: false });
    saveScreenshot('proof_transport_fee_slabs.png', shot6);

    // Close Slabs modal
    await page.evaluate(() => {
      const closeBtn = document.querySelector('button[aria-label="Close"]');
      if (closeBtn) closeBtn.click();
    });
    await sleep(1000);

    console.log('\n================================================================');
    console.log(`  VERIFICATION COMPLETE: ${passed} PASSED, ${failed} FAILED`);
    console.log('================================================================');
  } finally {
    await browser.close();
  }
}

run().catch((err) => {
  console.error('Test execution failed:', err);
  process.exit(1);
});
