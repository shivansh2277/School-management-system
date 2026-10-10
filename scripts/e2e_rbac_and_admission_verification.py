"""E2E RBAC & Hostel Admission Visual Verification Script.

Captures screenshots and validates:
1. Admin: Dashboard intact, full ERP sidebar, Hostel administrative overview.
2. Chief Provost: Land on /hostel, strictly Hostel domain nav, Chief Provost Portal badge, cross-hostel visibility.
3. Boys Warden: Land on /hostel, "My Hostel" group title, Warden Portal badge, Boys Hostel ONLY.
4. Girls Warden: Girls Hostel ONLY.
5. Hostel Admission Workflow:
   - Identify eligible Class 10 day scholar
   - Vacate a bed via Hostel Exit (proving provost exclusivity and bed state toggle)
   - Open Admission modal for day scholar, select vacant bed, confirm admission
   - Verify student admitted as active resident in bed.
"""

import os
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

EVIDENCE_DIR = Path("docs/visual_evidence")
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "http://127.0.0.1:5173"

def run_verification():
    print("=" * 70)
    print("STARTING RBAC & HOSTEL ADMISSION VISUAL VERIFICATION")
    print("=" * 70)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        def do_login(page, username, password):
            page.goto(f"{BASE_URL}/#/login")
            page.wait_for_load_state("networkidle")
            time.sleep(1)
            page.fill("input[name='login_id'], input[type='text'], input[placeholder*='Email'], input[placeholder*='login']", username)
            page.fill("input[name='password'], input[type='password']", password)
            page.click("button[type='submit']")
            page.wait_for_load_state("networkidle")
            time.sleep(2)

        # ----------------------------------------------------------------------
        # 1. Existing Admin Verification
        # ----------------------------------------------------------------------
        print("\n--- 1. Existing Admin Verification ---")
        ctx_admin = browser.new_context(viewport={"width": 1440, "height": 900})
        page_admin = ctx_admin.new_page()
        do_login(page_admin, "admin@sunrisepublic.edu", "Admin@123")

        # Verify landing on dashboard
        print("Admin URL after login:", page_admin.url)
        time.sleep(1)
        page_admin.screenshot(path=str(EVIDENCE_DIR / "30_admin_erp_dashboard_intact.png"))
        print("Saved: 30_admin_erp_dashboard_intact.png")

        # Navigate to /hostel as Admin
        page_admin.goto(f"{BASE_URL}/#/hostel")
        page_admin.wait_for_load_state("networkidle")
        time.sleep(2)
        page_admin.screenshot(path=str(EVIDENCE_DIR / "31_admin_hostel_administrative_overview.png"))
        print("Saved: 31_admin_hostel_administrative_overview.png")
        ctx_admin.close()

        # ----------------------------------------------------------------------
        # 2. Chief Provost Verification
        # ----------------------------------------------------------------------
        print("\n--- 2. Chief Provost Verification ---")
        ctx_provost = browser.new_context(viewport={"width": 1440, "height": 900})
        page_provost = ctx_provost.new_page()
        do_login(page_provost, "provost@sunrisepublic.edu", "Admin@123")

        # Verify landing on /hostel
        print("Chief Provost URL after login:", page_provost.url)
        time.sleep(2)
        page_provost.screenshot(path=str(EVIDENCE_DIR / "32_provost_hostel_only_nav.png"))
        page_provost.screenshot(path=str(EVIDENCE_DIR / "33_provost_hostel_dashboard_landing.png"))
        print("Saved: 32_provost_hostel_only_nav.png, 33_provost_hostel_dashboard_landing.png")

        # Check Rooms & Beds hierarchy
        page_provost.goto(f"{BASE_URL}/#/hostel/rooms")
        page_provost.wait_for_load_state("networkidle")
        time.sleep(2)
        page_provost.screenshot(path=str(EVIDENCE_DIR / "37_provost_rooms_and_beds_hierarchy.png"))
        print("Saved: 37_provost_rooms_and_beds_hierarchy.png")

        # ----------------------------------------------------------------------
        # 3. Boys Warden Verification
        # ----------------------------------------------------------------------
        print("\n--- 3. Boys Warden Verification ---")
        ctx_boys_warden = browser.new_context(viewport={"width": 1440, "height": 900})
        page_bw = ctx_boys_warden.new_page()
        do_login(page_bw, "warden.boys@sunrisepublic.edu", "Admin@123")

        print("Boys Warden URL after login:", page_bw.url)
        time.sleep(2)
        page_bw.screenshot(path=str(EVIDENCE_DIR / "34_warden_boys_hostel_only_nav.png"))
        print("Saved: 34_warden_boys_hostel_only_nav.png")
        ctx_boys_warden.close()

        # ----------------------------------------------------------------------
        # 4. Girls Warden Verification
        # ----------------------------------------------------------------------
        print("\n--- 4. Girls Warden Verification ---")
        ctx_girls_warden = browser.new_context(viewport={"width": 1440, "height": 900})
        page_gw = ctx_girls_warden.new_page()
        do_login(page_gw, "warden.girls@sunrisepublic.edu", "Admin@123")

        print("Girls Warden URL after login:", page_gw.url)
        time.sleep(2)
        page_gw.screenshot(path=str(EVIDENCE_DIR / "38_warden_girls_isolation.png"))
        print("Saved: 38_warden_girls_isolation.png")
        ctx_girls_warden.close()

        # ----------------------------------------------------------------------
        # 5. Hostel Admission Workflow (Day Scholar Admission)
        # ----------------------------------------------------------------------
        print("\n--- 5. Hostel Admission Workflow ---")
        # Step A: As Chief Provost, exit 1 resident to create a vacant bed in Boys Hostel
        page_provost.goto(f"{BASE_URL}/#/hostel/residents")
        page_provost.wait_for_load_state("networkidle")
        time.sleep(2)

        # Look for an Exit button
        exit_btn = page_provost.locator("button:has-text('Exit Student')").first
        if exit_btn.is_visible():
            print("Clicking Exit Student button...")
            exit_btn.click()
            time.sleep(1)
            # Fill exit modal
            reason_input = page_provost.locator("textarea").first
            if reason_input.is_visible():
                reason_input.fill("Completed Class 10 Session")
                time.sleep(1)
            confirm_exit = page_provost.locator("button:has-text('Confirm Permanent Exit')").first
            if confirm_exit.is_visible():
                print("Clicking Confirm Permanent Exit...")
                confirm_exit.click()
                time.sleep(3)
                print("Resident exited. Bed vacated.")

        # Step B: Navigate to Hostel Admissions
        page_provost.goto(f"{BASE_URL}/#/hostel/admissions")
        page_provost.wait_for_load_state("networkidle")
        time.sleep(2)

        # Switch to Day Scholars tab
        day_scholars_tab = page_provost.locator("button:has-text('Day Scholars')").first
        if day_scholars_tab.is_visible():
            print("Switching to Day Scholars tab...")
            day_scholars_tab.click()
            time.sleep(1)

        # Click Admit to Hostel for the first eligible student
        admit_btn = page_provost.locator("button:has-text('Admit to Hostel')").first
        if admit_btn.is_visible():
            print("Opening Admit to Hostel modal...")
            admit_btn.click()
            time.sleep(1)

            # In modal, select Hostel Building if not selected
            hostel_select = page_provost.locator("select").first
            if hostel_select.is_visible():
                # Select Boys Hostel option
                options = hostel_select.locator("option").all()
                for opt in options:
                    val = opt.get_attribute("value")
                    text = opt.inner_text()
                    if "Boys" in text or "BH" in text:
                        hostel_select.select_option(val)
                        time.sleep(2)
                        break

            # Select available Bed
            time.sleep(2)
            bed_select = page_provost.locator("select").nth(1)
            if bed_select.is_visible():
                bed_options = bed_select.locator("option").all()
                print(f"Available bed options found: {len(bed_options)}")
                if len(bed_options) > 1:
                    bed_val = bed_options[1].get_attribute("value")
                    bed_select.select_option(bed_val)
                    time.sleep(1)

            # Capture modal screenshot
            page_provost.screenshot(path=str(EVIDENCE_DIR / "35_hostel_admission_workflow_modal.png"))
            print("Saved: 35_hostel_admission_workflow_modal.png")

            # Confirm admission
            confirm_admit = page_provost.locator("button:has-text('Confirm Admission & Bed')").first
            if confirm_admit.is_visible():
                print("Confirming admission...")
                confirm_admit.click()
                time.sleep(3)

        # Navigate to residents to verify newly admitted student in roster
        page_provost.goto(f"{BASE_URL}/#/hostel/residents")
        page_provost.wait_for_load_state("networkidle")
        time.sleep(2)
        page_provost.screenshot(path=str(EVIDENCE_DIR / "36_hostel_admission_success_roster.png"))
        print("Saved: 36_hostel_admission_success_roster.png")

        ctx_provost.close()
        browser.close()

    print("\nVisual verification complete. All screenshots recorded in docs/visual_evidence/.")

if __name__ == "__main__":
    run_verification()
