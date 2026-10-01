# SESSION 24 PROMPT — Sunrise School ERP: Admission Documents, APAAR ID, Student ID Cards, Certificates & Holiday Management

> **Instructions for User:** Copy and paste the entire block below into the chat when starting the next session.

---

```markdown
# MANDATORY WORKFLOW RULE — READ THIS FIRST BEFORE ANYTHING ELSE

IMPORTANT:
First generate a comprehensive, detailed implementation plan and present it to me.
When I review it and give approval, then only proceed with making changes or modifying code.
Do NOT start writing code, creating migrations, or modifying files until I have explicitly approved your implementation plan.

---

# Sunrise School ERP — Admission Documents, APAAR ID, Student ID Cards, Certificates & Holiday Management

Implement the following changes in the existing Sunrise School ERP. Work within the current architecture, database, UI conventions, RBAC system, and existing workflows. Inspect the relevant code before making changes. Reuse existing components, services, tables, and permissions wherever appropriate. Do not create duplicate systems or change unrelated features.

Repository Location: `C:\Users\SHIVANSH\OneDrive\Documents\AGENTS\school-management-system`
Baseline to inspect first:
1. `SINGLE_SOURCE_OF_TRUTH.md` (all 23 sessions documented)
2. `CLAUDE.md` and `MEMORY.md` (core architectural invariants)
3. `SESSION-HANDOFF-23.md` (verified baseline: 778 backend tests, 125 web tests, 0 TS errors, clean production build)

============================================================
1. Admission Form — Conditional Birth Certificate Requirement
============================================================

Update the existing application form and its validation rules.

**Business rule:** A birth certificate is mandatory if either of these conditions is true:
- The student is applying for a class in the junior section through UKG, inclusive.
- The student is younger than 5 years old on the relevant admission date.

If neither condition is true, the birth certificate is optional.

Implement the rule dynamically based on the selected class and the student's date of birth. Calculate age using the admission date/session rules already established in the ERP; do not hardcode an arbitrary age-calculation method.

### Validation and Admin override
- Enforce the requirement in both the frontend and backend.
- Do not rely only on a frontend required-field indicator.
- If a mandatory birth certificate is missing, prevent final application submission by default.
- Provide an authorized Admin override for missing mandatory admission documents. The Admin must select or enter a reason, which must be stored in the audit log.
- When an authorized override is recorded, allow the application to be submitted without the missing document.
- Reuse this override mechanism for other mandatory admission documents, including APAAR-related requirements where applicable. Do not implement separate, inconsistent override logic for each document.
- Record the document, student/application, authorized user, timestamp, and reason for each override.
- Prevent unauthorized users from invoking the override through the UI or direct API requests.

**Important RBAC distinction:** The Admin does not manage or process applications in the existing ERP. Application processing belongs to the Admission Cell. Preserve that separation. The Admin override must be a narrowly scoped permission to authorize an exception; it must not grant Admin access to the Admission Cell's application-management screens or workflows. Keep application processing and normal document verification with the Admission Cell.

### Public admission website
Verify that the same birth-certificate rule works on the actual public admission website, not just the internal ERP application form.

Test the class-based and age-based conditions, including cases where only one condition is true. Ensure the public frontend displays the correct requirement and the backend independently validates it. Test the authorized override path as well.

============================================================
2. APAAR ID and Parental Consent
============================================================

Add an APAAR ID section to the existing student admission/application workflow.

### Required fields and behaviour
- Provide an APAAR ID field for applicants who already have an ID.
- Provide a separate parental/guardian consent option for new students who do not yet have an APAAR ID and whose parents authorize the school to facilitate its creation on their behalf.
- Make the APAAR section a required part of the admission workflow.
- Distinguish clearly between:
  1. An existing APAAR ID provided by the parent.
  2. Consent recorded for a new student whose APAAR ID is not yet available.
  3. An authorized exception recorded through the existing document-override mechanism.
- Do not treat consent as an existing APAAR ID or as proof that an ID has been created.
- Validate the selected option and its required data on both the frontend and backend.
- Store consent status and relevant consent metadata using the existing data conventions. Where a consent record is required, capture the consenting parent/guardian and the timestamp, and retain the record for audit purposes.
- Allow the APAAR ID to be updated later when it becomes available, without creating a duplicate student record.
- Do not invent an APAAR ID, automatically generate one locally, or imply that the ERP itself creates an official APAAR ID.

### Permissions
- Keep APAAR collection and admission processing within the existing Admission Cell workflow.
- Permit Admin to authorize an exception to the missing mandatory information through the same restricted override mechanism described above.
- Record the reason and audit information for the override.
- Do not give Admin general application-management access.

Ensure the APAAR field, consent option, validation, and saved data work on the public admission website and in the internal application workflow.

============================================================
3. Student ID Card Generation
============================================================

Implement a proper student ID card generation feature using the existing enrolled-student records.

### Card contents
Use the student's **Enrollment ID** as the identifier printed on the card. Do not create a second unique student ID for this purpose.

Include:
- School logo and name.
- Student photograph.
- Student name.
- Enrollment ID.
- Class and section.
- Academic session.
- QR code or barcode encoding the Enrollment ID, if supported by the existing technology stack.

Do not print a separate library card number or introduce another identifier merely for the library module.

Use the actual student data stored in the database. Handle missing photographs or other unavailable fields gracefully without generating misleading placeholder information.

### Generation workflows
Support both:
1. Individual ID card generation from the student's profile.
2. Bulk ID card generation for a selected class, section, academic session, or selected group of students.

Provide a print-ready layout and a reliable print/PDF workflow using the project's existing tools. Ensure the cards are properly sized, aligned, and suitable for physical printing.

Respect existing permissions for student records and ID card generation. Avoid exposing sensitive student information unnecessarily.

============================================================
4. Library Module — Use Enrollment ID Instead of a Separate Library Card
============================================================

The student ID card will serve as the student's primary physical identification card for library use. There must not be a separate library card system for students.

- Use the existing Enrollment ID to identify students in library operations.
- Allow staff to look up a student by Enrollment ID and, where practical, scan the ID card's QR code/barcode to retrieve the corresponding student record.
- Connect the library module directly to the existing enrolled-student records.
- Preserve the existing book issue, return, renewal, overdue, and borrowing-history workflows.
- Remove or retire the separate student library-card generation/number workflow wherever it exists.
- Migrate or map existing library-card references safely if required. Preserve historical issue/return records and outstanding book loans.
- Do not delete existing borrowing history or break existing library transactions while removing the separate card concept.
- Students should not become ineligible to borrow books merely because a physical ID card has not yet been printed. Use the existing eligibility and permission rules for borrowing.

Ensure Enrollment ID lookups handle invalid IDs, inactive or exited students, and duplicate/missing data safely according to existing ERP rules.

============================================================
5. Admin-Managed Student Certificates
============================================================

Implement a certificate issuance workflow for:
1. Transfer Certificate (TC).
2. Character Certificate.
3. Bonafide Certificate.

### Permissions and workflow
- Allow Admin and specifically authorized staff, including the Principal where permitted, to access certificate issuance according to existing RBAC permissions.
- Do not grant every staff role access by default.
- Admin and authorized staff must be able to select a student, choose a certificate type, review the populated details, and generate the certificate.
- Support direct certificate generation by authorized users.
- Also support a request-and-approval workflow for each certificate type: authorized staff can submit a request, and an authorized approver can approve or reject it before issuance.
- Enforce approval permissions and workflow rules on the backend, not only by hiding UI elements.
- Prevent unauthorized issuance and duplicate or inconsistent certificate records.

### Certificate templates
Use configurable school certificate templates rather than hardcoding the school's details into the generation code.

Templates should support:
- School logo, name, address, and configured institutional details.
- Certificate title and type.
- Certificate number.
- Issue date.
- Student name, Enrollment ID, class, and other relevant student details.
- Relevant certificate-specific information.
- Authorized signatory's name/designation and signature area.
- School seal area, where applicable.

Populate details from the existing student, school configuration, and academic-session records. Allow the authorized user to review the information before final issuance.

Generate a professional, print-ready PDF and support downloading and printing. Use the existing project's PDF/document-generation approach where possible.

### Certificate records and auditability
- Store certificate type, student reference, certificate number, issue date, issuing user, status, and relevant approval information.
- Maintain an issuance history so an authorized user can identify previously issued certificates.
- Prevent silent modification of an already issued certificate. If a correction or reissue is needed, follow an explicit, audited correction/reissue workflow.
- Use the existing audit-log conventions.

### Transfer Certificate (TC) rules
Issuing a TC has consequences beyond printing a document.

- Before final issuance, display a clear confirmation explaining that the TC will record the student's exit from the school.
- On confirmation, record the student's exit date and update their status using the existing student lifecycle and withdrawal/exit conventions.
- Make the status transition and TC issuance consistent and atomic wherever possible, so a failed issuance does not leave the student incorrectly marked as exited or vice versa.
- Preserve the student's academic records, fee ledger, payment history, and library history. Do not delete the student.
- Follow existing financial and record-retention rules.
- Prevent accidental issuance or an unintended exit through a simple one-click action.

Character Certificates and Bonafide Certificates must not automatically change the student's enrollment status.

============================================================
6. Holiday Management Integrated With Attendance
============================================================

Add a Holiday Management section to the existing Admin ERP.

Admin must be able to declare, edit, and cancel holidays. Holiday information must be available to the web ERP and mobile app so teachers cannot accidentally mark attendance on a holiday.

### Holiday creation and management
Support:
- Holiday name/reason.
- Start date and end date.
- School-wide holidays.
- Holidays applying only to selected classes and/or sections.
- Relevant academic session, following the existing session model.
- Holiday status, creator, and timestamps.

Validate date ranges and prevent accidental duplicate or conflicting holiday entries where appropriate. Use the existing calendar and date conventions.

When an Admin edits or cancels a holiday, update the affected attendance views and mobile-app experience accordingly. Keep an audit trail of creation, edits, and cancellation. Do not silently delete attendance records that already exist.

### Attendance behaviour
- Before allowing attendance marking, check whether the selected date is covered by a holiday applicable to that class/section and academic session.
- If it is a holiday, block normal attendance marking and clearly display the holiday name.
- Apply this rule in the web ERP, mobile app, and backend attendance APIs. A client-side-only restriction is insufficient.
- Add a narrowly scoped authorized Admin override for exceptional cases, such as a special class held on a declared holiday. Require a reason and record the user, date, applicable class/section, and reason in the audit log.
- Teachers must not be able to bypass the holiday restriction simply by calling the API directly.
- Ensure attendance history, reports, and summaries handle holidays consistently. A holiday must not be treated as an ordinary day of student absence or inadvertently inflate absence statistics.
- If attendance already exists for a date later declared a holiday, preserve the records and handle the conflict explicitly. Do not silently delete or rewrite historical attendance.

### Mobile app integration
- Ensure the mobile app receives the applicable holiday information through the existing API/data-fetching architecture.
- Teachers should see the holiday name and be prevented from opening normal attendance marking for that date unless the authorized exception workflow permits it.
- Ensure changes to holiday declarations are reflected correctly in the app.
- Preserve existing offline/sync behaviour and prevent queued attendance submissions from bypassing backend holiday validation.

============================================================
7. Database, RBAC, UI and Engineering Requirements
============================================================

Implement all features using the existing project's architecture and conventions.

- Inspect existing tables, models, migrations, API endpoints, screen registry, permissions, and relevant web/mobile screens before editing.
- Reuse existing student, Enrollment ID, school configuration, academic-session, audit-log, and permission structures wherever possible.
- Add database migrations only when needed. Migrations must be safe, reversible where appropriate, and compatible with existing data.
- Preserve multi-tenant isolation. Every new read/write and backend validation must be scoped to the correct school/tenant.
- Enforce authorization and validation server-side.
- Avoid duplicate student records, identifiers, certificate numbers, consent records, and conflicting holiday entries.
- Keep all changes consistent with the existing ERP UI conventions and responsive design.
- Keep the existing separation between Admin, Admission Cell, Receptionist, Principal, teachers, and other roles.
- Do not expose new screens or actions to unauthorized roles.
- Use the existing screen registry and navigation patterns.
- Follow the project's existing Indian date, currency, and terminology conventions where relevant.
- Do not introduce fabricated student data or hardcoded school details.
- Do not change unrelated modules or redesign the entire ERP.
- Do not remove existing records to simplify implementation.

============================================================
8. Verification and Acceptance Criteria
============================================================

After implementation, verify the actual workflows, not just whether the code compiles.

### Admission and APAAR
- Test a student in the junior section who is 5 or older: birth certificate is mandatory because of class.
- Test a student outside the junior section who is younger than 5: birth certificate is mandatory because of age.
- Test a student outside the junior section who is 5 or older: birth certificate is optional.
- Test an authorized override with a recorded reason.
- Test that unauthorized users cannot invoke the override.
- Verify the same rules on the public admission website, internal application workflow, and backend APIs.
- Test APAAR ID, parental consent, later ID updates, and authorized exceptions.
- Confirm that consent is not treated as an issued APAAR ID.

### Student ID and library
- Generate one ID card and a bulk batch.
- Verify Enrollment ID, student photo, class, section, session, and school branding.
- Test print/PDF output.
- Verify that the library can find a student using Enrollment ID and that QR/barcode scanning works if implemented.
- Verify that removing the separate library-card workflow does not break existing loans, returns, or borrowing history.

### Certificates
- Test direct issuance and request/approval workflows for all three certificate types.
- Verify role restrictions and backend authorization.
- Verify template configuration and print/PDF output.
- Test TC confirmation, exit-status update, record preservation, and failure/rollback behaviour.
- Verify that Character and Bonafide Certificates do not change student status.
- Test certificate history and correction/reissue controls.

### Holidays and attendance
- Test school-wide and class/section-specific holidays.
- Verify that teachers cannot mark attendance on applicable holidays through the web UI, mobile app, or direct API calls.
- Test the authorized Admin override with a reason and audit record.
- Verify holiday edits and cancellations in the mobile app.
- Test attendance submissions queued before a holiday is declared.
- Verify that holidays do not inflate absence reports and that existing attendance records are preserved.

### Final checks
Run the relevant backend tests, web tests, mobile checks, type checks, database migration checks, and production builds using the repository's established commands. Add or update regression tests for the new business rules.

Report:
1. Features implemented.
2. Files and database migrations changed.
3. RBAC and tenant-isolation safeguards.
4. Tests and build commands executed, with actual results.
5. Any incomplete work or limitations.
```
