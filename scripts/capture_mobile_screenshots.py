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

def capture_auth(browser):
    print("\n--- Capturing 00_auth ---")
    context = browser.new_context(**DEVICE_CONFIG)
    page = context.new_page()
    page.goto(BASE_URL, wait_until="networkidle")
    wait(2000)

    # 1. Student tab
    p1 = os.path.join(AUTH_DIR, "01_login_student_tab.png")
    page.screenshot(path=p1)
    print(f"Captured: {p1}")

    # 2. Parent tab
    page.get_by_text("parent", exact=True).click()
    wait(800)
    p2 = os.path.join(AUTH_DIR, "02_login_parent_tab.png")
    page.screenshot(path=p2)
    print(f"Captured: {p2}")

    # 3. Teacher tab
    page.get_by_text("teacher", exact=True).click()
    wait(800)
    p3 = os.path.join(AUTH_DIR, "03_login_teacher_tab.png")
    page.screenshot(path=p3)
    print(f"Captured: {p3}")

    # 4. Error state
    inputs = page.locator("input")
    if inputs.count() >= 2:
        inputs.nth(1).fill("WrongPassword999")
        page.get_by_text("Sign in", exact=True).click()
        wait(1500)
        p4 = os.path.join(AUTH_DIR, "04_login_validation_error.png")
        page.screenshot(path=p4)
        print(f"Captured: {p4}")

    context.close()

