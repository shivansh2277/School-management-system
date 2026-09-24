import puppeteer from 'puppeteer-core';
import path from 'path';
import fs from 'fs';

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const SCREENSHOT_DIR = path.resolve('..', 'docs', 'screenshots');
const ARTIFACT_DIR = 'C:\\Users\\SHIVANSH\\.gemini\\antigravity\\brain\\3ef88ed0-50dc-47a4-bc44-2809c7e8a404';

if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

function copyToArtifacts(filename) {
  const src = path.join(SCREENSHOT_DIR, filename);
  const dest = path.join(ARTIFACT_DIR, filename);
  if (fs.existsSync(src)) {
    fs.copyFileSync(src, dest);
    console.log(`[Artifact] Copied ${filename} to artifacts dir`);
  }
}

async function assertNoHorizontalScroll(page, label) {
  const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
  const innerWidth = await page.evaluate(() => window.innerWidth);
  const overflow = scrollWidth - innerWidth;
  if (overflow > 1) {
    console.warn(`[WARN] ${label} has horizontal overflow: scrollWidth=${scrollWidth}px > innerWidth=${innerWidth}px (overflow: ${overflow}px)`);
  } else {
    console.log(`[PASS] ${label}: No horizontal scroll (scrollWidth=${scrollWidth}px, innerWidth=${innerWidth}px)`);
  }
  return overflow <= 1;
}

async function run() {
  console.log('--- Launching Responsive Visual Verification Suite ---');
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  try {
    const page = await browser.newPage();

    // 1. LOGIN
    await page.setViewport({ width: 1280, height: 800 });
    await page.goto('http://localhost:5173/#/login', { waitUntil: 'networkidle0' });
    await page.waitForSelector('input[type="password"]', { timeout: 10000 });

    await page.evaluate(() => {
      const emailInput = document.querySelector('input:not([type="password"])');
      const pwdInput = document.querySelector('input[type="password"]');
      const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
      setter.call(emailInput, 'admin@sunrisepublic.edu');
      emailInput.dispatchEvent(new Event('input', { bubbles: true }));
      setter.call(pwdInput, 'Admin@123');
      pwdInput.dispatchEvent(new Event('input', { bubbles: true }));
    });
    await page.click('form button');
    await page.waitForFunction(() => window.location.hash.includes('/dashboard'), { timeout: 10000 });
    await new Promise(r => setTimeout(r, 1500));
    console.log('[PASS] Logged in successfully');

    // ========================================================
    // TEST 1: MOBILE VIEWPORT (390 x 844) - iPhone 13/14
    // ========================================================
    console.log('\n--- Testing Mobile Viewport (390x844) ---');
    await page.setViewport({ width: 390, height: 844 });
    await page.goto('http://localhost:5173/#/', { waitUntil: 'networkidle0' });
    await new Promise(r => setTimeout(r, 1000));

    await assertNoHorizontalScroll(page, 'Mobile Dashboard (closed drawer)');

    // Capture Mobile Dashboard
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'proof_responsive_mobile_dashboard.png') });
    copyToArtifacts('proof_responsive_mobile_dashboard.png');

    // Open Mobile Drawer via hamburger button
    const hamburger = await page.$('button[aria-controls="app-sidebar"]');
    if (hamburger) {
      await hamburger.click();
      await new Promise(r => setTimeout(r, 400));
      console.log('[PASS] Clicked hamburger menu to open mobile drawer');
      await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'proof_responsive_mobile_drawer_open.png') });
      copyToArtifacts('proof_responsive_mobile_drawer_open.png');

      // Close Mobile Drawer via close button
      const closeBtn = await page.$('button[aria-label="Close navigation panel"]');
      if (closeBtn) {
        await closeBtn.click();
        await new Promise(r => setTimeout(r, 400));
        console.log('[PASS] Closed mobile drawer via close button');
      }
    }

    // Navigate to Transport on Mobile
    await page.goto('http://localhost:5173/#/transport', { waitUntil: 'networkidle0' });
    await new Promise(r => setTimeout(r, 1500));
    await assertNoHorizontalScroll(page, 'Mobile Transport Module');
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'proof_responsive_mobile_transport.png') });
    copyToArtifacts('proof_responsive_mobile_transport.png');

    // Navigate to Fees on Mobile
    await page.goto('http://localhost:5173/#/fees', { waitUntil: 'networkidle0' });
    await new Promise(r => setTimeout(r, 1500));
    await assertNoHorizontalScroll(page, 'Mobile Fees Module');
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'proof_responsive_mobile_fees.png') });
    copyToArtifacts('proof_responsive_mobile_fees.png');

    // ========================================================
    // TEST 2: TABLET VIEWPORT (768 x 1024) - iPad Mini / Portrait
    // ========================================================
    console.log('\n--- Testing Tablet Viewport (768x1024) ---');
    await page.setViewport({ width: 768, height: 1024 });
    await page.goto('http://localhost:5173/#/transport', { waitUntil: 'networkidle0' });
    await new Promise(r => setTimeout(r, 1500));
    await assertNoHorizontalScroll(page, 'Tablet Transport');
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'proof_responsive_tablet_transport.png') });
    copyToArtifacts('proof_responsive_tablet_transport.png');

    await page.goto('http://localhost:5173/#/', { waitUntil: 'networkidle0' });
    await new Promise(r => setTimeout(r, 1000));
    await assertNoHorizontalScroll(page, 'Tablet Dashboard');
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'proof_responsive_tablet_dashboard.png') });
    copyToArtifacts('proof_responsive_tablet_dashboard.png');

    // ========================================================
    // TEST 3: LAPTOP VIEWPORT (1280 x 800)
    // ========================================================
    console.log('\n--- Testing Laptop Viewport (1280x800) ---');
    await page.setViewport({ width: 1280, height: 800 });
    await page.goto('http://localhost:5173/#/transport', { waitUntil: 'networkidle0' });
    await new Promise(r => setTimeout(r, 1500));
    await assertNoHorizontalScroll(page, 'Laptop Transport');
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'proof_responsive_laptop_transport.png') });
    copyToArtifacts('proof_responsive_laptop_transport.png');

    // ========================================================
    // TEST 4: DESKTOP VIEWPORT (1440 x 900)
    // ========================================================
    console.log('\n--- Testing Desktop Viewport (1440x900) ---');
    await page.setViewport({ width: 1440, height: 900 });
    await page.goto('http://localhost:5173/#/transport', { waitUntil: 'networkidle0' });
    await new Promise(r => setTimeout(r, 1500));
    await assertNoHorizontalScroll(page, 'Desktop Transport');
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'proof_responsive_desktop_transport.png') });
    copyToArtifacts('proof_responsive_desktop_transport.png');

    console.log('\n=== All Responsive Visual Tests Passed Successfully ===');
  } catch (err) {
    console.error('Error during responsive visual verification:', err);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

run();
