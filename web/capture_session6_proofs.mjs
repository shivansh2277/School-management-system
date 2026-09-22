import puppeteer from 'puppeteer-core';
import path from 'path';
import fs from 'fs';

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const SCREENSHOT_DIR = path.resolve('..', 'docs', 'screenshots');
const ARTIFACT_DIR = 'C:\\Users\\SHIVANSH\\.gemini\\antigravity\\brain\\fa280aa8-4aa8-497e-bd25-0330bac3f340';

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

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function loginMobile(page, roleName, loginId, password) {
  console.log(`\n--- Logging into Mobile as ${roleName} (${loginId}) ---`);
  await page.goto('http://localhost:8081', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.evaluate(() => localStorage.clear());
  await page.goto('http://localhost:8081', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await sleep(2500);

  // Click role tab
  await page.evaluate((r) => {
    const el = Array.from(document.querySelectorAll('*')).find(
      (e) => (e.innerText || '').trim().toLowerCase() === r.toLowerCase() && e.children.length === 0
    );
    if (el) el.click();
  }, roleName);
  await sleep(800);

  // Enter loginId and password
  await page.evaluate((lid, pwd) => {
    const inputs = document.querySelectorAll('input');
    if (inputs.length >= 2) {
      const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
      setter.call(inputs[0], lid);
      inputs[0].dispatchEvent(new Event('input', { bubbles: true }));
      inputs[0].dispatchEvent(new Event('change', { bubbles: true }));
      setter.call(inputs[1], pwd);
      inputs[1].dispatchEvent(new Event('input', { bubbles: true }));
      inputs[1].dispatchEvent(new Event('change', { bubbles: true }));
    }
  }, loginId, password);
  await sleep(800);

  // Click Sign in
  await page.evaluate(() => {
    const el = Array.from(document.querySelectorAll('*')).find(
      (e) => (e.innerText || '').trim() === 'Sign in' && e.children.length === 0
    );
    if (el) el.click();
  });
  await sleep(4000);
}

async function captureScreen(page, filename, desc) {
  const filePath = path.join(SCREENSHOT_DIR, filename);
  await page.screenshot({ path: filePath, fullPage: false });
  copyToArtifacts(filename);
  console.log(`[Captured] ${desc} -> ${filename}`);
}

async function main() {
  console.log('=== Capturing Session 6 Mobile Visual Proofs ===');
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--window-size=412,915'],
    defaultViewport: { width: 412, height: 915 },
  });

  try {
    const page = await browser.newPage();
    page.on('dialog', async (dialog) => {
      console.log(`[Dialog] ${dialog.message()}`);
      await dialog.accept();
    });

    // ==========================================
    // 1. TEACHER WORKFLOWS (TCH001 / Teacher@123)
    // ==========================================
    await loginMobile(page, 'teacher', 'TCH001', 'Teacher@123');

    // 1.1 Teacher Attendance Roll-Call
    console.log('Navigating to Teacher Attendance...');
    await page.goto('http://localhost:8081/(teacher)/attendance', { waitUntil: 'domcontentloaded', timeout: 20000 });
    await sleep(3500);
    await captureScreen(page, 'mobile_teacher_attendance.png', 'Teacher Classroom Roll-Call Screen');

    // 1.2 Teacher Homework Manager & Grading
    console.log('Navigating to Teacher Homework...');
    await page.goto('http://localhost:8081/(teacher)/homework', { waitUntil: 'domcontentloaded', timeout: 20000 });
    await sleep(3500);
    await captureScreen(page, 'mobile_teacher_homework.png', 'Teacher Homework Manager & Submissions');

    // 1.3 Teacher Marks Entry Keypad
    console.log('Navigating to Teacher Marks / Results...');
    await page.goto('http://localhost:8081/(teacher)/results', { waitUntil: 'domcontentloaded', timeout: 20000 });
    await sleep(3500);
    await captureScreen(page, 'mobile_teacher_results.png', 'Teacher Mobile Marks Entry Keypad');

    // ==========================================
    // 2. PARENT WORKFLOWS (9876500001 / Parent@123)
    // ==========================================
    await loginMobile(page, 'parent', '9876500001', 'Parent@123');

    // 2.1 Parent Attendance & Medical Leave
    console.log('Navigating to Parent Attendance...');
    await page.goto('http://localhost:8081/(parent)/attendance', { waitUntil: 'domcontentloaded', timeout: 20000 });
    await sleep(3500);
    await captureScreen(page, 'mobile_parent_attendance.png', 'Parent Attendance Calendar & Leave Request');

    // 2.2 Parent Fee Ledger & Receipt
    console.log('Navigating to Parent Fees...');
    await page.goto('http://localhost:8081/(parent)/fees', { waitUntil: 'domcontentloaded', timeout: 20000 });
    await sleep(3500);
    await captureScreen(page, 'mobile_parent_fees.png', 'Parent Fee Ledger & 2-Copy Receipt');

    // 2.3 Parent Results & Report Card Download
    console.log('Navigating to Parent Results...');
    await page.goto('http://localhost:8081/(parent)/results', { waitUntil: 'domcontentloaded', timeout: 20000 });
    await sleep(3500);
    await captureScreen(page, 'mobile_parent_results.png', 'Parent CBSE Report Card & Dues Gate');

    // ==========================================
    // 3. STUDENT WORKFLOWS (2024000001 / Student@123)
    // ==========================================
    await loginMobile(page, 'student', '2024000001', 'Student@123');

    // 3.1 Student Timetable
    console.log('Navigating to Student Timetable...');
    await page.goto('http://localhost:8081/(student)/timetable', { waitUntil: 'domcontentloaded', timeout: 20000 });
    await sleep(3500);
    await captureScreen(page, 'mobile_student_timetable.png', 'Student Weekly Timetable Grid');

    // 3.2 Student Homework Turn-in
    console.log('Navigating to Student Homework...');
    await page.goto('http://localhost:8081/(student)/homework', { waitUntil: 'domcontentloaded', timeout: 20000 });
    await sleep(3500);
    await captureScreen(page, 'mobile_student_homework.png', 'Student Digital Homework Turn-in Drawer');

    console.log('\n=== All 8 Visual Proofs Successfully Captured ===');
  } catch (err) {
    console.error('Error capturing proofs:', err);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

main();
