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
    ("comms.message.read", "View the outbox and its delivery report"),
    ("comms.message.send", "Compose and send a message"),
    (
        "comms.message.approve",
        "Approve a bulk send above the school's threshold (§5.9.9)",
    ),
    (
        "comms.emergency.broadcast",
        "Send an emergency broadcast, which overrides opt-out and quiet hours",
    ),
    ("comms.template.manage", "Create and supersede message templates"),
    # --- transport. Four rather than one per table: §5.6.8 distinguishes only
    # between designing the service and putting children on it, and a
    # permission nobody grants separately is a permission nobody needs.
    ("transport.setup.read", "View vehicles, routes, stops and fee slabs"),
    ("transport.setup.write", "Register vehicles and design routes, stops and fee slabs"),
    ("transport.assignment.read", "View which children ride which bus"),
    ("transport.assignment.manage", "Put a child on a stop, and end an assignment"),
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
    # --- inventory and stock
    ("inventory.item.read", "View stock items and requests"),
    ("inventory.item.write", "Create and update stock items"),
    ("inventory.request.create", "Flag low stock or request supplies"),
    ("inventory.request.approve", "Approve or reject stock purchase and issue requests"),
    # --- grievances and feedback
    ("grievance.read", "View grievances and complaints"),
    ("grievance.write", "Manage, update status, and resolve grievances"),
    ("grievance.assign", "Assign grievances to teachers or staff members"),
    ("grievance.submit", "Submit grievances and reply to threads"),
    # --- administration
    ("admin.settings.read", "View school settings"),
    ("admin.settings.write", "Change school settings"),
    ("admin.role.read", "View roles and permissions"),
    ("admin.role.write", "Change roles and permissions"),
    ("admin.year.write", "Open, close and switch academic years"),
    ("admin.audit.read", "Read the audit log"),

    # --- teacher leave & substitutions (mobile app)
    ("teacher.leave.apply", "Apply for personal teacher leave"),
    ("teacher.leave.view", "View personal leave status and substitution duties"),

    # --- reception & front desk operations
    ("reception.found_items.read", "View found items register"),
    ("reception.found_items.write", "Record found items, upload photos, broadcast alerts"),
    ("reception.found_items.collect", "Verify claimant and mark found item collected"),
    ("reception.passes.read", "View student gate passes"),
    ("reception.passes.write", "Issue one-time student gate passes"),
    ("reception.authorized_persons.manage", "Manage permanent authorized pickup roster for students"),
    ("reception.meetings.read", "View visitor meeting slips"),
    ("reception.meetings.write", "Create visitor meeting requests for Principal and Teachers"),
    ("reception.meetings.respond_principal", "Respond to Principal meeting requests"),
    ("reception.meetings.respond_teacher", "Respond to Teacher meeting requests"),
    ("reception.directory.read", "View important emergency and school directory contacts"),
    ("reception.directory.write", "Manage important directory contacts"),
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
            "comms.message.send",
            # §5.9.8 gives the emergency broadcast to the Principal alone. It
            # overrides every opt-out and the quiet hours, so it is the one
            # permission in this module that is not shared out.
            "comms.emergency.broadcast",
            "comms.message.approve",
            "comms.template.manage",
            "transport.setup.write",
            "transport.assignment.manage",
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
            "inventory.item.write",
            "inventory.request.create",
            "inventory.request.approve",
            "grievance.write",
            "grievance.assign",
            "grievance.submit",

            "teacher.leave.apply",
            "teacher.leave.view",

            "reception.found_items.read",
            "reception.passes.read",
            "reception.meetings.read",
            "reception.meetings.respond_principal",
            "reception.directory.read",
            "reception.directory.write",
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
            # §5.9.8: general communication. Deliberately not
            # `comms.message.approve` — whoever composes a bulk send is not who
            # signs it off, the same segregation the fee counter and the
            # payroll run already have.
            "comms.message.send",
            "comms.template.manage",
            # §5.6.8 gives the Admin Officer transport setup but not the
            # assignment desk: who rides the bus is the Transport Manager's.
            "transport.setup.write",
            "admission.enquiry.write",
            "admission.cycle.write",
            "admission.application.write",
            "admin.settings.write",
            "inventory.item.write",
            "inventory.request.create",
            "inventory.request.approve",
            "grievance.write",
            "grievance.assign",
            "grievance.submit",

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
            # §5.9.8 scopes the Accountant to fee-related communication. The
            # permission is held school-wide and the restriction is in the
            # service, the same separation the teacher's marks entry uses.
            "comms.message.send",
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
            "reception.found_items.read",
            "reception.found_items.write",
            "reception.found_items.collect",
            "reception.passes.read",
            "reception.passes.write",
            "reception.authorized_persons.manage",
            "reception.meetings.read",
            "reception.meetings.write",
            "reception.directory.read",
            # Only fees.payment.collect: the reception fee counter's API is
            # gated on this alone.  fees.invoice.read is deliberately omitted
            # so the admin-facing fee screens (Fees, Defaulters, Fee setup,
            # Period close) do not leak into the receptionist sidebar.
            "fees.payment.collect",
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
            "fees.payment.collect",
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
            # §5.9.8: own section only. The permission is unscoped and the
            # restriction lives in the service, which is the rule §4 of the
            # handoff warns about — a route that skips service scoping must be
            # gated on something a teacher does not hold.
            "comms.message.send",
            "transport.assignment.read",
            # §5.1.8: a teacher marks the papers for a slot they were given and
            # sits on interview panels. They do not otherwise work admissions.
            "admission.assessment.enter",
            "admission.interview.enter",
            "inventory.item.read",
            "inventory.request.create",
            "grievance.submit",
            "teacher.leave.apply",
            "teacher.leave.view",
            "reception.meetings.read",
            "reception.meetings.respond_teacher",
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
            "grievance.submit",
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
            "transport.assignment.read",
            "grievance.submit",
        ],
    ),
    (
        "transport_manager",
        "Transport Manager",
        [
            # Runs the service end to end, and sees nothing else. Notably no
            # fees permission: §5.6.8 gives transport money to the Accountant,
            # and the transport charge is billed by the ordinary fee run.
            "students.profile.read",
            "academics.class.read",
            "transport.setup.read",
            "transport.setup.write",
            "transport.assignment.read",
            "transport.assignment.manage",
            "hr.employee.read",
            "comms.notice.read",
            "comms.message.send",
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
