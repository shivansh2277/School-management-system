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

def capture_teacher_subviews(browser):
    print("--- Capturing Teacher Subviews ---")
    context = browser.new_context(**DEVICE_CONFIG)
    page = context.new_page()
    page.goto(BASE_URL, wait_until="networkidle")
    wait(1500)
    page.locator("text=teacher: TCH001").click(force=True)
    wait(500)
    page.get_by_text("Sign in", exact=True).click(force=True)
    wait(2500)

    # 1. Homework New Assignment
    page.locator('[aria-label="Open Menu"]').first.click(force=True)
    wait(800)
    page.get_by_text("Homework Manager", exact=True).last.click(force=True)
    wait(2000)
    page.locator('text=New assignment').first.click(force=True)
    wait(1000)
    p_hw = os.path.join(TEACHER_DIR, "08_teacher_homework_new_assignment_modal.png")
    page.screenshot(path=p_hw)
    print(f"Captured: {p_hw}")

    # 2. Stock Flag Modal
    page.locator('[aria-label="Open Menu"]').first.click(force=True)
    wait(800)
    page.get_by_text("Classroom Supplies / Stock", exact=True).last.click(force=True)
    wait(2000)
    try:
        page.locator('text=Flag, text=Request').first.click(force=True)
        wait(1000)
        p_st = os.path.join(TEACHER_DIR, "17_teacher_stock_flag_modal.png")
        page.screenshot(path=p_st)
        print(f"Captured: {p_st}")
    except Exception as e:
        print("Stock flag error:", e)

    context.close()

def capture_parent_subviews(browser):
    print("--- Capturing Parent Subviews ---")
    context = browser.new_context(**DEVICE_CONFIG)
    page = context.new_page()
    page.goto(BASE_URL, wait_until="networkidle")
    wait(1500)
    page.locator("text=parent: 9876500001").click(force=True)
    wait(500)
    page.get_by_text("Sign in", exact=True).click(force=True)
    wait(2500)

    # 1. Pay with UPI Modal
    page.locator('[aria-label="Open Menu"]').first.click(force=True)
    wait(800)
    page.get_by_text("Fees", exact=True).last.click(force=True)
    wait(2000)
    try:
        page.locator('text=/Pay with UPI/').first.click(force=True)
        wait(1200)
        p_pay = os.path.join(PARENT_DIR, "06_parent_fee_pay_now_modal.png")
        page.screenshot(path=p_pay)
        print(f"Captured: {p_pay}")
    except Exception as e:
        print("Pay with UPI error:", e)

    # 2. Apply Leave Modal
    page.locator('[aria-label="Open Menu"]').first.click(force=True)
    wait(800)
    page.get_by_text("Attendance", exact=True).last.click(force=True)
    wait(2000)
    try:
        page.locator('text=/Apply for Student Leave/').first.click(force=True)
        wait(1200)
        p_leave = os.path.join(PARENT_DIR, "08_parent_apply_leave_modal.png")
        page.screenshot(path=p_leave)
        print(f"Captured: {p_leave}")
    except Exception as e:
        print("Apply Leave error:", e)

    # 3. View Scorecard Detail
    page.locator('[aria-label="Open Menu"]').first.click(force=True)
    wait(800)
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

    context.close()

def capture_student_subviews(browser):
    print("--- Capturing Student Subviews ---")
    context = browser.new_context(**DEVICE_CONFIG)
    page = context.new_page()
    page.goto(BASE_URL, wait_until="networkidle")
    wait(1500)
    page.locator("text=student: 2024000001").click(force=True)
    wait(500)
    page.get_by_text("Sign in", exact=True).click(force=True)
    wait(2500)

    # 1. Homework All Tab
    page.locator('[aria-label="Open Menu"]').first.click(force=True)
    wait(800)
    page.get_by_text("Homework", exact=True).last.click(force=True)
    wait(2000)
    try:
        page.locator('text=All').first.click(force=True)
        wait(1000)
        p_all = os.path.join(STUDENT_DIR, "05_student_homework_all_tab.png")
        page.screenshot(path=p_all)
        print(f"Captured: {p_all}")
    except Exception as e:
        print("Student homework all error:", e)

    # 2. View Breakdown Report Card
    page.locator('[aria-label="Open Menu"]').first.click(force=True)
    wait(800)
    page.get_by_text("Exam Results & Scorecard", exact=True).last.click(force=True)
    wait(2000)
    try:
        page.locator('text=/View Breakdown/').first.click(force=True)
        wait(1200)
        p_rep = os.path.join(STUDENT_DIR, "07_student_report_card_detail.png")
        page.screenshot(path=p_rep)
        print(f"Captured: {p_rep}")
    except Exception as e:
        print("Student breakdown error:", e)

    context.close()

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        capture_teacher_subviews(browser)
        capture_parent_subviews(browser)
        capture_student_subviews(browser)
        browser.close()
    print("Done subviews!")
