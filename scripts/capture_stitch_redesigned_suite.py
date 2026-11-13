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

def wait(ms=1200):
    time.sleep(ms / 1000.0)

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # ==========================================
        # 00_AUTH
        # ==========================================
        print("\n--- 00_AUTH ---", flush=True)
        ctx = browser.new_context(**DEVICE_CONFIG)
        page = ctx.new_page()
        page.set_default_timeout(6000)
        page.goto(BASE_URL, wait_until="networkidle")
        wait(2000)

        # 1. Student tab
        p1 = os.path.join(AUTH_DIR, "01_login_student_tab.png")
        page.screenshot(path=p1)
        print(f"Captured: {p1}", flush=True)

        # 2. Parent tab
        try:
            page.get_by_text("parent", exact=True).click(force=True)
            wait(600)
            p2 = os.path.join(AUTH_DIR, "02_login_parent_tab.png")
            page.screenshot(path=p2)
            print(f"Captured: {p2}", flush=True)
        except Exception as e:
            print(f"Error on parent tab: {e}", flush=True)

        # 3. Teacher tab
        try:
            page.get_by_text("teacher", exact=True).click(force=True)
            wait(600)
            p3 = os.path.join(AUTH_DIR, "03_login_teacher_tab.png")
            page.screenshot(path=p3)
            print(f"Captured: {p3}", flush=True)
        except Exception as e:
            print(f"Error on teacher tab: {e}", flush=True)

        # 4. Error state
        try:
            inputs = page.locator("input")
            if inputs.count() >= 2:
                inputs.nth(1).fill("WrongPassword999")
                page.get_by_text("Sign In", exact=True).or_(page.get_by_text("Sign in", exact=True)).first.click(force=True)
                wait(1500)
                p4 = os.path.join(AUTH_DIR, "04_login_validation_error.png")
                page.screenshot(path=p4)
                print(f"Captured: {p4}", flush=True)
        except Exception as e:
            print(f"Error on validation state: {e}", flush=True)

        ctx.close()

        # ==========================================
        # 01_TEACHER
        # ==========================================
        print("\n--- 01_TEACHER ---", flush=True)
        ctx = browser.new_context(**DEVICE_CONFIG)
        page = ctx.new_page()
        page.set_default_timeout(6000)
        page.goto(BASE_URL, wait_until="networkidle")
        wait(2000)

        page.locator("text=teacher: TCH001").click(force=True)
        wait(400)
        page.get_by_text("Sign In", exact=True).or_(page.get_by_text("Sign in", exact=True)).first.click(force=True)
        wait(3000)

        # 1. Dashboard
        page.screenshot(path=os.path.join(TEACHER_DIR, "01_teacher_dashboard.png"))
        print("Captured: 01_teacher_dashboard.png", flush=True)

        # 2. Drawer
        try:
            page.locator('[aria-label="Open Menu"]').first.click(force=True)
            wait(800)
            page.screenshot(path=os.path.join(TEACHER_DIR, "02_teacher_navigation_drawer.png"))
            print("Captured: 02_teacher_navigation_drawer.png", flush=True)
            page.keyboard.press("Escape")
            wait(500)
        except Exception as e:
            print(f"Teacher drawer: {e}", flush=True)

        # 3. Attendance Roster
        page.goto(f"{BASE_URL}/(teacher)/attendance", wait_until="networkidle")
        wait(2000)
        page.screenshot(path=os.path.join(TEACHER_DIR, "03_teacher_attendance_roster.png"))
        print("Captured: 03_teacher_attendance_roster.png", flush=True)

        # 4. Homework Manager
        page.goto(f"{BASE_URL}/(teacher)/homework", wait_until="networkidle")
        wait(2000)
        page.screenshot(path=os.path.join(TEACHER_DIR, "04_teacher_homework_manager.png"))
        print("Captured: 04_teacher_homework_manager.png", flush=True)

        # 5. Homework Submissions Expanded
        try:
            card_btn = page.locator('text=View Submissions').first
            if card_btn.count() > 0:
                card_btn.click(force=True)
                wait(1200)
                page.screenshot(path=os.path.join(TEACHER_DIR, "05_teacher_homework_submissions_expanded.png"))
                print("Captured: 05_teacher_homework_submissions_expanded.png", flush=True)
        except Exception as e:
            print(f"Teacher homework expand: {e}", flush=True)

        # 6. Classes List
        page.goto(f"{BASE_URL}/(teacher)/classes", wait_until="networkidle")
        wait(2000)
        page.screenshot(path=os.path.join(TEACHER_DIR, "06_teacher_classes_list.png"))
        print("Captured: 06_teacher_classes_list.png", flush=True)

        # 7. Class Roster Expanded
        try:
            sec_card = page.locator('text=10-A').first
            if sec_card.count() > 0:
                sec_card.click(force=True)
                wait(1200)
                page.screenshot(path=os.path.join(TEACHER_DIR, "07_teacher_class_roster_expanded.png"))
                print("Captured: 07_teacher_class_roster_expanded.png", flush=True)
        except Exception as e:
            print(f"Teacher class roster expand: {e}", flush=True)

        # 8. Leave Apply
        page.goto(f"{BASE_URL}/(teacher)/leave", wait_until="networkidle")
        wait(2000)
        page.screenshot(path=os.path.join(TEACHER_DIR, "08_teacher_leave_apply.png"))
        print("Captured: 08_teacher_leave_apply.png", flush=True)

        # 9. Leave Requests Tab
        try:
            page.locator('text=Requests').first.click(force=True)
            wait(800)
            page.screenshot(path=os.path.join(TEACHER_DIR, "09_teacher_leave_requests_tab.png"))
            print("Captured: 09_teacher_leave_requests_tab.png", flush=True)
        except Exception as e:
            print(f"Leave requests tab: {e}", flush=True)

        # 10. Leave History Tab
        try:
            page.locator('text=My Leaves').first.click(force=True)
            wait(800)
            page.screenshot(path=os.path.join(TEACHER_DIR, "10_teacher_leave_history_tab.png"))
            print("Captured: 10_teacher_leave_history_tab.png", flush=True)
        except Exception as e:
            print(f"Leave history tab: {e}", flush=True)

        # 11. Leave Duties Tab
        try:
            page.locator('text=Duties').first.click(force=True)
            wait(800)
            page.screenshot(path=os.path.join(TEACHER_DIR, "11_teacher_leave_duties_tab.png"))
            print("Captured: 11_teacher_leave_duties_tab.png", flush=True)
        except Exception as e:
            print(f"Leave duties tab: {e}", flush=True)

        # 12. Timetable
        page.goto(f"{BASE_URL}/(teacher)/timetable", wait_until="networkidle")
        wait(2000)
        page.screenshot(path=os.path.join(TEACHER_DIR, "12_teacher_timetable.png"))
        print("Captured: 12_teacher_timetable.png", flush=True)

        # 13. Marks Entry Sheet
        page.goto(f"{BASE_URL}/(teacher)/results", wait_until="networkidle")
        wait(2000)
        try:
            paper_item = page.locator('div[role="button"]').first
            paper_item.click(force=True)
            wait(1200)
        except Exception:
            pass
        page.screenshot(path=os.path.join(TEACHER_DIR, "13_teacher_marks_entry_sheet.png"))
        print("Captured: 13_teacher_marks_entry_sheet.png", flush=True)

        # 14. Stock Inventory
        page.goto(f"{BASE_URL}/(teacher)/stock", wait_until="networkidle")
        wait(2000)
        page.screenshot(path=os.path.join(TEACHER_DIR, "14_teacher_stock_inventory.png"))
        print("Captured: 14_teacher_stock_inventory.png", flush=True)

        # 15. Announcements / Notices
        page.goto(f"{BASE_URL}/(teacher)/announcements", wait_until="networkidle")
        wait(2000)
        page.screenshot(path=os.path.join(TEACHER_DIR, "15_teacher_announcements.png"))
        print("Captured: 15_teacher_announcements.png", flush=True)

        # 16. Grievances
        page.goto(f"{BASE_URL}/(teacher)/grievances", wait_until="networkidle")
        wait(2000)
        page.screenshot(path=os.path.join(TEACHER_DIR, "16_teacher_grievances.png"))
        print("Captured: 16_teacher_grievances.png", flush=True)

        # 17. Faculty Profile
        page.goto(f"{BASE_URL}/(teacher)/profile", wait_until="networkidle")
        wait(2000)
        page.screenshot(path=os.path.join(TEACHER_DIR, "17_teacher_profile.png"))
        print("Captured: 17_teacher_profile.png", flush=True)

        ctx.close()

        # ==========================================
        # 02_PARENT
        # ==========================================
        print("\n--- 02_PARENT ---", flush=True)
        ctx = browser.new_context(**DEVICE_CONFIG)
        page = ctx.new_page()
        page.set_default_timeout(6000)
        page.goto(BASE_URL, wait_until="networkidle")
        wait(2000)

        page.locator("text=parent: 9876500001").click(force=True)
        wait(400)
        page.get_by_text("Sign In", exact=True).or_(page.get_by_text("Sign in", exact=True)).first.click(force=True)
        wait(3000)

        # 1. Dashboard
        page.screenshot(path=os.path.join(PARENT_DIR, "01_parent_dashboard.png"))
        print("Captured: 01_parent_dashboard.png", flush=True)

        # 2. Drawer
        try:
            page.locator('[aria-label="Open Menu"]').first.click(force=True)
            wait(800)
            page.screenshot(path=os.path.join(PARENT_DIR, "02_parent_navigation_drawer.png"))
            print("Captured: 02_parent_navigation_drawer.png", flush=True)
            page.keyboard.press("Escape")
            wait(500)
        except Exception as e:
            print(f"Parent drawer: {e}", flush=True)

        # 3. Fees Ledger
        page.goto(f"{BASE_URL}/(parent)/fees", wait_until="networkidle")
        wait(2000)
        page.screenshot(path=os.path.join(PARENT_DIR, "03_parent_fees_ledger.png"))
        print("Captured: 03_parent_fees_ledger.png", flush=True)

        # 4. Direct UPI Payment Flow Modal
        try:
            pay_btn = page.locator('text=Pay Online (Direct UPI), text=Pay Now').first
            if pay_btn.count() > 0:
                pay_btn.click(force=True)
                wait(1500)
                page.screenshot(path=os.path.join(PARENT_DIR, "04_parent_upi_payment_flow.png"))
                print("Captured: 04_parent_upi_payment_flow.png", flush=True)
                page.keyboard.press("Escape")
                wait(500)
        except Exception as e:
            print(f"UPI payment modal: {e}", flush=True)

        # 5. Attendance & Leave
        page.goto(f"{BASE_URL}/(parent)/attendance", wait_until="networkidle")
        wait(2000)
        page.screenshot(path=os.path.join(PARENT_DIR, "05_parent_attendance_calendar.png"))
        print("Captured: 05_parent_attendance_calendar.png", flush=True)

        # 6. Child Profile
        page.goto(f"{BASE_URL}/(parent)/child", wait_until="networkidle")
        wait(2000)
        page.screenshot(path=os.path.join(PARENT_DIR, "06_parent_child_profile.png"))
        print("Captured: 06_parent_child_profile.png", flush=True)

        # 7. Homework
        page.goto(f"{BASE_URL}/(parent)/homework", wait_until="networkidle")
        wait(2000)
        page.screenshot(path=os.path.join(PARENT_DIR, "07_parent_homework.png"))
        print("Captured: 07_parent_homework.png", flush=True)

        # 8. Timetable
        page.goto(f"{BASE_URL}/(parent)/timetable", wait_until="networkidle")
        wait(2000)
        page.screenshot(path=os.path.join(PARENT_DIR, "08_parent_timetable.png"))
        print("Captured: 08_parent_timetable.png", flush=True)

        # 9. Results & Scorecard
        page.goto(f"{BASE_URL}/(parent)/results", wait_until="networkidle")
        wait(2000)
        page.screenshot(path=os.path.join(PARENT_DIR, "09_parent_results_list.png"))
        print("Captured: 09_parent_results_list.png", flush=True)

        try:
            view_sc = page.locator('text=View Scorecard, text=view_scorecard').first
            if view_sc.count() > 0:
                view_sc.click(force=True)
                wait(1200)
                page.screenshot(path=os.path.join(PARENT_DIR, "10_parent_report_card_scorecard.png"))
                print("Captured: 10_parent_report_card_scorecard.png", flush=True)
        except Exception as e:
            print(f"Parent scorecard expand: {e}", flush=True)

        # 11. Notices
        page.goto(f"{BASE_URL}/(parent)/notices", wait_until="networkidle")
        wait(2000)
        page.screenshot(path=os.path.join(PARENT_DIR, "11_parent_school_notices.png"))
        print("Captured: 11_parent_school_notices.png", flush=True)

        # 12. Grievances
        page.goto(f"{BASE_URL}/(parent)/grievances", wait_until="networkidle")
        wait(2000)
        page.screenshot(path=os.path.join(PARENT_DIR, "12_parent_grievances.png"))
        print("Captured: 12_parent_grievances.png", flush=True)

        # 13. Hostel & Mess
        page.goto(f"{BASE_URL}/(parent)/hostel", wait_until="networkidle")
        wait(2000)
        page.screenshot(path=os.path.join(PARENT_DIR, "13_parent_hostel.png"))
        print("Captured: 13_parent_hostel.png", flush=True)

        # 14. Parent Profile
        page.goto(f"{BASE_URL}/(parent)/profile", wait_until="networkidle")
        wait(2000)
        page.screenshot(path=os.path.join(PARENT_DIR, "14_parent_profile.png"))
        print("Captured: 14_parent_profile.png", flush=True)

        ctx.close()

        # ==========================================
        # 03_STUDENT
        # ==========================================
        print("\n--- 03_STUDENT ---", flush=True)
        ctx = browser.new_context(**DEVICE_CONFIG)
        page = ctx.new_page()
        page.set_default_timeout(6000)
        page.goto(BASE_URL, wait_until="networkidle")
        wait(2000)

        page.locator("text=student: 2024000001").click(force=True)
        wait(400)
        page.get_by_text("Sign In", exact=True).or_(page.get_by_text("Sign in", exact=True)).first.click(force=True)
        wait(3000)

        # 1. Dashboard
        page.screenshot(path=os.path.join(STUDENT_DIR, "01_student_dashboard.png"))
        print("Captured: 01_student_dashboard.png", flush=True)

        # 2. Drawer
        try:
            page.locator('[aria-label="Open Menu"]').first.click(force=True)
            wait(800)
            page.screenshot(path=os.path.join(STUDENT_DIR, "02_student_navigation_drawer.png"))
            print("Captured: 02_student_navigation_drawer.png", flush=True)
            page.keyboard.press("Escape")
            wait(500)
        except Exception as e:
            print(f"Student drawer: {e}", flush=True)

        # 3. Homework
        page.goto(f"{BASE_URL}/(student)/homework", wait_until="networkidle")
        wait(2000)
        page.screenshot(path=os.path.join(STUDENT_DIR, "03_student_homework.png"))
        print("Captured: 03_student_homework.png", flush=True)

        # 4. Timetable
        page.goto(f"{BASE_URL}/(student)/timetable", wait_until="networkidle")
        wait(2000)
        page.screenshot(path=os.path.join(STUDENT_DIR, "04_student_timetable.png"))
        print("Captured: 04_student_timetable.png", flush=True)

        # 5. Results & Scorecard
        page.goto(f"{BASE_URL}/(student)/results", wait_until="networkidle")
        wait(2000)
        page.screenshot(path=os.path.join(STUDENT_DIR, "05_student_results.png"))
        print("Captured: 05_student_results.png", flush=True)

        try:
            bd_btn = page.locator('text=View Breakdown, text=Hide Details').first
            if bd_btn.count() > 0:
                bd_btn.click(force=True)
                wait(1200)
                page.screenshot(path=os.path.join(STUDENT_DIR, "06_student_scorecard.png"))
                print("Captured: 06_student_scorecard.png", flush=True)
        except Exception as e:
            print(f"Student scorecard expand: {e}", flush=True)

        # 7. Attendance
        page.goto(f"{BASE_URL}/(student)/attendance", wait_until="networkidle")
        wait(2000)
        page.screenshot(path=os.path.join(STUDENT_DIR, "07_student_attendance.png"))
        print("Captured: 07_student_attendance.png", flush=True)

        # 8. Notices
        page.goto(f"{BASE_URL}/(student)/notices", wait_until="networkidle")
        wait(2000)
        page.screenshot(path=os.path.join(STUDENT_DIR, "08_student_notices.png"))
        print("Captured: 08_student_notices.png", flush=True)

        # 9. Hostel
        page.goto(f"{BASE_URL}/(student)/hostel", wait_until="networkidle")
        wait(2000)
        page.screenshot(path=os.path.join(STUDENT_DIR, "09_student_hostel.png"))
        print("Captured: 09_student_hostel.png", flush=True)

        # 10. Profile
        page.goto(f"{BASE_URL}/(student)/profile", wait_until="networkidle")
        wait(2000)
        page.screenshot(path=os.path.join(STUDENT_DIR, "10_student_profile.png"))
        print("Captured: 10_student_profile.png", flush=True)

        ctx.close()
        browser.close()

    print("\n[SUCCESS] Completed capture of redesigned mobile suite!", flush=True)

if __name__ == "__main__":
    main()
