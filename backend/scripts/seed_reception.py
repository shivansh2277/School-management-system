"""Seed reception demo data: Directory contacts, found items, authorized persons."""
from datetime import date, timedelta
from app.core.db import SessionLocal
from app.models import DirectoryContact, FoundItem, Student, StudentAuthorizedPerson, User

def seed_reception():
    db = SessionLocal()
    try:
        school_id = 1
        # Check if contacts exist
        existing_contacts = db.query(DirectoryContact).filter_by(school_id=school_id).count()
        if existing_contacts == 0:
            contacts = [
                DirectoryContact(
                    school_id=school_id,
                    category="Medical",
                    name="City General Hospital & Trauma Centre",
                    designation_or_department="Emergency Response / Casualty",
                    phone_primary="+91 98765 43210",
                    phone_secondary="+91 11 2345 6700",
                    email="emergency@cityhospital.org",
                    address="Ring Road, Sector 4, New Delhi",
                    operating_hours="24x7 (Emergency)",
                    is_emergency=True,
                    display_order=1,
                    notes="Primary emergency hospital tie-up with dedicated student ward.",
                ),
                DirectoryContact(
                    school_id=school_id,
                    category="Law & Order",
                    name="Sector 12 Police Station",
                    designation_or_department="SHO / Women & Child Safety Cell",
                    phone_primary="112",
                    phone_secondary="+91 11 2345 6789",
                    email="sho-sector12@delhipolice.gov.in",
                    address="Police Station Complex, Sector 12, New Delhi",
                    operating_hours="24x7",
                    is_emergency=True,
                    display_order=2,
                    notes="Local beat officer: Insp. Vikram Singh (+91 98111 00001).",
                ),
                DirectoryContact(
                    school_id=school_id,
                    category="Medical",
                    name="School Pediatric Clinic & Ambulance",
                    designation_or_department="Campus Medical Center",
                    phone_primary="+91 98765 43211",
                    email="infirmary@sunrisepublic.edu",
                    address="Block A, Ground Floor, School Campus",
                    operating_hours="7:30 AM - 4:30 PM",
                    is_emergency=True,
                    display_order=3,
                    notes="Dr. Anita Sharma on duty with campus emergency defibrillator and oxygen kit.",
                ),
                DirectoryContact(
                    school_id=school_id,
                    category="Emergency",
                    name="District Fire & Rescue Services",
                    designation_or_department="Control Room",
                    phone_primary="101",
                    phone_secondary="+91 11 2345 0101",
                    address="Fire Station, Main Arterial Road, New Delhi",
                    operating_hours="24x7",
                    is_emergency=True,
                    display_order=4,
                    notes="School hydrants tested and certified quarterly.",
                ),
                DirectoryContact(
                    school_id=school_id,
                    category="Administration",
                    name="District Education Officer (DEO)",
                    designation_or_department="Directorate of Education, Zone 4",
                    phone_primary="+91 11 2345 1122",
                    email="deo-zone4@edudel.nic.in",
                    address="Vikas Bhawan, Civil Lines, New Delhi",
                    operating_hours="9:30 AM - 5:30 PM (Mon-Fri)",
                    is_emergency=False,
                    display_order=5,
                    notes="Contact for CBSE compliance and zonal liaison.",
                ),
                DirectoryContact(
                    school_id=school_id,
                    category="Transport",
                    name="School Bus Fleet Contractor",
                    designation_or_department="Apex Logistics & Fleet Ops",
                    phone_primary="+91 98765 43215",
                    phone_secondary="+91 98765 43216",
                    email="dispatch@apexlogistics.com",
                    address="Transport Depot, Bypass Road, New Delhi",
                    operating_hours="6:00 AM - 7:00 PM",
                    is_emergency=False,
                    display_order=6,
                    notes="Fleet manager: Mr. Harpreet Singh. Real-time GPS operations desk.",
                ),
                DirectoryContact(
                    school_id=school_id,
                    category="Utilities",
                    name="Chief Campus Electrician & Maintenance",
                    designation_or_department="Facilities & Engineering",
                    phone_primary="+91 98765 43219",
                    email="facilities@sunrisepublic.edu",
                    address="Maintenance Wing, Basement, Block C",
                    operating_hours="7:00 AM - 6:00 PM",
                    is_emergency=False,
                    display_order=7,
                    notes="Campus DG set and UPS backup switchover desk.",
                ),
            ]
            db.add_all(contacts)
            db.commit()
            print(f"Seeded {len(contacts)} directory contacts.")

        # Check sample found items
        if db.query(FoundItem).filter_by(school_id=school_id).count() == 0:
            rec = db.query(User).filter_by(email="receptionist@sunrisepublic.edu").first()
            rec_id = rec.id if rec else 1
            rec_name = rec.full_name if rec else "Receptionist"
            items = [
                FoundItem(
                    school_id=school_id,
                    item_name="Blue Milton Stainless Steel Water Bottle",
                    category="accessories",
                    description="750ml blue metallic bottle with silver cap and small Avengers sticker.",
                    found_location="Library Reading Hall, Table 4",
                    found_date=date.today() - timedelta(days=1),
                    found_time="11:45 AM",
                    recorded_by_id=rec_id,
                    recorded_by_name=rec_name,
                    status="broadcasted",
                ),
                FoundItem(
                    school_id=school_id,
                    item_name="Titan Fastrack Sports Watch",
                    category="electronics",
                    description="Black dial analog-digital watch with silicon strap.",
                    found_location="Senior Sports Pavilion",
                    found_date=date.today() - timedelta(days=3),
                    found_time="03:30 PM",
                    recorded_by_id=rec_id,
                    recorded_by_name=rec_name,
                    status="reported",
                ),
            ]
            db.add_all(items)
            db.commit()
            print(f"Seeded {len(items)} found items.")

        # Check authorized persons for first 2 students
        students = db.query(Student).filter_by(school_id=school_id).order_by(Student.id).limit(3).all()
        if students:
            for s in students:
                count = db.query(StudentAuthorizedPerson).filter_by(student_id=s.id).count()
                if count == 0:
                    ap1 = StudentAuthorizedPerson(
                        school_id=school_id,
                        student_id=s.id,
                        name="Rajesh Sharma",
                        relationship="Uncle (Maternal)",
                        phone="+91 98111 22334",
                        id_proof_type="Aadhaar",
                        id_proof_number="XXXX-XXXX-4589",
                        notes="Authorized for regular after-school pickup.",
                        is_active=True,
                    )
                    ap2 = StudentAuthorizedPerson(
                        school_id=school_id,
                        student_id=s.id,
                        name="Sunita Sharma",
                        relationship="Aunt",
                        phone="+91 98111 22335",
                        id_proof_type="Driver License",
                        id_proof_number="DL-0420110012345",
                        notes="Authorized for emergency medical or early pickup.",
                        is_active=True,
                    )
                    db.add_all([ap1, ap2])
            db.commit()
            print(f"Seeded authorized pickup persons for {len(students)} students.")

    finally:
        db.close()

if __name__ == "__main__":
    seed_reception()
