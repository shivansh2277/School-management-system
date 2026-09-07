"""The permission vocabulary, and the roles that ship with the product.

Defined in code rather than in the database because the vocabulary belongs to
the software: a school grants permissions, it does not invent them. The seed and
the migration both read from here, so there is one list to keep current.

Naming is `module.resource.action`. Note that `read` and `export` are separate:
being allowed to see a student's record on screen is not the same as being
allowed to download two thousand of them, and an authorised bulk export is the
most likely way a school's data actually leaks (ERP_BLUEPRINT §10.2).
"""

# (code, description)
PERMISSIONS: list[tuple[str, str]] = [
    # --- students and academics
    ("students.profile.read", "View student profiles"),
    ("students.profile.write", "Create and edit students"),
    ("students.profile.export", "Export student data in bulk"),
    ("students.enrolment.promote", "Run year-end promotion"),
    ("academics.class.read", "View classes and sections"),
    ("academics.class.write", "Create and edit classes and sections"),
    # --- attendance
    ("attendance.record.read", "View attendance"),
    ("attendance.record.mark", "Mark attendance"),
    ("attendance.record.correct", "Correct attendance after the fact"),
    # --- timetable
    ("timetable.slot.read", "View timetables"),
    ("timetable.slot.write", "Build and edit the timetable"),
    ("timetable.slot.override", "Schedule past a teacher's maximum weekly load"),
    ("timetable.substitution.manage", "Arrange cover for an absent teacher"),
    # --- examinations
    ("exam.definition.read", "View exams and datesheets"),
    ("exam.definition.write", "Create exams and schedule papers"),
    ("exam.marks.read", "View marks"),
    ("exam.marks.enter", "Enter marks"),
    (
        "exam.marks.manage_any",
        "View and enter marks for any paper, not only one's own subjects",
    ),
    ("exam.marks.lock", "Close marks entry on a paper, and reopen it"),
    (
        "exam.marks.override",
        "Change a mark after the paper is locked, with a reason",
    ),
    ("exam.result.publish", "Publish results and report cards"),
    # --- fees
    ("fees.setup.manage", "Define fee heads, plans and student assignments"),
    ("fees.invoice.read", "View invoices and dues"),
    ("fees.invoice.generate", "Generate invoices"),
    ("fees.payment.collect", "Collect a payment and issue a receipt"),
    ("fees.payment.pay_own", "Pay one's own (or one's child's) invoice"),
    ("fees.payment.void", "Void or reverse a payment"),
    ("fees.concession.approve", "Approve a fee concession or waiver"),
    # --- homework (retained in the mobile app only, ERP_BLUEPRINT §0.17)
    ("homework.item.read", "View homework"),
    ("homework.item.write", "Set homework"),
    ("homework.submission.submit", "Submit homework"),
    # --- admission
    ("admission.cycle.read", "View admission cycles and seat configuration"),
    ("admission.cycle.write", "Set up cycles, seats and document checklists"),
    ("admission.enquiry.read", "View the enquiry register"),
    ("admission.enquiry.write", "Record and follow up enquiries"),
    ("admission.application.read", "View applications"),
    ("admission.application.write", "Create and edit applications, and move them along"),
    ("admission.document.verify", "Verify or reject an applicant's documents"),
    ("admission.assessment.enter", "Schedule applicant tests and enter their marks"),
    ("admission.decision.make", "Admit, waitlist or reject an applicant"),
    (
        "admission.application.convert",
        "Turn an admitted applicant into an enrolled student",
    ),
    (
        "admission.decision.override",
        "Approve admitting past the seats configured for a class",
    ),
    ("admission.interview.enter", "Enter interview feedback as a panel member"),
    (
        "admission.medical.read",
        "View and edit an applicant's medical and special-needs section",
    ),
    # --- communication
    ("comms.notice.read", "Read notices"),
    ("comms.notice.publish", "Publish a notice"),
    # --- hr
    ("hr.employee.read", "View staff records"),
    ("hr.employee.write", "Create and edit staff records"),
    ("hr.employee.exit", "Record that a member of staff has left"),
    ("hr.department.write", "Create and edit departments"),
    (
        "hr.salary.read",
        "View PAN, PF, ESI and bank details — gated apart from the rest of the "
        "staff profile (§5.3.9)",
    ),
    ("hr.salary.write", "Edit PAN, PF, ESI and bank details"),
    ("hr.leave.read", "View staff leave requests and balances"),
    ("hr.leave.apply", "Apply for staff leave, and withdraw an application"),
    ("hr.leave.approve", "Approve or reject staff leave"),
    ("hr.leave.configure", "Define leave types and their entitlements"),
    ("hr.attendance.read", "View the staff register"),
    ("hr.attendance.mark", "Mark and correct the staff register"),
    # --- payroll. Separate from `hr.*` because §5.3.8 gives the Accountant
    # payroll and nothing else of HR, and the HR Manager staff records and not
    # the money.
    (
        "payroll.run.read",
        "View salary components, structures, runs and payslips",
    ),
    ("payroll.setup.manage", "Define salary components and set salary structures"),
    ("payroll.run.manage", "Open, calculate and discard a payroll run"),
    ("payroll.run.approve", "Approve a payroll run and mark it paid"),
    # --- administration
    ("admin.settings.read", "View school settings"),
    ("admin.settings.write", "Change school settings"),
    ("admin.role.read", "View roles and permissions"),
    ("admin.role.write", "Change roles and permissions"),
    ("admin.year.write", "Open, close and switch academic years"),
    ("admin.audit.read", "Read the audit log"),
]

