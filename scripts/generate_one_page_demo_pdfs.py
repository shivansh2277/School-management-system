"""Generates professional, exactly one-page institutional demo PDFs for Sunrise School.

Output directory: web/public/documents/
All generated PDFs are strictly 1 page in length (A4 size).
"""

import os
import sys
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """Canvas ensuring exact page footer and tracking page count."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        if num_pages != 1:
            raise ValueError(f"Document exceeded 1 page! Generated {num_pages} pages.")
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_footer()
            super().showPage()
        super().save()

    def draw_footer(self):
        self.saveState()
        self.setFont("Helvetica", 7.5)
        self.setFillColor(colors.HexColor("#64748b"))
        # Top rule for footer
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(28, 30, A4[0] - 28, 30)
        footer_text = "SUNRISE SCHOOL • Gomti Nagar, Lucknow, UP • Demo Institutional Document • Official Credentials 'To be configured'"
        self.drawString(28, 20, footer_text)
        self.drawRightString(A4[0] - 28, 20, "Page 1 of 1")
        self.restoreState()


NAVY = colors.HexColor("#042954")
SLATE_900 = colors.HexColor("#0f172a")
AMBER = colors.HexColor("#d97706")
BG_LIGHT = colors.HexColor("#f8fafc")
BORDER = colors.HexColor("#cbd5e1")


def get_styles():
    base = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "DocTitle",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=14,
        textColor=NAVY,
        alignment=1,  # Center
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#475569"),
        alignment=1,
    )
    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=NAVY,
    )
    cell_bold = ParagraphStyle(
        "CellBold",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9.5,
        textColor=SLATE_900,
    )
    cell_text = ParagraphStyle(
        "CellText",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#334155"),
    )
    cell_text_right = ParagraphStyle(
        "CellTextRight",
        parent=cell_text,
        alignment=2,
    )
    note_style = ParagraphStyle(
        "NoteText",
        parent=base["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=7,
        leading=8.5,
        textColor=colors.HexColor("#64748b"),
    )
    return {
        "title": title_style,
        "subtitle": subtitle_style,
        "heading": heading_style,
        "cell_bold": cell_bold,
        "cell_text": cell_text,
        "cell_text_right": cell_text_right,
        "note": note_style,
    }


def make_header(doc_title, ref_no, styles):
    flowables = []
    # School Header
    flowables.append(
        Paragraph("<b>SUNRISE SCHOOL</b>", styles["title"])
    )
    flowables.append(
        Paragraph("Sector 4, Gomti Nagar, Lucknow, Uttar Pradesh — 226010 | Tel: +91 522 299 0000 | Estd. 2011", styles["subtitle"])
    )
    flowables.append(Spacer(1, 4))
    flowables.append(
        HRFlowable(width="100%", thickness=1.5, color=NAVY, spaceAfter=4, spaceBefore=0)
    )
    # Document Sub-header
    sub_table_data = [
        [
            Paragraph(f"<b>{doc_title.upper()}</b>", styles["heading"]),
            Paragraph(f"<b>Doc Ref:</b> {ref_no}", styles["cell_text_right"]),
        ]
    ]
    t = Table(sub_table_data, colWidths=[380, 159])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    flowables.append(t)
    flowables.append(Spacer(1, 4))
    return flowables


def build_pdf(filepath, doc_title, ref_no, content_flowables):
    doc = SimpleDocTemplate(
        str(filepath),
        pagesize=A4,
        leftMargin=28,
        rightMargin=28,
        topMargin=26,
        bottomMargin=36,
    )
    styles = get_styles()
    story = []
    story.extend(make_header(doc_title, ref_no, styles))
    story.extend(content_flowables)
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Verified 1-page PDF: {filepath.name}")


# ----------------------------------------------------------------------
# 1. Public Disclosure Summary (Mandatory Public Disclosure)
# ----------------------------------------------------------------------
def generate_public_disclosure_summary(out_dir, styles):
    rows = [
        [Paragraph("<b>S.No.</b>", styles["cell_bold"]), Paragraph("<b>Information / Parameter</b>", styles["cell_bold"]), Paragraph("<b>Details & Compliance Status</b>", styles["cell_bold"])],
        [Paragraph("1", styles["cell_text"]), Paragraph("Name of the Institution", styles["cell_bold"]), Paragraph("Sunrise School (Sunrise Public School)", styles["cell_text"])],
        [Paragraph("2", styles["cell_text"]), Paragraph("Affiliation Status & Level", styles["cell_bold"]), Paragraph("CBSE Affiliated • Senior Secondary (Demo information)", styles["cell_text"])],
        [Paragraph("3", styles["cell_text"]), Paragraph("Affiliation No. / School Code", styles["cell_bold"]), Paragraph("Demo information / To be configured", styles["cell_text"])],
        [Paragraph("4", styles["cell_text"]), Paragraph("Complete Postal Address", styles["cell_bold"]), Paragraph("Sector 4, Gomti Nagar, Lucknow, Uttar Pradesh — 226010", styles["cell_text"])],
        [Paragraph("5", styles["cell_text"]), Paragraph("Principal Name & Qualification", styles["cell_bold"]), Paragraph("Dr. Ananya Sengupta, M.Sc., M.Ed., Ph.D.", styles["cell_text"])],
        [Paragraph("6", styles["cell_text"]), Paragraph("Official Email & Contact Desk", styles["cell_bold"]), Paragraph("info@sunrisepublic.edu • Tel: +91 522 299 0000", styles["cell_text"])],
        [Paragraph("7", styles["cell_text"]), Paragraph("School Management Committee (SMC)", styles["cell_bold"]), Paragraph("Constituted as per CBSE Bye-Laws (15 Members)", styles["cell_text"])],
        [Paragraph("8", styles["cell_text"]), Paragraph("Building Safety & Structural Certificate", styles["cell_bold"]), Paragraph("Issued by Municipal Corporation (Demo: Valid through 2028)", styles["cell_text"])],
        [Paragraph("9", styles["cell_text"]), Paragraph("Fire Safety & NOC Certificate", styles["cell_bold"]), Paragraph("Chief Fire Officer Lucknow (Demo: Valid through 2027)", styles["cell_text"])],
        [Paragraph("10", styles["cell_text"]), Paragraph("Safe Drinking Water & Sanitary Cert.", styles["cell_bold"]), Paragraph("Public Health Department (Demo: Annual Inspection Green)", styles["cell_text"])],
        [Paragraph("11", styles["cell_text"]), Paragraph("Fee Structure Notification", styles["cell_bold"]), Paragraph("Published annually; strictly adhering to state regulatory norms", styles["cell_text"])],
        [Paragraph("12", styles["cell_text"]), Paragraph("Academic Session Period", styles["cell_bold"]), Paragraph("1st April to 31st March (Vacation: May 20 to June 30)", styles["cell_text"])],
        [Paragraph("13", styles["cell_text"]), Paragraph("Teacher-Student Ratio", styles["cell_bold"]), Paragraph("1 : 20 (Optimal interactive learning ratio across all wings)", styles["cell_text"])],
        [Paragraph("14", styles["cell_text"]), Paragraph("Grievance Redressal / POCSO Committee", styles["cell_bold"]), Paragraph("Internal Committee constituted; Officer: grievance@sunrisepublic.edu", styles["cell_text"])],
    ]
    t = Table(rows, colWidths=[35, 204, 300])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BG_LIGHT),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    note = Paragraph("<b>Note:</b> In compliance with CBSE Mandatory Public Disclosure guidelines (Appendix IX). Official statutory certificates and credentials are provided for demonstration purposes.", styles["note"])
    return [t, Spacer(1, 6), note]


# ----------------------------------------------------------------------
# 2. School Information
# ----------------------------------------------------------------------
def generate_school_information(out_dir, styles):
    rows = [
        [Paragraph("<b>Category</b>", styles["cell_bold"]), Paragraph("<b>Institutional Profile Data</b>", styles["cell_bold"])],
        [Paragraph("Establishment & Motto", styles["cell_bold"]), Paragraph("Established 2011 • Motto: 'Nurturing Curious Minds. Building Confident Futures.'", styles["cell_text"])],
        [Paragraph("Campus Governance", styles["cell_bold"]), Paragraph("Sunrise Educational Society, Lucknow (Registered Non-Profit Trust)", styles["cell_text"])],
        [Paragraph("Affiliation Board", styles["cell_bold"]), Paragraph("Central Board of Secondary Education (CBSE), New Delhi (Demo information)", styles["cell_text"])],
        [Paragraph("Classes Offered", styles["cell_bold"]), Paragraph("Kindergarten (Nursery, LKG, UKG) to Senior Secondary (Grades 1 to 12)", styles["cell_text"])],
        [Paragraph("Curriculum Framework", styles["cell_bold"]), Paragraph("National Education Policy (NEP 2020) 5+3+3+4 Pedagogical Structure", styles["cell_text"])],
        [Paragraph("Senior Secondary Streams", styles["cell_bold"]), Paragraph("1. Science (PCM/PCB) • 2. Commerce • 3. Humanities", styles["cell_text"])],
        [Paragraph("Medium of Instruction", styles["cell_bold"]), Paragraph("English Medium (Hindi taught as compulsory second/third language)", styles["cell_text"])],
        [Paragraph("School Timings", styles["cell_bold"]), Paragraph("Summer: 7:30 AM – 1:30 PM | Winter: 8:00 AM – 2:00 PM (Monday to Saturday)", styles["cell_text"])],
        [Paragraph("Student Welfare", styles["cell_bold"]), Paragraph("Dedicated Child Counsellor, Special Educator, and Full-time Medical Infirmary", styles["cell_text"])],
        [Paragraph("Transportation", styles["cell_bold"]), Paragraph("Fleet of GPS-tracked school buses with CCTV and female attendants", styles["cell_text"])],
    ]
    t = Table(rows, colWidths=[150, 389])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BG_LIGHT),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    note = Paragraph("<b>Governance Declaration:</b> Sunrise School is committed to egalitarian admissions and values-centered academic excellence. Official credentials marked 'Demo / To be configured'.", styles["note"])
    return [t, Spacer(1, 8), note]


# ----------------------------------------------------------------------
# 3. Infrastructure Overview
# ----------------------------------------------------------------------
def generate_infrastructure_overview(out_dir, styles):
    rows = [
        [Paragraph("<b>Infrastructure Asset</b>", styles["cell_bold"]), Paragraph("<b>Capacity / Specification</b>", styles["cell_bold"]), Paragraph("<b>Remarks & Safety Standards</b>", styles["cell_bold"])],
        [Paragraph("Total Campus Land Area", styles["cell_bold"]), Paragraph("14,200 sq. meters (~3.5 Acres)", styles["cell_text"]), Paragraph("Single compact campus, secure boundary walls", styles["cell_text"])],
        [Paragraph("Built-up Area", styles["cell_bold"]), Paragraph("8,600 sq. meters (3 Wings)", styles["cell_text"]), Paragraph("Earthquake-resistant RCC structure", styles["cell_text"])],
        [Paragraph("Playground & Athletics Turf", styles["cell_bold"]), Paragraph("5,200 sq. meters outdoor area", styles["cell_text"]), Paragraph("400m running track, football turf, cricket nets", styles["cell_text"])],
        [Paragraph("Smart Classrooms", styles["cell_bold"]), Paragraph("48 Ergonomic Classrooms", styles["cell_text"]), Paragraph("Interactive digital flat panels, high ventilation", styles["cell_text"])],
        [Paragraph("Composite Science Lab", styles["cell_bold"]), Paragraph("1,200 sq. ft. fully equipped", styles["cell_text"]), Paragraph("Physics, Chemistry & Biology apparatus with shower", styles["cell_text"])],
        [Paragraph("Computer & AI Studio", styles["cell_bold"]), Paragraph("60 Modern Dual-Boot Desktops", styles["cell_text"]), Paragraph("High-speed gigabit fiber, AI/Coding syllabus", styles["cell_text"])],
        [Paragraph("Atal Tinkering / STEM Lab", styles["cell_bold"]), Paragraph("Robotics & IoT Prototyping kits", styles["cell_text"]), Paragraph("Arduino, 3D printing & sensor modules", styles["cell_text"])],
        [Paragraph("Central Knowledge Hub", styles["cell_bold"]), Paragraph("Over 10,500 Books & Periodicals", styles["cell_text"]), Paragraph("Digital catalog, reading rotunda, journal stacks", styles["cell_text"])],
        [Paragraph("Indoor Sports Complex", styles["cell_bold"]), Paragraph("Multi-Court Badminton / TT", styles["cell_text"]), Paragraph("Hardwood anti-skid athletic flooring", styles["cell_text"])],
        [Paragraph("CCTV Surveillance", styles["cell_bold"]), Paragraph("128 High-Definition IP Cameras", styles["cell_text"]), Paragraph("Covering 100% corridors, gates, and perimeters", styles["cell_text"])],
    ]
    t = Table(rows, colWidths=[150, 160, 229])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BG_LIGHT),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    note = Paragraph("<b>Campus Inspection:</b> Infrastructure parameters verified as per CBSE affiliation norms for Senior Secondary institutions.", styles["note"])
    return [t, Spacer(1, 8), note]


# ----------------------------------------------------------------------
# 4. Faculty & Staff Overview
# ----------------------------------------------------------------------
def generate_faculty_overview(out_dir, styles):
    rows = [
        [Paragraph("<b>Staff Cadre</b>", styles["cell_bold"]), Paragraph("<b>Headcount</b>", styles["cell_bold"]), Paragraph("<b>Minimum Required Qualification</b>", styles["cell_bold"]), Paragraph("<b>Responsibilities</b>", styles["cell_bold"])],
        [Paragraph("Principal", styles["cell_bold"]), Paragraph("1", styles["cell_text"]), Paragraph("Ph.D. / M.Sc., M.Ed. (15+ yrs exp)", styles["cell_text"]), Paragraph("Institutional Governance & Academic Vision", styles["cell_text"])],
        [Paragraph("Post Graduate Teachers (PGT)", styles["cell_bold"]), Paragraph("14", styles["cell_text"]), Paragraph("Post Graduate in Subject + B.Ed.", styles["cell_text"]), Paragraph("Senior Secondary Grades 11–12 Instruction", styles["cell_text"])],
        [Paragraph("Trained Graduate Teachers (TGT)", styles["cell_bold"]), Paragraph("18", styles["cell_text"]), Paragraph("Graduate in Subject + B.Ed.", styles["cell_text"]), Paragraph("Middle & Secondary Grades 6–10 Instruction", styles["cell_text"])],
        [Paragraph("Primary Teachers (PRT)", styles["cell_bold"]), Paragraph("16", styles["cell_text"]), Paragraph("Graduate + D.El.Ed. / B.Ed.", styles["cell_text"]), Paragraph("Foundational & Primary Stage Learning", styles["cell_text"])],
        [Paragraph("Pre-Primary / Nursery Mentors", styles["cell_bold"]), Paragraph("8", styles["cell_text"]), Paragraph("NTT / Early Childhood Certification", styles["cell_text"]), Paragraph("Play-Way & Activity-Based Early Childhood", styles["cell_text"])],
        [Paragraph("Special Educator", styles["cell_bold"]), Paragraph("1", styles["cell_text"]), Paragraph("B.Ed. in Special Education (RCI)", styles["cell_text"]), Paragraph("Inclusive Education & Remedial Support", styles["cell_text"])],
        [Paragraph("Student Wellness Counsellor", styles["cell_bold"]), Paragraph("1", styles["cell_text"]), Paragraph("M.A. Psychology / Guidance Dip.", styles["cell_text"]), Paragraph("Adolescent Guidance & Mental Health", styles["cell_text"])],
        [Paragraph("Physical Education Instructors", styles["cell_bold"]), Paragraph("3", styles["cell_text"]), Paragraph("M.P.Ed. / B.P.Ed.", styles["cell_text"]), Paragraph("Athletics, Inter-House Sports, Fitness", styles["cell_text"])],
        [Paragraph("Librarian & Tech Support", styles["cell_bold"]), Paragraph("3", styles["cell_text"]), Paragraph("M.Lib. / B.Tech Computer Science", styles["cell_text"]), Paragraph("Library Stacks & AI/Computer Labs", styles["cell_text"])],
        [Paragraph("Administrative & Office Staff", styles["cell_bold"]), Paragraph("7", styles["cell_text"]), Paragraph("B.Com / Graduate in Relevant Field", styles["cell_text"]), Paragraph("Accounts, Admissions, Reception & Logistics", styles["cell_text"])],
    ]
    t = Table(rows, colWidths=[140, 55, 174, 170])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BG_LIGHT),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    note = Paragraph("<b>Teacher Quality Assurance:</b> 100% of full-time teaching faculty are professionally certified in teacher education (B.Ed./NTT). Teacher-student ratio maintained at 1:20.", styles["note"])
    return [t, Spacer(1, 8), note]


# ----------------------------------------------------------------------
# 5. Academic Information & Results
# ----------------------------------------------------------------------
def generate_academic_information(out_dir, styles):
    rows = [
        [Paragraph("<b>Academic Metric / Stage</b>", styles["cell_bold"]), Paragraph("<b>Curriculum Specification</b>", styles["cell_bold"]), Paragraph("<b>Evaluation Methodology</b>", styles["cell_bold"])],
        [Paragraph("Foundational Stage (Nursery to Gr 2)", styles["cell_bold"]), Paragraph("Play-way discovery, language immersion, basic numeracy", styles["cell_text"]), Paragraph("Continuous holistic tracking (No formal exams)", styles["cell_text"])],
        [Paragraph("Preparatory Stage (Gr 3 to 5)", styles["cell_bold"]), Paragraph("Languages, Mathematics, Environmental Studies, Art", styles["cell_text"]), Paragraph("Skill-based worksheets & term assessments", styles["cell_text"])],
        [Paragraph("Middle Stage (Gr 6 to 8)", styles["cell_bold"]), Paragraph("Physics, Chem, Bio, Social Sci, Coding, Sanskrit/French", styles["cell_text"]), Paragraph("Periodic tests (Term 1 & Term 2) + Practical projects", styles["cell_text"])],
        [Paragraph("Secondary Stage (Gr 9 & 10)", styles["cell_bold"]), Paragraph("CBSE All India Secondary School Exam (AISSE) syllabus", styles["cell_text"]), Paragraph("Internal assessments (20%) + Board Exams (80%)", styles["cell_text"])],
        [Paragraph("Senior Secondary (Gr 11 & 12)", styles["cell_bold"]), Paragraph("Streams: Science (PCM/PCB), Commerce, Humanities", styles["cell_text"]), Paragraph("CBSE AISSCE Board Evaluation & Lab Practicals", styles["cell_text"])],
    ]
    t = Table(rows, colWidths=[150, 210, 179])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BG_LIGHT),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    results_header = Paragraph("<b>THREE-YEAR CBSE BOARD EXAMINATION PERFORMANCE (AISSE / AISSCE)</b>", styles["heading"])
    results_rows = [
        [Paragraph("<b>Academic Year</b>", styles["cell_bold"]), Paragraph("<b>Grade 10 Pass %</b>", styles["cell_bold"]), Paragraph("<b>Grade 10 Above 90%</b>", styles["cell_bold"]), Paragraph("<b>Grade 12 Pass %</b>", styles["cell_bold"]), Paragraph("<b>Grade 12 Above 90%</b>", styles["cell_bold"])],
        [Paragraph("2024–2025 (Demo)", styles["cell_text"]), Paragraph("100%", styles["cell_text"]), Paragraph("32.5% of students", styles["cell_text"]), Paragraph("99.2%", styles["cell_text"]), Paragraph("28.4% of students", styles["cell_text"])],
        [Paragraph("2023–2024 (Demo)", styles["cell_text"]), Paragraph("100%", styles["cell_text"]), Paragraph("30.8% of students", styles["cell_text"]), Paragraph("98.8%", styles["cell_text"]), Paragraph("26.1% of students", styles["cell_text"])],
        [Paragraph("2022–2023 (Demo)", styles["cell_text"]), Paragraph("99.4%", styles["cell_text"]), Paragraph("29.0% of students", styles["cell_text"]), Paragraph("98.5%", styles["cell_text"]), Paragraph("25.0% of students", styles["cell_text"])],
    ]
    t_res = Table(results_rows, colWidths=[120, 100, 119, 100, 100])
    t_res.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BG_LIGHT),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    note = Paragraph("<b>Institutional Record:</b> 100% transition rate to leading universities in India and abroad. Official statistics marked 'Demo / To be configured'.", styles["note"])
    return [t, Spacer(1, 6), results_header, Spacer(1, 4), t_res, Spacer(1, 6), note]


# ----------------------------------------------------------------------
# 6. School Prospectus (1 Page Summary)
# ----------------------------------------------------------------------
def generate_school_prospectus(out_dir, styles):
    rows = [
        [Paragraph("<b>Pillar / Distinctive</b>", styles["cell_bold"]), Paragraph("<b>Institutional Commitment</b>", styles["cell_bold"])],
        [Paragraph("Academic Rigor", styles["cell_bold"]), Paragraph("CBSE curriculum enriched with experiential pedagogy, inquiry-based STEM projects, and critical thinking development.", styles["cell_text"])],
        [Paragraph("Foundational Care", styles["cell_bold"]), Paragraph("1:15 adult-to-child ratio in early foundational grades ensuring every learner receives personalized nurturing and encouragement.", styles["cell_text"])],
        [Paragraph("Tinkering & Robotics", styles["cell_bold"]), Paragraph("Hands-on Atal Tinkering Lab empowering students from Grade 4 onwards with coding, 3D printing, and Arduino automation.", styles["cell_text"])],
        [Paragraph("Sports & Athletic Arena", styles["cell_bold"]), Paragraph("Professional training in basketball, football, cricket, lawn tennis, and martial arts with certified coaches.", styles["cell_text"])],
        [Paragraph("Cultural Heritage", styles["cell_bold"]), Paragraph("Performing arts studio for classical and western music, Kathak and contemporary dance, visual arts, and theatre.", styles["cell_text"])],
        [Paragraph("House System & Values", styles["cell_bold"]), Paragraph("Four houses (Agni, Prithvi, Vayu, Jal) instilling teamwork, healthy competition, social service, and moral courage.", styles["cell_text"])],
        [Paragraph("Global Citizenship", styles["cell_bold"]), Paragraph("Model United Nations (MUN), literary society, climate action club, and community outreach in Gomti Nagar.", styles["cell_text"])],
    ]
    t = Table(rows, colWidths=[140, 399])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BG_LIGHT),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    admissions_header = Paragraph("<b>ADMISSION CYCLE 2026–27 KEY HIGHLIGHTS</b>", styles["heading"])
    adm_rows = [
        [Paragraph("<b>Intake Grades</b>", styles["cell_bold"]), Paragraph("Nursery, LKG, UKG, and Grades 1 to 9 & 11 (Subject to seat availability)", styles["cell_text"])],
        [Paragraph("<b>Application Portal</b>", styles["cell_bold"]), Paragraph("Online 7-step application via official portal at https://sunrisepublic.edu/apply (Zero application fee)", styles["cell_text"])],
        [Paragraph("<b>Campus Visit Hours</b>", styles["cell_bold"]), Paragraph("Monday to Saturday: 8:30 AM to 2:30 PM (Prior appointment via admissions@sunrisepublic.edu)", styles["cell_text"])],
    ]
    t_adm = Table(adm_rows, colWidths=[140, 399])
    t_adm.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BG_LIGHT),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    note = Paragraph("<b>Prospectus Document:</b> Official summary overview for prospective parents. For full interactive inquiry, visit the school office or apply online.", styles["note"])
    return [t, Spacer(1, 6), admissions_header, Spacer(1, 4), t_adm, Spacer(1, 6), note]


# ----------------------------------------------------------------------
# 7. Academic Calendar 2026–27
# ----------------------------------------------------------------------
def generate_academic_calendar(out_dir, styles):
    rows = [
        [Paragraph("<b>Month & Term</b>", styles["cell_bold"]), Paragraph("<b>Key Academic & Institutional Events</b>", styles["cell_bold"]), Paragraph("<b>Holidays & Recess</b>", styles["cell_bold"])],
        [Paragraph("April 2026", styles["cell_bold"]), Paragraph("Session Commencement (Apr 1) • Orientation Week", styles["cell_text"]), Paragraph("Mahavir Jayanti • Good Friday • Eid-ul-Fitr", styles["cell_text"])],
        [Paragraph("May 2026", styles["cell_bold"]), Paragraph("Periodic Assessment 1 (Gr 3–12) • Investiture Ceremony", styles["cell_text"]), Paragraph("Buddha Purnima • Summer Vacation begins (May 20)", styles["cell_text"])],
        [Paragraph("June 2026", styles["cell_bold"]), Paragraph("Faculty Professional Development Workshops", styles["cell_text"]), Paragraph("Summer Vacation continues through June 30", styles["cell_text"])],
        [Paragraph("July 2026", styles["cell_bold"]), Paragraph("School Reopens (Jul 1) • Inter-House Debate Fest", styles["cell_text"]), Paragraph("Muharram (Subject to moon sighting)", styles["cell_text"])],
        [Paragraph("August 2026", styles["cell_bold"]), Paragraph("Independence Day Gala • Science Exhibition", styles["cell_text"]), Paragraph("Independence Day (Aug 15) • Raksha Bandhan", styles["cell_text"])],
        [Paragraph("September 2026", styles["cell_bold"]), Paragraph("Term 1 / Half-Yearly Examinations (Sep 14–26)", styles["cell_text"]), Paragraph("Milad-un-Nabi • Gandhi Jayanti eve", styles["cell_text"])],
        [Paragraph("October 2026", styles["cell_bold"]), Paragraph("Term 1 PTM & Report Card Day • Annual Cultural Udaan", styles["cell_text"]), Paragraph("Gandhi Jayanti (Oct 2) • Dussehra Autumn Break", styles["cell_text"])],
        [Paragraph("November 2026", styles["cell_bold"]), Paragraph("Periodic Assessment 2 • Tarang Annual Sports Meet", styles["cell_text"]), Paragraph("Diwali / Deepawali Break • Guru Nanak Jayanti", styles["cell_text"])],
        [Paragraph("December 2026", styles["cell_bold"]), Paragraph("Pre-Board 1 (Grades 10 & 12) • Winter Carnival", styles["cell_text"]), Paragraph("Christmas (Dec 25) • Winter Break (Dec 28 onwards)", styles["cell_text"])],
        [Paragraph("January 2027", styles["cell_bold"]), Paragraph("Pre-Board 2 (Grades 10 & 12) • Republic Day Parade", styles["cell_text"]), Paragraph("Winter Break ends (Jan 8) • Republic Day (Jan 26)", styles["cell_text"])],
        [Paragraph("February 2027", styles["cell_bold"]), Paragraph("Practical Exams & Project Vivas • Farewell Ceremony", styles["cell_text"]), Paragraph("Maha Shivratri", styles["cell_text"])],
        [Paragraph("March 2027", styles["cell_bold"]), Paragraph("Annual Final Examinations • Graduation & Results Day", styles["cell_text"]), Paragraph("Holi Festival of Colors (Mar 22–24)", styles["cell_text"])],
    ]
    t = Table(rows, colWidths=[100, 259, 180])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BG_LIGHT),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    note = Paragraph("<b>Notice:</b> Total working days: 220 days. Minor modifications to gazetted holidays are notified via official circulars and ERP alerts.", styles["note"])
    return [t, Spacer(1, 6), note]


# ----------------------------------------------------------------------
# 8. Admission Guidelines 2026–27
# ----------------------------------------------------------------------
def generate_admission_guidelines(out_dir, styles):
    rows = [
        [Paragraph("<b>Admission Stage / Step</b>", styles["cell_bold"]), Paragraph("<b>Procedural Requirement & Actionable Guidance</b>", styles["cell_bold"])],
        [Paragraph("Step 1: Online Registration", styles["cell_bold"]), Paragraph("Submit official application at https://sunrisepublic.edu/apply. No application registration fee is charged.", styles["cell_text"])],
        [Paragraph("Step 2: Readiness Interaction", styles["cell_bold"]), Paragraph("Foundational grades: Informal child-friendly developmental interaction. Grades 3+: Age-appropriate concept review.", styles["cell_text"])],
        [Paragraph("Step 3: Document Verification", styles["cell_bold"]), Paragraph("Verification of birth certificate, previous mark sheets, transfer certificate (TC), and guardian residence proof.", styles["cell_text"])],
        [Paragraph("Step 4: Offer & Enrollment", styles["cell_bold"]), Paragraph("Provisional offer issued via portal; confirmed atomically upon fee settlement through the secure payment cell.", styles["cell_text"])],
    ]
    t = Table(rows, colWidths=[150, 389])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BG_LIGHT),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    age_header = Paragraph("<b>AGE ELIGIBILITY NORMS (AS ON 31ST MARCH 2026)</b>", styles["heading"])
    age_rows = [
        [Paragraph("<b>Class / Grade</b>", styles["cell_bold"]), Paragraph("<b>Minimum Age Required</b>", styles["cell_bold"]), Paragraph("<b>Permissible DOB Range (Demo)</b>", styles["cell_bold"])],
        [Paragraph("Pre-Nursery / Nursery", styles["cell_bold"]), Paragraph("3 Years completed", styles["cell_text"]), Paragraph("01-Apr-2022 to 31-Mar-2023", styles["cell_text"])],
        [Paragraph("Lower Kindergarten (LKG)", styles["cell_bold"]), Paragraph("4 Years completed", styles["cell_text"]), Paragraph("01-Apr-2021 to 31-Mar-2022", styles["cell_text"])],
        [Paragraph("Upper Kindergarten (UKG)", styles["cell_bold"]), Paragraph("5 Years completed", styles["cell_text"]), Paragraph("01-Apr-2020 to 31-Mar-2021", styles["cell_text"])],
        [Paragraph("Grade 1", styles["cell_bold"]), Paragraph("6 Years completed (NEP norm)", styles["cell_text"]), Paragraph("01-Apr-2019 to 31-Mar-2020", styles["cell_text"])],
        [Paragraph("Grades 2 to 9", styles["cell_bold"]), Paragraph("Based on previous class TC", styles["cell_text"]), Paragraph("Progressive age matrix compliant with CBSE", styles["cell_text"])],
        [Paragraph("Grade 11 (Streams)", styles["cell_bold"]), Paragraph("Class 10 CBSE/ICSE Board Passed", styles["cell_text"]), Paragraph("Subject to stream cut-off marks in AISSE", styles["cell_text"])],
    ]
    t_age = Table(age_rows, colWidths=[150, 160, 229])
    t_age.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BG_LIGHT),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    note = Paragraph("<b>Mandatory Documents:</b> 1. Municipal Birth Certificate; 2. Recent passport-sized color photos; 3. Aadhaar copy; 4. Sibling admission proof (if applying under sibling category).", styles["note"])
    return [t, Spacer(1, 6), age_header, Spacer(1, 4), t_age, Spacer(1, 6), note]


# ----------------------------------------------------------------------
# 9. Fee Structure 2026–27
# ----------------------------------------------------------------------
def generate_fee_structure(out_dir, styles):
    rows = [
        [Paragraph("<b>Grade Wing / Stage</b>", styles["cell_bold"]), Paragraph("<b>Composite Annual Fee (₹)</b>", styles["cell_bold"]), Paragraph("<b>Quarterly Instalment (₹)</b>", styles["cell_bold"]), Paragraph("<b>Key Inclusions & Highlights</b>", styles["cell_bold"])],
        [Paragraph("Pre-Primary (Nursery–UKG)", styles["cell_bold"]), Paragraph("₹ 48,000", styles["cell_text"]), Paragraph("₹ 12,000 / quarter", styles["cell_text"]), Paragraph("Activity kits, smart-class, arts, field trips", styles["cell_text"])],
        [Paragraph("Primary Wing (Grades 1–5)", styles["cell_bold"]), Paragraph("₹ 54,000", styles["cell_text"]), Paragraph("₹ 13,500 / quarter", styles["cell_text"]), Paragraph("Composite lab, computer coding, sports tuition", styles["cell_text"])],
        [Paragraph("Middle Wing (Grades 6–8)", styles["cell_bold"]), Paragraph("₹ 60,000", styles["cell_text"]), Paragraph("₹ 15,000 / quarter", styles["cell_text"]), Paragraph("Science labs, robotics workshop, language club", styles["cell_text"])],
        [Paragraph("Secondary Wing (Grades 9–10)", styles["cell_bold"]), Paragraph("₹ 66,000", styles["cell_text"]), Paragraph("₹ 16,500 / quarter", styles["cell_text"]), Paragraph("CBSE registration, composite practicals, remedial", styles["cell_text"])],
        [Paragraph("Senior Sec. (Science Stream)", styles["cell_bold"]), Paragraph("₹ 78,000", styles["cell_text"]), Paragraph("₹ 19,500 / quarter", styles["cell_text"]), Paragraph("Physics, Chem, Bio/Computer lab consumables", styles["cell_text"])],
        [Paragraph("Senior Sec. (Comm / Hum)", styles["cell_bold"]), Paragraph("₹ 72,000", styles["cell_text"]), Paragraph("₹ 18,000 / quarter", styles["cell_text"]), Paragraph("Informatics, economics case studies, humanities lab", styles["cell_text"])],
    ]
    t = Table(rows, colWidths=[140, 110, 110, 179])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BG_LIGHT),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    rules_header = Paragraph("<b>FEE PAYMENT TERMS & CONCESSION POLICIES</b>", styles["heading"])
    rule_rows = [
        [Paragraph("<b>Payment Due Dates</b>", styles["cell_bold"]), Paragraph("Q1: 10th April • Q2: 10th July • Q3: 10th October • Q4: 10th January", styles["cell_text"])],
        [Paragraph("<b>Sibling Concession</b>", styles["cell_bold"]), Paragraph("15% concession on tuition fee for the younger biological sibling enrolled simultaneously.", styles["cell_text"])],
        [Paragraph("<b>Payment Methods</b>", styles["cell_bold"]), Paragraph("UPI, NetBanking, Debit/Credit Card via parent ERP portal, or Demand Draft at the fee counter.", styles["cell_text"])],
        [Paragraph("<b>Transport Facility</b>", styles["cell_bold"]), Paragraph("Optional transport charges levied separately based on distance slab (Slabs 1 to 4: ₹1,800–₹3,200/mo).", styles["cell_text"])],
    ]
    t_rules = Table(rule_rows, colWidths=[140, 399])
    t_rules.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BG_LIGHT),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    note = Paragraph("<b>Fee Regulation Compliance:</b> Sunrise School does not solicit capitation fee or mandatory donations. Fees approved by SMC. All amounts in INR (₹).", styles["note"])
    return [t, Spacer(1, 6), rules_header, Spacer(1, 4), t_rules, Spacer(1, 6), note]


# ----------------------------------------------------------------------
# 10. Syllabus Overview Grades 1–12
# ----------------------------------------------------------------------
def generate_syllabus_overview(out_dir, styles):
    rows = [
        [Paragraph("<b>Class Group</b>", styles["cell_bold"]), Paragraph("<b>Core Subject Offerings</b>", styles["cell_bold"]), Paragraph("<b>Curriculum Alignment & Co-Scholastic</b>", styles["cell_bold"])],
        [Paragraph("Grades 1 & 2 (Foundational)", styles["cell_bold"]), Paragraph("English, Hindi, Mathematics, Environmental Studies (EVS)", styles["cell_text"]), Paragraph("Art, Music, Physical Education, Storytelling & Phonics", styles["cell_text"])],
        [Paragraph("Grades 3 to 5 (Preparatory)", styles["cell_bold"]), Paragraph("English, Hindi, Mathematics, Science, Social Studies, ICT", styles["cell_text"]), Paragraph("Coding fundamentals, Yoga, Visual Arts, Library hour", styles["cell_text"])],
        [Paragraph("Grades 6 to 8 (Middle)", styles["cell_bold"]), Paragraph("English, Hindi, Third Language (Sanskrit/French), Math, General Science, Social Science, AI/Coding", styles["cell_text"]), Paragraph("Atal Tinkering robotics, Life Skills, SEWA community outreach, House athletics", styles["cell_text"])],
        [Paragraph("Grades 9 & 10 (Secondary)", styles["cell_bold"]), Paragraph("English Language & Lit, Hindi Course A, Mathematics (Standard/Basic), Science (Phy/Chem/Bio), Social Science, Artificial Intelligence (Skill Subject 417)", styles["cell_text"]), Paragraph("CBSE Board syllabus, composite science practicals, disaster management, art-integrated learning projects", styles["cell_text"])],
        [Paragraph("Grade 11 & 12 (Science)", styles["cell_bold"]), Paragraph("Compulsory: English Core. Electives: Physics, Chemistry, Mathematics / Biology, Computer Science (Python) / Physical Education", styles["cell_text"]), Paragraph("CBSE AISSCE Board Curriculum, weekly laboratory experiments, investigatory science projects, competitive exam foundation", styles["cell_text"])],
        [Paragraph("Grade 11 & 12 (Commerce)", styles["cell_bold"]), Paragraph("Compulsory: English Core. Electives: Accountancy, Business Studies, Economics, Applied Mathematics / Informatics Practices", styles["cell_text"]), Paragraph("Financial literacy, real-world case analysis, stock market simulations, entrepreneurship workshops", styles["cell_text"])],
        [Paragraph("Grade 11 & 12 (Humanities)", styles["cell_bold"]), Paragraph("Compulsory: English Core. Electives: History, Political Science, Psychology, Sociology / Geography", styles["cell_text"]), Paragraph("Social research dissertations, public policy debates, Model United Nations, heritage archiving", styles["cell_text"])],
    ]
    t = Table(rows, colWidths=[120, 220, 199])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BG_LIGHT),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    note = Paragraph("<b>Curriculum Alignment:</b> NCERT prescribed textbooks and learning outcomes integrated with NEP 2020 experiential benchmarks. Complete class-wise syllabus units available in ERP.", styles["note"])
    return [t, Spacer(1, 6), note]


def main():
    root = Path(__file__).resolve().parent.parent
    out_dir = root / "web" / "public" / "documents"
    out_dir.mkdir(parents=True, exist_ok=True)
    styles = get_styles()

    docs = [
        ("public-disclosure-summary.pdf", "Mandatory Public Disclosure (Appendix-IX)", "PUB-DISC-2026-01", generate_public_disclosure_summary),
        ("school-information.pdf", "School Institutional Profile & Governance", "SCH-INFO-2026-02", generate_school_information),
        ("infrastructure-overview.pdf", "Campus & Infrastructure Specifications", "INFRA-2026-03", generate_infrastructure_overview),
        ("faculty-staff-overview.pdf", "Faculty & Staff Qualifications Overview", "FAC-2026-04", generate_faculty_overview),
        ("academic-information.pdf", "Academic Structure & Board Results", "ACAD-2026-05", generate_academic_information),
        ("school-prospectus.pdf", "School Prospectus Overview 2026–27", "PROSP-2026-06", generate_school_prospectus),
        ("academic-calendar.pdf", "Academic Calendar 2026–27", "CAL-2026-07", generate_academic_calendar),
        ("admission-guidelines.pdf", "Admission Guidelines & Eligibility 2026–27", "ADM-GUIDE-2026-08", generate_admission_guidelines),
        ("fee-structure.pdf", "Approved Fee Structure Schedule 2026–27", "FEE-2026-09", generate_fee_structure),
        ("syllabus-overview.pdf", "Curriculum Framework & Syllabus Overview", "SYLL-2026-10", generate_syllabus_overview),
    ]

    for filename, title, ref_no, generator in docs:
        filepath = out_dir / filename
        flowables = generator(out_dir, styles)
        build_pdf(filepath, title, ref_no, flowables)

    # Also symlink/copy public-disclosure.pdf for direct reference matching
    p_disc = out_dir / "public-disclosure.pdf"
    import shutil
    shutil.copyfile(out_dir / "public-disclosure-summary.pdf", p_disc)
    print("Created public-disclosure.pdf mirror.")
    print("All 10 one-page PDFs generated successfully!")


if __name__ == "__main__":
    main()
