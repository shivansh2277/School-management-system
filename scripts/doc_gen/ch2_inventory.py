"""Chapter 3: Operational Feature Inventory Table."""

def render_ch2() -> str:
    return """
<div class="section-banner">
  <h2>3. Operational Feature Inventory</h2>
  <p class="desc">A consolidated audit of all 18 functional domains operational in the Sunrise ERP codebase.</p>
</div>

<p>
  The following inventory defines every feature currently running in the Sunrise ERP codebase. Each entry represents an active capability accessible via the Web Admin Console (27 live routes), the Mobile Faculty/Parent apps, or core REST APIs.
</p>

<table class="doc-table">
  <thead>
    <tr>
      <th style="width: 4%;">No.</th>
      <th style="width: 18%;">Feature / Module</th>
      <th style="width: 38%;">Operational Purpose in School Administration</th>
      <th style="width: 25%;">Implementation Status</th>
      <th style="width: 15%;">Documentation Scope</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>1</td>
      <td><strong>Authentication & RBAC</strong></td>
      <td>Identity verification, Bcrypt password checking, JWT claim generation, and role-based permissions gating.</td>
      <td><span class="badge-verified">Fully Operational</span><br><code>api/auth.py</code>, <code>core/permissions.py</code></td>
      <td>Included (Workflows 1.1 - 1.4)</td>
    </tr>
    <tr>
      <td>2</td>
      <td><strong>School Configuration & Tenancy</strong></td>
      <td>Tenant isolation via <code>school_id</code>, module feature switches, academic years, and custom fields registry.</td>
      <td><span class="badge-verified">Fully Operational</span><br><code>TenantBase</code>, <code>/configuration</code>, <code>/settings</code></td>
      <td>Included (Workflows 1.2, 1.4)</td>
    </tr>
    <tr>
      <td>3</td>
      <td><strong>Student & Guardian Master</strong></td>
      <td>Permanent student identity (<code>students</code>), unique admission numbers, demographic biodata, and family links.</td>
      <td><span class="badge-verified">Fully Operational</span><br><code>/students</code>, <code>user.py</code>, 100 seeded rows</td>
      <td>Included (Workflows 2.1 - 2.3)</td>
    </tr>
    <tr>
      <td>4</td>
      <td><strong>Admissions Pipeline</strong></td>
      <td>End-to-end intake: inquiries, 7-tab application dossier, entrance test scoring, merit ranking, waitlist, and 1-click conversion.</td>
      <td><span class="badge-verified">Fully Operational</span><br>6 live screens (<code>/admission/*</code>), 17 test proofs</td>
      <td>Included (Workflows 3.1 - 3.7)</td>
    </tr>
    <tr>
      <td>5</td>
      <td><strong>Academics & Timetabling</strong></td>
      <td>Class & section roster mapping, class teachers, subject-teacher allocations, and weekly timetable slot grid.</td>
      <td><span class="badge-verified">Fully Operational</span><br><code>/classes</code>, <code>timetable_slots</code> (300 rows)</td>
      <td>Included (Workflows 4.1 - 4.2)</td>
    </tr>
    <tr>
      <td>6</td>
      <td><strong>Student Attendance</strong></td>
      <td>Daily morning roll-call marking, attendance sessions, shortage threshold alerts (&lt;75%), and dashboard aggregation.</td>
      <td><span class="badge-verified">Fully Operational</span><br><code>/attendance</code>, <code>attendance</code> (5,800 rows)</td>
      <td>Included (Workflows 5.1 - 5.2)</td>
    </tr>
    <tr>
      <td>7</td>
      <td><strong>Fee Setup & Accounting</strong></td>
      <td>Class fee structures, monthly fee heads, sibling/staff concessions, and monthly academic year billing.</td>
      <td><span class="badge-verified">Fully Operational</span><br><code>/fees/setup</code>, <code>fee_plans</code>, <code>fee_heads</code></td>
      <td>Included (Workflows 6.1 - 6.3)</td>
    </tr>
    <tr>
      <td>8</td>
      <td><strong>Fee Collection & Defaulters</strong></td>
      <td>Counter payment collection, oldest-first FIFO invoice line allocation, payment vouchers, contra reversals, and aging chase list.</td>
      <td><span class="badge-verified">Fully Operational</span><br><code>/fees</code>, <code>/fees/ledger</code>, <code>/fees/defaulters</code></td>
      <td>Included (Workflows 6.4 - 6.7)</td>
    </tr>
    <tr>
      <td>9</td>
      <td><strong>Examinations & Grading</strong></td>
      <td>Exams setup, datesheets, marks entry grid, audited lock/unlock, CBSE 8-point scales, and report cards with fee withholding.</td>
      <td><span class="badge-verified">Fully Operational</span><br><code>/exams</code>, <code>marks</code> (2,400 rows)</td>
      <td>Included (Workflows 7.1 - 7.3)</td>
    </tr>
    <tr>
      <td>10</td>
      <td><strong>Session Rollover & Promotion</strong></td>
      <td>Multi-step progression wizard: cohort review, promote/detain decisions, dynamic roll numbers, and typed PROMOTE audit gate.</td>
      <td><span class="badge-verified">Fully Operational</span><br><code>/admin/session-rollover</code>, <code>promotion.py</code></td>
      <td>Included (Workflows 8.1 - 8.2)</td>
    </tr>
    <tr>
      <td>11</td>
      <td><strong>Employee Directory & HR</strong></td>
      <td>Staff master catalog (18 employees: teaching and non-teaching), employee codes, departments, and qualification records.</td>
      <td><span class="badge-verified">Fully Operational</span><br><code>/teachers</code>, <code>employees</code> (18 rows)</td>
      <td>Included (Workflow 9.1)</td>
    </tr>
    <tr>
      <td>12</td>
      <td><strong>Staff Attendance & Biometrics</strong></td>
      <td>Daily staff attendance register, check-in/check-out timestamps, present/absent/leave status, and biometric logging.</td>
      <td><span class="badge-verified">Fully Operational</span><br><code>staff_attendance</code> table, service API</td>
      <td>Included (Workflow 10.1)</td>
    </tr>
    <tr>
      <td>13</td>
      <td><strong>Staff Payroll & Disbursal</strong></td>
      <td>Compensation structures, allowances, deductions, monthly batch runs, statutory EPF/ESI/TDS registers, and bank CSV export.</td>
      <td><span class="badge-verified">Fully Operational</span><br><code>/payroll</code>, <code>payroll.py</code>, test verified</td>
      <td>Included (Workflows 11.1 - 11.3)</td>
    </tr>
    <tr>
      <td>14</td>
      <td><strong>Teacher Leave & Substitution</strong></td>
      <td>Mobile leave applications, review queue, timetable conflict detection, 100% substitution locked approval gate, and rejection purge.</td>
      <td><span class="badge-verified">Fully Operational</span><br><code>/staff-leave</code>, mobile app, 23 visual proofs</td>
      <td>Included (Workflows 12.1 - 12.3)</td>
    </tr>
    <tr>
      <td>15</td>
      <td><strong>Teacher Recruitment</strong></td>
      <td>Applicant tracking pipeline (Applied, Shortlisted, Offered, Hired), printable CBSE bio-data, job offer issuance, and auto-onboarding.</td>
      <td><span class="badge-verified">Fully Operational</span><br><code>/recruitment</code>, <code>recruitment.py</code></td>
      <td>Included (Workflows 13.1 - 13.3)</td>
    </tr>
    <tr>
      <td>16</td>
      <td><strong>School Notices & Broadcasts</strong></td>
      <td>Broadcast announcements with target audience segmentation (all, teachers, parents, students), and audited revocations.</td>
      <td><span class="badge-verified">Fully Operational</span><br><code>/notices</code>, <code>notices</code> (6 rows)</td>
      <td>Included (Workflows 14.1 - 14.2)</td>
    </tr>
    <tr>
      <td>17</td>
      <td><strong>Fleet Transport & Logistics</strong></td>
      <td>Bus routes, designated pickup/drop stops, vehicle fleet papers/maintenance tracking, and student bus pass assignments.</td>
      <td><span class="badge-verified">Fully Operational</span><br><code>/transport</code>, <code>routes</code>, <code>route_stops</code>, <code>vehicles</code></td>
      <td>Included (Workflows 15.1 - 15.2)</td>
    </tr>
    <tr>
      <td>18</td>
      <td><strong>Stock & Inventory</strong></td>
      <td>Consumable/equipment catalog, reorder threshold alerts, purchase/issue approval modals, and mobile teacher depletion flagging.</td>
      <td><span class="badge-verified">Fully Operational</span><br><code>/inventory</code>, <code>stock_items</code>, mobile screen</td>
      <td>Included (Workflows 16.1 - 16.3)</td>
    </tr>
    <tr>
      <td>19</td>
      <td><strong>Grievance Redressal</strong></td>
      <td>Parent & teacher helpdesk ticketing, administrative categorization, staff assignment, real-time threaded chat, and status triage.</td>
      <td><span class="badge-verified">Fully Operational</span><br>Dashboard feed, mobile parent/teacher tabs</td>
      <td>Included (Workflows 17.1 - 17.2)</td>
    </tr>
    <tr>
      <td>20</td>
      <td><strong>Reports Center & Analytics</strong></td>
      <td>Dynamic runner for 21 backend reports across 9 school operational categories, statistical cards, data tables, and CSV exports.</td>
      <td><span class="badge-verified">Fully Operational</span><br><code>/reports</code>, <code>core/report_registry.py</code></td>
      <td>Included (Workflow 18.1)</td>
    </tr>
  </tbody>
</table>
"""
