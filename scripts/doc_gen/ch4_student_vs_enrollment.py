"""Chapter 6: Special Section: Student ID vs Enrollment ID in Sunrise School ERP."""

def render_ch4() -> str:
    return """
<div class="page-break"></div>

<div class="section-banner">
  <h2>6. Special In-Depth Section: Student ID vs Enrollment ID</h2>
  <p class="desc">The architectural, relational, and operational distinction between permanent student identity and annual academic membership.</p>
</div>

<p>
  A central architectural principle of Sunrise School ERP is the strict separation between <strong>what is true about a student for life</strong> and <strong>what is true about a student for an academic year</strong> (codified in <code>ERP_BLUEPRINT §3.2</code> and implemented in <code>backend/app/models/user.py</code> and <code>backend/app/models/enrolment.py</code>).
</p>

<!-- PART 1: ACTUAL IMPLEMENTATION DISCOVERY -->
<div class="sub-heading">6.1 Codebase Ground-Truth & Schema Introspection</div>

<p>
  Inspection of the live PostgreSQL database (<code>sunrise_test</code>) and SQLAlchemy declarative models reveals the precise identifiers utilized by the system:
</p>

<table class="doc-table">
  <thead>
    <tr>
      <th style="width: 20%;">Identifier Metric</th>
      <th style="width: 40%;">Permanent Student Identity: <code>students</code></th>
      <th style="width: 40%;">Annual Class Association: <code>enrolments</code></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>Database Table</strong></td>
      <td><code>students</code> (defined in <code>backend/app/models/user.py</code>)</td>
      <td><code>enrolments</code> (spelled with single 'l', defined in <code>backend/app/models/enrolment.py</code>)</td>
    </tr>
    <tr>
      <td><strong>Surrogate Primary Key</strong></td>
      <td><code>students.id</code> (<code>BigInteger</code>, autoincrement primary key)</td>
      <td><code>enrolments.id</code> (<code>BigInteger</code>, autoincrement primary key)</td>
    </tr>
    <tr>
      <td><strong>Human-Facing Business Identifier</strong></td>
      <td><code>students.admission_no</code> (<code>String(32)</code>, e.g. <code>ADM-2024-001</code>)</td>
      <td><code>enrolments.roll_no</code> (<code>Integer</code>, unique within a <code>class_section_id</code>)</td>
    </tr>
    <tr>
      <td><strong>Tenant Scoping & Uniqueness</strong></td>
      <td>Unique per school: <code>UniqueConstraint("school_id", "admission_no", name="uq_student_admission_no")</code></td>
      <td>Unique per student-year and section-roll:
        <br>• <code>UniqueIndex("student_id", "academic_year_id", name="uq_enrolment_student_year")</code>
        <br>• <code>UniqueConstraint("class_section_id", "roll_no", name="uq_enrolment_roll")</code>
      </td>
    </tr>
    <tr>
      <td><strong>Lifecycle Mutability</strong></td>
      <td><strong>Immutable:</strong> Created on admission; never changes, overwrites, or deletes throughout schooling.</td>
      <td><strong>Session-Created:</strong> A new record is created for each academic year; old record is marked <code>promoted</code>.</td>
    </tr>
    <tr>
      <td><strong>Child Tables Referencing Key as FK</strong></td>
      <td>
        Point at <code>students.id</code> (Lifetime facts):<br>
        • <code>enrolments.student_id</code><br>
        • <code>student_guardian.student_id</code><br>
        • <code>applications.student_id</code><br>
        • <code>application_siblings.student_id</code><br>
        • <code>grievances.student_id</code><br>
        • <code>marks.student_id</code><br>
        • <code>homework_submissions.student_id</code><br>
        • <code>message_recipients.student_id</code>
      </td>
      <td>
        Point at <code>enrolments.id</code> (Year-scoped facts):<br>
        • <code>attendance.enrolment_id</code><br>
        • <code>fee_invoices.enrolment_id</code><br>
        • <code>fee_payments.enrolment_id</code><br>
        • <code>student_fee_plans.enrolment_id</code><br>
        • <code>fee_concessions.enrolment_id</code><br>
        • <code>report_card_publications.enrolment_id</code><br>
        • <code>transport_assignments.enrolment_id</code><br>
        • <code>student_leave_requests.enrolment_id</code>
      </td>
    </tr>
  </tbody>
</table>

<!-- PART 2: CONCEPTUAL DISTINCTION VS ACTUAL STATEMENT -->
<div class="sub-heading">6.2 Conceptual Distinction vs. Actual System Architecture</div>

<p>
  In general academic database theory:
</p>
<ul>
  <li><strong>Student ID</strong> conceptually represents the student as a physical individual and permanent institutional entity.</li>
  <li><strong>Enrollment ID</strong> conceptually represents a registration event or academic contract between the student and a school programme for a particular academic year or semester.</li>
</ul>

<div class="alert-box alert-amber">
  <strong>Mandatory Engineering Clarification:</strong><br>
  <em>“The current implementation does not maintain a distinct string business identifier called ‘Enrollment ID’. Instead, the ERP implements this relationship through the <code>enrolments</code> table (spelled with single ‘l’), whose surrogate primary key <code>enrolments.id</code> is referenced by child tables as foreign key <code>enrolment_id</code>, while the human-readable identifier during a session is the section-scoped <code>roll_no</code>. The conceptual distinction described above is a general database / ERP concept and should not be interpreted as a separate string code feature of Sunrise ERP.”</em>
</div>

<!-- PART 3: DETAILED COMPARISON TABLE -->
<div class="sub-heading">6.3 Comprehensive Identity Comparison Matrix</div>

<table class="doc-table">
  <thead>
    <tr>
      <th style="width: 15%;">Architectural Aspect</th>
      <th style="width: 42%;">Student ID (<code>students.id</code> / <code>admission_no</code>)</th>
      <th style="width: 43%;">Enrollment Record (<code>enrolments.id</code> / <code>roll_no</code>)</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>Core Meaning</strong></td>
      <td>The permanent institutional identity of the child.</td>
      <td>The student's membership in a specific class section for a single academic year.</td>
    </tr>
    <tr>
      <td><strong>Creation Timing</strong></td>
      <td>Created once at initial admission conversion or registration.</td>
      <td>Created at initial admission, and subsequently created anew at every annual session rollover.</td>
    </tr>
    <tr>
      <td><strong>Can it change?</strong></td>
      <td><strong>Never.</strong> Stays constant across all grades from Nursery to Class 12.</td>
      <td><strong>Session-Bound:</strong> Each year produces a new <code>enrolments.id</code>; roll number within the section can change.</td>
    </tr>
    <tr>
      <td><strong>Multiple Instances?</strong></td>
      <td>A student has exactly <strong>one</strong> <code>students</code> record in the school.</td>
      <td>A student has <strong>multiple</strong> <code>enrolments</code> rows over time (one per year attended).</td>
    </tr>
    <tr>
      <td><strong>Enforced Invariant</strong></td>
      <td><code>UniqueConstraint("school_id", "admission_no")</code></td>
      <td><code>UniqueIndex("student_id", "academic_year_id")</code> — A child can sit in only 1 section per year.</td>
    </tr>
    <tr>
      <td><strong>Operational Usage</strong></td>
      <td>Used for parent portal logins, legal guardianship links, transfer certificates, permanent transcripts, and grievances.</td>
      <td>Used for daily attendance registers, monthly fee invoicing, fee collections, bus seat allocations, and report cards.</td>
    </tr>
    <tr>
      <td><strong>Fictional Concrete Example</strong></td>
      <td><code>students.id = 55</code><br><code>admission_no = 'ADM-2024-001'</code></td>
      <td><code>enrolments.id = 142</code> (for Class 6-A in 2026-27)<br><code>roll_no = 14</code></td>
    </tr>
  </tbody>
</table>

<!-- PART 4: MULTI-YEAR LIFECYCLE WALKTHROUGH -->
<div class="sub-heading">6.4 Multi-Year Practical Lifecycle Simulation</div>

<p>
  To demonstrate how the system prevents data corruption across academic transitions, consider the realistic scenario of student <strong>Aarav Sharma</strong>:
</p>

<div class="scenario-box">
  <strong>Case Study: 3-Year Academic Lifecycle (Class 5-A to Class 7-A)</strong>
  <br><br>
  <strong>Year 1 (Academic Year 2024-25 — Admission):</strong>
  <br>• Aarav joins Class 5-A on 10 April 2024.
  <br>• System creates permanent record: <code>students.id = 12</code>, <code>admission_no = 'ADM-2024-001'</code>, linked to <code>users.id = 45</code>.
  <br>• System creates first session enrollment: <code>enrolments.id = 42</code> with <code>academic_year_id = 1</code> (2024-25), <code>class_section_id = 5</code> (5-A), <code>roll_no = 12</code>, <code>status = 'active'</code>.
  <br>• 180 daily attendance marks in <code>attendance</code> link to <code>enrolment_id = 42</code>.
  <br>• 12 monthly fee invoices in <code>fee_invoices</code> link to <code>enrolment_id = 42</code>.
  <br><br>
  <strong>Year 2 (Academic Year 2025-26 — First Promotion):</strong>
  <br>• In March 2025, the Principal runs Session Rollover from 2024-25 to 2025-26.
  <br>• System updates existing enrollment <code>enrolments.id = 42</code>: sets <code>status = 'promoted'</code> and <code>left_on = '2025-03-31'</code>.
  <br>• System inserts <strong>new</strong> enrollment: <code>enrolments.id = 95</code> with <code>academic_year_id = 2</code> (2025-26), <code>class_section_id = 8</code> (6-A), <code>roll_no = 14</code>, <code>status = 'active'</code>.
  <br>• <em>Crucial Invariant:</em> Aarav's <code>students.id = 12</code> and <code>admission_no = 'ADM-2024-001'</code> remain <strong>completely unchanged</strong>.
  <br>• New Year 2 attendance records and fee invoices point to <code>enrolment_id = 95</code>. Past Year 1 attendance records still point safely to <code>enrolment_id = 42</code>!
  <br><br>
  <strong>Year 3 (Academic Year 2026-27 — Second Promotion):</strong>
  <br>• In March 2026, Session Rollover advances Aarav to Class 7-A.
  <br>• System updates <code>enrolments.id = 95</code>: sets <code>status = 'promoted'</code>.
  <br>• System inserts <strong>new</strong> enrollment: <code>enrolments.id = 168</code> with <code>academic_year_id = 3</code> (2026-27), <code>class_section_id = 11</code> (7-A), <code>roll_no = 15</code>, <code>status = 'active'</code>.
  <br>• Aarav's permanent student ID is still <code>students.id = 12</code>.
</div>

<div class="alert-box alert-emerald">
  <strong>Why This Architectural Separation Prevents Critical Bugs:</strong><br>
  In legacy educational ERPs where <code>class_section_id</code> was placed directly on <code>students</code>, promoting a student silently overwritten the student's current class. As an unintended side effect, querying past attendance or past report cards would re-parent historical records to the new class! In Sunrise ERP, splitting lifetime facts (<code>students</code>) from year-scoped facts (<code>enrolments</code>) means promotion <strong>creates rows instead of destroying them</strong>. Past nominal rolls and past fee ledgers can be reconstructed at any time with 100% mathematical fidelity.
</div>
"""
