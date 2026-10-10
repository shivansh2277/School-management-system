"""Chapter 1 & 2: Executive Summary, Scope, and Codebase Inspection Rules."""

def render_ch1() -> str:
    return """
<!-- COVER / HERO BANNER -->
<div class="cover-hero">
  <h1>Sunrise School ERP — Operational Features, Database Data Flows & Entity Relationships</h1>
  <div class="subtitle">A Code-Verified Technical Documentation of Workflows, Tables, Data Transfers, and Student Identity</div>
  <div class="meta-grid">
    <div class="meta-item">
      <strong>PostgreSQL Schema</strong>
      105 Tables (72 Live, 33 Reserved)
    </div>
    <div class="meta-item">
      <strong>Integrity & Scale</strong>
      1,200+ Columns • 280+ Foreign Keys
    </div>
    <div class="meta-item">
      <strong>Application Footprint</strong>
      32+ Live Screens • 28 Staff (24 Teachers)
    </div>
    <div class="meta-item">
      <strong>Schema Head</strong>
      Migration <code>f7a8b9c0d1e2</code>
    </div>
  </div>
</div>

<!-- EXECUTIVE SUMMARY -->
<div class="section-banner">
  <h2>Executive Summary & Architectural Intent</h2>
  <p class="desc">A definitive technical guide for developers, database engineers, system architects, and administrators.</p>
</div>

<p>
  This document provides an exhaustive, code-verified explanation of how data flows through <strong>every currently implemented and functional operational feature</strong> of the Sunrise School ERP. It has been compiled directly from live database introspection (PostgreSQL <code>sunrise_test</code> on port 5432) and concrete application source code (FastAPI backend, React web console, and Expo React Native mobile apps).
</p>

<div class="alert-box alert-blue">
  <strong>Primary Architectural Objectives Addressed in This Documentation:</strong>
  <ul style="margin: 4px 0 0 0; padding-left: 18px;">
    <li><strong>Operational Purpose:</strong> What each implemented feature solves in the daily administration of a modern K-12 school.</li>
    <li><strong>End-to-End Tracing:</strong> Exactly which frontend user interactions, backend route handlers, service validators, and database tables participate in each transaction.</li>
    <li><strong>Data Movement & Lifecycle:</strong> How records are inserted, updated, joined, linked, allocated, soft-deleted, audited, and purged.</li>
    <li><strong>Student vs Enrollment Separation:</strong> The precise architectural and database distinction between permanent student identity (<code>students.id</code>, <code>admission_no</code>) and annual academic session membership (<code>enrolments.id</code>, <code>roll_no</code>).</li>
    <li><strong>Cross-Module Highways:</strong> How admissions, academics, fee accounting, examinations, HR payroll, library circulation, certificates, and operations interface through explicit foreign key constraints.</li>
  </ul>
</div>

<!-- SECTION 1: SCOPE AND INCLUSION RULES -->
<div class="section-banner">
  <h2>1. Scope and Inclusion Rules</h2>
  <p class="desc">Strict boundaries establishing verified production reality versus planned roadmap items.</p>
</div>

<table class="doc-table">
  <thead>
    <tr>
      <th style="width: 20%;">Category</th>
      <th style="width: 40%;">Strictly Included in This Documentation</th>
      <th style="width: 40%;">Strictly Excluded from This Documentation</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>School Operations</strong></td>
      <td>
        • Student Admissions Pipeline (Cycles, Enquiries, Applications, Scoring, Merit, Waitlist, 1-Click Conversion)<br>
        • Admission Document Overrides & Exceptions Automatic Pending Queue<br>
        • Permanent Student & Guardian Master Records (190 Active Students across 19 Sections)<br>
        • Academic Classes, Sections (Nursery to 12-Hum), 18 Subjects & Timetables (570 Slots)<br>
        • Daily Student Attendance Marking & Shortage Tracking (&lt;75% CBSE Alerts)<br>
        • Multi-Section Holiday Management with Class-Targeted Closures<br>
        • Fee Structure Setup, Concessions, Invoicing, Counter Collection & FIFO Line Allocations<br>
        • Contra Payment Reversals, Defaulters Chase & Period Closing<br>
        • Examinations, Marks Entry (2,400 marks), Paper Locking, CBSE Schemes & Report Cards<br>
        • Academic Session Rollover & Cohort Promotion Wizard across all 19 Sections<br>
        • Library Catalogue, Accession Copies & Circulation Desk with Dedicated Librarian RBAC<br>
        • Student Certificates Desk with Official Templates & Verification Serials<br>
        • Front Desk Reception Suite (Student Gate Passes, Principal Meeting Slips, Found Items)<br>
        • Employee Directory (28 Staff, 24 Teachers), Staff Attendance & Leave Substitution Gate<br>
        • Monthly Payroll Batches, EPF/ESI/TDS Registers & Disbursals<br>
        • Teacher Recruitment Pipeline, Job Offers & Auto-Onboarding<br>
        • School Notice Board & Targeted Broadcasts<br>
        • Fleet Transport Routes, Stops & Student Bus Allocations (Plans 1 & 2)<br>
        • Consumable/Equipment Inventory, Threshold Alerts & Teacher Flagging<br>
        • Parent/Staff Grievance Redressal & Threaded Resolution<br>
        • School Analytics & Reports Library (21 Operational Reports)<br>
        • Modern Public Website Portal (13 views) & Online Admissions Wizard
      </td>
      <td>
        • Hypothetical features or unmerged branches.<br>
        • Features mentioned only in legacy design drafts or future roadmap backlogs.<br>
        • Speculative leave balances or accrual calculation engines (Sunrise ERP currently operates a zero-balance, substitution-gated leave model).<br>
        • Speculative online payment gateway webhooks (currently operates counter collection with receipt voucher generation).<br>
        • Hypothetical GPS live vehicle telemetry tracking (currently operates route stop assignments and paper expiry management).
      </td>
    </tr>
    <tr>
      <td><strong>System Operations</strong></td>
      <td>
        • Multi-Tenancy & Tenant Isolation (<code>school_id</code> scoping on <code>TenantBase</code>)<br>
        • User Authentication, Argon2/Bcrypt Password Hashing & JWT Issuance<br>
        • Role-Based Access Control (RBAC) with granular permission checks (<code>Can.tsx</code>, <code>require_perm</code>)<br>
        • School Configuration, Module Feature Switches & Dynamic Custom Fields<br>
        • Audit Trail Logging for all destructive or sensitive state changes (<code>audit_log</code>)
      </td>
      <td>
        • Proposed cross-school global federated authentication.<br>
        • Speculative OAuth2 social login providers.<br>
        • Hypothetical automatic database sharding architectures.
      </td>
    </tr>
  </tbody>
</table>

<!-- SECTION 2: CODEBASE INSPECTION & ACCURACY RULES -->
<div class="section-banner">
  <h2>2. Codebase Ground-Truth Inspection & Accuracy Rules</h2>
  <p class="desc">Engineering integrity principles applied across all models, services, and diagrams.</p>
</div>

<p>
  Every statement in this document conforms to the following strict engineering verification rules:
</p>

<ul>
  <li><strong>No Invented Schema:</strong> Every table, primary key, column name, data type, and foreign key reference has been verified against PostgreSQL <code>information_schema</code> and SQLAlchemy declarative models in <code>backend/app/models/</code>.</li>
  <li><strong>Distinction Between Verified and Inferred:</strong>
    <br>• <span class="badge-verified">VERIFIED BY TEST</span> Workflows verified through active automated tests (e.g. <code>tests/test_admission_*.py</code>, <code>tests/test_payroll_disbursal.py</code>, <code>tests/test_teacher_leave_and_recruitment.py</code>, <code>tests/test_walkthrough.py</code>) or end-to-end browser execution.
    <br>• <span class="badge-inferred">INFERRED FROM CODE</span> Workflows verified through direct inspection of FastAPI routes, Pydantic schemas, and SQLAlchemy transactional code.
  </li>
  <li><strong>Zero Conceptual Aliasing:</strong> We do not conflate database reality with generic ERP textbooks. Specifically, where the ERP utilizes an integer surrogate primary key on <code>enrolments</code> rather than a business string named <code>enrollment_id</code>, this is stated clearly and unambiguously.</li>
  <li><strong>Preservation of Invariants:</strong> Multi-tenant isolation (<code>school_id</code>), financial immutability (reversals via contra records rather than in-place updates), and destructive audit mandates are documented as strict database invariants.</li>
</ul>
"""
