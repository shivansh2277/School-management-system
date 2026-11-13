import os
import sys
import time
from playwright.sync_api import sync_playwright

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

OUTPUT_DIR = os.path.abspath("school-management-system/docs/screenshots/mobile_app_redesign")
AUTH_DIR = os.path.join(OUTPUT_DIR, "00_auth")
TEACHER_DIR = os.path.join(OUTPUT_DIR, "01_teacher")
PARENT_DIR = os.path.join(OUTPUT_DIR, "02_parent")
STUDENT_DIR = os.path.join(OUTPUT_DIR, "03_student")

for d in [AUTH_DIR, TEACHER_DIR, PARENT_DIR, STUDENT_DIR]:
    os.makedirs(d, exist_ok=True)

DEVICE_CONFIG = {
    "viewport": {"width": 390, "height": 844},
    "device_scale_factor": 2,
    "is_mobile": True,
    "has_touch": True,
}

BASE_URL = "http://localhost:8081"

def wait(ms=1500):
    time.sleep(ms / 1000.0)

def safe_click(locator, timeout=3000):
    try:
        locator.first.click(force=True, timeout=timeout)
        return True
    except Exception as e:
        return False

def nav_via_drawer(page, item_title):
    try:
        # Click menu button
        page.locator('[aria-label="Open Menu"]').first.click(force=True, timeout=3000)
        wait(800)
        page.get_by_text(item_title, exact=True).last.click(force=True, timeout=3000)
        wait(2000)
    except Exception as e:
        print(f"  [Drawer nav warning] '{item_title}': {e}", flush=True)

# ==========================================
# 00_AUTH
# ==========================================
def capture_auth(browser):
    print("\n================== 00_AUTH ==================", flush=True)
    context = browser.new_context(**DEVICE_CONFIG)
    page = context.new_page()
    page.goto(BASE_URL, wait_until="networkidle")
    wait(2000)

    # 1. Student tab (Default)
    p1 = os.path.join(AUTH_DIR, "01_login_student_tab.png")
    page.screenshot(path=p1)
    print(f"Captured: {p1}", flush=True)

    # 2. Parent tab
    try:
        page.get_by_text("parent", exact=True).first.click(force=True)
        wait(600)
        p2 = os.path.join(AUTH_DIR, "02_login_parent_tab.png")
        page.screenshot(path=p2)
        print(f"Captured: {p2}", flush=True)
    except Exception as e:
        print("Error on parent tab:", e, flush=True)

    # 3. Teacher tab
    try:
        page.get_by_text("teacher", exact=True).first.click(force=True)
        wait(600)
        p3 = os.path.join(AUTH_DIR, "03_login_teacher_tab.png")
        page.screenshot(path=p3)
        print(f"Captured: {p3}", flush=True)
    except Exception as e:
        print("Error on teacher tab:", e, flush=True)

    # 4. Error state
    try:
        inputs = page.locator("input")
        if inputs.count() >= 2:
            inputs.nth(1).fill("WrongPassword999")
            page.get_by_text("Sign in", exact=True).click(force=True)
            wait(1500)
            p4 = os.path.join(AUTH_DIR, "04_login_validation_error.png")
            page.screenshot(path=p4)
            print(f"Captured: {p4}", flush=True)
    except Exception as e:
        print("Error on validation state:", e, flush=True)

    context.close()

