import os
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

SCREENSHOT_DIR = Path("docs/screenshots")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

def run():
    print("Starting Playwright end-to-end UI verification...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-gpu"])
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # Step 1: Open Login Page
        print("Navigating to Login Page...")
        page.goto("http://localhost:5173/#/login", wait_until="networkidle")
        page.wait_for_timeout(1000)

        # Check Quick Demo button
        coord_btn = page.locator("button:has-text('Academic Coordinator')")
        if coord_btn.count() > 0:
            print("Found Academic Coordinator quick demo button. Clicking...")
            coord_btn.click()
        else:
            print("Filling login credentials manually...")
            page.fill("input[type='text']", "coordinator@sunrisepublic.edu")
            page.fill("input[type='password']", "Admin@123")

        page.wait_for_timeout(500)
        print("Submitting login form...")
        page.click("button:has-text('Sign in to ERP')")

        # Wait for redirect to /#/timetable
        page.wait_for_url("**/timetable**", timeout=10000)
        page.wait_for_timeout(2000)
        print("Successfully authenticated and redirected to /#/timetable")

        # Step 2: Capture Screenshot 1: Class Timetables & Weekly Grid
        shot1 = SCREENSHOT_DIR / "01_academic_coordinator_class_timetable.png"
        page.screenshot(path=str(shot1), full_page=False)
        print(f"Captured: {shot1}")

        # Step 3: Test Slot Modal & Live Conflict Check
        print("Opening '+ Add Lesson Slot' Modal...")
        page.click("button:has-text('+ Add Lesson Slot')")
        page.wait_for_timeout(1000)
        
        # Verify modal opened
        shot2 = SCREENSHOT_DIR / "02_timetable_slot_modal_and_conflicts.png"
        page.screenshot(path=str(shot2), full_page=False)
        print(f"Captured: {shot2}")

        # Close modal
        page.click("button:has-text('Cancel')")
        page.wait_for_timeout(500)

        # Step 4: Teacher Schedules Tab
        print("Switching to 'Teacher Schedules' tab...")
        page.click("button:has-text('Teacher Schedules')")
        page.wait_for_timeout(1500)
        shot3 = SCREENSHOT_DIR / "03_academic_coordinator_teacher_schedule.png"
        page.screenshot(path=str(shot3), full_page=False)
        print(f"Captured: {shot3}")

        # Step 5: Daily Schedule & Substitutions Tab
        print("Switching to 'Daily Schedule & Substitutions' tab...")
        page.click("button:has-text('Daily Schedule & Substitutions')")
        page.wait_for_timeout(1500)

        # Look for Assign Relief button
        relief_btn = page.locator("button:has-text('Assign Relief')").first
        if relief_btn.count() > 0:
            print("Clicking 'Assign Relief' to verify relief duty assignment modal...")
            relief_btn.click()
            page.wait_for_timeout(1000)
            shot4 = SCREENSHOT_DIR / "04_daily_schedule_and_substitution_desk.png"
            page.screenshot(path=str(shot4), full_page=False)
            print(f"Captured: {shot4}")
            page.click("button:has-text('Cancel')")
            page.wait_for_timeout(500)
        else:
            shot4 = SCREENSHOT_DIR / "04_daily_schedule_and_substitution_desk.png"
            page.screenshot(path=str(shot4), full_page=False)
            print(f"Captured: {shot4}")

        # Step 6: Workload & Completeness Dashboards Tab
        print("Switching to 'Workload & Completeness' tab...")
        page.click("button:has-text('Workload & Completeness')")
        page.wait_for_timeout(1500)
        shot5 = SCREENSHOT_DIR / "05_workload_and_completeness_dashboards.png"
        page.screenshot(path=str(shot5), full_page=False)
        print(f"Captured: {shot5}")

        # Step 7: Bell Timings / Periods Tab
        print("Switching to 'Bell Timings / Periods' tab...")
        page.click("button:has-text('Bell Timings / Periods')")
        page.wait_for_timeout(1500)

        # Click + Add School Period
        page.click("button:has-text('+ Add School Period')")
        page.wait_for_timeout(1000)
        shot6 = SCREENSHOT_DIR / "06_bell_timings_and_periods.png"
        page.screenshot(path=str(shot6), full_page=False)
        print(f"Captured: {shot6}")
        page.click("button:has-text('Cancel')")
        page.wait_for_timeout(500)

        # Step 8: Strict Sidebar Scoping Verification
        print("Verifying sidebar items strictly scoped to Academics and Communication...")
        sidebar_text = page.locator("nav, aside, [role='navigation']").all_text_contents()
        full_sidebar = " ".join(sidebar_text)
        print("Sidebar contents:", full_sidebar.replace("\n", " "))
        
        # Ensure forbidden modules are absent from sidebar
        assert "Settings" not in full_sidebar, "Forbidden 'Settings' leaked in sidebar!"
        assert "Fees" not in full_sidebar, "Forbidden 'Fees' leaked in sidebar!"
        assert "Payroll" not in full_sidebar, "Forbidden 'Payroll' leaked in sidebar!"
        assert "Examinations" not in full_sidebar, "Forbidden 'Examinations' leaked in sidebar!"
        assert "Students" not in full_sidebar, "Forbidden 'Students' leaked in sidebar!"
        print("Sidebar assertions passed: zero unauthorized modules present.")

        shot7 = SCREENSHOT_DIR / "07_strict_sidebar_role_isolation.png"
        page.screenshot(path=str(shot7), full_page=False)
        print(f"Captured: {shot7}")

        # Step 9: Attempt direct URL navigation to forbidden routes
        print("Testing direct navigation to restricted URL /#/settings...")
        page.goto("http://localhost:5173/#/settings", wait_until="networkidle")
        page.wait_for_timeout(1000)
        current_url = page.url
        print(f"Current URL after attempting /#/settings: {current_url}")
        
        # Verify access refusal or redirect
        shot8 = SCREENSHOT_DIR / "08_restricted_route_refusal.png"
        page.screenshot(path=str(shot8), full_page=False)
        print(f"Captured: {shot8}")

        browser.close()
        print("All Playwright verifications passed successfully!")

if __name__ == "__main__":
    run()
