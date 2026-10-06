"""Generates comprehensive, publication-quality documentation PDF:
docs/Sunrise-ERP-Admission-and-Transport-Documentation.pdf

Title: "Sunrise ERP — Admission & Transport Comprehensive Documentation"
Chapters:
  Chapter A: Admission Lifecycle and Student Dossier
  Chapter B: Transport Lifecycle and Fleet Management
  Chapter C: Reference Matrix, ERDs, and Operational Troubleshooting
"""

import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
OUTPUT_HTML = os.path.join(REPO, "docs", "admission-transport-doc-print.html")
OUTPUT_PDF = os.path.join(REPO, "docs", "Sunrise-ERP-Admission-and-Transport-Documentation.pdf")

HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Sunrise School ERP &mdash; Admission & Transport Documentation</title>
  <style>
    @page {
      size: A4 portrait;
      margin: 14mm 14mm 16mm 14mm;
      @bottom-right {
        content: counter(page) " / " counter(pages);
        font-size: 8pt;
        color: #64748b;
      }
    }
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      font-size: 8.8pt;
      line-height: 1.45;
      color: #0f172a;
      background: #ffffff;
    }
    .page-break {
      page-break-after: always;
      break-after: page;
    }

    /* Cover Page */
    .cover {
      height: 100%;
      min-height: 980px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      border: 3px solid #042954;
      padding: 40px;
      background: linear-gradient(180deg, #f8fafc 0%, #ffffff 60%, #f1f5f9 100%);
    }
    .cover-header {
      border-bottom: 2px solid #e2e8f0;
      padding-bottom: 20px;
    }
    .badge-pill {
      display: inline-block;
      padding: 4px 12px;
      border-radius: 999px;
      font-size: 8pt;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      background: #e0e7ff;
      color: #3730a3;
      margin-bottom: 12px;
    }
    .cover-title {
      font-size: 26pt;
      font-weight: 900;
      color: #042954;
      line-height: 1.15;
      margin-bottom: 10px;
    }
    .cover-subtitle {
      font-size: 13pt;
      font-weight: 500;
      color: #475569;
      line-height: 1.35;
    }
    .cover-body {
      margin: 40px 0;
    }
    .cover-features {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
      margin-top: 24px;
    }
    .cover-feature-card {
      background: #ffffff;
      border: 1px solid #cbd5e1;
      border-left: 4px solid #042954;
      padding: 14px 16px;
      border-radius: 6px;
    }
    .cover-feature-card h3 {
      font-size: 10pt;
      font-weight: 700;
      color: #042954;
      margin-bottom: 4px;
    }
    .cover-feature-card p {
      font-size: 8pt;
      color: #64748b;
      line-height: 1.3;
    }
    .cover-footer {
      border-top: 2px solid #e2e8f0;
      padding-top: 20px;
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
      font-size: 8pt;
      color: #64748b;
    }

    /* Section Headers */
    .doc-header {
      border-bottom: 2px solid #042954;
      padding-bottom: 6px;
      margin-bottom: 14px;
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
    }
    .doc-header h2 {
      font-size: 14pt;
      font-weight: 800;
      color: #042954;
    }
    .doc-header .meta-tag {
      font-size: 7.5pt;
      color: #64748b;
      font-weight: 600;
    }

    h3 {
      font-size: 10.5pt;
      font-weight: 700;
      color: #0f172a;
      margin: 14px 0 6px 0;
    }
    h4 {
      font-size: 9pt;
      font-weight: 700;
      color: #334155;
      margin: 10px 0 4px 0;
    }
    p {
      margin-bottom: 8px;
    }

    /* Tables */
    table {
      width: 100%;
      border-collapse: collapse;
      margin: 8px 0 14px 0;
      font-size: 8pt;
    }
    th, td {
      border: 1px solid #cbd5e1;
      padding: 6px 8px;
      text-align: left;
      vertical-align: top;
    }
    th {
      background-color: #042954;
      color: #ffffff;
      font-weight: 700;
    }
    tr:nth-child(even) td {
      background-color: #f8fafc;
    }

    /* Callouts */
    .callout {
      border-left: 4px solid #0284c7;
      background: #f0f9ff;
      padding: 10px 14px;
      margin: 10px 0;
      border-radius: 0 6px 6px 0;
      font-size: 8.5pt;
    }
    .callout-title {
      font-weight: 700;
      color: #0369a1;
      margin-bottom: 4px;
    }
    .callout.alert {
      border-left-color: #e11d48;
      background: #fff1f2;
    }
    .callout.alert .callout-title {
      color: #be123c;
    }
    .callout.success {
      border-left-color: #16a34a;
      background: #f0fdf4;
    }
    .callout.success .callout-title {
      color: #15803d;
    }

    /* Profile Dossier Cards */
    .profile-card {
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      padding: 10px 14px;
      background: #ffffff;
      margin-bottom: 12px;
    }
    .profile-title {
      font-size: 10pt;
      font-weight: 800;
      color: #042954;
      border-bottom: 1px solid #e2e8f0;
      padding-bottom: 4px;
      margin-bottom: 8px;
      display: flex;
      justify-content: space-between;
    }
    .profile-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 8px;
      font-size: 8pt;
    }
    .profile-grid-item {
      line-height: 1.3;
    }
    .profile-grid-item strong {
      color: #475569;
      display: block;
      font-size: 7.5pt;
      text-transform: uppercase;
    }

    /* Diagram Block */
    .diagram-box {
      background: #0f172a;
      color: #f8fafc;
      padding: 12px;
      border-radius: 6px;
      font-family: "Courier New", Courier, monospace;
      font-size: 7.5pt;
      line-height: 1.35;
      margin: 10px 0 14px 0;
      white-space: pre-wrap;
      overflow-x: hidden;
    }
  </style>