# Permissions that end in `.read` but must NOT be handed out with the rest of
# them. `READ_ONLY` is a convenience for building "can see everything" roles,
# and anything sensitive enough to be gated separately has to be named here or
# the convenience quietly undoes the gate.
NOT_BLANKET_READ = {
    # §5.3.9 keeps salary information behind its own permission. Without this
    # line the Admin Officer — a records clerk — would read every colleague's
    # bank account by virtue of being able to read everything else.
    "hr.salary.read",
    # And payroll for the same reason: a run lists what every colleague is
    # paid. The Accountant, Principal and Auditor hold it explicitly.
    "payroll.run.read",
}

READ_ONLY = [
    c
    for c, _ in PERMISSIONS
    if c.rsplit(".", 1)[1] == "read" and c not in NOT_BLANKET_READ
]

_ALL = [c for c, _ in PERMISSIONS]

# (code, name, is_system, permissions)
SYSTEM_ROLES: list[tuple[str, str, list[str]]] = [
    ("super_admin", "Super Admin", _ALL),
    (
        "principal",
        "Principal",
        [
            *READ_ONLY,
            "students.profile.write",
            "students.enrolment.promote",
            "academics.class.write",
            "attendance.record.correct",
            "timetable.slot.write",
            "timetable.slot.override",
            "timetable.substitution.manage",
            "exam.definition.write",
            "exam.marks.manage_any",
            "exam.marks.lock",
            "exam.marks.override",
            "exam.result.publish",
            "fees.concession.approve",
            "fees.payment.void",
            "comms.notice.publish",
            "hr.employee.write",
            "hr.employee.exit",
            "hr.department.write",
            "hr.salary.read",
            "hr.salary.write",
            "hr.leave.apply",
            "hr.leave.approve",
            "hr.leave.configure",
            "hr.attendance.mark",
            # Granted explicitly, because `payroll.run.read` is excluded from
            # the blanket read set. Whoever signs a run off must be able to see
            # what they are signing.
            "payroll.run.read",
            "payroll.run.approve",
            "admission.enquiry.write",
            "admission.cycle.write",
            "admission.application.write",
            "admission.document.verify",
            "admission.assessment.enter",
            "admission.interview.enter",
            "admission.decision.make",
            "admission.decision.override",
            "admission.application.convert",
            "admission.medical.read",
            "admin.settings.write",
            "admin.year.write",
            "admin.audit.read",
        ],
    ),
    (
        "admin_officer",
        "Admin Officer",
        [
            *READ_ONLY,
            "students.profile.write",
            "students.profile.export",
            "academics.class.write",
            "attendance.record.correct",
            "timetable.slot.write",
            "timetable.substitution.manage",
            "exam.definition.write",
            "fees.setup.manage",
            "hr.leave.apply",
            "hr.attendance.mark",
            "comms.notice.publish",
            "admission.enquiry.write",
            "admission.cycle.write",
            "admission.application.write",
            "admin.settings.write",
        ],
    ),
    (
        "accountant",
        "Accountant",
        [
            # §5.3.8: payroll, and nothing else of HR. Notably not
            # `payroll.run.approve` — whoever prepares the payroll does not
            # sign it off, the same segregation the fee counter already has.
            "payroll.run.read",
            "payroll.setup.manage",
            "payroll.run.manage",
            "hr.employee.read",
            "hr.salary.read",
            "students.profile.read",
            "academics.class.read",
            "fees.setup.manage",
            "fees.invoice.read",
            "fees.invoice.generate",
            "fees.payment.collect",
            "fees.payment.void",
            "comms.notice.read",
        ],
    ),
    (
        "fee_collector",
        "Fee Collector",
        [
            # Deliberately no void and no concession approval: whoever takes the
            # money must not be able to cancel the record of it.
            "students.profile.read",
            "fees.invoice.read",
            "fees.payment.collect",
        ],
    ),
    (
        "exam_controller",
        "Exam Controller",
        [
            "students.profile.read",
            "academics.class.read",
            "exam.definition.read",
            "exam.definition.write",
            "exam.marks.read",
            "exam.marks.enter",
            "exam.marks.manage_any",
            "exam.marks.lock",
            "exam.marks.override",
            "exam.result.publish",
            "comms.notice.read",
        ],
    ),
    (
        "receptionist",
        "Receptionist",
        [
            # Deliberately narrow: the front desk creates and chases enquiries
            # and sees nothing about how an applicant scored or was decided
            # (ERP_BLUEPRINT §5.1.8).
            "admission.cycle.read",
            "admission.enquiry.read",
            "admission.enquiry.write",
            "comms.notice.read",
        ],
    ),
    (
        "document_verifier",
        "Document Verifier",
        [
            # Verifies and nothing else: no decisions, no scores, no register.
            "admission.application.read",
            "admission.document.verify",
        ],
    ),
    (
        "admission_officer",
        "Admission Officer",
        [
            "students.profile.read",
            "academics.class.read",
            "admission.cycle.read",
            "admission.enquiry.read",
            "admission.enquiry.write",
            "admission.application.read",
            "admission.application.write",
            "admission.document.verify",
            "admission.assessment.enter",
            "admission.interview.enter",
            "admission.decision.make",
            "admission.application.convert",
            # Not admission.decision.override: admitting past capacity is the
            # principal's call, not the pipeline's (§5.1.9(11)).
            # Not admission.medical.read: §15 keeps a child's medical section
            # behind its own permission, held by the school nurse and the
            # principal rather than by everyone who works the pipeline.
            "comms.notice.read",
        ],
    ),
    (
        "teacher",
        "Teacher",
        [
            "students.profile.read",
            "academics.class.read",
            "attendance.record.read",
            "attendance.record.mark",
            "exam.definition.read",
            "exam.marks.read",
            "exam.marks.enter",
            "homework.item.read",
            "homework.item.write",
            "comms.notice.read",
            "comms.notice.publish",
            # §5.1.8: a teacher marks the papers for a slot they were given and
            # sits on interview panels. They do not otherwise work admissions.
            "admission.assessment.enter",
            "admission.interview.enter",
        ],
    ),
    (
        "student",
        "Student",
        [
            "attendance.record.read",
            "exam.definition.read",
            "exam.marks.read",
            "homework.item.read",
            "homework.submission.submit",
            "comms.notice.read",
            "fees.invoice.read",
            "fees.payment.pay_own",
        ],
    ),
    (
        "guardian",
        "Guardian",
        [
            "students.profile.read",
            "attendance.record.read",
            "exam.marks.read",
            "homework.item.read",
            "comms.notice.read",
            "fees.invoice.read",
            "fees.payment.pay_own",
        ],
    ),
    (
        "auditor",
        "Auditor",
        # The test case for whether the permission model is real: everything
        # readable, nothing writable. Salary is granted explicitly rather than
        # by falling out of READ_ONLY — an auditor reading bank details is a
        # decision, not a side effect.
        [*READ_ONLY, "admin.audit.read", "hr.salary.read", "payroll.run.read"],
    ),
]

# Which system role a v0 `users.role` maps to, so existing accounts keep working.
LEGACY_ROLE_MAP = {
    "admin": "super_admin",
    "teacher": "teacher",
    "student": "student",
    "parent": "guardian",
}
