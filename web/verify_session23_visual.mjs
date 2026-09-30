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
  console.log('=== VISUAL VERIFICATION ACROSS DESKTOP, TABLET & MOBILE ===\n');

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--window-size=1440,900'],
  });

  try {
    // =========================================================================
    // PART 1: DESKTOP (1440x900)
    // =========================================================================
    console.log('--- PART 1: DESKTOP (1440x900) ---');
    const desktopPage = await browser.newPage();
    await desktopPage.setViewport({ width: 1440, height: 900 });

    // 1. Home Page top hero
    console.log('1. Capturing Desktop Home Hero & Navbar ...');
    await desktopPage.goto(`${WEB_BASE}/#/`, { waitUntil: 'networkidle0' });
    await sleep(1500);
    saveScreenshot('01_desktop_home_hero.png', await desktopPage.screenshot({ fullPage: false }));

    // 2. Home Page 4 Feature Cards & Principal Quote
    console.log('2. Capturing Desktop Home 4 Feature Cards & Principal ...');
    await desktopPage.evaluate(() => window.scrollBy(0, 750));
    await sleep(800);
    saveScreenshot('02_desktop_home_features_principal.png', await desktopPage.screenshot({ fullPage: false }));

    // 3. Admission Enquiry Modal
    console.log('3. Capturing Admission Enquiry Modal ...');
    await desktopPage.evaluate(() => {
      window.scrollTo(0, 0);
      const btns = Array.from(document.querySelectorAll('button'));
      const enquiryBtn = btns.find(b => b.textContent?.includes('Admission Enquiry'));
      if (enquiryBtn) enquiryBtn.click();
    });
    await sleep(800);
    saveScreenshot('03_desktop_admission_enquiry_modal.png', await desktopPage.screenshot({ fullPage: false }));

    // Close modal
    await desktopPage.evaluate(() => {
      const closeBtn = document.querySelector('button[aria-label="Close modal"]');
      if (closeBtn) closeBtn.click();
    });
    await sleep(400);

    // 4. About Page - Founder & History
    console.log('4. Capturing Desktop About Page (Founder Section) ...');
    await desktopPage.goto(`${WEB_BASE}/#/about`, { waitUntil: 'networkidle0' });
    await sleep(1200);
    saveScreenshot('04_desktop_about_overview.png', await desktopPage.screenshot({ fullPage: false }));

    await desktopPage.evaluate(() => window.scrollBy(0, 650));
    await sleep(600);
    saveScreenshot('05_desktop_about_founder_section.png', await desktopPage.screenshot({ fullPage: false }));

    // 5. School Life Page with merged Photo Gallery
    console.log('5. Capturing Desktop School Life Page ...');
    await desktopPage.goto(`${WEB_BASE}/#/school-life`, { waitUntil: 'networkidle0' });
    await sleep(1200);
    saveScreenshot('06_desktop_school_life_houses.png', await desktopPage.screenshot({ fullPage: false }));

    // Scroll to bottom gallery section
    await desktopPage.evaluate(() => {
      const gal = document.getElementById('gallery');
      if (gal) gal.scrollIntoView({ behavior: 'instant' });
    });
    await sleep(800);
    saveScreenshot('07_desktop_school_life_merged_gallery.png', await desktopPage.screenshot({ fullPage: false }));

    // 6. News & Announcements Page
    console.log('6. Capturing Desktop Announcements Catalog ...');
    await desktopPage.goto(`${WEB_BASE}/#/announcements`, { waitUntil: 'networkidle0' });
    await sleep(1200);
    saveScreenshot('08_desktop_announcements_catalog.png', await desktopPage.screenshot({ fullPage: false }));

    await desktopPage.close();

    // =========================================================================
    // PART 2: TABLET (768x1024 - iPad)
    // =========================================================================
    console.log('\n--- PART 2: TABLET (768x1024) ---');
    const tabletPage = await browser.newPage();
    await tabletPage.setViewport({ width: 768, height: 1024 });

    console.log('7. Capturing Tablet Home Page ...');
    await tabletPage.goto(`${WEB_BASE}/#/`, { waitUntil: 'networkidle0' });
    await sleep(1200);
    saveScreenshot('09_tablet_home.png', await tabletPage.screenshot({ fullPage: false }));

    console.log('8. Capturing Tablet About Page ...');
    await tabletPage.goto(`${WEB_BASE}/#/about`, { waitUntil: 'networkidle0' });
    await sleep(1200);
    await tabletPage.evaluate(() => window.scrollBy(0, 500));
    await sleep(600);
    saveScreenshot('10_tablet_about_founder.png', await tabletPage.screenshot({ fullPage: false }));

    await tabletPage.close();

    // =========================================================================
    // PART 3: MOBILE (390x844 - iPhone 14)
    // =========================================================================
    console.log('\n--- PART 3: MOBILE (390x844) ---');
    const mobilePage = await browser.newPage();
    await mobilePage.setViewport({ width: 390, height: 844, isMobile: true, hasTouch: true });

    console.log('9. Capturing Mobile Home Page with Phone Dialer Link ...');
    await mobilePage.goto(`${WEB_BASE}/#/`, { waitUntil: 'networkidle0' });
    await sleep(1200);
    saveScreenshot('11_mobile_home.png', await mobilePage.screenshot({ fullPage: false }));

    console.log('10. Capturing Mobile Navigation Drawer Open ...');
    await mobilePage.evaluate(() => {
      const btn = document.querySelector('button[aria-label="Toggle Navigation Menu"]');
      if (btn) btn.click();
    });
    await sleep(600);
    saveScreenshot('12_mobile_navbar_drawer_open.png', await mobilePage.screenshot({ fullPage: false }));

    console.log('11. Capturing Mobile Admission Enquiry Modal ...');
    await mobilePage.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const enquireBtn = btns.find(b => b.textContent?.trim() === 'Admission Enquiry' || b.textContent?.trim() === 'Enquire');
      if (enquireBtn) enquireBtn.click();
    });
    await sleep(600);
    saveScreenshot('13_mobile_admission_enquiry_modal.png', await mobilePage.screenshot({ fullPage: false }));

    console.log('12. Capturing Mobile School Life & Gallery ...');
    await mobilePage.goto(`${WEB_BASE}/#/school-life`, { waitUntil: 'networkidle0' });
    await sleep(1200);
    await mobilePage.evaluate(() => {
      const gal = document.getElementById('gallery');
      if (gal) gal.scrollIntoView({ behavior: 'instant' });
    });
    await sleep(600);
    saveScreenshot('14_mobile_school_life_gallery.png', await mobilePage.screenshot({ fullPage: false }));

    await mobilePage.close();

    console.log('\n=== VISUAL VERIFICATION COMPLETE ===');
  } catch (err) {
    console.error('Error during visual verification:', err);
    process.exitCode = 1;
  } finally {
    await browser.close();
  }
}

run();
