"""The message wording a school starts with, and then edits.

Defined in code for the same reason as the permission catalogue and the
document checklist: the seed needs it, and one list is easier to keep true than
two. These are **defaults, not a fixed set** — §0.18 says a records clerk must
be able to change how the school speaks to parents without a deploy, and
`comms.supersede()` is how, by adding a version rather than editing history.

Only the templates something actually sends are here. A template nothing sends
is a row nothing reads, and the rest arrive with the module that wires them:
the admission acknowledgement with admission's notifications, the payslip with
payroll's, and so on.

Placeholders are `$name`, substituted by `comms.render()`. The values available
depend on the audience — a guardian audience carries `$guardian_name`,
`$child_name`, `$class_label`; a staff one carries `$staff_name`. Every
template here carries `$school_name`, which all of them provide.
"""

# (code, name, category, subject, body)
DEFAULT_TEMPLATES = [
    (
        "general.notice",
        "General notice",
        "general",
        "$school_name: $notice_title",
        """Dear $guardian_name,

$notice_body

Regards,
$school_name
""",
    ),
    (
        "emergency.broadcast",
        "Emergency broadcast",
        "emergency",
        "URGENT - $school_name: $notice_title",
        """Dear $guardian_name,

$notice_body

This is an urgent notice from $school_name and has been sent to every family.
""",
    ),
    (
        "fees.overdue",
        "Fee reminder",
        "fees",
        "$school_name: fees outstanding for $child_name",
        """Dear $guardian_name,

Our records show an outstanding balance of Rs $amount_due for $child_name
($class_label), covering $months_due month(s). The oldest amount is
$days_overdue days past its due date.

If you have already paid, please ignore this message — or contact the school
office with your receipt number so we can correct our records.

Regards,
$school_name
""",
    ),
    (
        "transport.compliance_alert",
        "Vehicle and crew papers expiring",
        "transport",
        "$school_name: $expiring transport document(s) need attention",
        """Dear $staff_name,

$expiring transport document(s) are expiring within the next 60 days, of which
$already_expired have already lapsed.

$expiry_list

A vehicle whose insurance, fitness, permit or PUC has expired cannot be
assigned to an active route, and a driver without a current licence and police
verification cannot crew one. The system will refuse those assignments, so
please renew these before they lapse.

Regards,
$school_name
""",
    ),
]