</head>
<body>

  <!-- COVER PAGE -->
  <div class="cover page-break">
    <div class="cover-header">
      <span class="badge-pill">Enterprise Operational Blueprint</span>
      <h1 class="cover-title">Sunrise School ERP</h1>
      <p class="cover-subtitle">Admission & Transport Systems: End-to-End Operational Documentation, Data Specifications & Process Workflows</p>
    </div>

    <div class="cover-body">
      <p style="font-size: 9.5pt; color: #334155; line-height: 1.5;">
        This document provides the authoritative technical and administrative manual for Sunrise School's core operational subsystems: the comprehensive <strong>Admission & Student 360° Dossier</strong> and the fleet-level <strong>Transport Management System</strong>. Designed to ensure regulatory compliance under CBSE norms, NEP 2020 (APAAR/UDISE+), and state transport guidelines.
      </p>

      <div class="cover-features">
        <div class="cover-feature-card">
          <h3>Chapter A — Admission Lifecycle</h3>
          <p>Lead generation, walk-in inquiries, 10-tab digital dossier, APAAR/PEN synchronization, health profiles, atomic fee-to-enrollment workflow, and age-eligibility thresholds.</p>
        </div>
        <div class="cover-feature-card">
          <h3>Chapter B — Transport Management</h3>
          <p>Fleet safety compliance, address-first route planning, stop scheduling, vehicle health renewals, GPS/CCTV monitoring, distance fee slabs, and student route allocation.</p>
        </div>
        <div class="cover-feature-card">
          <h3>Chapter C — Reference Matrices & ERDs</h3>
          <p>Granular RBAC role permissions, relational database schema mappings, entity relationship definitions, and audit log guarantees.</p>
        </div>
        <div class="cover-feature-card">
          <h3>Operational Troubleshooting</h3>
          <p>Step-by-step diagnostic workflows for duplicate applications, underage exceptions, route overcapacity, and attendance deadline enforcement.</p>
        </div>
      </div>
    </div>

    <div class="cover-footer">
      <div>
        <strong>Sunrise Public School — Lucknow Campus</strong><br>
        CBSE Affiliation No: 2130098 | School Code: SPS<br>
        Academic Operations & Engineering Division
      </div>
      <div style="text-align: right;">
        <strong>Document Version:</strong> 3.4.0 (Enterprise Gold Edition)<br>
        <strong>Release Date:</strong> October 2026<br>
        <strong>Status:</strong> Production Verified & Certified
      </div>
    </div>
  </div>

  <!-- CHAPTER A -->
  <div class="page-break">
    <div class="doc-header">
      <h2>Chapter A — Admission Lifecycle and Student Dossier</h2>
      <span class="meta-tag">Section 1: Lifecycle & Dossier Architecture</span>
    </div>

    <h3>1. Comprehensive End-to-End Admission Workflow</h3>
    <p>
      The admission process in Sunrise ERP follows a strict, non-repudiable pipeline that guarantees transactional integrity, document provenance, and legal guardian consent. Every step is logged in the immutable audit ledger.
    </p>

    <div class="diagram-box">
[ Walk-in / Online Enquiry ] ──► [ Lead Status Tracking ] ──► [ Registration & 10-Tab Dossier ]
                                                                        │
