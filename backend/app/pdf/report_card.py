"""CBSE Report Card A4 PDF, generated on demand for a student and exam."""

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.orm import Session

from app.models import Exam, School, Student
from app.services import assessment
from app.services.common import require_current_enrolment


def build_report_card_pdf(db: Session, student_id: int, exam_id: int) -> bytes:
    student = db.get(Student, student_id)
    exam = db.get(Exam, exam_id)
    if not student or not exam:
        raise ValueError("Student or exam not found")
    school = db.get(School, student.school_id)
    enrolment = require_current_enrolment(db, student.id)
    rc = assessment.report_card(db, student_id, exam_id)

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "SchoolTitle",
        parent=styles["Heading1"],
        fontSize=18,
        leading=22,
        alignment=1,  # Center
        textColor=colors.HexColor("#1e3a8a"),
        fontName="Helvetica-Bold",
    )
    sub_title_style = ParagraphStyle(
        "SubTitle",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        alignment=1,
        textColor=colors.HexColor("#475569"),
    )
    badge_style = ParagraphStyle(
        "Badge",
        parent=styles["Normal"],
        fontSize=12,
        leading=16,
        alignment=1,
        textColor=colors.HexColor("#0f172a"),
        fontName="Helvetica-Bold",
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#1e293b"),
    )
    bold_style = ParagraphStyle(
        "Bold",
        parent=body_style,
        fontName="Helvetica-Bold",
    )

    story = []

    # 1. School Header
    school_name = school.name if school else "Sunrise Public School"
    story.append(Paragraph(school_name.upper(), title_style))
    story.append(Paragraph("CBSE Affiliation No. 2130001 · Sector B, Gomti Nagar, Lucknow - 226010", sub_title_style))
    story.append(Paragraph(f"OFFICIAL ACADEMIC PROGRESS REPORT · {rc.exam_name.upper()}", badge_style))
    story.append(Spacer(1, 4 * mm))

    # 2. Student Info Card
    info_data = [
        [
            Paragraph(f"<b>Student Name:</b> {rc.student_name}", body_style),
            Paragraph(f"<b>Admission No:</b> {student.admission_no}", body_style),
        ],
        [
            Paragraph(f"<b>Class & Section:</b> {rc.class_label}", body_style),
            Paragraph(f"<b>Roll No:</b> {enrolment.roll_no or '-'}", body_style),
        ],
        [
            Paragraph("<b>Academic Session:</b> 2025-26", body_style),
            Paragraph(f"<b>Exam Term:</b> {exam.term.capitalize()}", body_style),
        ],
    ]
    info_table = Table(info_data, colWidths=[90 * mm, 90 * mm])
    info_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(info_table)
    story.append(Spacer(1, 5 * mm))

    # 3. Subject-wise Marks Table
    marks_header = [
        Paragraph("<b>Subject</b>", bold_style),
        Paragraph("<b>Max Marks</b>", bold_style),
        Paragraph("<b>Marks Obtained</b>", bold_style),
        Paragraph("<b>Percentage</b>", bold_style),
        Paragraph("<b>Grade</b>", bold_style),
    ]
    marks_rows = [marks_header]

    for r in rc.rows:
        obtained_text = (
            "Absent" if r.is_absent else ("Exempted" if r.is_exempted else str(r.marks_obtained or "-"))
        )
        pct_text = f"{r.percent:.1f}%" if r.percent is not None else "-"
        grade_text = r.grade or "-"
        marks_rows.append(
            [
                Paragraph(r.subject, body_style),
                Paragraph(str(r.max_marks), body_style),
                Paragraph(obtained_text, body_style),
                Paragraph(pct_text, body_style),
                Paragraph(grade_text, bold_style),
            ]
        )

    # Summary row
    overall_pct = f"{rc.overall_percent:.1f}%" if rc.overall_percent is not None else "-"
    overall_grd = rc.overall_grade or "-"
    marks_rows.append(
        [
            Paragraph("<b>GRAND TOTAL</b>", bold_style),
            Paragraph(f"<b>{rc.total_max}</b>", bold_style),
            Paragraph(f"<b>{rc.total_obtained}</b>", bold_style),
            Paragraph(f"<b>{overall_pct}</b>", bold_style),
            Paragraph(f"<b>{overall_grd}</b>", bold_style),
        ]
    )

    marks_table = Table(marks_rows, colWidths=[60 * mm, 30 * mm, 30 * mm, 30 * mm, 30 * mm])
    marks_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#94a3b8")),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f1f5f9")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(marks_table)
    story.append(Spacer(1, 8 * mm))

    # 4. Grading Scale Legend
    scale_note = (
        "<b>CBSE 8-Point Scale:</b> A1 (91-100%), A2 (81-90%), B1 (71-80%), B2 (61-70%), "
        "C1 (51-60%), C2 (41-50%), D (33-40%), E (Needs Improvement / Essential Repeat)"
    )
    story.append(Paragraph(scale_note, sub_title_style))
    story.append(Spacer(1, 14 * mm))

    # 5. Signatures
    sig_data = [
        [
            Paragraph("____________________________<br/><b>Class Teacher</b>", sub_title_style),
            Paragraph("____________________________<br/><b>Exam In-charge</b>", sub_title_style),
            Paragraph("____________________________<br/><b>Principal / Stamp</b>", sub_title_style),
        ]
    ]
    sig_table = Table(sig_data, colWidths=[60 * mm, 60 * mm, 60 * mm])
    sig_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    story.append(sig_table)

    doc.build(story)
    return buf.getvalue()
