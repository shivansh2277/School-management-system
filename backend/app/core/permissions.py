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
    # --- examinations
    ("exam.definition.read", "View exams and datesheets"),
    ("exam.definition.write", "Create exams and schedule papers"),
    ("exam.marks.read", "View marks"),
    ("exam.marks.enter", "Enter marks"),
    ("exam.result.publish", "Publish results and report cards"),
    # --- fees
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
    # --- administration
    ("admin.settings.read", "View school settings"),
    ("admin.settings.write", "Change school settings"),
    ("admin.role.read", "View roles and permissions"),
    ("admin.role.write", "Change roles and permissions"),
    ("admin.year.write", "Open, close and switch academic years"),
    ("admin.audit.read", "Read the audit log"),
]

READ_ONLY = [c for c, _ in PERMISSIONS if c.rsplit(".", 1)[1] in ("read",)]

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
            "exam.definition.write",
            "exam.result.publish",
            "fees.concession.approve",
            "fees.payment.void",
            "comms.notice.publish",
            "hr.employee.write",
            "admission.enquiry.write",
            "admission.cycle.write",
            "admission.application.write",
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
            "exam.definition.write",
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
            "students.profile.read",
            "academics.class.read",
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
        # readable, nothing writable.
        [*READ_ONLY, "admin.audit.read"],
    ),
]

# Which system role a v0 `users.role` maps to, so existing accounts keep working.
LEGACY_ROLE_MAP = {
    "admin": "super_admin",
    "teacher": "teacher",
    "student": "student",
    "parent": "guardian",
}
