"""Seeds live public announcements for Sunrise School in the database.

Simulates publishing by Admin/Principal through the existing ERP architecture.
"""

from datetime import datetime, UTC
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from sqlalchemy import select
from app.core.db import SessionLocal
from app.models import Notice, NoticeAudience, School, User


ANNOUNCEMENTS = [
    {
        "title": "CBSE Class X & XII Board Results 2025–26: 100% Pass Rate with Top Honors",
        "summary": "Sunrise School celebrates outstanding CBSE board results with over 30% of candidates scoring 90% and above aggregate.",
        "body": "Sunrise School, Gomti Nagar, Lucknow is proud to announce another year of stellar academic excellence in the CBSE Class X and XII Board Examinations. 100% of our registered candidates cleared with distinction and first division honors. The School Management Committee and Principal Dr. Ananya Sengupta congratulate our hardworking students, dedicated faculty mentors, and supportive parents. Special felicitations will be awarded at the upcoming Academic Honors Assembly.",
        "category": "Achievement",
        "is_public": True,
        "is_pinned": True,
        "audience": NoticeAudience.all,
    },
    {
        "title": "Admissions Open for Academic Session 2026–27 (Pre-Primary to Grade XI)",
        "summary": "Online registration is now open for prospective students for the upcoming academic session. No application fees required.",
        "body": "Applications are officially open for admissions into Pre-Primary (Nursery, LKG, UKG) and Grades 1 through 9 & 11 (Science, Commerce, Humanities streams) for the Academic Session 2026–27. Prospective families may submit an online application dossier directly through our official admission portal. Campus tours and personal admissions counselling sessions are available Monday through Saturday. Early submission is recommended due to limited seat allocations.",
        "category": "Admission",
        "is_public": True,
        "is_pinned": True,
        "audience": NoticeAudience.all,
    },
    {
        "title": "Annual Science, STEM & Innovation Expo 2026",
        "summary": "Experience hands-on student robotics, AI prototypes, and composite science projects at the Central Campus.",
        "body": "Sunrise School cordially invites parents, guardians, and education enthusiasts to our Annual STEM & Innovation Expo. Students from the middle and secondary stages will showcase working prototypes developed in our Atal Tinkering Lab, including IoT home automations, solar trackers, and biological soil fertility sensors. Venue: Central Academic Quadrangle. Timings: 9:30 AM to 3:00 PM.",
        "category": "Event",
        "is_public": True,
        "is_pinned": False,
        "audience": NoticeAudience.all,
    },
    {
        "title": "Commencement of Senior Secondary Career Counselling & University Seminars",
        "summary": "Comprehensive guidance sessions on CUET, JEE, NEET, and liberal arts admissions for Grades 11 and 12.",
        "body": "The Academic Guidance Cell announces a series of expert-led career orientation seminars tailored for senior secondary students across Science, Commerce, and Humanities streams. Sessions will address emerging career pathways, profile building, and undergraduate entrance preparation for premier universities in India and abroad.",
        "category": "Academic",
        "is_public": True,
        "is_pinned": False,
        "audience": NoticeAudience.all,
    },
    {
        "title": "Autumn Break & Dussehra Recess Schedule",
        "summary": "School will observe autumn break from 10th to 16th October. Classes resume regularly thereafter.",
        "body": "In accordance with the approved Academic Calendar 2026–27, Sunrise School will remain closed for the Autumn Recess and Dussehra celebrations from 10th to 16th October. Classes will resume with normal summer timings on Monday, 17th October. The administrative office and front desk will operate for admission enquiries between 9:00 AM and 1:00 PM during the recess.",
        "category": "Holiday",
        "is_public": True,
        "is_pinned": False,
        "audience": NoticeAudience.all,
    },
    {
        "title": "Term 1 Parent-Teacher Interaction & Performance Dossier Release",
        "summary": "Parent-Teacher Meeting scheduled for Saturday, 24th October. Detailed progress reports will be shared.",
        "body": "The First Term Parent-Teacher Interaction will be conducted in person on Saturday, 24th October, from 8:30 AM to 1:00 PM. Parents are requested to adhere to the designated time slots shared by class mentors to ensure focused one-on-one academic discussion and review of holistic student portfolios.",
        "category": "Notice",
        "is_public": True,
        "is_pinned": False,
        "audience": NoticeAudience.all,
    },
]


def seed():
    db = SessionLocal()
    try:
        school = db.scalar(select(School).where(School.code == "SPS"))
        if not school:
            school = db.scalar(select(School).order_by(School.id.asc()))
        if not school:
            print("Error: No school found in database.")
            return

        admin_user = db.scalar(
            select(User)
            .where(User.school_id == school.id, User.email.like("%admin%"))
            .order_by(User.id.asc())
        )
        if not admin_user:
            admin_user = db.scalar(select(User).where(User.school_id == school.id).order_by(User.id.asc()))
        if not admin_user:
            print("Error: No user found to author notices.")
            return

        print(f"Publishing public announcements for {school.name} (Code: {school.code}) as {admin_user.full_name}...")

        count = 0
        now = datetime.now(UTC)
        for data in ANNOUNCEMENTS:
            # Check if an announcement with this title already exists
            existing = db.scalar(
                select(Notice).where(Notice.school_id == school.id, Notice.title == data["title"])
            )
            if existing:
                existing.category = data["category"]
                existing.is_public = data["is_public"]
                existing.is_pinned = data["is_pinned"]
                existing.summary = data["summary"]
                existing.body = data["body"]
                print(f"  Updated existing: {data['title'][:50]}...")
            else:
                notice = Notice(
                    school_id=school.id,
                    title=data["title"],
                    body=data["body"],
                    audience=data["audience"],
                    class_section_id=None,
                    published_by=admin_user.id,
                    published_at=now,
                    category=data["category"],
                    is_public=data["is_public"],
                    is_pinned=data["is_pinned"],
                    summary=data["summary"],
                )
                db.add(notice)
                count += 1
                print(f"  Created new: {data['title'][:50]}...")

        db.commit()
        print(f"Done! {count} new public announcements created and existing updated.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