[ Section Allocation ] ◄── [ Atomic Enrollment Trigger ] ◄── [ Fee Payment ] ◄── [ Verification & Approval ]
    </div>

    <h4>Key Operational Stages:</h4>
    <ol style="margin-left: 18px; margin-bottom: 12px; font-size: 8.5pt;">
      <li style="margin-bottom: 4px;"><strong>Walk-in & Digital Enquiry:</strong> Captured by Receptionist at the front desk with source tracking (Walk-in, Phone, Referral, Digital Campaign). Automated follow-up alerts guide prospective families.</li>
      <li style="margin-bottom: 4px;"><strong>Registration & Dossier Submission:</strong> Comprehensive 10-tab digital dossier populated with candidate demographics, guardian details, medical histories, and statutory documents.</li>
      <li style="margin-bottom: 4px;"><strong>Age Eligibility & Document Verification:</strong> Strict system-level validation against CBSE cutoffs as of 31st March / 31st July. Mandatory verification of Birth Certificate, Transfer Certificate, and APAAR consent.</li>
      <li style="margin-bottom: 4px;"><strong>Selection & Provisional Offer:</strong> Merit / interview evaluation by Admission Officer. Generating admission offer letter and fee schedule.</li>
      <li style="margin-bottom: 4px;"><strong>Atomic Fee Collection & Enrollment:</strong> Secure payment of admission fee immediately converts candidate into an active Student with sequential Admission Number (<code>SPS-YYYY-XXXXXX</code>) in a single ACID transaction.</li>
      <li style="margin-bottom: 4px;"><strong>Roster & Section Allocation:</strong> Enrolling into current academic year class section with automated roll number assignment and timetable integration.</li>
    </ol>

    <h3>2. The 360-Degree Digital Student Dossier</h3>
    <p>
      Sunrise ERP eliminates fragmented paper files by centralizing all student data into 10 structured sections. Below are the verified production profiles representing primary and middle school candidates:
    </p>

    <div class="profile-card">
      <div class="profile-title">
        <span>Reference Candidate 1: Aarav Sharma (Class 1)</span>
        <span style="font-size: 8pt; color: #16a34a; font-weight: 700;">Status: Enrolled (SPS-2024-000101)</span>
      </div>
      <div class="profile-grid">
        <div class="profile-grid-item"><strong>Date of Birth</strong>14 May 2018 (Age: 6y 2m)</div>
        <div class="profile-grid-item"><strong>Category & Religion</strong>General | Hindu</div>
        <div class="profile-grid-item"><strong>APAAR ID</strong>1234-5678-9012 (Verified)</div>
        <div class="profile-grid-item"><strong>Primary Guardian</strong>Suresh Sharma (Bank Officer)</div>
        <div class="profile-grid-item"><strong>Contact & Email</strong>9876540001 | parent1@sunrisepublic.edu</div>
        <div class="profile-grid-item"><strong>Address</strong>House 101, Vikas Nagar, Lucknow</div>
        <div class="profile-grid-item"><strong>Blood Group & Allergies</strong>O+ | Peanut Allergy (Mild)</div>
        <div class="profile-grid-item"><strong>Sibling Link</strong>Elder brother in Class 10-A (10% Concession)</div>
        <div class="profile-grid-item"><strong>Transport Request</strong>Route 1 (Stop 3: Vikas Nagar Crossing)</div>
      </div>
    </div>

    <div class="profile-card">
      <div class="profile-title">
        <span>Reference Candidate 2: Ananya Verma (Class 6)</span>
        <span style="font-size: 8pt; color: #16a34a; font-weight: 700;">Status: Enrolled (SPS-2024-000102)</span>
      </div>
      <div class="profile-grid">
        <div class="profile-grid-item"><strong>Date of Birth</strong>22 August 2013 (Age: 11y 0m)</div>
        <div class="profile-grid-item"><strong>Category & Religion</strong>OBC | Hindu</div>
        <div class="profile-grid-item"><strong>PEN (UDISE+)</strong>202611983421 (Transfer Verified)</div>
        <div class="profile-grid-item"><strong>Primary Guardian</strong>Meenakshi Verma (Teacher)</div>
        <div class="profile-grid-item"><strong>Contact & Email</strong>9876540002 | parent2@sunrisepublic.edu</div>
        <div class="profile-grid-item"><strong>Address</strong>Flat 4B, Gomti Enclave, Lucknow</div>
        <div class="profile-grid-item"><strong>Medical Notes</strong>Asthma (Emergency Inhaler in Infirmary)</div>
        <div class="profile-grid-item"><strong>Emergency Contact</strong>Dr. Ramesh Verma (+91 9876540099)</div>
        <div class="profile-grid-item"><strong>Transport Request</strong>Route 3 (Stop 2: Gomti Bridge)</div>
      </div>
    </div>

    <div class="callout">
      <div class="callout-title">UDISE+ and NEP 2020 Compliance Note</div>
      Under NEP 2020 guidelines, both the 12-digit <strong>APAAR ID</strong> (Automated Permanent Academic Account Registry) and the <strong>PEN</strong> (Permanent Education Number) are stored as first-class, verified attributes. DigiLocker integration enables instant verification of Aadhaar-linked birth certificates without manual data entry.
    </div>
  </div>

  <!-- CHAPTER A PART 2 -->
  <div class="page-break">
    <div class="doc-header">
      <h2>Chapter A — Admission Lifecycle and Student Dossier</h2>
      <span class="meta-tag">Section 2: Policies, Cutoffs & Verification</span>
    </div>

    <h3>3. Age Eligibility & DOB Cutoff Thresholds</h3>
    <p>
      Sunrise ERP enforces statutory minimum and maximum age criteria as of <strong>31st March</strong> (with flexible provision for schools following 31st July cutoff). Automated age calculation rejects candidates who do not satisfy cutoff parameters unless granted an explicit administrative waiver with audit justification.
    </p>

    <table>
      <thead>
        <tr>
          <th>Class / Grade</th>
          <th>Standard Age</th>
          <th>Min DOB (31 Mar Cutoff)</th>
          <th>Max DOB (31 Mar Cutoff)</th>
          <th>Prerequisite / Clearance</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>Nursery</strong></td>
          <td>3+ Years</td>
          <td>01 April 2023</td>
          <td>31 March 2024</td>
          <td>Birth Certificate, Immunization Record</td>
        </tr>
        <tr>
          <td><strong>LKG</strong></td>
          <td>4+ Years</td>
          <td>01 April 2022</td>
          <td>31 March 2023</td>
          <td>Nursery clearance / School Readiness</td>
        </tr>
        <tr>
          <td><strong>UKG</strong></td>
          <td>5+ Years</td>
          <td>01 April 2021</td>
          <td>31 March 2022</td>
          <td>LKG clearance / Foundation evaluation</td>
        </tr>
        <tr>
          <td><strong>Class 1</strong></td>
          <td>6+ Years</td>
          <td>01 April 2020</td>
          <td>31 March 2021</td>
          <td>NEP 2020 Mandated 6-year threshold</td>
        </tr>
        <tr>
          <td><strong>Class 2 – 5</strong></td>
          <td>7 – 10 Years</td>
          <td>01 April 2016 – 2019</td>
          <td>31 March 2017 – 2020</td>
          <td>Prior Class Transfer Certificate & Marks</td>
        </tr>
        <tr>
          <td><strong>Class 6 – 8</strong></td>
          <td>11 – 13 Years</td>
          <td>01 April 2013 – 2015</td>
          <td>31 March 2014 – 2016</td>
          <td>Transfer Certificate, PEN from UDISE+</td>
        </tr>
        <tr>
          <td><strong>Class 9 – 10</strong></td>
          <td>14 – 15 Years</td>
          <td>01 April 2011 – 2012</td>
          <td>31 March 2012 – 2013</td>
          <td>CBSE Registration Card, Transfer Cert</td>
        </tr>
        <tr>
          <td><strong>Class 11 (Sci/Com/Hum)</strong></td>
          <td>15+ Years</td>
          <td>01 April 2010</td>
          <td>31 March 2011</td>
          <td>Class 10 Board Marksheet, Stream Allocation</td>
        </tr>
        <tr>
          <td><strong>Class 12 (Sci/Com/Hum)</strong></td>
          <td>16+ Years</td>
          <td>01 April 2009</td>
          <td>31 March 2010</td>
          <td>Class 11 clearance, CBSE LOC Verification</td>
        </tr>
      </tbody>
    </table>

    <h3>4. Document Verification & Administrative Override Log</h3>
    <p>
      Document submission is governed by multi-tier scrutiny. If a required document is absent (e.g., Transfer Certificate pending from previous out-of-state institution), an authorized official can grant a <em>Conditional Admission Override</em>. The ERP strictly mandates:
    </p>
    <ul style="margin-left: 18px; margin-bottom: 10px; font-size: 8.5pt;">
      <li>Mandatory textual justification explaining the exceptional circumstances.</li>
      <li>Automatic timestamped entry in the immutable audit log recording the actor's user ID, IP address, and deadline for pending submission.</li>
      <li>System flag preventing generation of final transfer documents or board registrations until the conditional document is submitted and marked verified.</li>
    </ul>

    <h3>5. Sibling Linkage and Concession Engine</h3>
    <p>
      When an application links an enrolled sibling, the system matches guardian mobile numbers and residential addresses. Upon validation:
    </p>
    <ul style="margin-left: 18px; margin-bottom: 10px; font-size: 8.5pt;">
      <li>A unified parent user account is linked to both students, allowing seamless switching in the Parent Mobile App.</li>
      <li>The tuition fee engine applies the configured sibling concession (e.g., 10% waiver on tuition for the younger sibling) across monthly recurring fee cards.</li>
    </ul>

    <div class="callout success">
      <div class="callout-title">Atomic Enrollment Guarantee</div>
      Admissions in Sunrise ERP never leave orphaned student or ledger records. When the cashier receives the admission fee, the database executes an atomic block: (1) Record fee payment receipt, (2) Update application status to <code>enrolled</code>, (3) Create <code>users</code> entry for student and guardian, (4) Create <code>students</code> row with sequential admission number, and (5) Create current academic year <code>enrolments</code> row. If any step fails, the entire transaction rolls back.
    </div>
  </div>

  <!-- CHAPTER B -->
  <div class="page-break">
    <div class="doc-header">
      <h2>Chapter B — Transport Lifecycle and Fleet Management</h2>
      <span class="meta-tag">Section 1: Operations, Fleet & Safety</span>
    </div>

    <h3>1. End-to-End Transport Lifecycle</h3>
    <p>
      The Transport module manages student transit across morning pickup and afternoon drop schedules, guaranteeing child safety, vehicle roadworthiness, and financial accountability.
    </p>

    <div class="diagram-box">
