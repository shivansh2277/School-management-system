"""Seeds Aarav Sharma and Ananya Verma with complete 11-section digital dossiers into the live database.
"""
from datetime import date
from decimal import Decimal
from sqlalchemy import select
from app.core.db import SessionLocal
from app.models import (
    AdmissionCategory,
    AdmissionCycle,
    Application,
    ApplicationGuardian,
    ApplicationMedical,
    ApplicationSibling,
    ApplicationStatus,
    EnquirySource,
    Student,
    User,
)
from app.models.enums import ApplicationFeePurpose
from app.services import applications as svc
from app.services import conversion as conv_svc

def seed_demo_students():
    db = SessionLocal()
    try:
        admin_user = db.scalar(select(User).where(User.login_id == "admin@sunrisepublic.edu"))
        cycle = db.scalar(select(AdmissionCycle).where(AdmissionCycle.status == "open"))
        if not cycle:
            cycle = db.scalar(select(AdmissionCycle))

        print(f"Using Admin: {admin_user.login_id}, Cycle: {cycle.name} (ID: {cycle.id})")

        # -------------------------------------------------------------
        # 1. Aarav Sharma (Class 1)
        # -------------------------------------------------------------
        existing_aarav = db.scalar(
            select(Application).where(
                Application.first_name == "Aarav",
                Application.last_name == "Sharma",
                Application.cycle_id == cycle.id,
            )
        )
        if existing_aarav:
            print(f"Aarav Sharma already exists (App #{existing_aarav.id}). Skipping.")
            aarav_app = existing_aarav
        else:
            aarav_app = Application(
                school_id=admin_user.school_id,
                cycle_id=cycle.id,
                first_name="Aarav",
                middle_name="Kumar",
                last_name="Sharma",
                date_of_birth=date(2020, 5, 14),
                gender="male",
                class_applying_for="1",
                admission_category=AdmissionCategory.general,
                transport_required=True,
                source=EnquirySource.walk_in,
                nationality="Indian",
                religion="Hindu",
                caste_category="General",
                mother_tongue="Hindi",
                place_of_birth="Lucknow",
                identification_marks="Small mole on right cheek",
                is_single_child=False,
                aadhaar_last4="4321",
                second_language="Hindi",
                preferred_section="A",
                address={
                    "line1": "42/B, Vikas Nagar, Sector 4",
                    "address_line_1": "42/B, Vikas Nagar, Sector 4",
                    "city": "Lucknow",
                    "state": "Uttar Pradesh",
                    "pincode": "226022",
                    "country": "India",
                    "same_as_residential": True,
                },
                previous_school={
                    "is_fresh_admission": False,
                    "school_name": "Little Angels Montessori School",
                    "board": "Pre-School",
                    "last_class_passed": "UKG",
                    "tc_number": "LA/2026/042",
                    "tc_date": "2026-03-15",
                    "percentage_or_grade": "A+",
                    "reason_for_leaving": "Promoted to primary school",
                },
                declarations={
                    "information_accuracy": True,
                    "school_rules_accepted": True,
                    "data_processing_consent": True,
                    "transport_undertaking": True,
                    "parent_signature_name": "Rajesh Sharma",
                    "declared_on": "2026-04-02",
                },
            )
            db.add(aarav_app)
            db.flush()

            # Guardians
            g1 = ApplicationGuardian(
                school_id=admin_user.school_id,
                application_id=aarav_app.id,
                relation="father",
                full_name="Rajesh Sharma",
                date_of_birth=date(1985, 8, 12),
                qualification="B.Tech (Computer Science)",
                occupation="Service",
                designation="Senior Engineering Manager",
                organisation="Tata Consultancy Services",
                annual_income_band="₹15L - ₹25L",
                office_address="Cyber City, Phase 2, Gurugram / Gomti Nagar Lucknow",
                mobile="9811223344",
                alternate_mobile="9811223345",
                email="rajesh.sharma@example.com",
                is_primary=True,
                is_emergency_contact=True,
                is_authorised_for_pickup=True,
            )
            g2 = ApplicationGuardian(
                school_id=admin_user.school_id,
                application_id=aarav_app.id,
                relation="mother",
                full_name="Sunita Sharma",
                date_of_birth=date(1988, 11, 20),
                qualification="M.Sc, B.Ed",
                occupation="Education",
                designation="Senior PGT Teacher",
                organisation="St. Mary's Convent School",
                annual_income_band="₹8L - ₹15L",
                mobile="9811223355",
                email="sunita.sharma@example.com",
                is_primary=False,
                is_emergency_contact=True,
                is_authorised_for_pickup=True,
            )
            db.add_all([g1, g2])

            # Medical
            med1 = ApplicationMedical(
                school_id=admin_user.school_id,
                application_id=aarav_app.id,
                blood_group="B+",
                known_allergies=None,
                chronic_conditions=None,
                regular_medication=None,
                emergency_doctor="Dr. K. N. Rao",
                emergency_doctor_phone="9415012345",
                consent_for_emergency_treatment=True,
            )
            db.add(med1)
            db.flush()

            # Submit & Pay Fee -> Auto-Enroll
            svc.submit(db, aarav_app, actor=admin_user)
            conv_svc.collect(
                db,
                aarav_app,
                actor=admin_user,
                purpose=ApplicationFeePurpose.application_fee,
                amount=Decimal("500.00"),
                method="cash",
                reference="REC-CASH-0101",
            )
            db.commit()
            print(f"Aarav Sharma enrolled! Student ID: {aarav_app.student_id}, Adm No: {aarav_app.student.admission_no}")

        # -------------------------------------------------------------
        # 2. Ananya Verma (Class 6 Sibling Claim)
        # -------------------------------------------------------------
        existing_ananya = db.scalar(
            select(Application).where(
                Application.first_name == "Ananya",
                Application.last_name == "Verma",
                Application.cycle_id == cycle.id,
            )
        )
        if existing_ananya:
            print(f"Ananya Verma already exists (App #{existing_ananya.id}). Skipping.")
        else:
            ananya_app = Application(
                school_id=admin_user.school_id,
                cycle_id=cycle.id,
                first_name="Ananya",
                middle_name="",
                last_name="Verma",
                date_of_birth=date(2015, 8, 22),
                gender="female",
                class_applying_for="6",
                admission_category=AdmissionCategory.general,
                transport_required=False,
                source=EnquirySource.walk_in,
                nationality="Indian",
                religion="Hindu",
                caste_category="General",
                mother_tongue="Hindi",
                place_of_birth="Lucknow",
                identification_marks="None",
                is_single_child=False,
                aadhaar_last4="8765",
                second_language="Sanskrit",
                optional_subject="Computer Science",
                preferred_section="A",
                address={
                    "line1": "12/480, Indira Nagar, Ring Road",
                    "city": "Lucknow",
                    "state": "Uttar Pradesh",
                    "pincode": "226016",
                    "country": "India",
                    "same_as_residential": True,
                },
                previous_school={
                    "is_fresh_admission": False,
                    "school_name": "Delhi Public School",
                    "board": "CBSE",
                    "last_class_passed": "Class 5",
                    "tc_number": "DPS/LKO/2026/892",
                    "tc_date": "2026-03-20",
                    "percentage_or_grade": "94.5% (A1)",
                    "reason_for_leaving": "Relocated closer to Sunrise campus",
                },
                declarations={
                    "information_accuracy": True,
                    "school_rules_accepted": True,
                    "data_processing_consent": True,
                    "transport_undertaking": False,
                    "parent_signature_name": "Dr. Amit Verma",
                    "declared_on": "2026-04-05",
                },
            )
            db.add(ananya_app)
            db.flush()

            # Guardians
            g1 = ApplicationGuardian(
                school_id=admin_user.school_id,
                application_id=ananya_app.id,
                relation="father",
                full_name="Dr. Amit Verma",
                date_of_birth=date(1980, 4, 10),
                qualification="MBBS, MD (Medicine)",
                occupation="Doctor / Physician",
                designation="Senior Consultant Physician",
                organisation="Apollo Clinic Lucknow",
                annual_income_band="> ₹25 Lakhs",
                office_address="Sector B, Aliganj, Lucknow",
                mobile="9839011223",
                email="dr.amit.verma@example.com",
                is_primary=True,
                is_emergency_contact=True,
                is_authorised_for_pickup=True,
            )
            g2 = ApplicationGuardian(
                school_id=admin_user.school_id,
                application_id=ananya_app.id,
                relation="mother",
                full_name="Dr. Ritu Verma",
                date_of_birth=date(1982, 9, 15),
                qualification="Ph.D, M.Sc (Biochemistry)",
                occupation="Professor / Academic",
                designation="Associate Professor",
                organisation="University of Lucknow",
                annual_income_band="₹15L - ₹25L",
                mobile="9839011224",
                email="ritu.verma@example.com",
                is_primary=False,
                is_emergency_contact=True,
                is_authorised_for_pickup=True,
            )
            db.add_all([g1, g2])

            # Link Sibling: Aarav Sharma
            if aarav_app.student_id:
                sib = ApplicationSibling(
                    school_id=admin_user.school_id,
                    application_id=ananya_app.id,
                    student_id=aarav_app.student_id,
                    name="Aarav Sharma",
                    age=6,
                    school_name="Sunrise Public School (Class 1-A)",
                )
                db.add(sib)
                db.flush()
                svc.refresh_claims(db, ananya_app)

            # Medical
            med2 = ApplicationMedical(
                school_id=admin_user.school_id,
                application_id=ananya_app.id,
                blood_group="O+",
                known_allergies="Mild pollen allergy in spring",
                chronic_conditions=None,
                regular_medication="Cetirizine as needed",
                emergency_doctor="Dr. Amit Verma (Father)",
                emergency_doctor_phone="9839011223",
                consent_for_emergency_treatment=True,
            )
            db.add(med2)
            db.flush()

            # Submit & Pay Fee -> Auto-Enroll
            svc.submit(db, ananya_app, actor=admin_user)
            conv_svc.collect(
                db,
                ananya_app,
                actor=admin_user,
                purpose=ApplicationFeePurpose.application_fee,
                amount=Decimal("500.00"),
                method="upi",
                reference="UPI-HDFC-998822",
            )
            db.commit()
            st = db.get(Student, ananya_app.student_id)
            print(f"Ananya Verma enrolled! Student ID: {ananya_app.student_id}, Adm No: {st.admission_no if st else 'N/A'}")

    finally:
        db.close()

if __name__ == "__main__":
    seed_demo_students()