# ==========================================
# 01_TEACHER
# ==========================================
def capture_teacher(browser):
    print("\n================== 01_TEACHER ==================", flush=True)
    context = browser.new_context(**DEVICE_CONFIG)
    page = context.new_page()
    page.goto(BASE_URL, wait_until="networkidle")
    wait(2000)

    # Login as Teacher
    page.locator("text=teacher: TCH001").click(force=True)
    wait(500)
    page.get_by_text("Sign in", exact=True).click(force=True)
    wait(3000)

    # 1. Dashboard
    p1 = os.path.join(TEACHER_DIR, "01_teacher_dashboard.png")
    page.screenshot(path=p1)
    print(f"Captured: {p1}", flush=True)

    # 2. Drawer
    page.locator('[aria-label="Open Menu"]').first.click(force=True)
    wait(800)
    p2 = os.path.join(TEACHER_DIR, "02_teacher_navigation_drawer.png")
    page.screenshot(path=p2)
    print(f"Captured: {p2}", flush=True)

    # 3. My Classes
    page.get_by_text("My Classes", exact=True).last.click(force=True)
    wait(2000)
    p3 = os.path.join(TEACHER_DIR, "03_teacher_classes_list.png")
    page.screenshot(path=p3)
    print(f"Captured: {p3}", flush=True)

    # 4. Class roster (expand 10-A)
    try:
        page.locator("text=10-A").last.click(force=True, timeout=2500)
        wait(1200)
        p4 = os.path.join(TEACHER_DIR, "04_teacher_class_students_roster.png")
        page.screenshot(path=p4)
        print(f"Captured: {p4}", flush=True)
    except Exception as e:
        print("Could not expand class roster:", e, flush=True)

    # 5. Attendance roster
    nav_via_drawer(page, "Attendance")
    p5 = os.path.join(TEACHER_DIR, "05_teacher_attendance_roster.png")
    page.screenshot(path=p5)
    print(f"Captured: {p5}", flush=True)

    # 6. Homework manager
    nav_via_drawer(page, "Homework Manager")
    p6 = os.path.join(TEACHER_DIR, "06_teacher_homework_manager.png")
    page.screenshot(path=p6)
    print(f"Captured: {p6}", flush=True)

    # 7. Homework submissions (click a card)
    try:
        hw_card = page.locator('div:has-text("Mathematics - 8-A"), div:has-text("Due")').last
        hw_card.click(force=True, timeout=2500)
        wait(1500)
        p7 = os.path.join(TEACHER_DIR, "07_teacher_homework_submissions.png")
        page.screenshot(path=p7)
        print(f"Captured: {p7}", flush=True)
    except Exception as e:
        print("Could not expand homework submissions:", e, flush=True)

    # 8. New assignment composer
    try:
        new_btn = page.locator('text=New assignment').last
        if new_btn.count() > 0:
            new_btn.click(force=True, timeout=2500)
            wait(1000)
            p8 = os.path.join(TEACHER_DIR, "08_teacher_homework_new_assignment_modal.png")
            page.screenshot(path=p8)
            print(f"Captured: {p8}", flush=True)
            # Toggle off
            new_btn.click(force=True, timeout=2500)
            wait(500)
    except Exception as e:
        print("Could not open homework composer:", e, flush=True)

    # 9. Marks Entry / Results papers list
    nav_via_drawer(page, "Marks Entry & Results")
    p9 = os.path.join(TEACHER_DIR, "09_teacher_marks_entry_exams_list.png")
    page.screenshot(path=p9)
    print(f"Captured: {p9}", flush=True)

    # 10. Marks entry sheet for a paper
    try:
        paper_card = page.locator('text=Mathematics, div:has-text("Max:"), div[role="button"]:has-text("10-A")').last
        paper_card.click(force=True, timeout=2500)
        wait(1500)
        p10 = os.path.join(TEACHER_DIR, "10_teacher_marks_entry_sheet.png")
        page.screenshot(path=p10)
        print(f"Captured: {p10}", flush=True)
    except Exception as e:
        print("Could not open marks entry sheet:", e, flush=True)

    # 11. Leave apply form
    nav_via_drawer(page, "Leave & Substitution Duties")
    p11 = os.path.join(TEACHER_DIR, "11_teacher_leave_apply_form.png")
    page.screenshot(path=p11)
    print(f"Captured: {p11}", flush=True)

    # 12. Leave Requests tab
    try:
        req_btn = page.locator('div[role="button"]:has-text("Requests")').last
        req_btn.click(force=True, timeout=2500)
        wait(1000)
        p12 = os.path.join(TEACHER_DIR, "12_teacher_leave_requests_tab.png")
        page.screenshot(path=p12)
        print(f"Captured: {p12}", flush=True)
    except Exception as e:
        print("Could not click requests tab:", e, flush=True)

    # 13. Leave History tab
    try:
        hist_btn = page.locator('div[role="button"]:has-text("My Leaves")').last
        hist_btn.click(force=True, timeout=2500)
        wait(1000)
        p13 = os.path.join(TEACHER_DIR, "13_teacher_leave_history_tab.png")
        page.screenshot(path=p13)
        print(f"Captured: {p13}", flush=True)
    except Exception as e:
        print("Could not click history tab:", e, flush=True)

    # 14. Leave Duties tab
    try:
        duty_btn = page.locator('div[role="button"]:has-text("Duties")').last
        duty_btn.click(force=True, timeout=2500)
        wait(1000)
        p14 = os.path.join(TEACHER_DIR, "14_teacher_leave_duties_tab.png")
        page.screenshot(path=p14)
        print(f"Captured: {p14}", flush=True)
    except Exception as e:
        print("Could not click duties tab:", e, flush=True)

    # 15. Timetable
    nav_via_drawer(page, "Timetable & Slots")
    p15 = os.path.join(TEACHER_DIR, "15_teacher_timetable.png")
    page.screenshot(path=p15)
    print(f"Captured: {p15}", flush=True)

    # 16. Stock inventory
    nav_via_drawer(page, "Classroom Supplies / Stock")
    p16 = os.path.join(TEACHER_DIR, "16_teacher_stock_inventory.png")
    page.screenshot(path=p16)
    print(f"Captured: {p16}", flush=True)

    # 17. Stock flag modal
    try:
        flag_btn = page.locator('text=Flag, text=Request').last
        if flag_btn.count() > 0:
            flag_btn.click(force=True, timeout=2500)
            wait(1000)
            p17 = os.path.join(TEACHER_DIR, "17_teacher_stock_flag_modal.png")
            page.screenshot(path=p17)
            print(f"Captured: {p17}", flush=True)
            page.keyboard.press("Escape")
            wait(500)
    except Exception as e:
        print("Could not open stock modal:", e, flush=True)

    # 18. School notices
    nav_via_drawer(page, "School Notices")
    p18 = os.path.join(TEACHER_DIR, "18_teacher_school_notices.png")
    page.screenshot(path=p18)
    print(f"Captured: {p18}", flush=True)

    # 19. Grievance desk
    nav_via_drawer(page, "Grievance Desk")
    p19 = os.path.join(TEACHER_DIR, "19_teacher_grievances_desk.png")
    page.screenshot(path=p19)
    print(f"Captured: {p19}", flush=True)

    # 20. Profile
    nav_via_drawer(page, "Faculty Profile")
    p20 = os.path.join(TEACHER_DIR, "20_teacher_profile.png")
    page.screenshot(path=p20)
    print(f"Captured: {p20}", flush=True)

    context.close()

