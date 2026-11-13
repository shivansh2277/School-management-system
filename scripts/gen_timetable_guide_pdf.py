"""Script to generate Sunrise-Timetable-Architecture-and-Operations-Guide.pdf
Comprehensive architectural, operational, and consultant guide explaining:
1. Executive Summary & Purpose of Timetable in School Administration
2. Database Schema & Relational Model (SchoolPeriod, ClassSection, Employee, TimetableSlot, Substitution)
3. How Timetables are Generated & Built (Web Builder, Bell Timings, Completeness, Workload Spread)
4. Multi-Tier Conflict Management Engine (Teacher, Room Normalization, Section, Break, Workload Ceiling, Pre-Flight API)
5. Timetable Lifecycle: Draft vs Published State Management & Scoped Role Visibility
6. Dynamic Daily Operations: Substitution Desk, Leave Interlock, Ranked Free-Teacher Recommendation
7. Cross-Module ERP Highways (Attendance, Fees, Examinations, Mobile Apps)
8. Technical REST API Specification & Multi-Tenant Security Audit
9. Institutional Standard Operating Procedures (SOPs) & Runbook for School Principals / Coordinators
"""

import os
import sys
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and draw total page count and professional running headers/footers."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 7.5)
        self.setFillColor(colors.HexColor("#475569"))

        # Running header on page 2+
        if self._pageNumber > 1:
            self.drawString(40, 842 - 36, "SUNRISE SCHOOL ERP - TIMETABLE ARCHITECTURE & OPERATIONS GUIDE")
            self.setFont("Helvetica", 7.5)
            self.drawRightString(595 - 40, 842 - 36, "CBSE INSTITUTIONAL ARCHITECTURE - SESSION 34")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(40, 842 - 42, 595 - 40, 842 - 42)

        # Running footer on all pages
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(40, 42, 595 - 40, 42)
        self.setFont("Helvetica", 7.5)
        self.drawString(40, 30, "Sunrise School ERP | Timetable Module & Conflict Engine Manual | Confidential Internal Documentation")
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(595 - 40, 30, page_text)
        self.restoreState()


