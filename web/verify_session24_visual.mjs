import puppeteer from 'puppeteer-core';
import path from 'path';
import fs from 'fs';

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const SCREENSHOT_DIR = path.resolve('..', 'docs', 'screenshots', 'session24');
const ARTIFACT_DIR = 'C:\\Users\\SHIVANSH\\.gemini\\antigravity\\brain\\6f889fba-503e-46ca-b3b6-b0b91d35c2f9';
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
  console.log('=== SESSION 24 VISUAL VERIFICATION: ADMISSION, APAAR, ID CARDS, LIBRARY, CERTIFICATES, HOLIDAYS ===\n');

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--window-size=1440,900'],
  });

  try {
    const page = await browser.newPage();
    await page.setViewport({ width: 1440, height: 900 });

    // Enable request interception for mock API responses
    await page.setRequestInterception(true);

    page.on('request', (req) => {
      const url = req.url();
      const method = req.method();

      if (url.includes('/api/auth/me') || url.includes('/auth/me')) {
        return req.respond({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            user: { id: 1, role: 'admin', full_name: 'Administrator', login_id: 'admin@sunrisepublic.edu' },
            permissions: [
              'students.read', 'students.write', 'students.id_card',
              'admission.document.override', 'admission.read',
              'library.read', 'library.manage',
              'certificates.read', 'certificates.request', 'certificates.issue', 'certificates.manage_templates',
              'attendance.holiday.manage', 'attendance.holiday.override', 'attendance.read', 'attendance.record',
            ],
            roles: ['super_admin'],
            school_code: 'SPS',
            school_name: 'Sunrise Public School',
            academic_year: '2025-26',
            modules: ['academics', 'students', 'administration', 'library', 'certificates', 'attendance', 'admission'],
          }),
        });
      }

      if (url.includes('/public/SPS/admission/open')) {
        return req.respond({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            school: { code: 'SPS', name: 'Sunrise Public School', city: 'Lucknow' },
            cycle: {
              name: 'Academic Session 2025-26 Admissions',
              academic_year: '2025-26',
              starts_on: '2025-01-01',
              ends_on: '2025-04-30',
              application_fee: 500,
            },
            classes: [
              { class_name: 'Nursery', total_seats: 40, age_on: '2025-04-01', min_age_years: 3, max_age_years: 4, required_documents: ['birth_certificate', 'address_proof', 'photo'] },
              { class_name: 'LKG', total_seats: 40, age_on: '2025-04-01', min_age_years: 4, max_age_years: 5, required_documents: ['birth_certificate', 'address_proof', 'photo'] },
              { class_name: 'UKG', total_seats: 40, age_on: '2025-04-01', min_age_years: 5, max_age_years: 6, required_documents: ['birth_certificate', 'address_proof', 'photo'] },
              { class_name: 'Class 1', total_seats: 60, age_on: '2025-04-01', min_age_years: 6, max_age_years: 7, required_documents: ['address_proof', 'photo'] },
              { class_name: 'Class 6', total_seats: 60, age_on: '2025-04-01', min_age_years: 11, max_age_years: 12, required_documents: ['address_proof', 'photo'] },
            ],
          }),
        });
      }

      if (url.includes('/admin/admission/applications/drafts/lookup')) {
        return req.respond({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 42,
            reference_code: 'DFT-42',
            status: 'draft',
            first_name: 'Ananya',
            last_name: 'Sen',
            class_applying_for: 'Nursery',
            date_of_birth: '2021-08-15',
            age_years: 3.6,
            documents_checklist: [
              { code: 'birth_certificate', name: 'Birth Certificate', is_mandatory: true, is_uploaded: false, has_override: false },
              { code: 'address_proof', name: 'Address Proof', is_mandatory: true, is_uploaded: true, has_override: false },
              { code: 'apaar', name: 'APAAR ID / Consent Exception', is_mandatory: true, is_uploaded: false, has_override: false },
            ],
            overrides: [],
          }),
        });
      }

      if (url.includes('/admin/admission/applications/42/document-overrides') && method === 'POST') {
        return req.respond({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({ id: 101, status: 'authorized', message: 'Exception authorized' }),
        });
      }

      if (url.includes('/admin/students') && !url.includes('/id-card')) {
        return req.respond({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: [
              {
                id: 1,
                admission_no: 'SPS/2024/001',
                roll_no: '101',
                full_name: 'Aarav Sharma',
                gender: 'male',
                date_of_birth: '2010-05-14',
                class_label: '10-A',
                class_section_id: 1,
                status: 'enrolled',
                apaar_id: '987654321098',
                apaar_consent: true,
                apaar_consent_at: '2024-04-01T10:00:00Z',
                guardians: [{ full_name: 'Ramesh Sharma', relation: 'Father', mobile: '9876543210', is_primary: true }],
              },
              {
                id: 2,
                admission_no: 'SPS/2024/002',
                roll_no: '102',
                full_name: 'Diya Patel',
                gender: 'female',
                date_of_birth: '2010-08-22',
                class_label: '10-A',
                class_section_id: 1,
                status: 'enrolled',
                apaar_id: null,
                apaar_consent: true,
                apaar_consent_at: '2024-04-02T11:30:00Z',
                guardians: [{ full_name: 'Sanjay Patel', relation: 'Father', mobile: '9876543211', is_primary: true }],
              },
            ],
            total: 2,
          }),
        });
      }

      if (url.includes('/classes')) {
        return req.respond({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            { id: 1, class_name: '10', section_name: 'A', label: '10-A', student_count: 35 },
            { id: 2, class_name: '10', section_name: 'B', label: '10-B', student_count: 34 },
          ]),
        });
      }

      if (url.includes('/admin/library/books')) {
        return req.respond({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: [
              { id: 1, isbn: '978-0143335405', title: 'Malgudi Days', author: 'R. K. Narayan', publisher: 'Indian Thought', category: 'Fiction', total_copies: 3, available_copies: 2, shelf_location: 'Shelf A1', copies: [{ id: 1, accession_no: 'ACC-1001', barcode: 'BC-ACC-1001', status: 'issued' }, { id: 2, accession_no: 'ACC-1002', barcode: 'BC-ACC-1002', status: 'available' }, { id: 3, accession_no: 'ACC-1003', barcode: 'BC-ACC-1003', status: 'available' }] },
              { id: 2, isbn: '978-8172234980', title: 'Wings of Fire', author: 'A. P. J. Abdul Kalam', publisher: 'Universities Press', category: 'Biography', total_copies: 3, available_copies: 3, shelf_location: 'Shelf C3', copies: [{ id: 4, accession_no: 'ACC-1004', barcode: 'BC-ACC-1004', status: 'available' }, { id: 5, accession_no: 'ACC-1005', barcode: 'BC-ACC-1005', status: 'available' }, { id: 6, accession_no: 'ACC-1006', barcode: 'BC-ACC-1006', status: 'available' }] },
            ],
            total: 2,
          }),
        });
      }

      if (url.includes('/admin/library/borrowers/ENR-1')) {
        return req.respond({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            enrolment_id: 1,
            enrollment_code: 'ENR-1',
            student_id: 1,
            admission_no: 'SPS/2024/001',
            student_name: 'Aarav Sharma',
            class_label: '10-A',
            roll_no: '101',
            active_loans_count: 1,
            unpaid_fines: 0.0,
            is_eligible: true,
            ineligibility_reasons: [],
            active_loans: [
              { loan_id: 10, book_id: 1, book_title: 'Malgudi Days', barcode: 'BC-ACC-1001', issued_on: '2026-09-25', due_date: '2026-10-09', is_overdue: false },
            ],
          }),
        });
      }

      if (url.includes('/admin/certificates/templates')) {
        return req.respond({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            { id: 1, certificate_type: 'transfer_certificate', title: 'SCHOOL LEAVING / TRANSFER CERTIFICATE', header_text: 'Recognized & Affiliated to CBSE, New Delhi', body_template: 'This is to certify that the particulars furnished above have been verified from the official records and registers.', signatory_name: 'Dr. S. K. Sharma', signatory_title: 'Principal / Head of Institution', show_seal: true },
            { id: 2, certificate_type: 'bonafide_certificate', title: 'BONAFIDE CERTIFICATE', header_text: 'Recognized & Affiliated to CBSE, New Delhi', body_template: 'This is to certify that the student is a bonafide student of this institution studying in the class and session indicated above.', signatory_name: 'Dr. S. K. Sharma', signatory_title: 'Principal / Head of Institution', show_seal: true },
            { id: 3, certificate_type: 'character_certificate', title: 'CHARACTER CERTIFICATE', header_text: 'Recognized & Affiliated to CBSE, New Delhi', body_template: 'This is to certify that during the period of study, the student bore good moral character and exemplary conduct.', signatory_name: 'Dr. S. K. Sharma', signatory_title: 'Principal / Head of Institution', show_seal: true },
          ]),
        });
      }

      if (url.includes('/admin/certificates/requests') || (url.includes('/admin/certificates') && !url.includes('/templates'))) {
        return req.respond({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            { id: 1, certificate_type: 'transfer_certificate', student_name: 'Rohan Verma', admission_no: 'SPS/2023/045', class_name: 'Class 8', certificate_number: 'TC/2026/0001', status: 'requested', requested_by_name: 'Office Admin', reason: 'Parent relocation to Bengaluru', created_at: '2026-09-28T10:00:00Z' },
            { id: 2, certificate_type: 'bonafide_certificate', student_name: 'Aarav Sharma', admission_no: 'SPS/2024/001', class_name: '10-A', certificate_number: 'BC/2026/0012', status: 'approved', requested_by_name: 'Admin', reason: 'Passport application verification', created_at: '2026-09-29T14:30:00Z' },
            { id: 3, certificate_type: 'character_certificate', student_name: 'Pooja Iyer', admission_no: 'SPS/2022/012', class_name: 'Class 12', certificate_number: 'CC/2026/0008', status: 'issued', requested_by_name: 'Admin', reason: 'College admissions', created_at: '2026-09-20T09:15:00Z' },
          ]),
        });
      }

      if (url.includes('/admin/holidays')) {
        return req.respond({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            { id: 1, name: 'Mahatma Gandhi Jayanti', start_date: '2026-10-02', end_date: '2026-10-02', description: 'National Holiday observed school-wide', is_cancelled: false, scope: 'School-Wide', is_school_wide: true },
            { id: 2, name: 'Dussehra & Autumn Break', start_date: '2026-10-20', end_date: '2026-10-24', description: 'Autumn vacation for all classes', is_cancelled: false, scope: 'School-Wide', is_school_wide: true },
          ]),
        });
      }

      // Default continue
      req.continue();
    });

    // Helper to inject auth token
    const injectAuth = async () => {
      await page.evaluate(() => {
        localStorage.setItem('sunrise.token', 'mock_token_super_admin');
      });
    };

    // -------------------------------------------------------------------------
    // 1. PUBLIC ADMISSION PORTAL: Conditional Birth Cert & APAAR Section
    // -------------------------------------------------------------------------
    console.log('1. Capturing Public Online Admission Portal...');
    await page.goto(`${WEB_BASE}/#/apply`, { waitUntil: 'networkidle0' });
    await sleep(1500);

    // Capture Step 1 & Conditional Birth Certificate Badge
    saveScreenshot('01_public_admission_step1_birth_cert_badge.png', await page.screenshot({ fullPage: false }));

    // Scroll to APAAR ID section in step 1/wizard
    await page.evaluate(() => {
      const apaarHeading = Array.from(document.querySelectorAll('h3, h4, div')).find(el => el.textContent?.includes('APAAR ID (Automated Permanent Academic Account Registry)'));
      if (apaarHeading) apaarHeading.scrollIntoView({ behavior: 'instant' });
    });
    await sleep(600);
    saveScreenshot('02_public_admission_apaar_section.png', await page.screenshot({ fullPage: false }));

    // Click "Save Application Draft" button
    await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const draftBtn = btns.find(b => b.textContent?.includes('Save Application Draft') || b.textContent?.includes('Save Draft'));
      if (draftBtn) draftBtn.click();
    });
    await sleep(600);
    saveScreenshot('03_public_admission_save_draft_modal.png', await page.screenshot({ fullPage: false }));

    // Close draft modal
    await page.evaluate(() => {
      const closeBtn = document.querySelector('button[aria-label="Close modal"]') || Array.from(document.querySelectorAll('button')).find(b => b.textContent?.includes('Close'));
      if (closeBtn) closeBtn.click();
    });
    await sleep(400);

    // -------------------------------------------------------------------------
    // 2. ADMIN ADMISSION EXCEPTIONS SCREEN
    // -------------------------------------------------------------------------
    console.log('2. Capturing Admin Admission Document Exceptions...');
    await page.goto(`${WEB_BASE}/#/admin/admission-exceptions`, { waitUntil: 'networkidle0' });
    await injectAuth();
    await page.goto(`${WEB_BASE}/#/admin/admission-exceptions`, { waitUntil: 'networkidle0' });
    await sleep(1000);

    // Look up draft DFT-42
    await page.evaluate(() => {
      const input = document.querySelector('input[placeholder*="Enter Draft Ref"]');
      if (input) {
        const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        setter.call(input, 'DFT-42');
        input.dispatchEvent(new Event('input', { bubbles: true }));
      }
    });
    await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const lookupBtn = btns.find(b => b.textContent?.includes('Lookup Draft'));
      if (lookupBtn) lookupBtn.click();
    });
    await sleep(800);
    saveScreenshot('04_admin_admission_exception_lookup.png', await page.screenshot({ fullPage: false }));

    // -------------------------------------------------------------------------
    // 3. STUDENT PROFILE: APAAR ID & CR80 / BULK ID CARDS
    // -------------------------------------------------------------------------
    console.log('3. Capturing Student Profile & ID Cards...');
    await page.goto(`${WEB_BASE}/#/students`, { waitUntil: 'networkidle0' });
    await sleep(1200);

    // Click first student row to open profile
    await page.evaluate(() => {
      const row = document.querySelector('table tbody tr');
      if (row) row.click();
    });
    await sleep(800);
    saveScreenshot('05_student_profile_apaar_and_cr80_card.png', await page.screenshot({ fullPage: false }));

    // Open Bulk ID Cards modal
    await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const bulkBtn = btns.find(b => b.textContent?.includes('Bulk Print ID Cards'));
      if (bulkBtn) bulkBtn.click();
    });
    await sleep(600);
    saveScreenshot('06_bulk_id_cards_8up_modal.png', await page.screenshot({ fullPage: false }));

    // Close bulk modal
    await page.evaluate(() => {
      const closeBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent?.includes('Cancel') || b.textContent?.includes('Close'));
      if (closeBtn) closeBtn.click();
    });
    await sleep(400);

    // -------------------------------------------------------------------------
    // 4. UNIFIED LIBRARY MANAGEMENT
    // -------------------------------------------------------------------------
    console.log('4. Capturing Unified Library Management...');
    await page.goto(`${WEB_BASE}/#/library`, { waitUntil: 'networkidle0' });
    await sleep(1200);

    // Look up borrower ENR-1
    await page.evaluate(() => {
      const input = document.querySelector('input[placeholder*="ENR-"]');
      if (input) {
        const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        setter.call(input, 'ENR-1');
        input.dispatchEvent(new Event('input', { bubbles: true }));
      }
    });
    await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const btn = btns.find(b => b.textContent?.includes('Find Borrower'));
      if (btn) btn.click();
    });
    await sleep(800);
    saveScreenshot('07_library_circulation_desk.png', await page.screenshot({ fullPage: false }));

    // Switch to Books Catalogue tab
    await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const tab = btns.find(b => b.textContent?.includes('Books Catalogue'));
      if (tab) tab.click();
    });
    await sleep(800);
    saveScreenshot('08_library_books_catalogue.png', await page.screenshot({ fullPage: false }));

    // Open Add Book Modal
    await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const addBtn = btns.find(b => b.textContent?.includes('Add Book Title'));
      if (addBtn) addBtn.click();
    });
    await sleep(600);
    saveScreenshot('09_library_add_book_modal.png', await page.screenshot({ fullPage: false }));

    // Close Add Book modal
    await page.evaluate(() => {
      const closeBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent?.includes('Cancel'));
      if (closeBtn) closeBtn.click();
    });
    await sleep(400);

    // -------------------------------------------------------------------------
    // 5. ADMIN STUDENT CERTIFICATES
    // -------------------------------------------------------------------------
    console.log('5. Capturing Student Certificates Module...');
    await page.goto(`${WEB_BASE}/#/certificates`, { waitUntil: 'networkidle0' });
    await sleep(1200);
    saveScreenshot('10_certificates_requests_log.png', await page.screenshot({ fullPage: false }));

    // Open Request Certificate Modal
    await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const reqBtn = btns.find(b => b.textContent?.includes('Request Certificate'));
      if (reqBtn) reqBtn.click();
    });
    await sleep(600);
    saveScreenshot('11_certificates_request_modal_tc_warning.png', await page.screenshot({ fullPage: false }));

    // Close Request modal
    await page.evaluate(() => {
      const closeBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent?.includes('Cancel'));
      if (closeBtn) closeBtn.click();
    });
    await sleep(400);

    // Switch to Certificate Templates tab
    await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const tmplTab = btns.find(b => b.textContent?.includes('Certificate Templates'));
      if (tmplTab) tmplTab.click();
    });
    await sleep(800);
    saveScreenshot('12_certificates_templates_config.png', await page.screenshot({ fullPage: false }));

    // -------------------------------------------------------------------------
    // 6. HOLIDAY MANAGEMENT & ATTENDANCE BANNER
    // -------------------------------------------------------------------------
    console.log('6. Capturing Holiday Management & Attendance Banner...');
    await page.goto(`${WEB_BASE}/#/admin/holidays`, { waitUntil: 'networkidle0' });
    await sleep(1200);
    saveScreenshot('13_holiday_management_calendar.png', await page.screenshot({ fullPage: false }));

    // Check attendance screen with holiday banner
    await page.goto(`${WEB_BASE}/#/attendance`, { waitUntil: 'networkidle0' });
    await sleep(1200);
    saveScreenshot('14_attendance_declared_holiday_banner.png', await page.screenshot({ fullPage: false }));

    console.log('\n=== ALL 14 VISUAL ARTIFACTS CAPTURED SUCCESSFULLY ===');
  } catch (err) {
    console.error('Error during visual verification:', err);
    process.exitCode = 1;
  } finally {
    await browser.close();
  }
}

run();
