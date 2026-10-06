# SESSION 28 HANDOFF PROMPT — Sunrise School ERP: Public Enquiry, Admission Steps, Librarian RBAC & Document Overrides Queue

> **Instructions for User:** Copy and paste the prompt below into the chat when starting the next session.

---

```markdown
# MANDATORY WORKFLOW RULE — READ THIS FIRST BEFORE ANYTHING ELSE

IMPORTANT:
First generate a comprehensive, detailed implementation plan and present it to me.
When I review it and give approval, then only proceed with making changes or modifying code.
Do NOT start writing code, creating migrations, or modifying files until I have explicitly approved your implementation plan.

---

# Sunrise School ERP — Public Enquiry, Admission Steps, Librarian RBAC & Document Overrides Queue

Read SINGLE_SOURCE_OF_TRUTH.md, MEMORY.md, and SESSION-HANDOFF-28.md.
Work on the existing **Sunrise School ERP**. First inspect the current implementation, database models, APIs, RBAC, public website admission flow, admission document override system, and existing Library module. Extend the existing architecture instead of creating duplicate systems.

Implement the following:

## 1. Public Website — Admission Enquiry Is Not Submitting

The public **Admission Enquiry** form is currently failing.
The UI is showing an error similar to:
> "No such school"
even though the enquiry is being submitted from the Sunrise School public website.

Investigate the complete flow:
**Public Website → School/Tenant identification → Enquiry API → Backend validation → Database → ERP Admission/Enquiry**

Find and fix the actual root cause.

Requirements:
- The enquiry must successfully submit for the correct Sunrise School tenant.
- Do not simply hide/change the error message.
- Preserve the existing enquiry fields and validation.
- After successful submission, show an appropriate success confirmation to the visitor.
- Verify that the enquiry is actually stored in the ERP/database and becomes available to the appropriate Admission/Reception workflow.
- Preserve multi-tenant isolation.
- Do not break existing enquiry functionality.

---

## 2. Public Website — "View Admission Steps"

On the public Sunrise School Admissions page, clicking **View Admission Steps** is currently redirecting the visitor to the ERP Sign In page.
This is incorrect.

Fix the routing so that:
**Public Website → Admissions → View Admission Steps**
opens the public admission-steps (smooth scroll to the `#process` section or appropriate route without colliding with HashRouter).

---

## 3. Librarian RBAC + Library Module

Add a dedicated **Librarian** role to the ERP.
There is already an existing **Library** module. The Librarian role should have access to this module.

### Librarian responsibilities
The Librarian should be able to access and manage the existing Library functionality, including where supported by the current module.

### RBAC isolation
The Librarian should **not** automatically receive access to unrelated ERP modules such as:
- Admissions
- Fees
- Recruitment
- Transport
- Staff management
- Attendance administration
- Finance
- Other administrative modules

Give the Librarian only the permissions necessary for Library operations.
The role must work correctly at:
- Backend authorization level
- API level
- Website navigation/sidebar level
Do not rely only on hiding menu items.

### User management
Ensure the new Librarian role can be assigned to a staff/user account through the existing Admin user-management/RBAC system (`/user-access`).

Preserve:
- Tenant isolation
- Existing Admin permissions
- Existing roles
- Existing authentication
- Existing Library functionality

Add the required database migration/seed updates and tests.

---

## 4. Admission Document Overrides — Automatic Pending Queue

The existing **Admission Document Overrides & Exceptions** page currently requires the Admin/authorized user to search for an application manually.
Change this workflow.

Whenever a parent/student application creates a **document override or exception request**, it should automatically appear in the Admission Document Overrides page as a pending item.
The user should **not have to search for the application**.

### Expected workflow
**Parent submits application/request → override/exception is created → it immediately appears in the Overrides & Exceptions queue → authorized Admin reviews it.**

Display useful information directly in the queue, such as:
- Student name
- Application ID
- Requested document
- Reason/exception details
- Date/time requested
- Current status
- Appropriate action such as Review/Approve/Reject

Example:
> **Rahul Sharma**  
> Application: APP-1024  
> Document: Birth Certificate  
> Reason: Document exception requested  
> Status: Pending  
> **Review / Approve / Reject**

### Status lifecycle
Maintain a clear lifecycle such as:
**Pending → Approved / Rejected**

Do not remove the existing audit trail.
The reviewer should be able to understand:
- What was requested
- Why it was requested
- Who processed it
- When it was processed
- What decision was made

---

## 5. Verification

After implementation, run all quality gates:
1. Backend pytest suite (`pytest -q`)
2. Web vitest suite (`npm test`)
3. Web TypeScript check (`npx tsc -b`)
4. Mobile TypeScript check (`npx tsc --noEmit`)

At the end, provide:
1. Root cause of the enquiry failure.
2. Fix for View Admission Steps.
3. Librarian RBAC implementation.
4. Admission override queue changes.
5. Tests executed and results.
6. Any remaining issues requiring manual verification.
```