def build_timetable_guide_pdf(filename="Sunrise-Timetable-Architecture-and-Operations-Guide.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=48,
        bottomMargin=50,
    )

    styles = getSampleStyleSheet()

    # Color Palette
    PRIMARY = colors.HexColor("#0f172a")       # Slate 900
    NAVY = colors.HexColor("#1e293b")          # Slate 800
    SLATE = colors.HexColor("#334155")         # Slate 700
    EMERALD = colors.HexColor("#047857")       # Emerald 700
    TEAL = colors.HexColor("#0f766e")          # Teal 700
    AMBER = colors.HexColor("#b45309")         # Amber 700
    RED = colors.HexColor("#b91c1c")            # Red 700
    BG_LIGHT = colors.HexColor("#f8fafc")      # Slate 50
    BG_CARD = colors.HexColor("#f1f5f9")       # Slate 100
    BORDER_COLOR = colors.HexColor("#cbd5e1")  # Slate 300

    # Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=PRIMARY,
        spaceAfter=4,
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=TEAL,
        spaceAfter=10,
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=NAVY,
        spaceBefore=8,
        spaceAfter=5,
        keepWithNext=True,
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=SLATE,
        spaceBefore=6,
        spaceAfter=4,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.3,
        leading=11.5,
        textColor=PRIMARY,
        spaceAfter=5,
    )

    code_style = ParagraphStyle(
        'Code_Custom',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7.2,
        leading=9.2,
        textColor=colors.HexColor("#1e1e2e"),
    )

    table_cell = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.6,
        leading=10,
        textColor=PRIMARY,
    )

    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.6,
        leading=10,
        textColor=PRIMARY,
    )

    table_cell_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.8,
        leading=10.5,
        textColor=colors.white,
    )

    callout_style = ParagraphStyle(
        'Callout',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=NAVY,
    )

    story = []

    # ==================================================================
    # PAGE 1: TITLE, EXECUTIVE SUMMARY & DOMAIN ARCHITECTURE
    # ==================================================================
    story.append(Paragraph("SUNRISE SCHOOL MANAGEMENT SYSTEM (ERP)", title_style))
    story.append(Paragraph("Timetable Architecture, Conflict Management Engine & Operations Manual", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceAfter=8))

    # Metadata Banner
    meta_data = [
        [
            Paragraph("<b>Target System:</b> Sunrise School ERP (Multi-Tenant)", table_cell),
            Paragraph("<b>Module:</b> Academics & Timetable Management", table_cell),
            Paragraph("<b>Regulatory Framework:</b> CBSE K-12 Lucknow Standard", table_cell),
        ],
        [
            Paragraph("<b>Author:</b> Senior QA Engineer & School ERP Consultant", table_cell),
            Paragraph("<b>Baseline:</b> Session 34 Post-Remediation", table_cell),
            Paragraph("<b>Database:</b> PostgreSQL (105 Normalized Tables)", table_cell),
        ]
    ]
    meta_table = Table(meta_data, colWidths=[175, 170, 170])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BG_CARD),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 8))

    story.append(Paragraph("1. Executive Summary & Operational Mission", h1_style))
    story.append(Paragraph(
        "In a modern K-12 institutional school, the timetable is not merely a static calendar of classes; "
        "it is the master operational heartbeat coordinating three physical and human constraints: "
        "<b>(1) Faculty Availability</b>, <b>(2) Student Cohorts</b>, and <b>(3) Physical Infrastructure</b> (classrooms, computer labs, science labs, athletic grounds). "
        "A defect in timetable scheduling produces immediate cascading disruption: two teachers arriving at the same room, a classroom sitting unattended without supervision, "
        "or a teacher assigned to teach two classes simultaneously. In our codebase audit, <i>'a grid that lets you put a teacher in two rooms at once is worse than no grid, "
        "because someone will trust it and a class will sit unattended'</i> (§5.7.3).",
        body_style
    ))
    story.append(Paragraph(
        "To deliver enterprise reliability, Sunrise ERP implements a <b>Dual-Layer Conflict Prevention Architecture</b>: "
        "an asynchronous, real-time pre-flight inspection engine at the REST API/UI layer, backed by strict, non-bypassable unique constraints "
        "and normalized indexes at the PostgreSQL database storage layer. Furthermore, the system decouples Master Schedule Design from Daily Operational Reality "
        "via a dedicated Substitution Desk and a Draft-to-Published lifecycle gate.",
        body_style
    ))

    story.append(Paragraph("2. Relational Data Architecture & Domain Model", h1_style))
    story.append(Paragraph(
        "The Timetable engine is anchored on five primary tables operating within a multi-tenant schema isolated by <code>school_id</code>:",
        body_style
    ))

    schema_data = [
        [
            Paragraph("Database Table", table_cell_header),
            Paragraph("Primary Responsibility", table_cell_header),
            Paragraph("Key Columns & Relationships", table_cell_header),
            Paragraph("Integrity Guarantees & Constraints", table_cell_header),
        ],
        [
            Paragraph("<b><code>school_periods</code></b>", table_cell),
            Paragraph("Defines institutional bell timings once per school instead of duplicating timestamps across hundreds of slots.", table_cell),
            Paragraph("<code>id, school_id, period_no, start_time, end_time, name, is_break</code>", table_cell),
            Paragraph("<code>uq_school_period_no (school_id, period_no)</code>.<br/>Break slots (<code>is_break=True</code>) reject teaching assignments.", table_cell),
        ],
        [
            Paragraph("<b><code>class_sections</code></b>", table_cell),
            Paragraph("The student cohort unit (e.g. Class 10-A) linked to an academic year and class teacher.", table_cell),
            Paragraph("<code>id, school_id, academic_year_id, class_name, section, class_teacher_id</code>", table_cell),
            Paragraph("<code>uq_class_section (academic_year_id, class_name, section)</code>.<br/>Maintains student enrolment boundaries.", table_cell),
        ],
        [
            Paragraph("<b><code>employees</code></b>", table_cell),
            Paragraph("Faculty members eligible for teaching and relief duty assignments.", table_cell),
            Paragraph("<code>id, school_id, user_id, employee_code, employee_type, status, department_id</code>", table_cell),
            Paragraph("Only <code>employee_type = 'teaching'</code> and <code>status != 'exited'</code> qualify for slot assignment.", table_cell),
        ],
        [
            Paragraph("<b><code>timetable_slots</code></b>", table_cell),
            Paragraph("The master recurring schedule nexus linking section, day, period, subject, teacher, and room.", table_cell),
            Paragraph("<code>id, school_id, class_section_id, day_of_week, period_id, subject_id, teacher_id, room, is_published</code>", table_cell),
            Paragraph("<code>uq_timetable_slot</code> (section conflict)<br/><code>uq_timetable_teacher_slot</code> (teacher clash)<br/><code>uq_timetable_room_slot</code> (normalized room clash).", table_cell),
        ],
        [
            Paragraph("<b><code>substitutions</code></b>", table_cell),
            Paragraph("Single-day relief coverage overlay. Preserves master timetable while tracking absent teacher substitutions.", table_cell),
            Paragraph("<code>id, school_id, timetable_slot_id, date, absent_teacher_id, substitute_teacher_id, reason, status</code>", table_cell),
            Paragraph("<code>uq_substitution_slot_date (timetable_slot_id, date)</code>.<br/>Leaves master timetable unmodified.", table_cell),
        ],
    ]
    schema_table = Table(schema_data, colWidths=[95, 125, 145, 150])
    schema_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(schema_table)
    story.append(Spacer(1, 8))

    # Architecture ASCII Box
    ascii_arch = (
        "+-------------------------------------------------------------------------------------------------+\n"
        "|                              SUNRISE ERP TIMETABLE DOMAIN TOPOLOGY                              |\n"
        "+-------------------------------------------------------------------------------------------------+\n"
        "|  [SchoolPeriod] (Bell Timings: 1..8, is_break)          [Employee] (Teaching Faculty)            |\n"
        "|         |                                                       |                               |\n"
        "|         +---------------------------+       +-------------------+                               |\n"
        "|                                     |       |                                                   |\n"
        "|  [ClassSection] (10-A, 10-B) ---> [TimetableSlot] <--- [Subject] (Maths, English, Science)      |\n"
        "|                                        |                                                        |\n"
        "|       [uq_timetable_slot]              | (Draft: is_published=false | Published: true)          |\n"
        "|       [uq_timetable_teacher_slot]      v                                                        |\n"
        "|       [uq_timetable_room_slot]   [Substitution Desk] (Target Date Overlay)                      |\n"
        "|                                        |                                                        |\n"
        "|                                        +---> [Daily Day Plan] -> Mobile App (Teacher/Parent)    |\n"
        "+-------------------------------------------------------------------------------------------------+"
    )
    story.append(Paragraph(f"<font face='Courier' size='6.8'>{ascii_arch.replace(chr(10), '<br/>').replace(' ', '&nbsp;')}</font>", code_style))

    story.append(PageBreak())

    # ==================================================================
    # PAGE 2: HOW TIMETABLES ARE GENERATED & BUILT
    # ==================================================================
    story.append(Paragraph("3. Master Data Foundations & School Setup", h1_style))
    story.append(Paragraph(
        "Before generating a single timetable slot, Sunrise ERP enforces the configuration of three institutional pillars:",
        body_style
    ))
    story.append(Paragraph(
        "<b>1. Bell Timings (School Periods):</b> Administrators define periods via <code>/admin/timetable/periods</code>. "
        "Each period has a <code>period_no</code>, <code>start_time</code>, and <code>end_time</code>. "
        "A period can be flagged as <code>is_break=True</code> (e.g. Period 6 Lunch Break). Breaks appear on visual grids but reject all lesson scheduling. "
        "Centralizing bell timings means adjusting school start times requires one database update rather than mutating 360 separate slot rows.<br/>"
        "<b>2. Section Subject Teacher Allotment:</b> Through <code>ClassSubjectTeacher</code>, academic heads allocate qualified faculty to specific subjects per section. "
        "The Timetable engine references these allocations during validation and relief recommendations.<br/>"
        "<b>3. Institutional Workload Policy:</b> Configured via <code>timetable.max_periods_per_week</code> (default: 30 periods). "
        "This defines the regulatory ceiling for teacher workload under standard CBSE guidelines.",
        body_style
    ))

    story.append(Paragraph("4. How Timetables are Generated: The Interactive Web Builder", h1_style))
    story.append(Paragraph(
        "Sunrise ERP provides an interactive, full-lifecycle timetable builder within <code>Classes.tsx</code>. "
        "Operating as a weekly matrix (Monday through Saturday across Periods 1 to 8), it empowers academic coordinators to design, "
        "test, and refine classroom schedules seamlessly.",
        body_style
    ))

    builder_steps = [
        [
            Paragraph("Builder Step", table_cell_header),
            Paragraph("UI / Workflow Action", table_cell_header),
            Paragraph("Underlying Engine / API Interaction", table_cell_header),
            Paragraph("Operational Safeguard", table_cell_header),
        ],
        [
            Paragraph("<b>1. Section Selection</b>", table_cell),
            Paragraph("Coordinator selects Academic Year and Class Section (e.g., Grade 10, Section A).", table_cell),
            Paragraph("Invokes <code>GET /admin/timetable/slots?class_section_id=X</code>.", table_cell),
            Paragraph("Tenant-isolated; queries only current school's active section slots.", table_cell),
        ],
        [
            Paragraph("<b>2. Grid Rendering</b>", table_cell),
            Paragraph("Renders a responsive weekly grid. Period 6 automatically renders with a distinct 'Break' badge.", table_cell),
            Paragraph("Calculates published vs draft counters (e.g. '5 Draft Changes').", table_cell),
            Paragraph("Break periods disable the '+ Add Lesson' button, preventing user errors.", table_cell),
        ],
        [
            Paragraph("<b>3. Interactive Slot Creation</b>", table_cell),
            Paragraph("Clicking an empty period cell opens <code>SlotModal</code>, pre-populating Day and Period.", table_cell),
            Paragraph("Fetches period metadata, eligible subjects, and active teaching faculty.", table_cell),
            Paragraph("Dropdowns exclude non-teaching staff and exited personnel.", table_cell),
        ],
        [
            Paragraph("<b>4. Live Pre-Flight Conflict Check</b>", table_cell),
            Paragraph("As user selects Teacher and enters Room, modal fires real-time check in the background.", table_cell),
            Paragraph("Calls <code>POST /admin/timetable/slots/check</code> asynchronously.", table_cell),
            Paragraph("Displays amber/red warning banners with exact conflict details before save.", table_cell),
        ],
        [
            Paragraph("<b>5. Draft Commitment</b>", table_cell),
            Paragraph("User clicks 'Add Slot'. Slot is created in <b>Draft Mode</b> (<code>is_published=false</code>).", table_cell),
            Paragraph("Calls <code>POST /admin/timetable/slots</code>; runs transactional validation.", table_cell),
            Paragraph("Guarantees that unfinished schedule reorganizations never leak to parents/students.", table_cell),
        ],
        [
            Paragraph("<b>6. Slot Editing & Deletion</b>", table_cell),
            Paragraph("Clicking an existing slot allows changing Teacher/Room or removing the slot entirely.", table_cell),
            Paragraph("Calls <code>PUT /admin/timetable/slots/{id}</code> or <code>DELETE .../{id}</code>.", table_cell),
            Paragraph("Validates tenant ownership and re-verifies conflicts excluding the current slot.", table_cell),
        ],
    ]
    builder_table = Table(builder_steps, colWidths=[90, 140, 145, 140])
    builder_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(builder_table)
    story.append(Spacer(1, 8))

    story.append(Paragraph("5. Timetable Quality Control: Completeness & Workload Metrics", h1_style))
    story.append(Paragraph(
        "To ensure timetable generation is not an ad-hoc exercise, Sunrise ERP provides two analytical oversight modules:",
        body_style
    ))
    story.append(Paragraph(
        "<b>A. Timetable Completeness Engine (<code>/admin/timetable/completeness</code>):</b><br/>"
        "An incomplete timetable must be visibly incomplete. The engine calculates expected teaching periods per week "
        "(<code>expected = teaching_periods * 6 days</code>). For every section, it compares placed slots against expected slots. "
        "If a section is short 4 periods, it is explicitly flagged as <code>missing = 4</code> so academic coordinators cannot overlook empty timetable gaps.<br/>"
        "<b>B. Faculty Workload Balancing View (<code>/admin/timetable/workload</code>):</b><br/>"
        "Timetable equity is vital for faculty morale and CBSE compliance. The workload engine evaluates every active teacher: "
        "<br/>&bull; <i>Fair Share Metric:</i> Computes <code>fair_share = total_placed_periods / total_teaching_staff</code>. "
        "<br/>&bull; <i>Spread Metric:</i> Computes <code>spread = heaviest_load - lightest_load</code>. A spread of 0 indicates perfect equity. "
        "<br/>&bull; <i>Outlier Detection:</i> Identifies unassigned teachers (0 periods) and overloaded teachers (> 30 periods).",
        body_style
    ))

    story.append(PageBreak())

    # ==================================================================
    # PAGE 3: THE MULTI-TIER CONFLICT MANAGEMENT ENGINE
    # ==================================================================
    story.append(Paragraph("6. The Multi-Tier Conflict Management Engine", h1_style))
    story.append(Paragraph(
        "The defining strength of Sunrise ERP is its uncompromising conflict detection engine (<code>timetable_svc.conflicts()</code>). "
        "A timetable builder that validates sequentially wastes hours of administrative time. Sunrise ERP evaluates "
        "<b>all five conflict dimensions simultaneously</b> and returns comprehensive diagnostics in a single payload.",
        body_style
    ))

    conflict_data = [
        [
            Paragraph("Conflict Dimension", table_cell_header),
            Paragraph("Clash Condition & Detection Logic", table_cell_header),
            Paragraph("Database Constraint / Index", table_cell_header),
            Paragraph("Remediation / Overridability", table_cell_header),
        ],
        [
            Paragraph("<b>1. Teacher Double-Booking</b>", table_cell),
            Paragraph("A teacher is scheduled in two different class sections during the exact same day and period.", table_cell),
            Paragraph("<code>uq_timetable_teacher_slot</code><br/><code>(teacher_id, day_of_week, period_id)</code>", table_cell),
            Paragraph("<font color='#b91c1c'><b>STRICT BLOCK (409)</b></font><br/>Non-overridable. Must choose an alternative period or teacher.", table_cell),
        ],
        [
            Paragraph("<b>2. Room Double-Booking</b>", table_cell),
            Paragraph("Two classes assigned to the same room at the same time. Normalizes input with <code>UPPER(TRIM(room))</code>.", table_cell),
            Paragraph("<code>uq_timetable_room_slot</code><br/>Partial unique index where room is not null/empty.", table_cell),
            Paragraph("<font color='#b91c1c'><b>STRICT BLOCK (409)</b></font><br/>Non-overridable. Prevents room double-booking.", table_cell),
        ],
        [
            Paragraph("<b>3. Class Section Double-Booking</b>", table_cell),
            Paragraph("A class section is assigned two distinct lessons during the same period.", table_cell),
            Paragraph("<code>uq_timetable_slot</code><br/><code>(class_section_id, day_of_week, period_id)</code>", table_cell),
            Paragraph("<font color='#b91c1c'><b>STRICT BLOCK (409)</b></font><br/>Non-overridable. A section can only have one subject at a time.", table_cell),
        ],
        [
            Paragraph("<b>4. Break Period Collision</b>", table_cell),
            Paragraph("Attempting to schedule a teaching slot during a designated recess or lunch period (<code>is_break=True</code>).", table_cell),
            Paragraph("Application service validation on <code>SchoolPeriod.is_break</code>.", table_cell),
            Paragraph("<font color='#b91c1c'><b>STRICT BLOCK (409)</b></font><br/>Non-overridable. Periods marked as breaks reject teaching slots.", table_cell),
        ],
        [
            Paragraph("<b>5. Teacher Workload Ceiling</b>", table_cell),
            Paragraph("Assigning a slot pushes the teacher's weekly teaching periods past <code>timetable.max_periods_per_week</code> (e.g. > 30).", table_cell),
            Paragraph("Dynamic load aggregation in <code>teacher_load()</code> joined with <code>school_periods</code>.", table_cell),
            Paragraph("<font color='#b45309'><b>OVERRIDABLE WITH REASON</b></font><br/>Requires <code>override_reason</code>; logged to <code>audit_logs</code>.", table_cell),
        ],
    ]
    conflict_table = Table(conflict_data, colWidths=[105, 140, 135, 135])
    conflict_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(conflict_table)
    story.append(Spacer(1, 8))

    story.append(Paragraph("7. Technical Deep-Dive: Room Normalization & Race-Condition Defense", h1_style))
    story.append(Paragraph(
        "During our audit, two subtle vulnerabilities were analyzed and permanently remediated:",
        body_style
    ))
    story.append(Paragraph(
        "<b>Case 1: Room Normalization Defect Remediation (Defect TT-02):</b><br/>"
        "In naive implementations, entering <code>'Room 301'</code> for Section 10-A and <code>'  room 301  '</code> for Section 9-B "
        "bypassed string equality checks. Sunrise ERP resolves this at two levels: "
        "(1) In <code>timetable_svc.conflicts()</code>, room identifiers are sanitized: <code>norm_room = room.strip().upper()</code>. "
        "(2) In PostgreSQL, migration <code>d0f27b59a4e1</code> added the partial unique index <code>uq_timetable_room_slot</code>, "
        "guaranteeing identical physical rooms can never host concurrent lessons regardless of whitespace or casing variations.<br/>"
        "<b>Case 2: Concurrent Collision Protection:</b><br/>"
        "If two administrators schedule two conflicting classes at the exact same millisecond, application-level checks might read "
        "a clean state simultaneously. Sunrise ERP wraps slot persistence in database transaction blocks. "
        "If concurrent requests violate <code>uq_timetable_teacher_slot</code> or <code>uq_timetable_room_slot</code>, "
        "PostgreSQL raises an atomic <code>IntegrityError</code>. The API catches this, executes a clean <code>db.rollback()</code>, "
        "and returns a standardized HTTP 409 Conflict with descriptive messaging.",
        body_style
    ))

    # Code / Flow Representation
    flow_box = (
        "+--------------------------------------------------------------------------------------------------+\n"
        "|                             PRE-FLIGHT VS PERSISTENCE CONFLICT FLOW                              |\n"
        "+--------------------------------------------------------------------------------------------------+\n"
        "|  User Edits Slot in UI                                                                           |\n"
        "|        |                                                                                         |\n"
        "|        +---> [POST /admin/timetable/slots/check] (Pre-Flight)                                    |\n"
        "|                    |                                                                             |\n"
        "|                    +---> conflicts() -> Evaluates: Break, Teacher, Section, Room, Workload      |\n"
        "|                    |                                                                             |\n"
        "|                    +---> Returns: {ok: false, conflicts: [{kind: 'teacher', detail: '...'}]}    |\n"
        "|                                                                                                  |\n"
        "|  User Clicks Save -> [POST /admin/timetable/slots] (Atomic Write)                                |\n"
        "|        |                                                                                         |\n"
        "|        +---> Blocking Conflicts Present? ---> YES: Raise HTTP 409 Conflict                      |\n"
        "|        |                                                                                         |\n"
        "|        +---> Overridable Workload? ---------> NO REASON: Raise HTTP 409 (needs override_reason)  |\n"
        "|        |                                      WITH REASON: Record in AuditLog & Proceed          |\n"
        "|        v                                                                                         |\n"
        "|  db.flush() -> PostgreSQL DB Constraints: uq_timetable_teacher_slot, uq_timetable_room_slot     |\n"
        "|        |                                                                                         |\n"
        "|        +---> Concurrency Race? -------------> Trap IntegrityError -> Rollback -> HTTP 409       |\n"
        "|        v                                                                                         |\n"
        "|  Success: Slot Created (Draft: is_published=false)                                               |\n"
        "+--------------------------------------------------------------------------------------------------+"
    )
    story.append(Paragraph(f"<font face='Courier' size='6.7'>{flow_box.replace(chr(10), '<br/>').replace(' ', '&nbsp;')}</font>", code_style))

    story.append(PageBreak())

    # ==================================================================
    # PAGE 4: TIMETABLE LIFECYCLE: DRAFT VS PUBLISHED STATE MANAGEMENT
    # ==================================================================
    story.append(Paragraph("8. Timetable Lifecycle: Draft vs Published State Management", h1_style))
    story.append(Paragraph(
        "Prior to remediation (Defect TT-05), editing a timetable slot mutated live schedules immediately. "
        "A coordinator making changes mid-week inadvertently caused mobile app confusion, as students and parents saw half-finished, "
        "clashing schedules. Sunrise ERP establishes a strict <b>Draft-to-Published Lifecycle Architecture</b>.",
        body_style
    ))

    story.append(Paragraph("Lifecycle State Machine & Transition Rules", h2_style))
    story.append(Paragraph(
        "<b>1. Default Draft Mode (<code>is_published = False</code>):</b> Every newly created or edited slot defaults to Draft state. "
        "Draft slots exist in the database and are fully visible and editable by Academic Administrators on the web builder, "
        "but are completely shielded from end-user consumers.<br/>"
        "<b>2. Atomic 1-Click Publication (<code>POST /admin/timetable/publish</code>):</b> When the coordinator finishes arranging "
        "the entire section or school schedule, clicking 'Publish Changes' atomically flips all slots for that section to <code>is_published = True</code>. "
        "Mobile apps receive instant synchronized updates.<br/>"
        "<b>3. Safe Reversion / Unpublishing (<code>POST /admin/timetable/unpublish</code>):</b> During annual restructuring or emergency timetable rewrites, "
        "administrators can click 'Revert to Draft'. This reverts slots back to draft state, freezing mobile schedules until republished.",
        body_style
    ))

    story.append(Spacer(1, 4))
    story.append(Paragraph("Multi-Persona Scoped Visibility Matrix", h2_style))
    story.append(Paragraph(
        "Visibility of timetable data is enforced at the backend routing level through strict role-based scoping:",
        body_style
    ))

    role_matrix = [
        [
            Paragraph("User Role / Persona", table_cell_header),
            Paragraph("Access Channel & Endpoint", table_cell_header),
            Paragraph("Draft Slots Visibility", table_cell_header),
            Paragraph("Published Slots Visibility", table_cell_header),
            Paragraph("Modification Rights", table_cell_header),
        ],
        [
            Paragraph("<b>Super Admin & Principal</b>", table_cell),
            Paragraph("Web ERP<br/><code>/admin/timetable/slots</code>", table_cell),
            Paragraph("<font color='#047857'><b>FULL VISIBILITY</b></font><br/>Badged as 'Draft'.", table_cell),
            Paragraph("<font color='#047857'><b>FULL VISIBILITY</b></font><br/>Badged as 'Published'.", table_cell),
            Paragraph("<font color='#047857'><b>FULL WRITE</b></font><br/>Create, Edit, Delete, Publish.", table_cell),
        ],
        [
            Paragraph("<b>Academic Coordinator</b>", table_cell),
            Paragraph("Web ERP<br/><code>/admin/timetable/slots</code>", table_cell),
            Paragraph("<font color='#047857'><b>FULL VISIBILITY</b></font><br/>Full builder controls.", table_cell),
            Paragraph("<font color='#047857'><b>FULL VISIBILITY</b></font><br/>Completeness & Workload.", table_cell),
            Paragraph("<font color='#047857'><b>FULL WRITE</b></font><br/>Create, Edit, Delete, Publish.", table_cell),
        ],
        [
            Paragraph("<b>Subject Teacher</b>", table_cell),
            Paragraph("Teacher Mobile & Web<br/><code>/teacher/timetable</code>", table_cell),
            Paragraph("<font color='#b91c1c'><b>ZERO (HIDDEN)</b></font><br/><code>published_only=True</code>", table_cell),
            Paragraph("<font color='#047857'><b>OWN SLOTS ONLY</b></font><br/>Includes daily relief duty.", table_cell),
            Paragraph("<font color='#b91c1c'><b>READ ONLY</b></font><br/>Cannot modify slots.", table_cell),
        ],
        [
            Paragraph("<b>Student</b>", table_cell),
            Paragraph("Student Mobile App<br/><code>/student/dashboard</code>", table_cell),
            Paragraph("<font color='#b91c1c'><b>ZERO (HIDDEN)</b></font><br/><code>published_only=True</code>", table_cell),
            Paragraph("<font color='#047857'><b>SECTION SLOTS</b></font><br/>Enrolled section schedule.", table_cell),
            Paragraph("<font color='#b91c1c'><b>READ ONLY</b></font><br/>View daily & weekly timetable.", table_cell),
        ],
        [
            Paragraph("<b>Parent / Guardian</b>", table_cell),
            Paragraph("Parent Mobile App<br/><code>/parent/children/{id}/timetable</code>", table_cell),
            Paragraph("<font color='#b91c1c'><b>ZERO (HIDDEN)</b></font><br/><code>published_only=True</code>", table_cell),
            Paragraph("<font color='#047857'><b>CHILD SECTION SLOTS</b></font><br/>Filtered by child enrollment.", table_cell),
            Paragraph("<font color='#b91c1c'><b>READ ONLY</b></font><br/>View child's weekly timetable.", table_cell),
        ],
    ]
    role_table = Table(role_matrix, colWidths=[95, 120, 95, 110, 95])
    role_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(role_table)
    story.append(Spacer(1, 8))

    story.append(Paragraph("Security Enforcement Evidence", h2_style))
    story.append(Paragraph(
        "Scoping is not left to frontend UI toggles. In <code>backend/app/api/teacher/classes.py</code> line 88, "
        "<code>backend/app/api/student/dashboard.py</code> line 53, and <code>backend/app/api/parent/children.py</code> line 299, "
        "the backend router hardcodes <code>published_only=True</code>. Even if a modified client queries these endpoints while draft "
        "slots exist, the SQL query appends <code>WHERE timetable_slots.is_published = true</code>, returning zero unpublished records. "
        "This architectural invariant was verified in our automated QA test suite.",
        body_style
    ))

    story.append(PageBreak())

    # ==================================================================
    # PAGE 5: DYNAMIC DAILY OPERATIONS & SUBSTITUTION DESK
    # ==================================================================
    story.append(Paragraph("9. Dynamic Daily Operations: Substitution Desk & Relief Management", h1_style))
    story.append(Paragraph(
        "A published timetable represents the school's ideal plan; the <b>Substitution Desk</b> manages the reality of daily operations. "
        "When teachers are absent due to illness, personal leave, or administrative training, their scheduled classes cannot be left unattended. "
        "Sunrise ERP provides an intelligent, automated substitution management subsystem.",
        body_style
    ))

    story.append(Paragraph("Core Architectural Principle: Date-Based Substitution Overlays", h2_style))
    story.append(Paragraph(
        "A naive system updates the <code>teacher_id</code> on <code>TimetableSlot</code> when arranging cover. "
        "That is fatal: it destroys the permanent timetable record, meaning next Tuesday the original teacher is lost. "
        "Sunrise ERP treats substitutions as <b>single-date overlays</b> stored in the <code>substitutions</code> table. "
        "The master slot remains untouched; for the target date, queries merge the slot with active substitution records.",
        body_style
    ))

    story.append(Spacer(1, 4))
    story.append(Paragraph("The Ranked Substitute Recommendation Algorithm", h2_style))
    story.append(Paragraph(
        "When finding relief cover (<code>/admin/timetable/slots/{id}/free-teachers</code>), the system runs a multi-tier filtering and ranking pipeline:",
        body_style
    ))

    algo_steps = [
        [
            Paragraph("Algorithm Stage", table_cell_header),
            Paragraph("Filtering / Ranking Rule", table_cell_header),
            Paragraph("Business Justification & Pedagogical Rationale", table_cell_header),
        ],
        [
            Paragraph("<b>Stage 1: Scheduled Busy Filter</b>", table_cell),
            Paragraph("Exclude any teacher who has a scheduled teaching slot on that day and period (<code>TimetableSlot.period_id == slot.period_id</code>).", table_cell),
            Paragraph("A teacher cannot be in two places at once. Eliminates obvious double-booking.", table_cell),
        ],
        [
            Paragraph("<b>Stage 2: Already Covering Filter</b>", table_cell),
            Paragraph("Exclude any teacher already assigned to cover another substitution on that date and period.", table_cell),
            Paragraph("Covering another class makes a teacher just as occupied as having a regular class.", table_cell),
        ],
        [
            Paragraph("<b>Stage 3: Approved Leave Filter</b>", table_cell),
            Paragraph("Interlocks with HR: excludes teachers who are on approved leave on that date (<code>staff_leave.on_leave()</code>).", table_cell),
            Paragraph("Prevents the embarrassing blunder of assigning cover duty to someone who is sick at home.", table_cell),
        ],
        [
            Paragraph("<b>Stage 4: Subject Specialist Priority</b>", table_cell),
            Paragraph("Rank teachers who teach the <i>same subject</i> in other classes at the top of the list (<code>teaches_this_subject = True</code>).", table_cell),
            Paragraph("Cover by someone who knows the subject is genuine instruction; anyone else is mere classroom supervision.", table_cell),
        ],
        [
            Paragraph("<b>Stage 5: Workload Load Balancing</b>", table_cell),
            Paragraph("Among qualified teachers, secondary sort by <code>weekly_load ASC</code> (lowest teaching periods first).", table_cell),
            Paragraph("Distributes relief duty equitably, preventing overburdening the same faculty members.", table_cell),
        ],
    ]
    algo_table = Table(algo_steps, colWidths=[120, 195, 200])
    algo_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(algo_table)
    story.append(Spacer(1, 8))

    story.append(Paragraph("The 100% Substitution Coverage Gate", h2_style))
    story.append(Paragraph(
        "Sunrise ERP interlocks Staff Leave approval with the Timetable Substitution Desk. "
        "When an administrator attempts to approve a teacher's leave request, the system detects all timetable slots taught by that teacher "
        "during the leave window. <b>Leave approval is locked until 100% of the vacant periods are paired with assigned relief teachers.</b> "
        "If a slot has no available substitute, it is recorded explicitly as <code>status = 'unfilled'</code>, creating an urgent morning operational alert.",
        body_style
    ))

    story.append(Paragraph("The Day Plan: Real-Time Operational Schedule", h2_style))
    story.append(Paragraph(
        "Through <code>GET /admin/timetable/day?date=YYYY-MM-DD</code>, school leadership views the day as it will actually run. "
        "On the Teacher Mobile App, substitute teachers receive push notifications and see relief periods highlighted with an "
        "<b>'On Relief Duty'</b> badge and original teacher notes. On the Student and Parent apps, the period displays: "
        "<i>'Mathematics (Cover: Mrs. Sharma)'</i>, maintaining transparency across all school stakeholders.",
        body_style
    ))

    story.append(PageBreak())

    # ==================================================================
    # PAGE 6: CROSS-MODULE ERP INTEGRATIONS & MOBILE WORKFLOWS
    # ==================================================================
    story.append(Paragraph("10. Cross-Module ERP Integrations & Data Highways", h1_style))
    story.append(Paragraph(
        "The Timetable module does not exist in isolation. It forms the structural framework upon which Attendance, "
        "Staff Leave, Examination Scheduling, and Mobile Portals operate. The following operational integrations were audited:",
        body_style
    ))

    integrations_data = [
        [
            Paragraph("Integration Highway", table_cell_header),
            Paragraph("Interacting Modules", table_cell_header),
            Paragraph("Integration Contract & Synchronization Flow", table_cell_header),
            Paragraph("Integrity Safeguard", table_cell_header),
        ],
        [
            Paragraph("<b>Timetable -> Daily Attendance</b>", table_cell),
            Paragraph("Academics <-> Student Attendance", table_cell),
            Paragraph("Class teacher roll-call authority is derived from <code>ClassSection.class_teacher_id</code>. Daily attendance operates independently of single-period relief teachers.", table_cell),
            Paragraph("Prevents temporary substitute teachers from erroneously locking official morning daily attendance registers.", table_cell),
        ],
        [
            Paragraph("<b>Timetable -> Staff Leave & HR</b>", table_cell),
            Paragraph("Timetable <-> HR & Payroll", table_cell),
            Paragraph("When staff leave is requested, system auto-generates vacant substitution candidate rows. Approved leave decrements active teaching capacity.", table_cell),
            Paragraph("100% substitution coverage gate blocks leave authorization until all classes are reassigned.", table_cell),
        ],
        [
            Paragraph("<b>Timetable -> Exam Scheduling</b>", table_cell),
            Paragraph("Timetable <-> Examination Desk", table_cell),
            Paragraph("Exam cycles schedule subject papers in physical rooms. The exam scheduler references room allocations to prevent clashes with ongoing junior classes.", table_cell),
            Paragraph("Prevents scheduling an exam in a physics laboratory already in use for standard practical classes.", table_cell),
        ],
        [
            Paragraph("<b>Timetable -> Teacher App</b>", table_cell),
            Paragraph("Timetable <-> Teacher Mobile Portal", table_cell),
            Paragraph("Fetches teacher's weekly periods via <code>/teacher/timetable</code> (scoped to <code>published_only=True</code>). Injects daily relief duty assignments.", table_cell),
            Paragraph("Draft slots hidden; relief duty pushed instantly to teacher's daily agenda tab.", table_cell),
        ],
        [
            Paragraph("<b>Timetable -> Parent/Student App</b>", table_cell),
            Paragraph("Timetable <-> Parent & Student Portals", table_cell),
            Paragraph("Provides full weekly schedule of the enrolled section. Highlights current active period based on live device clock and period bell timings.", table_cell),
            Paragraph("Parents can monitor homework and subject schedules; draft changes remain completely invisible.", table_cell),
        ],
    ]
    integrations_table = Table(integrations_data, colWidths=[105, 110, 160, 140])
    integrations_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(integrations_table)
    story.append(Spacer(1, 8))

    story.append(Paragraph("11. Mobile App End-User Experience & Bell Synchronization", h1_style))
    story.append(Paragraph(
        "The Sunrise Mobile application suite (built with React Native / Expo) translates complex timetable data "
        "into an intuitive daily companion for teachers, students, and parents:",
        body_style
    ))
    story.append(Paragraph(
        "<b>1. Live Period Tracker:</b> The mobile client correlates local system time with <code>SchoolPeriod.start_time</code> "
        "and <code>end_time</code>. The current ongoing period is highlighted with an emerald pulse animation, showing remaining minutes until the next bell.<br/>"
        "<b>2. Relief Notification Service:</b> When a teacher is assigned cover duty via the Substitution Desk, the backend triggers "
        "an urgent push notification: <i>'Relief Assignment: Class 9-B, Period 3, Science Lab'</i>. The teacher's schedule updates dynamically.<br/>"
        "<b>3. Day-by-Day Tabbed Navigation:</b> Students and parents can swipe between Monday through Saturday, reviewing periods, "
        "subject names, faculty names, and designated classroom numbers.",
        body_style
    ))

    # ASCII Mobile Preview
    mobile_box = (
        "+--------------------------------------------------------------------------------------------------+\n"
        "|                             MOBILE APP DAILY SCHEDULE VIEW (STUDENT)                             |\n"
        "+--------------------------------------------------------------------------------------------------+\n"
        "|  Grade 10-A  |  Academic Year: 2026-27  |  Today: Tuesday, 30 Oct 2026                           |\n"
        "|  [Mon] >[Tue]< [Wed] [Thu] [Fri] [Sat]                                                           |\n"
        "|  ----------------------------------------------------------------------------------------------  |\n"
        "|  08:00 - 08:45 | Period 1 : English Literature     | Mr. R. Verma    | Room 101                  |\n"
        "|  08:45 - 09:30 | Period 2 : Mathematics            | Mrs. A. Gupta   | Room 101                  |\n"
        "|  09:30 - 10:15 | Period 3 : Science (Chemistry)    | Dr. S. K. Roy   | Science Lab 2             |\n"
        "|  10:15 - 11:00 | Period 4 : Social Studies         | Mrs. P. Joshi   | Room 101                  |\n"
        "|  11:00 - 11:45 | Period 5 : Hindi Core             | Mr. M. Tripathi | Room 101                  |\n"
        "|  11:45 - 12:15 | Period 6 : [RECESS / LUNCH BREAK] | Institutional   | Cafeteria                 |\n"
        "|  12:15 - 01:00 | Period 7 : Computer Applications  | Mr. Amit Kumar  | Computer Lab 1            |\n"
        "|  01:00 - 01:45 | Period 8 : Physical Education     | Coach R. Singh  | Sports Complex            |\n"
        "+--------------------------------------------------------------------------------------------------+"
    )
    story.append(Paragraph(f"<font face='Courier' size='6.7'>{mobile_box.replace(chr(10), '<br/>').replace(' ', '&nbsp;')}</font>", code_style))

    story.append(PageBreak())

    # ==================================================================
    # PAGE 7: TECHNICAL REST API SPECIFICATION & SECURITY AUDIT
    # ==================================================================
    story.append(Paragraph("12. Technical REST API Specification", h1_style))
    story.append(Paragraph(
        "All timetable interactions are powered by well-defined REST endpoints secured by OAuth2 JWT tokens "
        "and granular Role-Based Access Control (RBAC) permissions:",
        body_style
    ))

    api_data = [
        [
            Paragraph("HTTP Verb & Endpoint", table_cell_header),
            Paragraph("Permission Required", table_cell_header),
            Paragraph("Purpose & Description", table_cell_header),
            Paragraph("Payload / Parameters", table_cell_header),
            Paragraph("Expected Responses", table_cell_header),
        ],
        [
            Paragraph("<code>GET /admin/timetable/periods</code>", table_cell),
            Paragraph("<code>timetable.slot.read</code>", table_cell),
            Paragraph("Fetch school bell timings.", table_cell),
            Paragraph("None (school-scoped).", table_cell),
            Paragraph("200 OK: List of period objects.", table_cell),
        ],
        [
            Paragraph("<code>POST /admin/timetable/periods</code>", table_cell),
            Paragraph("<code>timetable.slot.write</code>", table_cell),
            Paragraph("Create new school bell period.", table_cell),
            Paragraph("<code>period_no, start_time, end_time, name, is_break</code>", table_cell),
            Paragraph("201 Created<br/>409 Conflict (dup period).", table_cell),
        ],
        [
            Paragraph("<code>GET /admin/timetable/slots</code>", table_cell),
            Paragraph("<code>timetable.slot.read</code>", table_cell),
            Paragraph("Query timetable grid.", table_cell),
            Paragraph("<code>class_section_id, teacher_id, day_of_week</code>", table_cell),
            Paragraph("200 OK: Array of slot objects.", table_cell),
        ],
        [
            Paragraph("<code>POST /admin/timetable/slots/check</code>", table_cell),
            Paragraph("<code>timetable.slot.read</code>", table_cell),
            Paragraph("Pre-flight live conflict check.", table_cell),
            Paragraph("<code>SlotIn</code> (section, day, period, teacher, room)", table_cell),
            Paragraph("200 OK: <code>{ok: bool, conflicts: []}</code>", table_cell),
        ],
        [
            Paragraph("<code>POST /admin/timetable/slots</code>", table_cell),
            Paragraph("<code>timetable.slot.write</code>", table_cell),
            Paragraph("Create timetable slot (Draft).", table_cell),
            Paragraph("<code>SlotIn</code> + optional <code>override_reason</code>", table_cell),
            Paragraph("201 Created<br/>409 Conflict (clash).", table_cell),
        ],
        [
            Paragraph("<code>PUT /admin/timetable/slots/{id}</code>", table_cell),
            Paragraph("<code>timetable.slot.write</code>", table_cell),
            Paragraph("Update slot details.", table_cell),
            Paragraph("<code>SlotIn</code> payload", table_cell),
            Paragraph("200 OK<br/>404 Not Found / 409 Conflict.", table_cell),
        ],
        [
            Paragraph("<code>DELETE /admin/timetable/slots/{id}</code>", table_cell),
            Paragraph("<code>timetable.slot.write</code>", table_cell),
            Paragraph("Remove a timetable slot.", table_cell),
            Paragraph("URL path parameter <code>slot_id</code>", table_cell),
            Paragraph("204 No Content<br/>404 Not Found.", table_cell),
        ],
        [
            Paragraph("<code>POST /admin/timetable/publish</code>", table_cell),
            Paragraph("<code>timetable.slot.write</code>", table_cell),
            Paragraph("Publish draft slots institutional wide.", table_cell),
            Paragraph("Optional <code>class_section_id</code> query", table_cell),
            Paragraph("200 OK: <code>{published: true, count: N}</code>", table_cell),
        ],
        [
            Paragraph("<code>POST /admin/timetable/unpublish</code>", table_cell),
            Paragraph("<code>timetable.slot.write</code>", table_cell),
            Paragraph("Revert slots back to draft state.", table_cell),
            Paragraph("Optional <code>class_section_id</code> query", table_cell),
            Paragraph("200 OK: <code>{published: false, count: N}</code>", table_cell),
        ],
        [
            Paragraph("<code>GET /admin/timetable/completeness</code>", table_cell),
            Paragraph("<code>timetable.slot.read</code>", table_cell),
            Paragraph("Inspect section timetable gaps.", table_cell),
            Paragraph("Optional <code>academic_year_id</code> query", table_cell),
            Paragraph("200 OK: Placed vs missing slots.", table_cell),
        ],
        [
            Paragraph("<code>GET /admin/timetable/workload</code>", table_cell),
            Paragraph("<code>timetable.slot.read</code>", table_cell),
            Paragraph("Teacher weekly workload chart.", table_cell),
            Paragraph("None (evaluates all active staff)", table_cell),
            Paragraph("200 OK: Spread, limits, fair share.", table_cell),
        ],
        [
            Paragraph("<code>GET .../free-teachers</code>", table_cell),
            Paragraph("<code>timetable.substitution.manage</code>", table_cell),
            Paragraph("Ranked substitute candidates.", table_cell),
            Paragraph("URL path <code>slot_id</code> + date query", table_cell),
            Paragraph("200 OK: Ranked free teachers.", table_cell),
        ],
        [
            Paragraph("<code>POST /admin/timetable/substitutions</code>", table_cell),
            Paragraph("<code>timetable.substitution.manage</code>", table_cell),
            Paragraph("Arrange single-day relief cover.", table_cell),
            Paragraph("<code>slot_id, date, substitute_id, reason</code>", table_cell),
            Paragraph("201 Created<br/>409 Conflict (clash/leave).", table_cell),
        ],
    ]
    api_table = Table(api_data, colWidths=[105, 95, 110, 105, 100])
    api_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(api_table)
    story.append(Spacer(1, 8))

    story.append(Paragraph("13. Multi-Tenant Security & Privilege Isolation Audit", h1_style))
    story.append(Paragraph(
        "Tenant isolation is strictly maintained across all timetable operations. "
        "Every query filters explicitly by <code>school_id == user.school_id</code>. "
        "During our security penetration tests: "
        "(1) Attempting to update or delete a timetable slot belonging to another school returned HTTP 404 Not Found without leaking existence. "
        "(2) An authenticated Teacher attempting to invoke <code>POST /admin/timetable/publish</code> was refused with HTTP 403 Forbidden. "
        "(3) Student and Parent API requests strictly filter by <code>published_only = True</code>, preventing information disclosure of preliminary drafts.",
        body_style
    ))

    story.append(PageBreak())

    # ==================================================================
    # PAGE 8: SCHOOL ADMINISTRATION SOPS & OPERATIONAL RUNBOOK
    # ==================================================================
    story.append(Paragraph("14. Institutional Standard Operating Procedures (SOPs)", h1_style))
    story.append(Paragraph(
        "For Principals, Vice-Principals, and Academic Coordinators, the following SOPs dictate standardized timetable operations:",
        body_style
    ))

    sop_data = [
        [
            Paragraph("Standard Operating Procedure", table_cell_header),
            Paragraph("Execution Timeline", table_cell_header),
            Paragraph("Responsible Role", table_cell_header),
            Paragraph("Mandatory Operational Protocol", table_cell_header),
        ],
        [
            Paragraph("<b>SOP-TT-01: Academic Year Bell Timing Setup</b>", table_cell),
            Paragraph("3 Weeks Before Term Start", table_cell),
            Paragraph("Principal & Academic Head", table_cell),
            Paragraph("1. Audit period bell timings via <code>/admin/timetable/periods</code>.<br/>2. Ensure Period 6 is flagged as <code>is_break=True</code> (Lunch).<br/>3. Verify period start and end times match institutional bus schedules.", table_cell),
        ],
        [
            Paragraph("<b>SOP-TT-02: Master Schedule Construction</b>", table_cell),
            Paragraph("2 Weeks Before Term Start", table_cell),
            Paragraph("Academic Coordinators", table_cell),
            Paragraph("1. Build section schedules using Web Builder in Draft mode.<br/>2. Resolve all teacher and room collisions flagged in <code>SlotModal</code>.<br/>3. Review <code>/admin/timetable/completeness</code> to ensure zero empty periods.<br/>4. Review <code>/admin/timetable/workload</code> to verify teacher spread < 5 periods.", table_cell),
        ],
        [
            Paragraph("<b>SOP-TT-03: Timetable Publication & Rollout</b>", table_cell),
            Paragraph("Friday Before Term Opening", table_cell),
            Paragraph("Vice-Principal (Academics)", table_cell),
            Paragraph("1. Verify all sections are 100% configured.<br/>2. Execute 'Publish Changes' on each section or school-wide.<br/>3. Verify that Teacher, Student, and Parent mobile apps reflect published schedules.", table_cell),
        ],
        [
            Paragraph("<b>SOP-TT-04: Daily 07:30 AM Substitution Desk</b>", table_cell),
            Paragraph("Daily: 07:15 AM - 07:45 AM", table_cell),
            Paragraph("Duty Coordinator / Office Head", table_cell),
            Paragraph("1. Review incoming morning teacher leave applications.<br/>2. Open Substitution Desk; review automatically flagged vacant periods.<br/>3. Select free teachers (specialists prioritized); commit substitutions.<br/>4. Ensure zero 'unfilled' slots remain before morning assembly (08:00 AM).", table_cell),
        ],
        [
            Paragraph("<b>SOP-TT-05: Mid-Term Faculty Resignation Protocol</b>", table_cell),
            Paragraph("Upon Faculty Exit", table_cell),
            Paragraph("HR & Academic Coordinator", table_cell),
            Paragraph("1. Before marking teacher 'Exited', reassign all their slots via Web Builder.<br/>2. Allocate replacement teacher.<br/>3. Publish updated slots to immediately refresh student schedules.", table_cell),
        ],
    ]
    sop_table = Table(sop_data, colWidths=[115, 80, 85, 235])
    sop_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(sop_table)
    story.append(Spacer(1, 8))

    story.append(Paragraph("15. Diagnostic & Troubleshooting Runbook", h1_style))
    story.append(Paragraph(
        "<b>Q1: Why does slot creation fail with HTTP 409 'Teacher or room is already booked'?</b><br/>"
        "<i>Diagnosis:</i> Another lesson is already scheduled for that teacher or normalized room in that period. "
        "Open <code>/admin/timetable/slots</code> for that day and period to identify the conflicting section. "
        "Reassign the conflicting lesson or select an alternative period.<br/>"
        "<b>Q2: Why are changes made by coordinators not visible on the Student Mobile App?</b><br/>"
        "<i>Diagnosis:</i> The slots are currently in <b>Draft Mode</b> (<code>is_published=false</code>). "
        "The coordinator must click 'Publish Changes' in the Web Builder header to make them live institutional-wide.<br/>"
        "<b>Q3: Why does assigning cover to a free teacher fail with HTTP 409 'on approved leave'?</b><br/>"
        "<i>Diagnosis:</i> The candidate teacher has an approved staff leave request for that date. The Substitution engine "
        "refuses to assign relief duty to absent staff. Select another candidate from the ranked list.",
        body_style
    ))
    story.append(Spacer(1, 8))

    # Formal Institutional Signoff Block
    signoff_table_data = [
        [
            Paragraph("<b>Senior QA Auditor:</b><br/>Senior QA Engineer & Enterprise Architect<br/>Certified Software Quality Analyst (CSQA)", table_cell),
            Paragraph("<b>School Operations Consultant:</b><br/>Lead ERP Systems Consultant<br/>CBSE Institutional Administration Advisory", table_cell),
            Paragraph("<b>Operational Status:</b><br/><font color='#047857'><b>FULLY OPERATIONAL & VERIFIED</b></font><br/>All conflict engines & workflows green.", table_cell_bold),
        ]
    ]
    signoff_table = Table(signoff_table_data, colWidths=[175, 170, 170])
    signoff_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BG_CARD),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(signoff_table)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Timetable Architecture & Operations Guide generated successfully: {filename}")


if __name__ == "__main__":
    out_path = sys.argv[1] if len(sys.argv) > 1 else "Sunrise-Timetable-Architecture-and-Operations-Guide.pdf"
    build_timetable_guide_pdf(out_path)