def capture_teacher(browser):
    print("\n--- Capturing 01_teacher ---")
    context = browser.new_context(**DEVICE_CONFIG)
    page = context.new_page()
    page.goto(BASE_URL, wait_until="networkidle")
    wait(2000)

    # Login as Teacher
    page.locator("text=teacher: TCH001").click()
    wait(500)
    page.get_by_text("Sign in", exact=True).click()
    wait(3500)

    # 1. Dashboard
    p1 = os.path.join(TEACHER_DIR, "01_teacher_dashboard.png")
    page.screenshot(path=p1)
    print(f"Captured: {p1}")

    # 2. Drawer
    page.locator('[aria-label="Open Menu"]').first.click()
    wait(800)
    p2 = os.path.join(TEACHER_DIR, "02_teacher_navigation_drawer.png")
    page.screenshot(path=p2)
    print(f"Captured: {p2}")

    # Close drawer by clicking Close button (cross icon)
    close_btn = page.locator('div[role="button"]').first
    try:
        # Click the top-right close icon in drawer
        page.locator('div[aria-label="Close"], div:has-text("✕")').first.click()
    except Exception:
        page.keyboard.press("Escape")
    wait(600)

    # 3. Classes list
    page.goto(f"{BASE_URL}/(teacher)/classes", wait_until="networkidle")
    wait(2000)
    p3 = os.path.join(TEACHER_DIR, "03_teacher_classes_list.png")
    page.screenshot(path=p3)
    print(f"Captured: {p3}")

    # 4. Student roster in class
    try:
        page.locator("text=10-A").first.click()
        wait(1200)
        p4 = os.path.join(TEACHER_DIR, "04_teacher_class_students_roster.png")
        page.screenshot(path=p4)
        print(f"Captured: {p4}")
    except Exception as e:
        print("Could not expand class roster:", e)

    # 5. Attendance
    page.goto(f"{BASE_URL}/(teacher)/attendance", wait_until="networkidle")
    wait(2000)
    p5 = os.path.join(TEACHER_DIR, "05_teacher_attendance_roster.png")
    page.screenshot(path=p5)
    print(f"Captured: {p5}")

    # 6. Homework manager
    page.goto(f"{BASE_URL}/(teacher)/homework", wait_until="networkidle")
    wait(2000)
    p6 = os.path.join(TEACHER_DIR, "06_teacher_homework_manager.png")
    page.screenshot(path=p6)
    print(f"Captured: {p6}")

    # 7. Homework submissions
    try:
        first_hw = page.locator('div[role="button"]:has-text("Submissions"), div:has-text("submitted")').first
        if first_hw.count() > 0:
            first_hw.click()
            wait(1200)
            p7 = os.path.join(TEACHER_DIR, "07_teacher_homework_submissions.png")
            page.screenshot(path=p7)
            print(f"Captured: {p7}")
        else:
            # Click any card
            cards = page.locator('div[style*="background-color"]')
            cards.nth(3).click()
            wait(1200)
            p7 = os.path.join(TEACHER_DIR, "07_teacher_homework_submissions.png")
            page.screenshot(path=p7)
            print(f"Captured: {p7}")
    except Exception as e:
        print("Could not expand homework submissions:", e)

    # 8. New assignment composer
    try:
        new_btn = page.locator('text=New assignment')
        if new_btn.count() > 0:
            new_btn.first.click()
            wait(1000)
            p8 = os.path.join(TEACHER_DIR, "08_teacher_homework_new_assignment_modal.png")
            page.screenshot(path=p8)
            print(f"Captured: {p8}")
    except Exception as e:
        print("Could not open homework composer:", e)

    # 9. Marks Entry / Results papers list
    page.goto(f"{BASE_URL}/(teacher)/results", wait_until="networkidle")
    wait(2000)
    p9 = os.path.join(TEACHER_DIR, "09_teacher_marks_entry_exams_list.png")
    page.screenshot(path=p9)
    print(f"Captured: {p9}")

    # 10. Marks entry sheet for a paper
    try:
        page.locator('text=Term 1, text=Periodic Test, div:has-text("Max:")').first.click()
        wait(1500)
        p10 = os.path.join(TEACHER_DIR, "10_teacher_marks_entry_sheet.png")
        page.screenshot(path=p10)
        print(f"Captured: {p10}")
    except Exception as e:
        print("Could not open marks entry sheet:", e)

    # 11. Leave overview
    page.goto(f"{BASE_URL}/(teacher)/leave", wait_until="networkidle")
    wait(2000)
    p11 = os.path.join(TEACHER_DIR, "11_teacher_leave_overview.png")
    page.screenshot(path=p11)
    print(f"Captured: {p11}")

    # 12. Leave Apply inspection
    try:
        inspect_btn = page.locator('text=Inspect Periods, text=Check Substitutions, text=Apply Leave').first
        if inspect_btn.count() > 0:
            # Scroll down to see full form
            page.evaluate("window.scrollBy(0, 300)")
            wait(800)
            p12 = os.path.join(TEACHER_DIR, "12_teacher_leave_apply_modal.png")
            page.screenshot(path=p12)
            print(f"Captured: {p12}")
    except Exception as e:
        print("Could not inspect leave:", e)

    # 13. Substitution requests
    try:
        req_tab = page.locator('text=Requests, text=Substitution Requests').first
        if req_tab.count() > 0:
            req_tab.click()
            wait(1000)
            p13 = os.path.join(TEACHER_DIR, "13_teacher_leave_substitution_requests.png")
            page.screenshot(path=p13)
            print(f"Captured: {p13}")
    except Exception as e:
        print("Could not open requests tab:", e)

    # 14. Substitution duties
    try:
        duties_tab = page.locator('text=Duties, text=My Duties').first
        if duties_tab.count() > 0:
            duties_tab.click()
            wait(1000)
            p14 = os.path.join(TEACHER_DIR, "14_teacher_leave_substitution_duties.png")
            page.screenshot(path=p14)
            print(f"Captured: {p14}")
    except Exception as e:
        print("Could not open duties tab:", e)

    # 15. Timetable
    page.goto(f"{BASE_URL}/(teacher)/timetable", wait_until="networkidle")
    wait(2000)
    p15 = os.path.join(TEACHER_DIR, "15_teacher_timetable.png")
    page.screenshot(path=p15)
    print(f"Captured: {p15}")

    # 16. Stock inventory
    page.goto(f"{BASE_URL}/(teacher)/stock", wait_until="networkidle")
    wait(2000)
    p16 = os.path.join(TEACHER_DIR, "16_teacher_stock_inventory.png")
    page.screenshot(path=p16)
    print(f"Captured: {p16}")

    # 17. Stock flag modal
    try:
        flag_btn = page.locator('text=Flag Low, text=Flag, text=Request').first
        if flag_btn.count() > 0:
            flag_btn.click()
            wait(1000)
            p17 = os.path.join(TEACHER_DIR, "17_teacher_stock_flag_modal.png")
            page.screenshot(path=p17)
            print(f"Captured: {p17}")
            # Close modal if open
            page.keyboard.press("Escape")
            wait(500)
    except Exception as e:
        print("Could not open stock modal:", e)

    # 18. Announcements / Notices
    page.goto(f"{BASE_URL}/(teacher)/announcements", wait_until="networkidle")
    wait(2000)
    p18 = os.path.join(TEACHER_DIR, "18_teacher_school_notices.png")
    page.screenshot(path=p18)
    print(f"Captured: {p18}")

    # 19. Grievances desk
    page.goto(f"{BASE_URL}/(teacher)/grievances", wait_until="networkidle")
    wait(2000)
    p19 = os.path.join(TEACHER_DIR, "19_teacher_grievances_desk.png")
    page.screenshot(path=p19)
    print(f"Captured: {p19}")

    # 20. Profile
    page.goto(f"{BASE_URL}/(teacher)/profile", wait_until="networkidle")
    wait(2000)
    p20 = os.path.join(TEACHER_DIR, "20_teacher_profile.png")
    page.screenshot(path=p20)
    print(f"Captured: {p20}")

    context.close()

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        capture_auth(browser)
        capture_teacher(browser)
        browser.close()
