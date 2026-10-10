"""Generates the non-technical, human-friendly feature guide PDF:
Sunrise-ERP-Features-Operational-and-Planned.pdf

Target Audience: School Owner, Principal, Administrator, Trustee, or Auditor.
Format:
  - What You Can View (Screens, numbers, student cards, alerts)
  - What You Can Do (Actions, one-click exports, decisions, approvals)
  - Real School Workflow Context (In plain, non-jargon language)
"""
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
OUTPUT_HTML = os.path.join(REPO, "docs", "features-operational-and-planned.html")
OUTPUT_PDF = os.path.join(REPO, "docs", "Sunrise-ERP-Features-Operational-and-Planned.pdf")

HTML_CONTENT = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Sunrise School ERP — Non-Technical Feature Guide</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');

    @page {
      size: A4 portrait;
      margin: 11mm 13mm 13mm 13mm;
      @bottom-right {
        content: "Page " counter(page);
        font-family: 'Inter', sans-serif;
        font-size: 8pt;
        color: #94a3b8;
      }
    }

    * {
      box-sizing: border-box;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }

    body {
      font-family: 'Inter', sans-serif;
      font-size: 8.8pt;
      line-height: 1.48;
      color: #1e293b;
      background: #ffffff;
      margin: 0;
      padding: 0;
    }

    h1, h2, h3, h4 {
      font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Cover / Header Header */
    .header-banner {
      background: linear-gradient(135deg, #1e1b4b 0%, #312e81 60%, #4338ca 100%);
      color: #ffffff;
      padding: 18px 22px;
      border-radius: 12px;
      margin-bottom: 16px;
    }
    .header-banner h1 {
      margin: 0 0 4px 0;
      font-size: 18pt;
      font-weight: 800;
      letter-spacing: -0.5px;
    }
    .header-banner .tagline {
      font-size: 9.6pt;
      color: #c7d2fe;
      font-weight: 500;
      margin-bottom: 10px;
    }
    .header-meta-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-top: 1px solid rgba(255, 255, 255, 0.18);
      padding-top: 8px;
      font-size: 7.8pt;
      color: #e0e7ff;
    }

    /* Key Metrics Chips */
    .metrics-bar {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 9px;
      margin-bottom: 16px;
    }
    .metric-box {
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      padding: 9px 11px;
      text-align: left;
    }
    .metric-num {
      font-size: 14pt;
      font-weight: 800;
      color: #1e1b4b;
      font-family: 'Plus Jakarta Sans', sans-serif;
    }
    .metric-label {
      font-size: 7.6pt;
      color: #64748b;
      font-weight: 600;
      margin-top: 1px;
    }

    /* Section Headings */
    .section-title {
      font-size: 12pt;
      font-weight: 800;
      color: #0f172a;
      display: flex;
      align-items: center;
      gap: 8px;
      margin: 16px 0 9px 0;
      padding-bottom: 4px;
      border-bottom: 2px solid #e2e8f0;
      break-after: avoid;
    }
    .part-tag {
      font-size: 7.2pt;
      font-weight: 800;
      padding: 2px 7px;
      border-radius: 5px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .tag-live {
      background: #15803d;
      color: #ffffff;
    }
    .tag-planned {
      background: #b45309;
      color: #ffffff;
    }

    /* Module Feature Card */
    .feature-card {
      background: #ffffff;
      border: 1px solid #cbd5e1;
      border-radius: 8px;
      margin-bottom: 8px;
      break-inside: avoid;
      overflow: hidden;
    }
    .feature-card-header {
      background: #f1f5f9;
      border-bottom: 1px solid #e2e8f0;
      padding: 5px 10px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .feature-card-title {
      font-size: 9.2pt;
      font-weight: 700;
      color: #0f172a;
      margin: 0;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .screen-route {
      font-family: monospace;
      font-size: 7.6pt;
      background: #e2e8f0;
      color: #334155;
      padding: 1px 5px;
      border-radius: 4px;
    }
    .feature-card-body {
      padding: 6px 10px;
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
    }
    .col-view {
      border-right: 1px solid #f1f5f9;
      padding-right: 8px;
    }
    .sub-head {
      font-size: 7.3pt;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 3px;
      display: flex;
      align-items: center;
      gap: 5px;
    }
    .head-view { color: #2563eb; }
    .head-action { color: #059669; }

    ul.feature-list {
      margin: 0;
      padding-left: 13px;
      font-size: 8pt;
      color: #334155;
      line-height: 1.42;
    }
    ul.feature-list li {
      margin-bottom: 2px;
    }
    ul.feature-list li strong {
      color: #0f172a;
    }

    /* Planned Grid */
    .planned-table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 6px;
      font-size: 8.2pt;
      break-inside: avoid;
    }
    .planned-table th {
      background: #f8fafc;
      text-align: left;
      padding: 6px 9px;
      font-weight: 700;
      font-size: 7.6pt;
      text-transform: uppercase;
      color: #475569;
      border-top: 1px solid #cbd5e1;
      border-bottom: 1.5px solid #cbd5e1;
    }
    .planned-table td {
      padding: 6px 9px;
      border-bottom: 1px solid #e2e8f0;
      vertical-align: top;
    }
    .planned-table tr:nth-child(even) td {
      background: #fafafa;
    }
    .priority-badge {
      font-size: 6.8pt;
      font-weight: 700;
      padding: 2px 6px;
      border-radius: 4px;
      text-transform: uppercase;
    }
    .p-high { background: #fee2e2; color: #991b1b; }
    .p-med { background: #fef3c7; color: #92400e; }
    .p-v2 { background: #f1f5f9; color: #475569; }

    .summary-box {
      background: #eff6ff;
      border: 1px solid #bfdbfe;
      border-radius: 8px;
      padding: 9px 13px;
      margin-bottom: 14px;
      font-size: 8.5pt;
      color: #1e3a8a;
    }
    .page-break {
      break-after: page;
    }
  </style>
</head>
<body>

  <!-- BANNER -->
  <div class="header-banner">
    <h1>Sunrise Public School ERP</h1>
    <div class="tagline">Complete Non-Technical Feature Guide: What You Can View & What You Can Do</div>
    <div class="header-meta-row">
      <div><strong>School:</strong> Sunrise Public School (CBSE Affiliated, Lucknow)</div>
      <div><strong>Target Audience:</strong> School Owner, Principal, Administrator, Auditor</div>
      <div><strong>Verified as of:</strong> October 2026 (Live System State)</div>
    </div>
  </div>

  <!-- STATS -->
  <div class="metrics-bar">
    <div class="metric-box">
      <div class="metric-num">32+ Live Screens</div>
      <div class="metric-label">Website & Portal Features Working Today</div>
    </div>
    <div class="metric-box">
      <div class="metric-num">19 Academic Groups</div>
      <div class="metric-label">Nursery to Class 12 (Sci / Com / Hum)</div>
    </div>
    <div class="metric-box">
      <div class="metric-num">190 Active Students</div>
      <div class="metric-label">Enrolled with Permanent Lifetime IDs</div>
    </div>
    <div class="metric-box">
      <div class="metric-num">28 Staff (24 Teachers)</div>
      <div class="metric-label">All 19 Class Teachers Assigned</div>
    </div>
  </div>

  <div class="summary-box">
    <strong>How to read this document:</strong> This guide explains what the Sunrise Public School management system does in clear, everyday terms. For every section, it details <em>"What You Can View"</em> (the exact information, tables, and summaries shown on the screen) and <em>"What You Can Do"</em> (the tasks, approvals, exports, and actions you can perform).
  </div>

  <!-- PART 1: OPERATIONAL FEATURES -->
  <div class="section-title">
    <span class="part-tag tag-live">Part 1</span>
    Operational Features: Available on the Website Today
  </div>

  <!-- 1. DASHBOARD -->
  <div class="feature-card">
    <div class="feature-card-header">
      <div class="feature-card-title">1. Executive Dashboard &amp; Leadership Command Center</div>
      <span class="screen-route">/dashboard</span>
    </div>
    <div class="feature-card-body">
      <div class="col-view">
        <div class="sub-head head-view">👁 What You Can View</div>
        <ul class="feature-list">
          <li><strong>School Vital Signs:</strong> Live counts of Total Students (190), Active Teachers (24), Classrooms (19), and Total Realized Fees.</li>
          <li><strong>Fees Overview Card:</strong> Real-time split showing <em>Fees Collected</em> vs <em>Fees Remaining</em> with interactive drilldown modals.</li>
          <li><strong>Grievance Activity:</strong> Live counter chips showing Open, In Progress, and Resolved complaints from teachers and parents.</li>
          <li><strong>Quick Notice &amp; Holiday Board:</strong> Summary of upcoming official school holidays and recent circulars.</li>
        </ul>
      </div>
      <div>
        <div class="sub-head head-action">⚡ What You Can Do</div>
        <ul class="feature-list">
          <li><strong>Click "Fees Remaining":</strong> Instantly opens a complete roster of all students with pending fee dues.</li>
          <li><strong>Export Defaulters Report:</strong> Download a full 10-column spreadsheet report with one click, showing pending amounts and due dates.</li>
          <li><strong>Open Grievances:</strong> Click any complaint to read the full conversation thread between parents, teachers, and leadership.</li>
          <li><strong>Reply &amp; Assign:</strong> Write a response back to the parent/teacher, assign tickets to staff, and mark resolved.</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- 2. ADMISSION OVERVIEW & INTAKE -->
  <div class="feature-card">
    <div class="feature-card-header">
      <div class="feature-card-title">2. New Student Admissions &amp; Seat Intake Management</div>
      <span class="screen-route">/admission</span>
    </div>
    <div class="feature-card-body">
      <div class="col-view">
        <div class="sub-head head-view">👁 What You Can View</div>
        <ul class="feature-list">
          <li><strong>Class Seat Capacity:</strong> Approved seats, enrolled children, and remaining vacancies across all 19 sections (Nursery through Class 12).</li>
          <li><strong>Admission Funnel:</strong> Visual drop-off funnel showing lead movement from Inquiry &rarr; Application &rarr; Test &rarr; Offer &rarr; Final Enrolment.</li>
          <li><strong>Active Academic Cycle:</strong> Which session is currently accepting applications (2025-26 or 2026-27).</li>
        </ul>
      </div>
      <div>
        <div class="sub-head head-action">⚡ What You Can Do</div>
        <ul class="feature-list">
          <li><strong>Edit Class Capacities:</strong> Adjust maximum seat ceiling for any class as physical room availability permits.</li>
          <li><strong>Monitor Over-Enrolment:</strong> The system automatically blocks admitting more children than the physical seat cap allows.</li>
          <li><strong>Track Cycle Progress:</strong> Inspect conversion percentages to know which classes still have vacant seats.</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- 3. ENQUIRIES REGISTER -->
  <div class="feature-card">
    <div class="feature-card-header">
      <div class="feature-card-title">3. Walk-In, Phone &amp; Web Inquiry Register</div>
      <span class="screen-route">/admission/enquiries</span>
    </div>
    <div class="feature-card-body">
      <div class="col-view">
        <div class="sub-head head-view">👁 What You Can View</div>
        <ul class="feature-list">
          <li><strong>Inquiry Log:</strong> Chronological log of visiting parents, telephone queries, web submissions, student names, and desired class.</li>
          <li><strong>Follow-Up Notes:</strong> Detailed conversation history recorded by reception staff (e.g. "Parent called asking for fee structure").</li>
          <li><strong>Status Badges:</strong> Whether the inquiry is New, Contacted, Interested, Form Issued, Converted, or Closed.</li>
        </ul>
      </div>
      <div>
        <div class="sub-head head-action">⚡ What You Can Do</div>
        <ul class="feature-list">
          <li><strong>Log Inquiries in 30s:</strong> Receptionists can record parent phone numbers, source (walk-in, website, referral), and child interest.</li>
          <li><strong>Record Follow-Ups:</strong> Schedule call-back reminders and log staff notes directly onto the parent's file.</li>
          <li><strong>One-Click Conversion:</strong> Click "Convert to Application" to prefill the formal admission form without re-typing.</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- 4. APPLICANT DOSSIER -->
  <div class="feature-card">
    <div class="feature-card-header">
      <div class="feature-card-title">4. Complete 360° Applicant Dossier</div>
      <span class="screen-route">/admission/applications</span>
    </div>
    <div class="feature-card-body">
      <div class="col-view">
        <div class="sub-head head-view">👁 What You Can View</div>
        <ul class="feature-list">
          <li><strong>Applicant Profile (7 Tabs):</strong> Personal biodata, residential address, parent occupation, and previous school transfer details.</li>
          <li><strong>Document Checklist:</strong> Verified status of Birth Certificate, Aadhaar, Transfer Certificate, and Report Cards.</li>
          <li><strong>Medical &amp; Allergy Notes:</strong> Blood group, known allergies, medical emergency notes, and family physician contacts.</li>
          <li><strong>Sibling Links:</strong> Identifies elder siblings already studying in the school for fee concession eligibility.</li>
        </ul>
      </div>
      <div>
        <div class="sub-head head-action">⚡ What You Can Do</div>
        <ul class="feature-list">
          <li><strong>Verify Documents:</strong> Mark certificates as Verified or Incomplete with official auditor remarks.</li>
          <li><strong>Record Admission Test Scores:</strong> Enter written test and interview scorecards directly on candidate files.</li>
          <li><strong>Issue Admission Offers:</strong> Approve applications and generate official offer letters.</li>
          <li><strong>Convert to Enrolled Student:</strong> Once the admission fee is cleared, finalize enrollment to assign permanent Admission ID.</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- 5. ADMISSION DOCUMENT OVERRIDES QUEUE (NEW) -->
  <div class="feature-card">
    <div class="feature-card-header">
      <div class="feature-card-title">5. Admission Document Overrides &amp; Exceptions Queue</div>
      <span class="screen-route">/admin/admission-exceptions</span>
    </div>
    <div class="feature-card-body">
      <div class="col-view">
        <div class="sub-head head-view">👁 What You Can View</div>
        <ul class="feature-list">
          <li><strong>Automatic Pending Queue:</strong> When an applicant submits a document exception request online, it immediately surfaces here without manual search.</li>
          <li><strong>Request Details:</strong> Student name (e.g. Rahul Sharma), Application ID (APP-1024), requested document, applicant's reason, and submission time.</li>
          <li><strong>Audit Trail Table:</strong> Complete historical log of previously approved and rejected exception requests with reviewer identity and timestamps.</li>
        </ul>
      </div>
      <div>
        <div class="sub-head head-action">⚡ What You Can Do</div>
        <ul class="feature-list">
          <li><strong>Review Request:</strong> Click "Review" to inspect full applicant details and supporting justification in a focused modal.</li>
          <li><strong>One-Click Approval:</strong> Click "Approve" to immediately grant the document exemption, satisfying application checklist rules.</li>
          <li><strong>Reject with Reason:</strong> Click "Reject" with mandatory typed rejection justification (e.g. "Original document required for Class 11 admission").</li>
          <li><strong>Manual Lookup Tool:</strong> Collapsible tool allows searching any application by ID to create ad-hoc administrative overrides.</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- 6. MERIT & WAITLIST -->
  <div class="feature-card">
    <div class="feature-card-header">
      <div class="feature-card-title">6. Merit Ranking, Selection &amp; Waiting List</div>
      <span class="screen-route">/admission/merit &amp; /admission/waitlist</span>
    </div>
    <div class="feature-card-body">
      <div class="col-view">
        <div class="sub-head head-view">👁 What You Can View</div>
        <ul class="feature-list">
          <li><strong>Merit Lists:</strong> Candidates ordered automatically by total test and interview scores per class.</li>
          <li><strong>Ordered Waiting List:</strong> Candidates who qualified but did not receive an immediate seat, ranked strictly by merit.</li>
          <li><strong>Capacity Meters:</strong> Live visual bars indicating whether seats are full or open for promotion.</li>
        </ul>
      </div>
      <div>
        <div class="sub-head head-action">⚡ What You Can Do</div>
        <ul class="feature-list">
          <li><strong>Batch Approvals:</strong> Select top candidates and issue admission offers in one batch with shared audit reason.</li>
          <li><strong>Promote from Waitlist:</strong> When an admitted candidate drops out, click "Promote" to offer seat to next student in line.</li>
        </ul>
      </div>
    </div>
  </div>

  <div class="page-break"></div>

  <!-- 7. PUBLIC WEBSITE & ONLINE ADMISSION PORTAL (NEW) -->
  <div class="feature-card">
    <div class="feature-card-header">
      <div class="feature-card-title">7. Public Website Portal &amp; Online Admissions</div>
      <span class="screen-route">/#/ &amp; /#/apply</span>
    </div>
    <div class="feature-card-body">
      <div class="col-view">
        <div class="sub-head head-view">👁 What You Can View</div>
        <ul class="feature-list">
          <li><strong>13 Institutional Views:</strong> Modern public website covering Home, About, Academics, Admissions, Facilities, School Life, Events, Gallery, Mandatory Disclosure, Resources, and Announcements.</li>
          <li><strong>Admissions Guide:</strong> Interactive 4-step admission guide with smooth DOM scrolling directly to the process section.</li>
          <li><strong>Admission Enquiry Modal:</strong> Accessible modal available from any page for prospective parents to submit quick enquiries.</li>
          <li><strong>Online 7-Step Application Wizard:</strong> Full public admission portal (`/apply`) allowing parents to complete applications from home.</li>
        </ul>
      </div>
      <div>
        <div class="sub-head head-action">⚡ What You Can Do</div>
        <ul class="feature-list">
          <li><strong>Submit Admission Enquiry:</strong> Parents submit student details, preferred class, and phone number with instant on-screen green confirmation.</li>
          <li><strong>Multi-Tenant Alias Routing:</strong> Resolves `sunrise`, `sunrisepublic`, and `SPS` aliases automatically to the canonical school tenant.</li>
          <li><strong>Direct Application Creation:</strong> Submit formal admission drafts and uploaded documents directly into ERP database.</li>
          <li><strong>Submit Exception Requests:</strong> Parents missing a certificate can submit exception justifications that route to the Overrides Queue.</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- 8. STUDENT DIRECTORY -->
  <div class="feature-card">
    <div class="feature-card-header">
      <div class="feature-card-title">8. Student Directory &amp; 360° Profile Dossier</div>
      <span class="screen-route">/students</span>
    </div>
    <div class="feature-card-body">
      <div class="col-view">
        <div class="sub-head head-view">👁 What You Can View</div>
        <ul class="feature-list">
          <li><strong>School Roster:</strong> Complete roster of all 190 students across all 19 sections (Nursery-A through 12-Hum).</li>
          <li><strong>Student Details:</strong> Permanent Admission Number, section, guardian name, emergency phone, and fee clearance status.</li>
          <li><strong>Class &amp; Stream Filter:</strong> Filter roster by individual class and senior secondary stream (Science, Commerce, Humanities).</li>
        </ul>
      </div>
      <div>
        <div class="sub-head head-action">⚡ What You Can Do</div>
        <ul class="feature-list">
          <li><strong>Real-Time Search:</strong> Search any student in under 2 seconds by typing name, admission number, or father's phone.</li>
          <li><strong>Profile Drilldown:</strong> Click any student to review complete academic records, past attendance, and family details.</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- 9. TEACHERS & STAFF DIRECTORY -->
  <div class="feature-card">
    <div class="feature-card-header">
      <div class="feature-card-title">9. Teachers &amp; Staff Directory</div>
      <span class="screen-route">/teachers</span>
    </div>
    <div class="feature-card-body">
      <div class="col-view">
        <div class="sub-head head-view">👁 What You Can View</div>
        <ul class="feature-list">
          <li><strong>Staff Directory:</strong> Complete listing of 28 school employees (24 active teachers, administrators, and support staff).</li>
          <li><strong>Class Teacher Assignments:</strong> Exactly which teacher is the appointed Class Teacher for each of the 19 sections.</li>
          <li><strong>Department Load:</strong> Qualifications, departments (Science, Languages, Humanities, Primary), and designations (PGT, TGT, PRT).</li>
        </ul>
      </div>
      <div>
        <div class="sub-head head-action">⚡ What You Can Do</div>
        <ul class="feature-list">
          <li><strong>Find Emergency Contact:</strong> Quickly look up an educator's phone number during emergency office situations.</li>
          <li><strong>Verify Subject Load:</strong> Check which teacher is responsible for curriculum subjects across primary, middle, and senior wings.</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- 10. CLASSES & TIMETABLE -->
  <div class="feature-card">
    <div class="feature-card-header">
      <div class="feature-card-title">10. 19 Class Sections, Streams &amp; Timetable Grid</div>
      <span class="screen-route">/classes</span>
    </div>
    <div class="feature-card-body">
      <div class="col-view">
        <div class="sub-head head-view">👁 What You Can View</div>
        <ul class="feature-list">
          <li><strong>All 19 Academic Groups:</strong> Nursery-A, LKG-A, UKG-A, 1-A to 10-A, 11-Sci, 11-Com, 11-Hum, 12-Sci, 12-Com, 12-Hum.</li>
          <li><strong>Stream Badges:</strong> Senior Secondary sections cleanly badged with Science, Commerce, and Humanities stream tags.</li>
          <li><strong>18 Distinct Subjects:</strong> Primary foundation subjects through advanced Senior Secondary electives.</li>
          <li><strong>570 Conflict-Free Slots:</strong> 30 weekly timetable slots per section with zero teacher double-booking.</li>
        </ul>
      </div>
      <div>
        <div class="sub-head head-action">⚡ What You Can Do</div>
        <ul class="feature-list">
          <li><strong>Assign Class Teachers:</strong> Appoint or reassign the lead teacher for any of the 19 sections.</li>
          <li><strong>Review Schedule Grid:</strong> Inspect period-by-period timetables from Monday to Saturday for every section.</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- 11. LIBRARY DESK & CIRCULATION (NEW) -->
  <div class="feature-card">
    <div class="feature-card-header">
      <div class="feature-card-title">11. Library Catalogue &amp; Circulation Desk</div>
      <span class="screen-route">/library</span>
    </div>
    <div class="feature-card-body">
      <div class="col-view">
        <div class="sub-head head-view">👁 What You Can View</div>
        <ul class="feature-list">
          <li><strong>Book Catalogue:</strong> Complete registry of library book titles, ISBNs, authors, publishers, categories, and accession copies.</li>
          <li><strong>Circulation Desk:</strong> Active loans tab displaying borrower name, canonical student/staff ID, book title, copy accession, due date, and return status.</li>
          <li><strong>Overdue Highlights:</strong> Color-coded badges highlighting loans that have passed their loan expiry date.</li>
        </ul>
      </div>
      <div>
        <div class="sub-head head-action">⚡ What You Can Do</div>
        <ul class="feature-list">
          <li><strong>Issue Book:</strong> Search borrower by student name or admission number, select book copy, and issue with automatic 14-day due date.</li>
          <li><strong>Process Return:</strong> One-click return processing resetting physical book copy status to Available.</li>
          <li><strong>Add New Titles &amp; Copies:</strong> Register new acquisitions with multiple barcode copies in a single modal.</li>
          <li><strong>Dedicated Librarian RBAC:</strong> Scoped strictly to Library Desk and Notices; isolated from fees, admissions, and payroll.</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- 12. USER ACCESS & GRANULAR RBAC (NEW) -->
  <div class="feature-card">
    <div class="feature-card-header">
      <div class="feature-card-title">12. User Access &amp; Role-Based Access Control (RBAC)</div>
      <span class="screen-route">/admin/users</span>
    </div>
    <div class="feature-card-body">
      <div class="col-view">
        <div class="sub-head head-view">👁 What You Can View</div>
        <ul class="feature-list">
          <li><strong>User Access Directory:</strong> Comprehensive table of user accounts with login email, primary role, account active state, and assigned RBAC roles.</li>
          <li><strong>RBAC Roles Badges:</strong> Visual chips showing granted functional roles (`librarian`, `fee_collector`, `receptionist`, `transport_incharge`, `accounts`).</li>
          <li><strong>Audited Permissions Scope:</strong> Clear separation between general administration and duty-segregated operational accounts.</li>
        </ul>
      </div>
      <div>
        <div class="sub-head head-action">⚡ What You Can Do</div>
        <ul class="feature-list">
          <li><strong>Manage Roles Modal:</strong> Click "Manage Roles" on any user to add or revoke specialized functional roles with one click.</li>
          <li><strong>Instant Token Invalidation:</strong> Assigning or revoking a role increments the user's `token_version`, ensuring instant permission revocation.</li>
          <li><strong>Audited Role Grants:</strong> Every role change is recorded in `audit_log` with administrator identity and timestamp.</li>
        </ul>
      </div>
    </div>
  </div>

  <div class="page-break"></div>

  <!-- 13. STUDENT CERTIFICATES (NEW) -->
  <div class="feature-card">
    <div class="feature-card-header">
      <div class="feature-card-title">13. Student Certificates &amp; Verification Desk</div>
      <span class="screen-route">/certificates</span>
    </div>
    <div class="feature-card-body">
      <div class="col-view">
        <div class="sub-head head-view">👁 What You Can View</div>
        <ul class="feature-list">
          <li><strong>Certificate Registry:</strong> All issued and requested certificates with canonical Enrollment ID, student name, and template type.</li>
          <li><strong>Official Templates:</strong> Pre-configured CBSE templates including Study Certificate, Character Certificate, and Transfer Certificate (TC).</li>
          <li><strong>Verification Serial Numbers:</strong> Unique generated certificate serial numbers for external board verification.</li>
        </ul>
      </div>
      <div>
        <div class="sub-head head-action">⚡ What You Can Do</div>
        <ul class="feature-list">
          <li><strong>Generate Certificate:</strong> Select student, choose template, enter purpose, and issue certificate in seconds.</li>
          <li><strong>Print Official Certificate:</strong> Print formatted certificate on official school letterhead with seal and principal signature block.</li>
          <li><strong>Review &amp; Approve:</strong> Administrative verification workflow before final certificate issuance.</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- 14. HOLIDAY MANAGEMENT (NEW) -->
  <div class="feature-card">
    <div class="feature-card-header">
      <div class="feature-card-title">14. Multi-Section Holiday Management</div>
      <span class="screen-route">/holidays</span>
    </div>
    <div class="feature-card-body">
      <div class="col-view">
        <div class="sub-head head-view">👁 What You Can View</div>
        <ul class="feature-list">
          <li><strong>Declared Holidays List:</strong> Chronological calendar of declared gazetted, festive, and weather closures with start and end dates.</li>
          <li><strong>Class Scope Indicator:</strong> Identifies whether the closure applies school-wide or selectively to specific sections (e.g., Pre-primary only).</li>
        </ul>
      </div>
      <div>
        <div class="sub-head head-action">⚡ What You Can Do</div>
        <ul class="feature-list">
          <li><strong>Declare Holiday:</strong> Add new single-day or multi-day holidays with title and optional class-section targeting.</li>
          <li><strong>Cancel with Mandatory Reason:</strong> Canceling a holiday requires a typed human justification saved directly to `audit_log`.</li>
          <li><strong>Attendance Protection:</strong> Automatically protects attendance registers from accidental marking on declared closure days.</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- 15. FRONT DESK RECEPTION SUITE (NEW) -->
  <div class="feature-card">
    <div class="feature-card-header">
      <div class="feature-card-title">15. Front Desk Reception &amp; Campus Security Suite</div>
      <span class="screen-route">/admin/reception/*</span>
    </div>
    <div class="feature-card-body">
      <div class="col-view">
        <div class="sub-head head-view">👁 What You Can View</div>
        <ul class="feature-list">
          <li><strong>Student Gate Passes:</strong> Real-time register of early exit gate passes with student name, escort details, reason, and checkout timestamp.</li>
          <li><strong>Principal Meeting Slips:</strong> Visitor appointment requests with visitor name, organization, student link, purpose, and meeting status.</li>
          <li><strong>Lost &amp; Found Registry:</strong> Catalog of recovered campus items with item description, location found, claimant, and return status.</li>
          <li><strong>Important Directory:</strong> Quick-dial directory for police, child helpline, ambulance, fire, and board liaisons.</li>
        </ul>
      </div>
      <div>
        <div class="sub-head head-action">⚡ What You Can Do</div>
        <ul class="feature-list">
          <li><strong>Issue Student Pass:</strong> Receptionist creates verified gate pass ensuring child leaves only with an authorized guardian.</li>
          <li><strong>Log Visitor Slips:</strong> Record visiting parents and schedule formal appointments with Principal or Vice Principal.</li>
          <li><strong>Claim Found Items:</strong> Verify claimant identity and mark items returned with claim notes.</li>
          <li><strong>Reception Fee Counter:</strong> Dedicated counter collection screen allowing receptionists to accept basic fees without full admin access.</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- 16. STUDENT ATTENDANCE REGISTER -->
  <div class="feature-card">
    <div class="feature-card-header">
      <div class="feature-card-title">16. Daily Student Attendance Register</div>
      <span class="screen-route">/attendance</span>
    </div>
    <div class="feature-card-body">
      <div class="col-view">
        <div class="sub-head head-view">👁 What You Can View</div>
        <ul class="feature-list">
          <li><strong>Daily Roll-Call Sheet:</strong> Roster of children with status badges: Present, Absent, Late, or Approved Leave.</li>
          <li><strong>Short Attendance Warning:</strong> Immediate warning alert highlighting any student whose attendance drops below CBSE's mandatory 75%.</li>
          <li><strong>Holiday Safeguard:</strong> Clearly flags official school holidays and declared weather closures to prevent erroneous marking.</li>
        </ul>
      </div>
      <div>
        <div class="sub-head head-action">⚡ What You Can Do</div>
        <ul class="feature-list">
          <li><strong>Mark Roll-Call:</strong> Class teachers or clerks record attendance with a single click per child.</li>
          <li><strong>Generate Absence Lists:</strong> Pull a list of all children absent today so office staff can phone parents immediately.</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- 17. EXAMINATIONS, MARKS & REPORT CARDS -->
  <div class="feature-card">
    <div class="feature-card-header">
      <div class="feature-card-title">17. Examinations, Marks Entry &amp; CBSE Report Cards</div>
      <span class="screen-route">/exams</span>
    </div>
    <div class="feature-card-body">
      <div class="col-view">
        <div class="sub-head head-view">👁 What You Can View</div>
        <ul class="feature-list">
          <li><strong>Exam Datesheets:</strong> Schedule of upcoming Half-Yearly, Unit Tests, and Final Board examinations with dates and max marks.</li>
          <li><strong>CBSE Grading Rules:</strong> Official 8-point grading scale (A1 for 91-100%, A2 for 81-90%, down to E).</li>
          <li><strong>Marks Roster:</strong> Grid listing all students with individual marks, Absent flags, or Medical Exemptions across 2,400 scores.</li>
          <li><strong>Official CBSE Report Card Preview:</strong> Term 1 &amp; Term 2 marks, internal assessments, and aggregate grades.</li>
        </ul>
      </div>
      <div>
        <div class="sub-head head-action">⚡ What You Can Do</div>
        <ul class="feature-list">
          <li><strong>Enter Marks in Grid:</strong> Input scores directly into a spreadsheet-like interface with instant range validation.</li>
          <li><strong>Lock Exam Papers:</strong> Permanently lock marks after verification. Once locked, changing a mark requires an audited reason.</li>
          <li><strong>Check Publication Readiness:</strong> The system automatically verifies that all papers are scored before issuing report cards.</li>
          <li><strong>Withhold Report Cards for Dues:</strong> Automatically marks report cards as "Withheld" if a student has unpaid school fees.</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- 18. FEES & LEDGERS -->
  <div class="feature-card">
    <div class="feature-card-header">
      <div class="feature-card-title">18. Student Fees, Ledgers &amp; Counter Collections</div>
      <span class="screen-route">/fees &amp; /fees/ledger</span>
    </div>
    <div class="feature-card-body">
      <div class="col-view">
        <div class="sub-head head-view">👁 What You Can View</div>
        <ul class="feature-list">
          <li><strong>Financial Snapshot:</strong> Total fees billed vs realized cash collections across 300 invoices and 900 line items.</li>
          <li><strong>Student Account Ledger:</strong> Complete chronological financial history for any child showing every bill and receipt.</li>
          <li><strong>Late Fee Calculations:</strong> Automatic late-fee charges (₹300 after 5 days, then ₹100/day capped at 50% of the invoice).</li>
          <li><strong>Fee Receipts:</strong> Official numbered receipts with transaction date, payment mode (Cash, Cheque, UPI), and clerk ID.</li>
        </ul>
      </div>
      <div>
        <div class="sub-head head-action">⚡ What You Can Do</div>
        <ul class="feature-list">
          <li><strong>Generate Monthly Invoices:</strong> Raise tuition and transport bills across all 19 classes in an automated batch.</li>
          <li><strong>Collect Payments:</strong> Record counter fee payments against invoice heads with FIFO oldest-first allocation.</li>
          <li><strong>Audited Payment Reversals:</strong> If a cheque bounces or an error is made, reverse the entry with a mandatory typed audit explanation.</li>
          <li><strong>Close Accounting Periods:</strong> Lock completed calendar months to prevent backdated edits by clerks.</li>
        </ul>
      </div>
    </div>
  </div>

  <div class="page-break"></div>

  <!-- 19. DEFAULTER CHASE LIST -->
  <div class="feature-card">
    <div class="feature-card-header">
      <div class="feature-card-title">19. Fee Defaulter Chasing Register</div>
      <span class="screen-route">/fees/defaulters</span>
    </div>
    <div class="feature-card-body">
      <div class="col-view">
        <div class="sub-head head-view">👁 What You Can View</div>
        <ul class="feature-list">
          <li><strong>Worst-First Ranking:</strong> Complete list of all families behind on payments, ranked from highest overdue balance down.</li>
          <li><strong>Guardian Emergency Contacts:</strong> Displays father's and mother's mobile numbers directly alongside amount owed.</li>
          <li><strong>Months Overdue:</strong> Exactly how many billing cycles (1 month, 2 months, 3+ months) the student has missed.</li>
        </ul>
      </div>
      <div>
        <div class="sub-head head-action">⚡ What You Can Do</div>
        <ul class="feature-list">
          <li><strong>Filter by Amount:</strong> Set a threshold (e.g. show only students owing more than ₹5,000) for prioritized chasing.</li>
          <li><strong>Phone Calling Roster:</strong> Staff can sit with this screen and ring parents directly with exact figures at hand.</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- 20. INVENTORY & STOCK -->
  <div class="feature-card">
    <div class="feature-card-header">
      <div class="feature-card-title">20. Classroom Supplies &amp; Lab Stock Management</div>
      <span class="screen-route">/inventory</span>
    </div>
    <div class="feature-card-body">
      <div class="col-view">
        <div class="sub-head head-view">👁 What You Can View</div>
        <ul class="feature-list">
          <li><strong>Supplies Catalogue:</strong> 31 catalog items covering lab chemicals, glassware, math kits, chalks, and exam paper.</li>
          <li><strong>Low-Stock Highlights:</strong> Real-time alerts when supplies fall below minimum threshold (e.g. Printer Paper &lt; 2 reams).</li>
          <li><strong>Pending Approval Counter:</strong> Number of purchase and item-issue requests awaiting leadership approval.</li>
        </ul>
      </div>
      <div>
        <div class="sub-head head-action">⚡ What You Can Do</div>
        <ul class="feature-list">
          <li><strong>Add New Stock:</strong> Register new supplies, set units (bottles, boxes, kits), and define minimum reorder thresholds.</li>
          <li><strong>Approve / Reject Requests:</strong> Review teacher indents and approve distributions.</li>
          <li><strong>Receive Mobile Flags:</strong> When teachers report low supplies from their phone, it appears here instantly.</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- 21. NOTICE BOARD -->
  <div class="feature-card">
    <div class="feature-card-header">
      <div class="feature-card-title">21. Notice Board &amp; Parent Circulars</div>
      <span class="screen-route">/notices</span>
    </div>
    <div class="feature-card-body">
      <div class="col-view">
        <div class="sub-head head-view">👁 What You Can View</div>
        <ul class="feature-list">
          <li><strong>Published Circulars:</strong> Chronological board of school notices (exam schedules, winter vacations, staff meetings).</li>
          <li><strong>Target Audience Tags:</strong> Whether the notice was published for Everyone, Parents Only, Teachers Only, or Specific Classes.</li>
        </ul>
      </div>
      <div>
        <div class="sub-head head-action">⚡ What You Can Do</div>
        <ul class="feature-list">
          <li><strong>Compose Notices:</strong> Write announcements with rich titles and body text, and select the recipient group.</li>
          <li><strong>Audited Archival:</strong> Delete or archive outdated circulars with a permanent recorded reason.</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- 22. TRANSPORT DESK UPGRADE (NEW) -->
  <div class="feature-card">
    <div class="feature-card-header">
      <div class="feature-card-title">22. School Bus Routes, Fleet Safety &amp; Rider Allocation</div>
      <span class="screen-route">/transport</span>
    </div>
    <div class="feature-card-body">
      <div class="col-view">
        <div class="sub-head head-view">👁 What You Can View</div>
        <ul class="feature-list">
          <li><strong>Plan 1 (Fleet &amp; Route Setup):</strong> Configured routes (Gomti Nagar &amp; Alambagh), 7 pickup stops with scheduled timings, 2 buses, and 3 distance fee slabs.</li>
          <li><strong>Plan 2 (Student Allocation Desk):</strong> Roster of 30 active student passengers with assigned route, stop, distance slab, and fee amount.</li>
          <li><strong>Seating Occupancy &amp; Safety:</strong> Real-time seat occupancy gauge preventing vehicle overcrowding beyond legal limits.</li>
          <li><strong>Address-First Geocoding:</strong> Stop locations and student residences mapped with landmark descriptions.</li>
        </ul>
      </div>
      <div>
        <div class="sub-head head-action">⚡ What You Can Do</div>
        <ul class="feature-list">
          <li><strong>Allocate Bus Seats:</strong> Assign students to routes and stops; fees automatically bill to the student's monthly ledger.</li>
          <li><strong>Update Route Stops:</strong> Add pickup landmarks and adjust morning/afternoon timing schedules.</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- 23. REPORTS LIBRARY -->
  <div class="feature-card">
    <div class="feature-card-header">
      <div class="feature-card-title">23. Official Reports Library &amp; Audit Exports</div>
      <span class="screen-route">/reports</span>
    </div>
    <div class="feature-card-body">
      <div class="col-view">
        <div class="sub-head head-view">👁 What You Can View</div>
        <ul class="feature-list">
          <li><strong>21 Standard School Reports:</strong> Categorized across Fees, Attendance, Academics, Timetable, Transport, Communication, and HR.</li>
          <li><strong>Interactive Data Previews:</strong> Live tabular formatting with student names, dates, amounts, and contact details.</li>
          <li><strong>KPI Stat Cards:</strong> High-level visual metrics for quick executive reviews.</li>
        </ul>
      </div>
      <div>
        <div class="sub-head head-action">⚡ What You Can Do</div>
        <ul class="feature-list">
          <li><strong>Dynamic Filtering:</strong> Run reports by specific date ranges, classes, or fee balance thresholds.</li>
          <li><strong>Export to CSV / Excel:</strong> Download clean, audit-ready spreadsheets for board meetings or tax filings.</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- 24. MOBILE APPS -->
  <div class="feature-card">
    <div class="feature-card-header">
      <div class="feature-card-title">24. Mobile Apps: In-Classroom Teacher &amp; Parent Portals</div>
      <span class="screen-route">mobile/(teacher) &amp; mobile/(parent)</span>
    </div>
    <div class="feature-card-body">
      <div class="col-view">
        <div class="sub-head head-view">👁 What You Can View</div>
        <ul class="feature-list">
          <li><strong>Teacher In-Classroom Roll Call:</strong> Fast mobile roll marking with real-time toggle buttons (Present, Absent, Late).</li>
          <li><strong>Homework Management Drawer:</strong> Compose homework, assign due dates, and inspect student turn-in status.</li>
          <li><strong>Mobile Marks Keypad:</strong> Rapid score entry keypad for class tests and unit exams.</li>
          <li><strong>Parent App Dashboard:</strong> Monthly attendance calendar, fee ledger, receipt view, CBSE report cards, and grievance lodging.</li>
        </ul>
      </div>
      <div>
        <div class="sub-head head-action">⚡ What You Can Do</div>
        <ul class="feature-list">
          <li><strong>Conduct Morning Roll Call:</strong> Teachers mark roll call directly from their smartphone while moving around the room.</li>
          <li><strong>Grade Homework Submissions:</strong> View attached work and grade homework submissions with feedback notes.</li>
          <li><strong>Parent Medical Leave Application:</strong> Parents submit medical leave notes directly to class teachers.</li>
        </ul>
      </div>
    </div>
  </div>

  <div class="page-break"></div>

  <!-- 25. STAFF LEAVE & SUBSTITUTION GATE -->
  <div class="feature-card">
    <div class="feature-card-header">
      <div class="feature-card-title">25. Staff Leave Management &amp; Timetable Substitution Gate</div>
      <span class="screen-route">/staff-leave</span>
    </div>
    <div class="feature-card-body">
      <div class="col-view">
        <div class="sub-head head-view">👁 What You Can View</div>
        <ul class="feature-list">
          <li><strong>Staff Leave Queue:</strong> Chronological register of teacher leave applications showing applicant name, dates, reason, and status.</li>
          <li><strong>Dynamic Substitution Matrix:</strong> Affected periods breakdown (Period #, Class, Subject, Scheduled Teacher) derived from timetable.</li>
          <li><strong>100% Coverage Gate:</strong> Visual progress gauge and alert banner. Approval button remains strictly locked until 100% covered.</li>
          <li><strong>Free Teacher Availability:</strong> System dynamically calculates free, non-conflicting faculty members for each affected period.</li>
        </ul>
      </div>
      <div>
        <div class="sub-head head-action">⚡ What You Can Do</div>
        <ul class="feature-list">
          <li><strong>Assign Substitutes:</strong> Select available teachers from dropdowns for each uncovered classroom period.</li>
          <li><strong>Approve Leave with 100% Coverage:</strong> Once all slots are covered, click "Approve Leave &amp; Confirm Substitutions".</li>
          <li><strong>Reject Application:</strong> Reject an application with audited justification, immediately purging provisional substitutions.</li>
          <li><strong>Mobile Duty Reflection:</strong> Assigned substitute teachers automatically receive duty notices on their phone.</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- 26. TEACHER RECRUITMENT -->
  <div class="feature-card">
    <div class="feature-card-header">
      <div class="feature-card-title">26. Teacher Recruitment &amp; Candidate Intake Dossier</div>
      <span class="screen-route">/recruitment</span>
    </div>
    <div class="feature-card-body">
      <div class="col-view">
        <div class="sub-head head-view">👁 What You Can View</div>
        <ul class="feature-list">
          <li><strong>Recruitment Pipeline:</strong> Visual stage cards tracking Applied, Shortlisted, Interviewed, Offered, Hired, and Rejected applicants.</li>
          <li><strong>CBSE A4 Application Preview:</strong> Printable standard candidate dossier with passport photograph box and credentials.</li>
          <li><strong>Offer &amp; Salary Terms:</strong> Offered designation, department, monthly CTC salary (₹), and scheduled joining date.</li>
        </ul>
      </div>
      <div>
        <div class="sub-head head-action">⚡ What You Can Do</div>
        <ul class="feature-list">
          <li><strong>Front-Desk Candidate Intake:</strong> Receptionist registers walk-in teacher applicants and prints official submission dossiers.</li>
          <li><strong>Issue Job Offer:</strong> Admin sets designation and salary terms via "Issue Job Offer" modal.</li>
          <li><strong>One-Click Onboarding:</strong> Confirming joining automatically provisions active teacher employee records and login credentials.</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- 27. PAYROLL -->
  <div class="feature-card">
    <div class="feature-card-header">
      <div class="feature-card-title">27. Payroll Processing &amp; Teacher Salary Disbursal</div>
      <span class="screen-route">/payroll</span>
    </div>
    <div class="feature-card-body">
      <div class="col-view">
        <div class="sub-head head-view">👁 What You Can View</div>
        <ul class="feature-list">
          <li><strong>Monthly Payroll Batches:</strong> Total school wage bill, employee headcount, gross earnings, statutory deductions, and net payout.</li>
          <li><strong>Salary Structure Registry:</strong> Compensation packages by designation (PGT ₹42,000, TGT ₹32,000, PRT ₹19,500, Driver ₹16,000).</li>
          <li><strong>Statutory Breakdown:</strong> Itemized Provident Fund (EPF 12%), Employee State Insurance (ESI 0.75%), TDS, and Professional Tax.</li>
          <li><strong>Printable CBSE Payslip:</strong> Official Lucknow school letterhead, earnings vs deductions grid, amount in words, and authorized sign-off.</li>
        </ul>
      </div>
      <div>
        <div class="sub-head head-action">⚡ What You Can Do</div>
        <ul class="feature-list">
          <li><strong>Run Monthly Payroll:</strong> One-click batch calculation applying attendance loss-of-pay and generating itemized payslips.</li>
          <li><strong>Export Bank Disbursal CSV:</strong> Download electronic bank transfer spreadsheet in standard NEFT/RTGS format.</li>
          <li><strong>Print Official Payslips:</strong> Print individual or batch staff payslips via browser print with official school seals.</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- 28. SESSION ROLLOVER -->
  <div class="feature-card">
    <div class="feature-card-header">
      <div class="feature-card-title">28. Session Rollover &amp; Promotion Wizard</div>
      <span class="screen-route">/admin/session-rollover</span>
    </div>
    <div class="feature-card-body">
      <div class="col-view">
        <div class="sub-head head-view">👁 What You Can View</div>
        <ul class="feature-list">
          <li><strong>4-Step Wizard Workflow:</strong> Session selector (2025-26 to 2026-27), Class Card Selector, Roster Review &amp; Overrides, and Confirmation.</li>
          <li><strong>Cohort Progression Grid:</strong> Class roster displaying student name, admission ID, current class/sec, proposed next class/sec, and new roll number.</li>
          <li><strong>Decision Outcome Badges:</strong> Visual chips for Promote, Detain, Pass Out (Class 10/12), and Transfer Out.</li>
          <li><strong>Capacity &amp; Blocker Alerts:</strong> Live indicators warning of section capacity overflows or unallocated students.</li>
        </ul>
      </div>
      <div>
        <div class="sub-head head-action">⚡ What You Can Do</div>
        <ul class="feature-list">
          <li><strong>Batch Student Progression:</strong> Advance entire classes while reallocating roll numbers alphabetically across all 19 sections.</li>
          <li><strong>Individual Overrides:</strong> Selectively detain failed students or mark departing students as Pass Out / Transfer Out.</li>
          <li><strong>Audited Safety Gate:</strong> Enforces typed <code>PROMOTE</code> confirmation with a user-entered audit justification saved to `audit_log`.</li>
          <li><strong>Preserve Historical Ledger:</strong> Creates new academic year enrolments while keeping past grades, attendance, and fee history intact.</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- PART 2: PLANNED FEATURES -->
  <div class="section-title">
    <span class="part-tag tag-planned">Part 2</span>
    Planned Features: What Will Be Built Next
  </div>
  <p style="margin-top: 0; color: #475569; font-size: 8.5pt;">
    These upcoming capabilities are part of the planned roadmap for subsequent ERP expansion phases:
  </p>

  <table class="planned-table">
    <thead>
      <tr>
        <th style="width: 25%;">Upcoming Feature</th>
        <th style="width: 15%;">Who Uses It</th>
        <th style="width: 12%;">Priority</th>
        <th>What It Will Do For The School</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>Online Fee Payment Gateway (UPI / Cards)</strong></td>
        <td>Parents</td>
        <td><span class="priority-badge p-v2">V2 Scope</span></td>
        <td>Integrating Razorpay/PayU webhooks so parents can pay school fees securely from their phone and receive instant verified digital receipts.</td>
      </tr>
      <tr>
        <td><strong>Automated Biometric Hardware Integration</strong></td>
        <td>Staff &amp; Students</td>
        <td><span class="priority-badge p-v2">V2 Scope</span></td>
        <td>IoT hardware relay pushing thumbprint and facial recognition biometric check-in data directly into `staff_attendance` and student roll call.</td>
      </tr>
      <tr>
        <td><strong>Automated SMS &amp; WhatsApp Push Notifications</strong></td>
        <td>School Office</td>
        <td><span class="priority-badge p-v2">V2 Scope</span></td>
        <td>Automated SMS and WhatsApp messages sent to parents at 09:30 AM if their child is marked absent, plus automated fee overdue reminders.</td>
      </tr>
      <tr>
        <td><strong>Live GPS Bus Telemetry &amp; Speed Tracking</strong></td>
        <td>Transport Manager</td>
        <td><span class="priority-badge p-v2">V2 Scope</span></td>
        <td>Integrating on-board GPS hardware devices for real-time bus location tracking, route deviation alerts, and live parent arrival countdowns.</td>
      </tr>
      <tr>
        <td><strong>Bulk Excel Student &amp; Historical Balance Importer</strong></td>
        <td>Office Clerk</td>
        <td><span class="priority-badge p-v2">Onboarding</span></td>
        <td>A spreadsheet upload wizard allowing school administrators to import hundreds of past student records and opening fee balances in one go.</td>
      </tr>
    </tbody>
  </table>

  <!-- FOOTER -->
  <div style="font-size: 8pt; color: #64748b; margin-top: 22px; border-top: 1px solid #e2e8f0; padding-top: 8px; display: flex; justify-content: space-between;">
    <span>Sunrise Public School ERP • Official Non-Technical Capability Guide</span>
    <span>Generated October 2026 • 32+ Live Screens &amp; 19 Class Sections Verified</span>
  </div>

</body>
</html>
"""

def main():
    print("Writing HTML non-technical specification template...")
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(HTML_CONTENT)
    print(f"Wrote {OUTPUT_HTML} ({len(HTML_CONTENT)} bytes)")

    print(f"Invoking Chrome headless to generate PDF: {OUTPUT_PDF}...")
    cmd = [
        CHROME,
        "--headless",
        "--disable-gpu",
        "--no-pdf-header-footer",
        "--print-to-pdf=" + OUTPUT_PDF,
        "file:///" + OUTPUT_HTML.replace("\\", "/"),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("Chrome error:", res.stderr)
        sys.exit(1)

    size = os.path.getsize(OUTPUT_PDF)
    print(f"Successfully generated PDF: {OUTPUT_PDF} ({size:,} bytes)")

if __name__ == "__main__":
    main()