# ==========================================
# 02_PARENT
# ==========================================
def capture_parent(browser):
    print("\n================== 02_PARENT ==================", flush=True)
    context = browser.new_context(**DEVICE_CONFIG)
    page = context.new_page()
    page.goto(BASE_URL, wait_until="networkidle")
    wait(2000)

    # Login as Parent
    page.locator("text=parent: 9876500001").click(force=True)
    wait(500)
    page.get_by_text("Sign in", exact=True).click(force=True)
    wait(3000)

    # 1. Dashboard (Child 1 - Aarav)
    p1 = os.path.join(PARENT_DIR, "01_parent_dashboard_child1.png")
    page.screenshot(path=p1)
    print(f"Captured: {p1}", flush=True)

    # 2. Dashboard (Child 2 - Ishita)
    try:
        page.locator('text=Ishita Sharma').last.click(force=True, timeout=2500)
        wait(1500)
        p2 = os.path.join(PARENT_DIR, "02_parent_dashboard_child2.png")
        page.screenshot(path=p2)
        print(f"Captured: {p2}", flush=True)
        # Switch back to Aarav
        page.locator('text=Aarav Sharma').last.click(force=True, timeout=2500)
        wait(1000)
    except Exception as e:
        print("Could not switch to Ishita:", e, flush=True)

    # 3. Navigation Drawer
    page.locator('[aria-label="Open Menu"]').first.click(force=True)
    wait(800)
    p3 = os.path.join(PARENT_DIR, "03_parent_navigation_drawer.png")
    page.screenshot(path=p3)
    print(f"Captured: {p3}", flush=True)

    # 4. Child profile
    page.get_by_text("Child", exact=True).last.click(force=True)
    wait(2000)
    p4 = os.path.join(PARENT_DIR, "04_parent_child_profile.png")
    page.screenshot(path=p4)
    print(f"Captured: {p4}", flush=True)

    # 5. Fees ledger
    nav_via_drawer(page, "Fees")
    p5 = os.path.join(PARENT_DIR, "05_parent_fees_ledger.png")
    page.screenshot(path=p5)
    print(f"Captured: {p5}", flush=True)

    # 6. Fee breakdown / invoice detail
    try:
        inv_item = page.locator('text=Pay Online, text=Outstanding, text=₹').last
        inv_item.click(force=True, timeout=2500)
        wait(1200)
        p6 = os.path.join(PARENT_DIR, "06_parent_fee_breakdown_detail.png")
        page.screenshot(path=p6)
        print(f"Captured: {p6}", flush=True)
    except Exception as e:
        print("Could not expand fee breakdown:", e, flush=True)

    # 7. Attendance calendar
    nav_via_drawer(page, "Attendance")
    p7 = os.path.join(PARENT_DIR, "07_parent_attendance_calendar.png")
    page.screenshot(path=p7)
    print(f"Captured: {p7}", flush=True)

    # 8. Apply Leave Modal
    try:
        leave_btn = page.locator('text=Request Leave, text=Apply Leave').last
        if leave_btn.count() > 0:
            leave_btn.click(force=True, timeout=2500)
            wait(1000)
            p8 = os.path.join(PARENT_DIR, "08_parent_apply_leave_modal.png")
            page.screenshot(path=p8)
            print(f"Captured: {p8}", flush=True)
            page.keyboard.press("Escape")
            wait(500)
    except Exception as e:
        print("Could not open parent leave modal:", e, flush=True)

    # 9. Results / Report Card list
    nav_via_drawer(page, "Results")
    p9 = os.path.join(PARENT_DIR, "09_parent_results_report_card.png")
    page.screenshot(path=p9)
    print(f"Captured: {p9}", flush=True)

    # 10. Report card detail / breakdown
    try:
        exam_item = page.locator('text=Term 1, text=Periodic Test').last
        exam_item.click(force=True, timeout=2500)
        wait(1200)
        p10 = os.path.join(PARENT_DIR, "10_parent_report_card_breakdown.png")
        page.screenshot(path=p10)
        print(f"Captured: {p10}", flush=True)
    except Exception as e:
        print("Could not open report card detail:", e, flush=True)

    # 11. Timetable
    nav_via_drawer(page, "Timetable")
    p11 = os.path.join(PARENT_DIR, "11_parent_weekly_timetable.png")
    page.screenshot(path=p11)
    print(f"Captured: {p11}", flush=True)

    # 12. Homework
    nav_via_drawer(page, "Homework")
    p12 = os.path.join(PARENT_DIR, "12_parent_homework.png")
    page.screenshot(path=p12)
    print(f"Captured: {p12}", flush=True)

    # 13. Notices
    nav_via_drawer(page, "Notices")
    p13 = os.path.join(PARENT_DIR, "13_parent_school_notices.png")
    page.screenshot(path=p13)
    print(f"Captured: {p13}", flush=True)

    # 14. Grievances
    nav_via_drawer(page, "Grievances")
    p14 = os.path.join(PARENT_DIR, "14_parent_grievances_desk.png")
    page.screenshot(path=p14)
    print(f"Captured: {p14}", flush=True)

    # 15. Hostel & Mess
    nav_via_drawer(page, "Hostel & Mess")
    p15 = os.path.join(PARENT_DIR, "15_parent_hostel_mess.png")
    page.screenshot(path=p15)
    print(f"Captured: {p15}", flush=True)

    # 16. Profile
    nav_via_drawer(page, "Profile")
    p16 = os.path.join(PARENT_DIR, "16_parent_profile.png")
    page.screenshot(path=p16)
    print(f"Captured: {p16}", flush=True)

    context.close()

