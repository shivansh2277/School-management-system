"""The document checklist a CBSE school starts with.

Defined in code for the same reason as the permission catalogue: the migration
and the seed both need it, and one list is easier to keep true than two. Schools
edit their own copy afterwards — these are defaults, not a fixed enum
(ERP_BLUEPRINT §3.8).
"""

# (code, name, applies_to, mandatory, required_if_category, has_expiry, confidential)
DEFAULT_TYPES = [
    ("birth_certificate", "Birth Certificate", "application", True, None, False, False),
    ("transfer_certificate", "Transfer Certificate", "application", True, None, False, False),
    ("previous_marksheet", "Previous Report Card", "application", True, None, False, False),
    ("photo", "Passport Photograph", "application", True, None, False, False),
    ("address_proof", "Address Proof", "application", True, None, False, False),
    ("aadhaar_child", "Aadhaar (Child)", "application", False, None, False, True),
    ("aadhaar_parent", "Aadhaar (Parent)", "application", False, None, False, True),
    ("caste_certificate", "Caste / Category Certificate", "application", True, "SC", False, True),
    ("income_certificate", "Income Certificate", "application", True, "EWS", False, True),
    ("medical_certificate", "Medical Certificate", "application", False, None, True, True),
    ("disability_certificate", "Disability Certificate", "application", False, None, False, True),
    ("migration_certificate", "Migration Certificate", "application", False, None, False, False),
    ("student_photo", "Student Photograph", "student", False, None, False, False),
    ("employee_id_proof", "Identity Proof", "employee", True, None, False, True),
    ("employee_qualification", "Qualification Certificate", "employee", True, None, False, False),
    ("police_verification", "Police Verification", "employee", True, None, True, True),
    ("vehicle_insurance", "Insurance", "vehicle", True, None, True, False),
    ("vehicle_fitness", "Fitness Certificate", "vehicle", True, None, True, False),
    ("vehicle_permit", "Permit", "vehicle", True, None, True, False),
    ("vehicle_puc", "Pollution Certificate", "vehicle", True, None, True, False),
]
