import puppeteer from 'puppeteer-core';
import path from 'path';
import fs from 'fs';

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const SCREENSHOT_DIR = path.resolve('..', 'docs', 'screenshots', 'session21');
const ARTIFACT_DIR = 'C:\\Users\\SHIVANSH\\.gemini\\antigravity\\brain\\dacf39af-d91c-4745-83f9-4c6a76c383d8';
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
  console.log('=== VISUAL VERIFICATION OF 9 PUBLIC WEBSITE PAGES ACROSS DESKTOP & MOBILE ===\n');

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--window-size=1440,900'],
  });

  try {
    // =========================================================================
    // PART 1: DESKTOP VIEWS (1440x900)
    // =========================================================================
    console.log('--- PART 1: DESKTOP VIEWS (1440x900) ---');
    const desktopPage = await browser.newPage();
    await desktopPage.setViewport({ width: 1440, height: 900 });

    // 1. Home Page (/)
    console.log('1. Capturing Desktop Home Page (/) ...');
    await desktopPage.goto(`${WEB_BASE}/#/`, { waitUntil: 'networkidle0' });
    await sleep(1500);
    saveScreenshot('session21_01_desktop_home.png', await desktopPage.screenshot({ fullPage: false }));

    // 2. About Page (/about)
    console.log('2. Capturing Desktop About Page (/about) ...');
    await desktopPage.goto(`${WEB_BASE}/#/about`, { waitUntil: 'networkidle0' });
    await sleep(1200);
    saveScreenshot('session21_02_desktop_about.png', await desktopPage.screenshot({ fullPage: false }));

    // 3. Academics Page (/academics)
    console.log('3. Capturing Desktop Academics Page (/academics) ...');
    await desktopPage.goto(`${WEB_BASE}/#/academics`, { waitUntil: 'networkidle0' });
    await sleep(1200);
    saveScreenshot('session21_03_desktop_academics.png', await desktopPage.screenshot({ fullPage: false }));

    // 4. Admissions Page (/admissions)
    console.log('4. Capturing Desktop Admissions Page (/admissions) ...');
    await desktopPage.goto(`${WEB_BASE}/#/admissions`, { waitUntil: 'networkidle0' });
    await sleep(1200);
    saveScreenshot('session21_04_desktop_admissions.png', await desktopPage.screenshot({ fullPage: false }));

    // 5. Facilities Page (/facilities)
    console.log('5. Capturing Desktop Campus Facilities Page (/facilities) ...');
    await desktopPage.goto(`${WEB_BASE}/#/facilities`, { waitUntil: 'networkidle0' });
    await sleep(1200);
    saveScreenshot('session21_05_desktop_facilities.png', await desktopPage.screenshot({ fullPage: false }));

    // 6. School Life Page (/school-life)
    console.log('6. Capturing Desktop School Life Page (/school-life) ...');
    await desktopPage.goto(`${WEB_BASE}/#/school-life`, { waitUntil: 'networkidle0' });
    await sleep(1200);
    saveScreenshot('session21_06_desktop_school_life.png', await desktopPage.screenshot({ fullPage: false }));

    // 7. Events Page (/events)
    console.log('7. Capturing Desktop Events Page (/events) ...');
    await desktopPage.goto(`${WEB_BASE}/#/events`, { waitUntil: 'networkidle0' });
    await sleep(1200);
    saveScreenshot('session21_07_desktop_events.png', await desktopPage.screenshot({ fullPage: false }));

    // 8. Gallery Page (/gallery)
    console.log('8. Capturing Desktop Gallery Page (/gallery) ...');
    await desktopPage.goto(`${WEB_BASE}/#/gallery`, { waitUntil: 'networkidle0' });
    await sleep(1200);
    saveScreenshot('session21_08_desktop_gallery.png', await desktopPage.screenshot({ fullPage: false }));

    // 9. Contact Page (/contact)
    console.log('9. Capturing Desktop Contact Page (/contact) ...');
    await desktopPage.goto(`${WEB_BASE}/#/contact`, { waitUntil: 'networkidle0' });
    await sleep(1200);
    saveScreenshot('session21_09_desktop_contact.png', await desktopPage.screenshot({ fullPage: false }));

    // 10. Gallery Lightbox Modal
    console.log('10. Capturing Gallery Lightbox Modal ...');
    await desktopPage.goto(`${WEB_BASE}/#/gallery`, { waitUntil: 'networkidle0' });
    await sleep(1000);
    // Click first gallery item
    const galleryCard = await desktopPage.$('div[role="dialog"]');
    if (!galleryCard) {
      await desktopPage.evaluate(() => {
        const cards = document.querySelectorAll('div.group.cursor-pointer');
        if (cards.length > 0) cards[0].click();
      });
      await sleep(600);
    }
    saveScreenshot('session21_10_desktop_gallery_lightbox.png', await desktopPage.screenshot({ fullPage: false }));

    // 11. Contact Page Submitted State
    console.log('11. Capturing Contact Page Interactive Enquiry Form Submission ...');
    await desktopPage.goto(`${WEB_BASE}/#/contact`, { waitUntil: 'networkidle0' });
    await sleep(1000);
    await desktopPage.evaluate(() => {
      const inputs = document.querySelectorAll('input');
      const textarea = document.querySelector('textarea');
      const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
      const textSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;

      if (inputs[0]) {
        setter.call(inputs[0], 'Dr. Alok Srivastava');
        inputs[0].dispatchEvent(new Event('input', { bubbles: true }));
      }
      if (inputs[1]) {
        setter.call(inputs[1], 'alok.srivastava@example.com');
        inputs[1].dispatchEvent(new Event('input', { bubbles: true }));
      }
      if (inputs[2]) {
        setter.call(inputs[2], '+91 98765 43210');
        inputs[2].dispatchEvent(new Event('input', { bubbles: true }));
      }
      if (inputs[3]) {
        setter.call(inputs[3], 'Campus Tour & Admission Query');
        inputs[3].dispatchEvent(new Event('input', { bubbles: true }));
      }
      if (textarea) {
        textSetter.call(textarea, 'We would like to schedule a campus tour for Class 9 admission in 2026-27.');
        textarea.dispatchEvent(new Event('input', { bubbles: true }));
      }
    });
    // Submit form
    await desktopPage.evaluate(() => {
      const form = document.querySelector('form');
      if (form) {
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) submitBtn.click();
      }
    });
    await sleep(800);
    saveScreenshot('session21_11_desktop_contact_submitted.png', await desktopPage.screenshot({ fullPage: false }));

    await desktopPage.close();

    // =========================================================================
    // PART 2: MOBILE VIEWS (390x844 - iPhone 14)
    // =========================================================================
    console.log('\n--- PART 2: MOBILE VIEWS (390x844) ---');
    const mobilePage = await browser.newPage();
    await mobilePage.setViewport({ width: 390, height: 844, isMobile: true, hasTouch: true });

    // 12. Mobile Home Page
    console.log('12. Capturing Mobile Home Page ...');
    await mobilePage.goto(`${WEB_BASE}/#/`, { waitUntil: 'networkidle0' });
    await sleep(1200);
    saveScreenshot('session21_12_mobile_home.png', await mobilePage.screenshot({ fullPage: false }));

    // 13. Mobile Drawer Open
    console.log('13. Capturing Mobile Drawer Open (9 links + ERP CTA) ...');
    await mobilePage.evaluate(() => {
      const btn = document.querySelector('button[aria-label="Open menu"]');
      if (btn) btn.click();
    });
    await sleep(600);
    saveScreenshot('session21_13_mobile_navbar_drawer_open.png', await mobilePage.screenshot({ fullPage: false }));

    // 14. Mobile Admissions Page
    console.log('14. Capturing Mobile Admissions Page ...');
    await mobilePage.goto(`${WEB_BASE}/#/admissions`, { waitUntil: 'networkidle0' });
    await sleep(1200);
    saveScreenshot('session21_14_mobile_admissions.png', await mobilePage.screenshot({ fullPage: false }));

    // 15. Mobile School Life Page
    console.log('15. Capturing Mobile School Life Page ...');
    await mobilePage.goto(`${WEB_BASE}/#/school-life`, { waitUntil: 'networkidle0' });
    await sleep(1200);
    saveScreenshot('session21_15_mobile_school_life.png', await mobilePage.screenshot({ fullPage: false }));

    // 16. Mobile Events Page
    console.log('16. Capturing Mobile Events Page ...');
    await mobilePage.goto(`${WEB_BASE}/#/events`, { waitUntil: 'networkidle0' });
    await sleep(1200);
    saveScreenshot('session21_16_mobile_events.png', await mobilePage.screenshot({ fullPage: false }));

    // 17. Mobile Contact Page
    console.log('17. Capturing Mobile Contact Page ...');
    await mobilePage.goto(`${WEB_BASE}/#/contact`, { waitUntil: 'networkidle0' });
    await sleep(1200);
    saveScreenshot('session21_17_mobile_contact.png', await mobilePage.screenshot({ fullPage: false }));

    await mobilePage.close();

    console.log('\n=== ALL 17 VISUAL PROOFS SUCCESSFULLY CAPTURED ===');
  } catch (err) {
    console.error('Error during visual verification:', err);
    process.exitCode = 1;
  } finally {
    await browser.close();
  }
}

run();