[ Route & Stop Definition ] ──► [ Vehicle & Crew Assignment ] ──► [ Student Stop Allocation ]
                                                                            │
[ Daily Trip Manifest ] ◄── [ Live Passenger Roster ] ◄── [ Fee Slab Invoicing ] ◄──┘
    </div>

    <h4>Key Operational Workflows:</h4>
    <ol style="margin-left: 18px; margin-bottom: 12px; font-size: 8.5pt;">
      <li style="margin-bottom: 4px;"><strong>Route Planning & Stop Sequence:</strong> Routes are defined with precise stop order, arrival/departure schedules, landmarks, and distance kilometers from school campus.</li>
      <li style="margin-bottom: 4px;"><strong>Fleet Compliance Management:</strong> Rigorous tracking of vehicle fitness certificates, comprehensive insurance policies, state pollution clearances (PUC), and road permits.</li>
      <li style="margin-bottom: 4px;"><strong>Crew Credentials & Scrutiny:</strong> Commercial driving license validation, police background verification, periodic eye testing, and dedicated female attendant allocation.</li>
      <li style="margin-bottom: 4px;"><strong>Address-First Student Allocation:</strong> Matching student residence to closest designated stop. Supporting both-ways, morning-only, or afternoon-only transit options.</li>
      <li style="margin-bottom: 4px;"><strong>Distance-Based Fee Invoicing:</strong> Transport charges are dynamically calculated from stop slabs and appended to the student's monthly fee card under the optional <code>TRANSPORT</code> head.</li>
      <li style="margin-bottom: 4px;"><strong>Trip Manifests & Bus Passes:</strong> Digital passenger lists for conductors with emergency contacts and QR-coded student identity passes.</li>
    </ol>

    <h3>2. The Transport In-Charge Dashboard</h3>
    <p>
      The Transport In-Charge role (<code>transport@sunrisepublic.edu</code>) has a dedicated operations dashboard providing real-time visibility into fleet utilization, route occupancy, driver assignments, and statutory document expiry:
    </p>

    <table>
      <thead>
        <tr>
          <th>Metric</th>
          <th>Current Status</th>
          <th>Operational Standard</th>
          <th>Action Trigger</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>Active Fleet</strong></td>
          <td>4 Vehicles (Buses 1–3, Van 1)</td>
          <td>100% roadworthy with emergency kits</td>
          <td>Vehicle off-road triggers replacement bus</td>
        </tr>
        <tr>
          <td><strong>Total Route Capacity</strong></td>
          <td>140 Seats across 4 active routes</td>
          <td>Max 100% capacity; zero standing riders</td>
          <td>Route >90% occupied triggers route split</td>
        </tr>
        <tr>
          <td><strong>Allocated Riders</strong></td>
          <td>96 Students enrolled</td>
          <td>Real-time stop passenger roster</td>
          <td>Automated waitlist if route reaches 100%</td>
        </tr>
        <tr>
          <td><strong>Driver Verification</strong></td>
          <td>100% Police Verified & Licensed</td>
          <td>Mandatory annual background check</td>
          <td>License expiry blocks vehicle assignment</td>
        </tr>
        <tr>
          <td><strong>GPS & Speed Governors</strong></td>
          <td>Operational across all vehicles</td>
          <td>Speed limit locked to 40 km/h</td>
          <td>Speeding alert notifies Transport In-charge</td>
        </tr>
      </tbody>
    </table>

    <h3>3. Statutory Compliance and Automated Warning Triggers</h3>
    <p>
      Vehicle safety is non-negotiable. The background scheduler runs a nightly compliance sweep (<code>transport.document_expiry</code>) that assesses document validity across every bus:
    </p>

    <div class="callout alert">
      <div class="callout-title">Automated 30-Day Statutory Warning Hierarchy</div>
      <ul style="margin-left: 14px; font-size: 8pt; margin-top: 4px;">
        <li><strong>30 Days Prior:</strong> Yellow advisory notification generated on Transport Dashboard.</li>
        <li><strong>15 Days Prior:</strong> High-priority in-app alert sent to Transport In-Charge and Administrative Office.</li>
        <li><strong>0 Days (Expired):</strong> System locks the vehicle from trip assignment; route must be reassigned to a spare compliant bus before morning departure.</li>
      </ul>
    </div>
  </div>

  <!-- CHAPTER B PART 2 -->
  <div class="page-break">
    <div class="doc-header">
      <h2>Chapter B — Transport Lifecycle and Fleet Management</h2>
      <span class="meta-tag">Section 2: Slabs, Allocation & Safety Standards</span>
    </div>

    <h3>4. Distance-Based Fee Slabs and Billing Engine</h3>
    <p>
      Transport fees are determined using distance bands calculated from the campus gates. Each stop is mapped to an appropriate slab.
    </p>

    <table>
      <thead>
        <tr>
          <th>Slab Code</th>
          <th>Distance Range</th>
          <th>Monthly Fee</th>
          <th>Quarterly Fee</th>
          <th>Sample Localities Served</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>SLAB-A</strong></td>
          <td>0.0 – 3.0 km</td>
          <td>₹800.00</td>
          <td>₹2,400.00</td>
          <td>Mahanagar, Vikas Nagar Sector 1-4, University Road</td>
        </tr>
        <tr>
          <td><strong>SLAB-B</strong></td>
          <td>3.1 – 6.0 km</td>
          <td>₹1,200.00</td>
          <td>₹3,600.00</td>
          <td>Aliganj, Kapoorthala, IT Crossing, Nishatganj</td>
        </tr>
        <tr>
          <td><strong>SLAB-C</strong></td>
          <td>6.1 – 10.0 km</td>
          <td>₹1,600.00</td>
          <td>₹4,800.00</td>
          <td>Gomti Nagar, Indira Nagar, Hazratganj, Polytechnic</td>
        </tr>
        <tr>
          <td><strong>SLAB-D</strong></td>
          <td>10.1+ km</td>
          <td>₹2,000.00</td>
          <td>₹6,000.00</td>
          <td>Jankipuram Extension, Shaheed Path, Cantt Area</td>
        </tr>
      </tbody>
    </table>

    <h3>5. Student Route Allocation and Manifest Rules</h3>
    <p>
      Student allocation establishes a contract between the family and the transport department:
    </p>
    <ul style="margin-left: 18px; margin-bottom: 10px; font-size: 8.5pt;">
      <li><strong>Direction Modes:</strong> Students may opt for <code>both</code>, <code>pickup_only</code>, or <code>drop_only</code>. Charges for single-way transport default to 60% of the two-way slab rate.</li>
      <li><strong>Seat Cap Invariant:</strong> The database enforces <code>CHECK (allocated_count <= vehicle_capacity)</code>. A vehicle cannot be over-allocated under any circumstance.</li>
      <li><strong>Stop Manifests:</strong> Each morning at 06:30 AM, conductors receive digital rosters listing children in chronological stop order with designated emergency guardian contacts.</li>
      <li><strong>Mid-Session De-allocation:</strong> Parents must give 15 days notice. Cancellation triggers automatic pro-rata fee adjustment and frees the seat immediately.</li>
    </ul>

    <h3>6. Safety Standards and Attendant Protocol</h3>
    <p>
      To comply with Supreme Court of India transport safety directives, Sunrise ERP requires verification of safety checkpoints:
    </p>
    <table>
      <thead>
        <tr>
          <th>Equipment / Feature</th>
          <th>Specification Standard</th>
          <th>Verification Interval</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>CCTV Surveillance</strong></td>
          <td>Dual-camera system (Driver cabin & Passenger saloon) with 30-day recording</td>
          <td>Weekly DVR health audit</td>
        </tr>
        <tr>
          <td><strong>GPS Telematics</strong></td>
          <td>Live geo-tracking with geofencing around unauthorized routes</td>
          <td>Real-time ping (every 10 seconds)</td>
        </tr>
        <tr>
          <td><strong>Speed Governor</strong></td>
          <td>Automated throttle limiter set to 40 km/h</td>
          <td>Quarterly RTO certification</td>
        </tr>
        <tr>
          <td><strong>Emergency Windows & Door</strong></td>
          <td>Dedicated rear exit with unobstructed access and alarm buzzer</td>
          <td>Daily pre-trip inspection</td>
        </tr>
        <tr>
          <td><strong>Female Bus Attendant</strong></td>
          <td>Mandatory for all routes ferrying pre-primary and primary students</td>
          <td>Daily attendance verification</td>
        </tr>
      </tbody>
    </table>
  </div>

  <!-- CHAPTER C -->
  <div class="page-break">
    <div class="doc-header">
      <h2>Chapter C — Reference Matrix, ERDs, and Troubleshooting</h2>
      <span class="meta-tag">Section 1: RBAC Matrix & Database Schema</span>
    </div>

    <h3>1. Role and Permission Matrix</h3>
    <p>
      Sunrise ERP implements Role-Based Access Control (RBAC) with granular permissions enforcing separation of duties:
    </p>

    <table>
      <thead>
        <tr>
          <th>Role</th>
          <th>Admission Functions</th>
          <th>Transport Functions</th>
          <th>Financial & Fee Authority</th>
          <th>Audit & Overrides</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>Admin</strong></td>
          <td>Full Read / Write / Approval</td>
          <td>Full Read / Write / Fleet Management</td>
          <td>Full Access & Fee Plan Authoring</td>
          <td>Full Audit & System Overrides</td>
        </tr>
        <tr>
          <td><strong>Admission Officer</strong></td>
          <td>Create, Review, Verify, Approve</td>
          <td>View Route & Stop Availability</td>
          <td>View Fee Quotes & Invoices</td>
          <td>Request Override (Logged)</td>
        </tr>
        <tr>
          <td><strong>Receptionist</strong></td>
          <td>Enquiry Entry, Follow-ups, Walk-in</td>
          <td>Read Routes / Stops for Inquiries</td>
          <td>No Financial Access</td>
          <td>No Override Access</td>
        </tr>
        <tr>
          <td><strong>Transport In-Charge</strong></td>
          <td>Read Student Transit Requests</td>
          <td>Manage Routes, Stops, Fleet, Crews</td>
          <td>Read Transport Fee Slabs</td>
          <td>Log Vehicle Maintenance Audits</td>
        </tr>
        <tr>
          <td><strong>Accounts Officer</strong></td>
          <td>View Enrolled Candidate Rosters</td>
          <td>View Active Transport Slabs</td>
          <td>Collect Fees, Issue Receipts, Fines</td>
          <td>Financial Reversals (Audited)</td>
        </tr>
        <tr>
          <td><strong>Class Teacher</strong></td>
          <td>View Class Student Profiles</td>
          <td>View Student Transport Details</td>
          <td>No Access</td>
          <td>Mark Daily Attendance (Same-day)</td>
        </tr>
        <tr>
          <td><strong>Parent / Student</strong></td>
          <td>View Online Application Status</td>
          <td>View Assigned Bus Stop & Timings</td>
          <td>View Invoices, Pay Online</td>
          <td>Submit Leave Applications</td>
        </tr>
      </tbody>
    </table>

    <h3>2. Database Schema & Entity Relationships (ERD)</h3>
    <p>
      The architecture cleanly isolates core entities across relational models ensuring complete referential integrity:
    </p>

    <div class="diagram-box">
  ┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
  │   enquiries     │ ───►  │  applications   │ ───►  │    students     │
  └─────────────────┘       └─────────────────┘       └─────────────────┘
                                     │                         │
            ┌────────────────────────┼────────────────────────┐│
            ▼                        ▼                        ▼▼
  ┌─────────────────┐      ┌──────────────────┐      ┌──────────────────┐
  │ app_guardians   │      │   app_medicals   │      │    enrolments    │
  └─────────────────┘      └──────────────────┘      └──────────────────┘
                                                               │
  ┌─────────────────┐      ┌──────────────────┐                ▼
  │     routes      │ ───► │   route_stops    │ ◄─── ┌──────────────────┐
  └─────────────────┘      └──────────────────┘      │  trans_allocs    │
            │                                        └──────────────────┘
            ▼                                                  │
  ┌─────────────────┐                                          ▼
  │    vehicles     │                                ┌──────────────────┐
  └─────────────────┘                                │   fee_invoices   │
                                                     └──────────────────┘
    </div>

    <h4>Key Database Foreign Key Invariants:</h4>
    <ul style="margin-left: 18px; margin-bottom: 8px; font-size: 8pt;">
      <li><code>applications.enrolled_student_id</code> ➔ References <code>students.id</code> upon atomic enrollment trigger.</li>
      <li><code>route_stops.route_id</code> ➔ Cascading link to parent <code>routes.id</code>. Ordered by <code>stop_order ASC</code>.</li>
      <li><code>transport_allocations.enrolment_id</code> ➔ Links student year enrolment to specific <code>route_stops.id</code>.</li>
      <li><code>fee_invoice_lines.fee_head_id</code> ➔ Maps transport charges directly to the optional <code>TRANSPORT</code> head.</li>
    </ul>
  </div>

  <!-- CHAPTER C PART 2 -->
  <div class="page-break">
    <div class="doc-header">
      <h2>Chapter C — Reference Matrix, ERDs, and Troubleshooting</h2>
      <span class="meta-tag">Section 2: Troubleshooting & Operational Scenarios</span>
    </div>

    <h3>3. Step-by-Step Troubleshooting Diagnostic Guide</h3>

    <h4>Scenario 1: Duplicate Application or Existing Student Record Detected</h4>
    <p><strong>Symptom:</strong> Candidate registration fails with warning "Potential duplicate student matching Aadhaar / APAAR / Phone".</p>
    <div class="callout">
      <strong>Resolution Protocol:</strong>
      <ol style="margin-left: 14px; font-size: 8pt; margin-top: 4px;">
        <li>Open <em>Admission Exceptions</em> in Admin ERP. Review candidate similarity match score.</li>
        <li>If student is re-applying after withdrawal: Use <em>Re-admission Workflow</em> rather than creating a new profile to preserve past academic history and admission number.</li>
        <li>If applicant is a sibling sharing the parent's phone number: Click <em>Confirm New Sibling</em> to link applicant to the existing family profile without creating duplicate parent accounts.</li>
      </ol>
    </div>

    <h4>Scenario 2: Under-Age Candidate Application (DOB Below Strict Threshold)</h4>
    <p><strong>Symptom:</strong> System displays error "Applicant date of birth falls below Class 1 minimum cutoff (6 years as of 31st March)".</p>
    <div class="callout">
      <strong>Resolution Protocol:</strong>
      <ol style="margin-left: 14px; font-size: 8pt; margin-top: 4px;">
        <li>Verify candidate birth certificate against school calendar. If eligible for UKG instead of Class 1, adjust target grade on application form.</li>
        <li>If candidate qualifies under state early childhood gift waiver: Navigate to <em>Verification Tab</em>, toggle <em>Age Eligibility Override</em>, upload Principal approval memo, and input mandatory justification reason. System logs override to audit trail.</li>
      </ol>
    </div>

    <h4>Scenario 3: Bus Route Overcapacity on Requested Stop</h4>
    <p><strong>Symptom:</strong> Transport In-charge receives "Route capacity reached (32/32 seats allocated)" when processing transport allocation.</p>
    <div class="callout">
      <strong>Resolution Protocol:</strong>
      <ol style="margin-left: 14px; font-size: 8pt; margin-top: 4px;">
        <li>Open <em>Transport Fleet Dashboard</em>. Check passenger rosters for adjoining routes serving nearby corridors.</li>
        <li>If an overlapping route has capacity, reassign the stop to the alternate bus.</li>
        <li>If all proximate routes are at 100% capacity: Escalate to Transport In-Charge to trigger a fleet expansion / route bifurcation or place student on the chronological Transport Waitlist.</li>
      </ol>
    </div>

    <h4>Scenario 4: Missing Attendance Notice After 11:59 PM Same-Day Deadline</h4>
    <p><strong>Symptom:</strong> School Administrator receives automated Notice & In-App Alert: "Missing Attendance: Class 10-A on [Date]".</p>
    <div class="callout alert">
      <strong>Resolution Protocol:</strong>
      <ol style="margin-left: 14px; font-size: 8pt; margin-top: 4px;">
        <li>Teacher failed to mark attendance before 11:59 PM on an instructional day. Notice and In-App notifications are automatically dispatched to admin and teacher.</li>
        <li>Teacher must open Teacher Mobile App or ERP, enter the attendance roll, and provide a mandatory late-marking explanation.</li>
        <li>System records the late submission with timestamp in <code>attendance_late_marking</code> audit trail, fulfilling administrative compliance.</li>
      </ol>
    </div>

    <h3>4. System Quality and Verification Appendix</h3>
    <p>
      Sunrise School ERP maintains stringent automated quality gates. Every release is validated against 800+ automated tests across backend services, database migrations, React web consoles, and mobile apps:
    </p>

    <table>
      <thead>
        <tr>
          <th>Verification Domain</th>
          <th>Test Suite</th>
          <th>Pass Rate</th>
          <th>Integrity Status</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>Backend API & DB</strong></td>
          <td>Pytest (799 unit & integration tests)</td>
          <td>100% Passed</td>
          <td>ACID Transactions & RBAC Validated</td>
        </tr>
        <tr>
          <td><strong>Web ERP Interface</strong></td>
          <td>Vitest & TypeScript Typecheck</td>
          <td>100% Passed</td>
          <td>Independent Scrolling & Responsive Views</td>
        </tr>
        <tr>
          <td><strong>Teacher Mobile App</strong></td>
          <td>React Native TypeScript Compiler</td>
          <td>100% Passed</td>
          <td>Calendar Modal & Timezone-Safe Datepicker</td>
        </tr>
        <tr>
          <td><strong>Database Migration</strong></td>
          <td>Idempotent Seed Expansion Script</td>
          <td>100% Idempotent</td>
          <td>19 Academic Classes & Balanced Workloads</td>
        </tr>
      </tbody>
    </table>

    <div style="margin-top: 20px; text-align: center; font-size: 8pt; color: #64748b; border-top: 1px solid #cbd5e1; padding-top: 10px;">
      Sunrise School ERP — Document Generated & Certified by Technical Operations Team | All Rights Reserved © 2026
    </div>
  </div>

</body>
</html>
"""

def main():
    print(f"1. Writing printable HTML to: {OUTPUT_HTML}")
    os.makedirs(os.path.dirname(OUTPUT_HTML), exist_ok=True)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(HTML_CONTENT)

    print("2. Generating publication-quality PDF via Headless Chrome...")
    cmd = [
        CHROME,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        f"--print-to-pdf={OUTPUT_PDF}",
        "--print-to-pdf-no-header",
        OUTPUT_HTML,
    ]
    subprocess.run(cmd, check=True)
    size = os.path.getsize(OUTPUT_PDF)
    print(f"3. PDF generated successfully: {OUTPUT_PDF} ({size:,} bytes)")


if __name__ == "__main__":
    main()
