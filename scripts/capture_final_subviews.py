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
TEACHER_DIR = os.path.join(OUTPUT_DIR, "01_teacher")
PARENT_DIR = os.path.join(OUTPUT_DIR, "02_parent")
STUDENT_DIR = os.path.join(OUTPUT_DIR, "03_student")

DEVICE_CONFIG = {
    "viewport": {"width": 390, "height": 844},
    "device_scale_factor": 2,
    "is_mobile": True,
    "has_touch": True,
}

BASE_URL = "http://localhost:8081"

def wait(ms=1500):
    time.sleep(ms / 1000.0)

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # 1. Teacher Stock Flag Modal
        print("Capturing Teacher Flag Modal...")
        c_tch = browser.new_context(**DEVICE_CONFIG)
        page = c_tch.new_page()
        page.goto(BASE_URL, wait_until="networkidle")
        wait(1500)
        page.locator("text=teacher: TCH001").click(force=True)
        wait(400)
        page.get_by_text("Sign in", exact=True).click(force=True)
        wait(2500)
        page.locator('[aria-label="Open Menu"]').first.click(force=True)
        wait(600)
        page.get_by_text("Classroom Supplies / Stock", exact=True).last.click(force=True)
        wait(2000)
        try:
            page.locator('text=/Flag/').first.click(force=True)
            wait(1200)
            p_flag = os.path.join(TEACHER_DIR, "17_teacher_stock_flag_modal.png")
            page.screenshot(path=p_flag)
            print(f"Captured: {p_flag}")
        except Exception as e:
            print("Flag error:", e)
        c_tch.close()

        # 2. Parent Leave Modal & Scorecard
        print("Capturing Parent Subviews...")
        c_par = browser.new_context(**DEVICE_CONFIG)
        page = c_par.new_page()
        page.goto(BASE_URL, wait_until="networkidle")
        wait(1500)
        page.locator("text=parent: 9876500001").click(force=True)
        wait(400)
        page.get_by_text("Sign in", exact=True).click(force=True)
        wait(2500)

        # Open drawer -> Attendance
        page.locator('[aria-label="Open Menu"]').first.click(force=True)
        wait(600)
        page.get_by_text("Attendance", exact=True).last.click(force=True)
        wait(2000)
        try:
            page.locator('text=/Apply for Student Leave/').first.click(force=True)
            wait(1200)
            p_leave = os.path.join(PARENT_DIR, "08_parent_apply_leave_modal.png")
            page.screenshot(path=p_leave)
            print(f"Captured: {p_leave}")
        except Exception as e:
            print("Leave modal error:", e)

        # Open drawer -> Results
        page.locator('[aria-label="Open Menu"]').first.click(force=True)
        wait(600)
        page.get_by_text("Results", exact=True).last.click(force=True)
        wait(2000)
        try:
            page.locator('text=/View Scorecard/').first.click(force=True)
            wait(1200)
            p_card = os.path.join(PARENT_DIR, "10_parent_report_card_breakdown.png")
            page.screenshot(path=p_card)
            print(f"Captured: {p_card}")
        except Exception as e:
            print("Scorecard error:", e)
        c_par.close()

        # 3. Student Homework All Tab & Scorecard
        print("Capturing Student Subviews...")
        c_stu = browser.new_context(**DEVICE_CONFIG)
        page = c_stu.new_page()
        page.goto(BASE_URL, wait_until="networkidle")
        wait(1500)
        page.locator("text=student: 2024000001").click(force=True)
        wait(400)
        page.get_by_text("Sign in", exact=True).click(force=True)
        wait(2500)

        # Open drawer -> Homework
        page.locator('[aria-label="Open Menu"]').first.click(force=True)
        wait(600)
        page.get_by_text("Homework", exact=True).last.click(force=True)
        wait(2000)
        try:
            page.locator('text=All').first.click(force=True)
            wait(1200)
            p_all = os.path.join(STUDENT_DIR, "05_student_homework_all_tab.png")
            page.screenshot(path=p_all)
            print(f"Captured: {p_all}")
        except Exception as e:
            print("Student homework all error:", e)

        # Open drawer -> Results
        page.locator('[aria-label="Open Menu"]').first.click(force=True)
        wait(600)
        page.get_by_text("Exam Results & Scorecard", exact=True).last.click(force=True)
        wait(2000)
        try:
            page.locator('text=/View Breakdown/').first.click(force=True)
            wait(1200)
            p_rep = os.path.join(STUDENT_DIR, "07_student_report_card_detail.png")
            page.screenshot(path=p_rep)
            print(f"Captured: {p_rep}")
        except Exception as e:
            print("Student scorecard error:", e)
        c_stu.close()

        browser.close()
    print("Done all remaining captures!")

if __name__ == "__main__":
    main()