# ==========================================
# 03_STUDENT
# ==========================================
def capture_student(browser):
    print("\n================== 03_STUDENT ==================", flush=True)
    context = browser.new_context(**DEVICE_CONFIG)
    page = context.new_page()
    page.goto(BASE_URL, wait_until="networkidle")
    wait(2000)

    # Login as Student
    page.locator("text=student: 2024000001").click(force=True)
    wait(500)
    page.get_by_text("Sign in", exact=True).click(force=True)
    wait(3000)

    # 1. Dashboard
    p1 = os.path.join(STUDENT_DIR, "01_student_dashboard.png")
    page.screenshot(path=p1)
    print(f"Captured: {p1}", flush=True)

    # 2. Drawer
    page.locator('[aria-label="Open Menu"]').first.click(force=True)
    wait(800)
    p2 = os.path.join(STUDENT_DIR, "02_student_navigation_drawer.png")
    page.screenshot(path=p2)
    print(f"Captured: {p2}", flush=True)

    # 3. Weekly Timetable
    page.get_by_text("Weekly Timetable", exact=True).last.click(force=True)
    wait(2000)
    p3 = os.path.join(STUDENT_DIR, "03_student_weekly_timetable.png")
    page.screenshot(path=p3)
    print(f"Captured: {p3}", flush=True)

    # 4. Homework list
    nav_via_drawer(page, "Homework")
    p4 = os.path.join(STUDENT_DIR, "04_student_homework_list.png")
    page.screenshot(path=p4)
    print(f"Captured: {p4}", flush=True)

    # 5. Homework detail
    try:
        hw_item = page.locator('text=Mathematics, text=Solve, text=Chapter, text=Due').last
        hw_item.click(force=True, timeout=2500)
        wait(1200)
        p5 = os.path.join(STUDENT_DIR, "05_student_homework_detail.png")
        page.screenshot(path=p5)
        print(f"Captured: {p5}", flush=True)
    except Exception as e:
        print("Could not expand student homework detail:", e, flush=True)

    # 6. Results
    nav_via_drawer(page, "Exam Results & Scorecard")
    p6 = os.path.join(STUDENT_DIR, "06_student_results_scorecard.png")
    page.screenshot(path=p6)
    print(f"Captured: {p6}", flush=True)

    # 7. Report card detail
    try:
        exam_row = page.locator('text=Term 1, text=Periodic Test').last
        exam_row.click(force=True, timeout=2500)
        wait(1200)
        p7 = os.path.join(STUDENT_DIR, "07_student_report_card_detail.png")
        page.screenshot(path=p7)
        print(f"Captured: {p7}", flush=True)
    except Exception as e:
        print("Could not expand student report card:", e, flush=True)

    # 8. Attendance history
    nav_via_drawer(page, "Attendance History")
    p8 = os.path.join(STUDENT_DIR, "08_student_attendance_record.png")
    page.screenshot(path=p8)
    print(f"Captured: {p8}", flush=True)

    # 9. School notices
    nav_via_drawer(page, "School Notices")
    p9 = os.path.join(STUDENT_DIR, "09_student_school_notices.png")
    page.screenshot(path=p9)
    print(f"Captured: {p9}", flush=True)

    # 10. Hostel & Mess
    nav_via_drawer(page, "Hostel & Mess")
    p10 = os.path.join(STUDENT_DIR, "10_student_hostel_mess.png")
    page.screenshot(path=p10)
    print(f"Captured: {p10}", flush=True)

    # 11. Profile
    nav_via_drawer(page, "Student Profile")
    p11 = os.path.join(STUDENT_DIR, "11_student_profile.png")
    page.screenshot(path=p11)
    print(f"Captured: {p11}", flush=True)

    context.close()

def main():
    print("Beginning automated capture of Sunrise School ERP Mobile App...", flush=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        capture_auth(browser)
        capture_teacher(browser)
        capture_parent(browser)
        capture_student(browser)
        browser.close()
    print("\n================== COMPLETE ==================", flush=True)
    print("All mobile screenshots captured successfully!", flush=True)

if __name__ == "__main__":
    main()
