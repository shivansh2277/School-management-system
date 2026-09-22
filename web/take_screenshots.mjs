import puppeteer from 'puppeteer-core';
import path from 'path';
import fs from 'fs';

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const SCREENSHOT_DIR = path.resolve('..', 'docs', 'screenshots');
const ARTIFACT_DIR = 'C:\\Users\\SHIVANSH\\.gemini\\antigravity\\brain\\1b17fef1-50bc-497d-8705-4bc777e19f3c';

if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

function copyToArtifacts(filename) {
  const src = path.join(SCREENSHOT_DIR, filename);
  const dest = path.join(ARTIFACT_DIR, filename);
  if (fs.existsSync(src)) {
    fs.copyFileSync(src, dest);
    console.log(`Copied ${filename} to artifacts dir`);
  }
}

async function run() {
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--window-size=1440,900'],
  });

  try {
    // ----------------------------------------------------
    // 1. Admin login & screens
    // ----------------------------------------------------
    const adminCtx = await browser.createBrowserContext();
    const adminPage = await adminCtx.newPage();
    await adminPage.setViewport({ width: 1440, height: 900 });

    await adminPage.goto('http://localhost:5173/#/login', { waitUntil: 'networkidle0' });
    await adminPage.waitForSelector('input[type="password"]');

    await adminPage.evaluate(() => {
      const emailInput = document.querySelector('input:not([type="password"])');
      const pwdInput = document.querySelector('input[type="password"]');
      const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
      setter.call(emailInput, 'admin@sunrisepublic.edu');
      emailInput.dispatchEvent(new Event('input', { bubbles: true }));
      setter.call(pwdInput, 'Admin@123');
      pwdInput.dispatchEvent(new Event('input', { bubbles: true }));
    });
    await adminPage.click('form button');
    await adminPage.waitForFunction(() => window.location.hash.includes('/dashboard'), { timeout: 10000 });
    await new Promise(r => setTimeout(r, 2000));

    // Admin Dashboard Screenshot
    await adminPage.screenshot({
      path: path.join(SCREENSHOT_DIR, 'admin_dashboard.png'),
      fullPage: false,
    });
    copyToArtifacts('admin_dashboard.png');

    await adminPage.screenshot({
      path: path.join(SCREENSHOT_DIR, 'admin_dashboard_attendance_overview.png'),
      fullPage: true,
    });
    copyToArtifacts('admin_dashboard_attendance_overview.png');

    // Admin Sidebar links
    const adminSidebar = await adminPage.$$eval('aside nav a, aside a', els =>
      els.map(el => ({ text: el.innerText.trim(), href: el.getAttribute('href') })).filter(l => l.text)
    );
    console.log('\n=== ADMIN SIDEBAR LINKS ===\n', adminSidebar.map(s => s.text));

    // Admin Admission Dashboard page
    await adminPage.goto('http://localhost:5173/#/admission', { waitUntil: 'networkidle0' });
    await new Promise(r => setTimeout(r, 2000));
    await adminPage.screenshot({
      path: path.join(SCREENSHOT_DIR, 'admin_admission_dashboard.png'),
      fullPage: false,
    });
    copyToArtifacts('admin_admission_dashboard.png');

    // Admin tries to access operational admission: /admission/enquiries
    await adminPage.goto('http://localhost:5173/#/admission/enquiries', { waitUntil: 'networkidle0' });
    await new Promise(r => setTimeout(r, 2000));
    await adminPage.screenshot({
      path: path.join(SCREENSHOT_DIR, 'admin_blocked_admission_enquiries.png'),
      fullPage: false,
    });
    copyToArtifacts('admin_blocked_admission_enquiries.png');

    await adminCtx.close();

    // ----------------------------------------------------
    // 2. Receptionist login & screens
    // ----------------------------------------------------
    const recCtx = await browser.createBrowserContext();
    const recPage = await recCtx.newPage();
    await recPage.setViewport({ width: 1440, height: 900 });

    await recPage.goto('http://localhost:5173/#/login', { waitUntil: 'networkidle0' });
    await recPage.waitForSelector('input[type="password"]');

    await recPage.evaluate(() => {
      const emailInput = document.querySelector('input:not([type="password"])');
      const pwdInput = document.querySelector('input[type="password"]');
      const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
      setter.call(emailInput, 'receptionist@sunrisepublic.edu');
      emailInput.dispatchEvent(new Event('input', { bubbles: true }));
      setter.call(pwdInput, 'Admin@123');
      pwdInput.dispatchEvent(new Event('input', { bubbles: true }));
    });
    await recPage.click('form button');
    await recPage.waitForFunction(() => window.location.hash.includes('/admission/enquiries'), { timeout: 10000 });
    await new Promise(r => setTimeout(r, 2000));

    // Receptionist Landing (Enquiries) Screenshot
    await recPage.screenshot({
      path: path.join(SCREENSHOT_DIR, 'receptionist_admission_enquiries.png'),
      fullPage: false,
    });
    copyToArtifacts('receptionist_admission_enquiries.png');

    const recSidebar = await recPage.$$eval('aside nav a, aside a', els =>
      els.map(el => ({ text: el.innerText.trim(), href: el.getAttribute('href') })).filter(l => l.text)
    );
    console.log('\n=== RECEPTIONIST SIDEBAR LINKS ===\n', recSidebar.map(s => s.text));

    // Receptionist tries to access Admission Overview: /admission
    await recPage.goto('http://localhost:5173/#/admission', { waitUntil: 'networkidle0' });
    await new Promise(r => setTimeout(r, 2000));
    await recPage.screenshot({
      path: path.join(SCREENSHOT_DIR, 'receptionist_blocked_admission_dashboard.png'),
      fullPage: false,
    });
    copyToArtifacts('receptionist_blocked_admission_dashboard.png');

    // Receptionist tries to access non-admission: /students
    await recPage.goto('http://localhost:5173/#/students', { waitUntil: 'networkidle0' });
    await new Promise(r => setTimeout(r, 2000));
    await recPage.screenshot({
      path: path.join(SCREENSHOT_DIR, 'receptionist_blocked_students.png'),
      fullPage: false,
    });
    copyToArtifacts('receptionist_blocked_students.png');

    await recCtx.close();
  } finally {
    await browser.close();
  }
}

run();
