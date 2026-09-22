import puppeteer from 'puppeteer-core';
import fs from 'fs';
import path from 'path';

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
  console.log('Starting headless browser verification with isolated browser contexts...');
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--window-size=1280,800'],
  });

  const operationalAdmissionSections = ['Enquiries', 'Applications', 'Merit & selection', 'Waitlist', 'Admission reports'];

  try {
    // -------------------------------------------------------------
    // Test 1: Receptionist Login & Strict Admission Isolation
    // -------------------------------------------------------------
    console.log('\n--- 1. Testing Receptionist Login (receptionist@sunrisepublic.edu) ---');
    const recContext = await browser.createBrowserContext();
    const recPage = await recContext.newPage();
    await recPage.setViewport({ width: 1280, height: 800 });

    await recPage.goto('http://localhost:5173/#/login', { waitUntil: 'networkidle0' });
    await recPage.waitForSelector('input[type="password"]');

    await recPage.evaluate(() => {
      const emailInput = document.querySelector('input:not([type="password"])');
      const pwdInput = document.querySelector('input[type="password"]');
      const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;

      nativeInputValueSetter.call(emailInput, 'receptionist@sunrisepublic.edu');
      emailInput.dispatchEvent(new Event('input', { bubbles: true }));

      nativeInputValueSetter.call(pwdInput, 'Admin@123');
      pwdInput.dispatchEvent(new Event('input', { bubbles: true }));
    });

    await recPage.click('form button');

    await recPage.waitForFunction(() => window.location.hash.includes('/admission/enquiries'), { timeout: 10000 });
    await new Promise(r => setTimeout(r, 1000));

    const recHash = await recPage.evaluate(() => window.location.hash);
    console.log('Receptionist landed Hash:', recHash);
    if (!recHash.includes('/admission/enquiries')) {
      throw new Error(`Expected Receptionist to land on /admission/enquiries, got: ${recHash}`);
    }

    // Extract sidebar navigation links
    const recSidebarLinks = await recPage.$$eval('aside nav a, aside a', els =>
      els.map(el => ({ text: el.innerText.trim(), href: el.getAttribute('href') })).filter(l => l.text)
    );
    console.log('Receptionist sidebar links:', recSidebarLinks.map(l => l.text));

    const recLinkTexts = recSidebarLinks.map(l => l.text);
    // Receptionist MUST have the 5 operational links
    for (const expected of operationalAdmissionSections) {
      if (!recLinkTexts.some(t => t.toLowerCase() === expected.toLowerCase())) {
        throw new Error(`Missing expected admission link for receptionist: ${expected}`);
      }
    }

    // Receptionist must NOT have Admission Dashboard
    if (recLinkTexts.some(t => t.toLowerCase().includes('admission dashboard'))) {
      throw new Error('Receptionist sidebar must NOT contain Admission dashboard!');
    }

    // Receptionist must NOT have any non-admission links
    const forbiddenForRec = ['Dashboard', 'Students', 'Staff', 'Classes', 'Attendance', 'Fees', 'Transport', 'Stock', 'Settings', 'Examinations', 'Reports library', 'Configuration'];
    for (const forbidden of forbiddenForRec) {
      if (recLinkTexts.some(t => t.trim().toLowerCase() === forbidden.toLowerCase())) {
        throw new Error(`Forbidden link appeared in receptionist sidebar: ${forbidden}`);
      }
    }
    console.log('✓ Receptionist sidebar contains ONLY the 5 operational admission links!');

    // Screenshot Receptionist enquiries
    const recScreenshotPath = path.join(SCREENSHOT_DIR, 'receptionist_admission_enquiries.png');
    await recPage.screenshot({ path: recScreenshotPath, fullPage: true });
    copyToArtifacts('receptionist_admission_enquiries.png');

    // Test URL Guarding: Directly attempt #/admission (Admission Dashboard)
    console.log('Testing Receptionist direct navigation to #/admission (Admission Dashboard)...');
    await recPage.goto('http://localhost:5173/#/admission', { waitUntil: 'networkidle0' });
    await new Promise(r => setTimeout(r, 1000));

    const pageContentRecAdmission = await recPage.content();
    if (!pageContentRecAdmission.includes('You do not have permission')) {
      throw new Error('Receptionist was NOT blocked from navigating to /admission!');
    }
    console.log('✓ Receptionist successfully blocked with "You do not have permission" on #/admission');
    const recBlockedAdmissionPath = path.join(SCREENSHOT_DIR, 'receptionist_blocked_admission_dashboard.png');
    await recPage.screenshot({ path: recBlockedAdmissionPath });
    copyToArtifacts('receptionist_blocked_admission_dashboard.png');

    // Test URL Guarding: Directly attempt #/students
    console.log('Testing Receptionist direct navigation to #/students...');
    await recPage.goto('http://localhost:5173/#/students', { waitUntil: 'networkidle0' });
    await new Promise(r => setTimeout(r, 1000));

    const pageContentRecStudents = await recPage.content();
    if (!pageContentRecStudents.includes('You do not have permission')) {
      throw new Error('Receptionist was NOT blocked from navigating to /students!');
    }
    console.log('✓ Receptionist successfully blocked with "You do not have permission" on #/students');
    const recBlockedStudentsPath = path.join(SCREENSHOT_DIR, 'receptionist_blocked_students.png');
    await recPage.screenshot({ path: recBlockedStudentsPath });
    copyToArtifacts('receptionist_blocked_students.png');

    await recContext.close();

    // -------------------------------------------------------------
    // Test 2: Admin Login & Admission Dashboard on Main Website
    // -------------------------------------------------------------
    console.log('\n--- 2. Testing Admin Login (admin@sunrisepublic.edu) ---');
    const adminContext = await browser.createBrowserContext();
    const adminPage = await adminContext.newPage();
    await adminPage.setViewport({ width: 1280, height: 800 });

    await adminPage.goto('http://localhost:5173/#/login', { waitUntil: 'networkidle0' });
    await adminPage.waitForSelector('input[type="password"]');

    await adminPage.evaluate(() => {
      const emailInput = document.querySelector('input:not([type="password"])');
      const pwdInput = document.querySelector('input[type="password"]');
      const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;

      nativeInputValueSetter.call(emailInput, 'admin@sunrisepublic.edu');
      emailInput.dispatchEvent(new Event('input', { bubbles: true }));

      nativeInputValueSetter.call(pwdInput, 'Admin@123');
      pwdInput.dispatchEvent(new Event('input', { bubbles: true }));
    });

    await adminPage.click('form button');

    await adminPage.waitForFunction(() => window.location.hash.includes('/dashboard'), { timeout: 10000 });
    await new Promise(r => setTimeout(r, 1000));

    const adminHash = await adminPage.evaluate(() => window.location.hash);
    console.log('Admin landed Hash:', adminHash);
    if (!adminHash.includes('/dashboard')) {
      throw new Error(`Expected Admin to land on #/dashboard, got: ${adminHash}`);
    }

    const adminSidebarLinks = await adminPage.$$eval('aside nav a, aside a', els =>
      els.map(el => ({ text: el.innerText.trim(), href: el.getAttribute('href') })).filter(l => l.text)
    );
    const adminLinkTexts = adminSidebarLinks.map(l => l.text);
    console.log('Admin sidebar link texts:', adminLinkTexts);

    // Admin MUST have "Admission dashboard"
    if (!adminLinkTexts.some(t => t.toLowerCase() === 'admission dashboard')) {
      throw new Error("Admin sidebar missing 'Admission dashboard'!");
    }
    console.log('✓ Admin sidebar contains Admission dashboard!');

    // Admin must NOT have any of the 5 operational admission links
    for (const operational of operationalAdmissionSections) {
      if (adminLinkTexts.some(t => t.toLowerCase() === operational.toLowerCase())) {
        throw new Error(`Admin sidebar must NOT contain operational admission link '${operational}'!`);
      }
    }
    console.log('✓ Admin sidebar contains ZERO operational front-desk admission links!');

    // Assert non-admission links exist
    const expectedAdminModules = ['Dashboard', 'Students', 'Classes', 'Fees', 'Settings'];
    for (const mod of expectedAdminModules) {
      if (!adminLinkTexts.some(t => t.toLowerCase().includes(mod.toLowerCase()))) {
        throw new Error(`Expected admin module missing: ${mod}`);
      }
    }
    console.log('✓ Admin retains all standard non-admission modules!');

    // Now test navigation to Admission Dashboard (/admission)
    console.log('Testing Admin navigation to Admission Dashboard (#/admission)...');
    await adminPage.goto('http://localhost:5173/#/admission', { waitUntil: 'networkidle0' });
    await new Promise(r => setTimeout(r, 1500));

    const pageContentAdmission = await adminPage.content();
    if (!pageContentAdmission.includes('Admission Season') && !pageContentAdmission.includes('Active Cycle') && !pageContentAdmission.includes('Class Seat Capacity')) {
      throw new Error('Admission Dashboard did not load properly for Admin!');
    }
    console.log('✓ Admin successfully loaded the Admission Dashboard (#/admission)!');

    const adminAdmissionPath = path.join(SCREENSHOT_DIR, 'admin_admission_dashboard.png');
    await adminPage.screenshot({ path: adminAdmissionPath, fullPage: true });
    copyToArtifacts('admin_admission_dashboard.png');

    // Test Admin URL Guarding: Directly attempt #/admission/enquiries
    console.log('Testing Admin direct navigation to #/admission/enquiries...');
    await adminPage.goto('http://localhost:5173/#/admission/enquiries', { waitUntil: 'networkidle0' });
    await new Promise(r => setTimeout(r, 1000));

    const pageContentAdminEnquiries = await adminPage.content();
    if (!pageContentAdminEnquiries.includes('You do not have permission')) {
      throw new Error('Admin was NOT blocked from navigating to /admission/enquiries!');
    }
    console.log('✓ Admin successfully blocked with "You do not have permission" on #/admission/enquiries');
    const adminBlockedEnquiriesPath = path.join(SCREENSHOT_DIR, 'admin_blocked_admission_enquiries.png');
    await adminPage.screenshot({ path: adminBlockedEnquiriesPath });
    copyToArtifacts('admin_blocked_admission_enquiries.png');

    await adminContext.close();

    console.log('\n======================================================');
    console.log('ALL BROWSER E2E VERIFICATIONS PASSED 100% CLEANLY!');
    console.log('======================================================');
  } catch (err) {
    console.error('Test execution failed:', err);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

run();
