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

DEVICE_CONFIG = {
    "viewport": {"width": 390, "height": 844},
    "device_scale_factor": 2,
    "is_mobile": True,
    "has_touch": True,
}

BASE_URL = "http://localhost:8081"

def wait(ms=1500):
    time.sleep(ms / 1000.0)

def capture_remaining():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        # 1. Teacher Stock Flag
        context = browser.new_context(**DEVICE_CONFIG)
        page = context.new_page()
        page.goto(BASE_URL, wait_until="networkidle")
        wait(1500)
        page.locator("text=teacher: TCH001").click(force=True)
        wait(500)
        page.get_by_text("Sign in", exact=True).click(force=True)
        wait(2500)
        page.locator('[aria-label="Open Menu"]').first.click(force=True)
        wait(800)
        page.get_by_text("Classroom Supplies / Stock", exact=True).last.click(force=True)
        wait(2000)
        try:
            # Click Flag on first stock item
            page.locator('text=Flag').first.click(force=True)
            wait(1200)
            p_st = os.path.join(TEACHER_DIR, "17_teacher_stock_flag_modal.png")
            page.screenshot(path=p_st)
            print(f"Captured: {p_st}")
        except Exception as e:
            print("Stock flag error:", e)
        context.close()

        # 2. Parent Leave Modal & Scorecard
        context = browser.new_context(**DEVICE_CONFIG)
        page = context.new_page()
        page.goto(BASE_URL, wait_until="networkidle")
        wait(1500)
        page.locator("text=parent: 9876500001").click(force=True)
        wait(500)
        page.get_by_text("Sign in", exact=True).click(force=True)
        wait(2500)

        # Parent Attendance -> Apply Leave
        page.locator('[aria-label="Open Menu"]').first.click(force=True)
        wait(800)
        # Look for Attendance in drawer sections
        page.locator('div[role="button"]:has-text("Attendance")').last.click(force=True)
        wait(2000)
        try:
            page.locator('text=/Apply for Student Leave/').first.click(force=True)
            wait(1200)
            p_leave = os.path.join(PARENT_DIR, "08_parent_apply_leave_modal.png")
            page.screenshot(path=p_leave)
            print(f"Captured: {p_leave}")
        except Exception as e:
            print("Parent leave modal error:", e)

        # Parent Results -> View Scorecard
        page.locator('[aria-label="Open Menu"]').first.click(force=True)
        wait(800)
        page.locator('div[role="button"]:has-text("Results")').last.click(force=True)
        wait(2000)
        try:
            page.locator('text=/View Scorecard/').first.click(force=True)
            wait(1500)
            p_card = os.path.join(PARENT_DIR, "10_parent_report_card_breakdown.png")
            page.screenshot(path=p_card)
            print(f"Captured: {p_card}")
        except Exception as e:
            print("Parent scorecard error:", e)
        context.close()

        # 3. Student Homework All & Scorecard
        context = browser.new_context(**DEVICE_CONFIG)
        page = context.new_page()
        page.goto(BASE_URL, wait_until="networkidle")
        wait(1500)
        page.locator("text=student: 2024000001").click(force=True)
        wait(500)
        page.get_by_text("Sign in", exact=True).click(force=True)
        wait(2500)

        # Student Homework
        page.locator('[aria-label="Open Menu"]').first.click(force=True)
        wait(800)
        page.locator('div[role="button"]:has-text("Homework")').last.click(force=True)
        wait(2000)
        try:
            page.locator('text=All').first.click(force=True)
            wait(1200)
            p_all = os.path.join(STUDENT_DIR, "05_student_homework_all_tab.png")
            page.screenshot(path=p_all)
            print(f"Captured: {p_all}")
        except Exception as e:
            print("Student homework all error:", e)

        # Student Results
        page.locator('[aria-label="Open Menu"]').first.click(force=True)
        wait(800)
        page.locator('div[role="button"]:has-text("Exam Results & Scorecard")').last.click(force=True)
        wait(2000)
        try:
            page.locator('text=/View Breakdown/').first.click(force=True)
            wait(1500)
            p_rep = os.path.join(STUDENT_DIR, "07_student_report_card_detail.png")
            page.screenshot(path=p_rep)
            print(f"Captured: {p_rep}")
        except Exception as e:
            print("Student report card error:", e)
        context.close()

        browser.close()

if __name__ == "__main__":
    capture_remaining()
