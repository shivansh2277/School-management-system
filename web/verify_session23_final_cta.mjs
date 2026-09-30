import puppeteer from 'puppeteer-core';
import path from 'path';
import fs from 'fs';

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const SCREENSHOT_DIR = path.resolve('..', 'docs', 'screenshots', 'session23');
const ARTIFACT_DIR = 'C:\\Users\\SHIVANSH\\.gemini\\antigravity\\brain\\0da948cb-a6a9-4a9b-8134-9afe1207dd71';
const WEB_BASE = 'http://localhost:5173';

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
  console.log(`[CAPTURED] ${filename}`);
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function run() {
  console.log('=== VISUAL VERIFICATION: ERP LOGIN NAVBAR & ADMISSION SIDE CTA ===\n');

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
  });

  try {
    // =========================================================================
    // PART 1: DESKTOP (1440x900)
    // =========================================================================
    console.log('--- PART 1: DESKTOP (1440x900) ---');
    const desktopPage = await browser.newPage();
    await desktopPage.setViewport({ width: 1440, height: 900 });

    // 1. Home Page top hero showing ERP Login button in navbar & persistent Side CTA
    console.log('1. Capturing Desktop Home Hero with ERP Login & Side CTA ...');
    await desktopPage.goto(`${WEB_BASE}/#/`, { waitUntil: 'networkidle0' });
    await sleep(1500);
    saveScreenshot('01_desktop_home_hero.png', await desktopPage.screenshot({ fullPage: false }));

    // 2. Open Admission Enquiry Modal via the Persistent Side CTA
    console.log('2. Opening Admission Enquiry Modal via Side CTA ...');
    await desktopPage.evaluate(() => {
      const sideCta = document.querySelector('[data-testid="admission-side-cta-desktop"]');
      if (sideCta) sideCta.click();
    });
    await sleep(800);
    saveScreenshot('03_desktop_admission_enquiry_modal.png', await desktopPage.screenshot({ fullPage: false }));

    // Close modal
    await desktopPage.evaluate(() => {
      const closeBtn = document.querySelector('button[aria-label="Close modal"]');
      if (closeBtn) closeBtn.click();
    });
    await sleep(400);

    // 3. About Page showing persistent side CTA on informational pages
    console.log('3. Capturing Desktop About Page with Side CTA ...');
    await desktopPage.goto(`${WEB_BASE}/#/about`, { waitUntil: 'networkidle0' });
    await sleep(1200);
    saveScreenshot('04_desktop_about_overview.png', await desktopPage.screenshot({ fullPage: false }));

    // 4. Verify /apply workflow excludes side CTA and announcement strip
    console.log('4. Verifying /apply application workflow isolates from Side CTA & Announcement strip ...');
    await desktopPage.goto(`${WEB_BASE}/#/apply`, { waitUntil: 'networkidle0' });
    await sleep(1200);
    saveScreenshot('15_desktop_apply_workflow_no_cta.png', await desktopPage.screenshot({ fullPage: false }));

    await desktopPage.close();

    // =========================================================================
    // PART 2: TABLET (768x1024)
    // =========================================================================
    console.log('\n--- PART 2: TABLET (768x1024) ---');
    const tabletPage = await browser.newPage();
    await tabletPage.setViewport({ width: 768, height: 1024 });

    console.log('5. Capturing Tablet Home with ERP Login & Side CTA ...');
    await tabletPage.goto(`${WEB_BASE}/#/`, { waitUntil: 'networkidle0' });
    await sleep(1500);
    saveScreenshot('09_tablet_home.png', await tabletPage.screenshot({ fullPage: false }));

    await tabletPage.close();

    // =========================================================================
    // PART 3: MOBILE (390x844)
    // =========================================================================
    console.log('\n--- PART 3: MOBILE (390x844) ---');
    const mobilePage = await browser.newPage();
    await mobilePage.setViewport({ width: 390, height: 844, isMobile: true, hasTouch: true });

    // 6. Mobile Home with compact floating Admission Enquiry CTA and ERP Login button
    console.log('6. Capturing Mobile Home with ERP Login & Compact Floating CTA ...');
    await mobilePage.goto(`${WEB_BASE}/#/`, { waitUntil: 'networkidle0' });
    await sleep(1500);
    saveScreenshot('11_mobile_home.png', await mobilePage.screenshot({ fullPage: false }));

    // 7. Mobile Navbar Drawer Open showing ERP Login & Apply Portal
    console.log('7. Capturing Mobile Navigation Drawer with ERP Login ...');
    await mobilePage.evaluate(() => {
      const toggleBtn = document.querySelector('button[aria-label="Toggle Navigation Menu"]');
      if (toggleBtn) toggleBtn.click();
    });
    await sleep(600);
    saveScreenshot('12_mobile_navbar_drawer_open.png', await mobilePage.screenshot({ fullPage: false }));

    // Close drawer
    await mobilePage.evaluate(() => {
      const toggleBtn = document.querySelector('button[aria-label="Toggle Navigation Menu"]');
      if (toggleBtn) toggleBtn.click();
    });
    await sleep(400);

    // 8. Open Admission Enquiry Modal via Mobile Compact CTA
    console.log('8. Opening Admission Enquiry Modal via Mobile Compact CTA ...');
    await mobilePage.evaluate(() => {
      const mobileCta = document.querySelector('[data-testid="admission-side-cta-mobile"]');
      if (mobileCta) mobileCta.click();
    });
    await sleep(800);
    saveScreenshot('13_mobile_admission_enquiry_modal.png', await mobilePage.screenshot({ fullPage: false }));

    await mobilePage.close();

    console.log('\n=== VISUAL VERIFICATION COMPLETE! ALL SCREENSHOTS SAVED ===');
  } catch (err) {
    console.error('Visual verification error:', err);
    process.exitCode = 1;
  } finally {
    await browser.close();
  }
}

run();
