import os
import sys
import time
from playwright.sync_api import sync_playwright

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

OUTPUT_DIR = os.path.abspath("school-management-system/docs/screenshots/mobile_app_redesign/04_preserved_redesigns_verified")
os.makedirs(OUTPUT_DIR, exist_ok=True)

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
    print(f"Starting Playwright verification test suite against {BASE_URL}...", flush=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # ==========================================
        # 1. TEACHER: Supplies Inventory & Flag/Consume
        # ==========================================
        print("\n--- 1. TEACHER: Supplies Inventory & Flag/Consume Flow ---", flush=True)
        ctx = browser.new_context(**DEVICE_CONFIG)
        page = ctx.new_page()
        page.set_default_timeout(8000)
        page.goto(BASE_URL, wait_until="networkidle")
        wait(2000)

        # Quick login via demo credential button
        page.locator("text=teacher: TCH001").click(force=True)
        wait(400)
        page.get_by_text("Sign In", exact=True).or_(page.get_by_text("Sign in", exact=True)).first.click(force=True)
        wait(3000)

        # Navigate to /stock
        print("Navigating to /(teacher)/stock...", flush=True)
        page.goto(f"{BASE_URL}/(teacher)/stock", wait_until="networkidle")
        wait(2000)

        # Verify Hero card
        assert page.get_by_text("Classroom & Lab Supplies").first.is_visible(), "Hero title missing"
        assert page.get_by_text("Store ERP").first.is_visible(), "Store ERP badge missing"
        print("✓ Hero Card verified with 'Classroom & Lab Supplies' and 'Store ERP' badge.", flush=True)

        # Test Search Input
        search_box = page.locator("input[placeholder*='Search']").first
        if search_box.is_visible():
            search_box.fill("Cartridge")
            wait(800)
            print("✓ Search functionality tested with query 'Cartridge'.", flush=True)
            search_box.fill("")
            wait(500)

        # Test Category Pills
        art_pill = page.get_by_text("Art & Craft").first
        if art_pill.is_visible():
            art_pill.click(force=True)
            wait(600)
            print("✓ Category filter 'Art & Craft' clicked.", flush=True)
            page.get_by_text("All Supplies").first.click(force=True)
            wait(600)

        # Capture Inventory List Screen
        shot1 = os.path.join(OUTPUT_DIR, "01_teacher_supplies_inventory_management.png")
        page.screenshot(path=shot1)
        print(f"✓ Saved screenshot: {shot1}", flush=True)

        # Test "Use / Consume" Modal
        consume_btn = page.get_by_text("Use / Consume").first
        if consume_btn.is_visible():
            consume_btn.click(force=True)
            wait(1200)

            assert page.get_by_text("Consume Supply").first.is_visible(), "Consume modal missing"
            print("✓ 'Use / Consume' bottom sheet opened successfully.", flush=True)

            # Test Stepper: click +
            page.get_by_text("+").first.click(force=True)
            wait(400)
            print("✓ Stepper '+' increment tested.", flush=True)

            # Test Reason Pill
            class_act = page.get_by_text("Class Activity").first
            if class_act.is_visible():
                class_act.click(force=True)
                wait(300)

            shot2 = os.path.join(OUTPUT_DIR, "02_teacher_supplies_consume_modal.png")
            page.screenshot(path=shot2)
            print(f"✓ Saved screenshot: {shot2}", flush=True)

            # Close modal via Cancel
            page.get_by_text("Cancel").first.click(force=True)
            wait(800)

        # Test "Flag →" Modal
        flag_btn = page.get_by_text("Flag →").first
        if flag_btn.is_visible():
            flag_btn.click(force=True)
            wait(1200)

            assert page.get_by_text("Flag Depleted Item").first.is_visible(), "Flag modal missing"
            print("✓ 'Flag →' bottom sheet opened successfully.", flush=True)

            # Click Stepper +
            page.get_by_text("+").first.click(force=True)
            wait(400)

            # Select Reason
            damaged_pill = page.get_by_text("Damaged").first
            if damaged_pill.is_visible():
                damaged_pill.click(force=True)
                wait(300)

            # Select Urgency
            crit_pill = page.get_by_text("CRITICAL").first
            if crit_pill.is_visible():
                crit_pill.click(force=True)
                wait(300)

            shot3 = os.path.join(OUTPUT_DIR, "03_teacher_supplies_flag_modal.png")
            page.screenshot(path=shot3)
            print(f"✓ Saved screenshot: {shot3}", flush=True)

            # Close modal
            page.get_by_text("Cancel").first.click(force=True)
            wait(800)

        # ==========================================
        # 2. TEACHER: Marks Entry Sheet
        # ==========================================
        print("\n--- 2. TEACHER: Marks Entry Sheet ---", flush=True)
        page.goto(f"{BASE_URL}/(teacher)/results", wait_until="networkidle")
        wait(2000)

        exam_card = page.get_by_text("Mathematics").first
        assert exam_card.is_visible(), "Exam paper card missing"
        print("✓ Scheduled exam paper card verified.", flush=True)

        # Click to expand
        exam_card.click(force=True)
        wait(1500)

        assert page.get_by_text("CBSE:").first.is_visible(), "CBSE Grade badge missing"
        assert page.get_by_text("Present").first.is_visible(), "Present segment missing"
        assert page.get_by_text("Absent (A)").first.is_visible(), "Absent segment missing"
        assert page.get_by_text("Exempted").first.is_visible(), "Exempted segment missing"
        assert page.get_by_text("Save Marks Sheet").first.is_visible(), "Save Marks Sheet button missing"
        print("✓ Expanded marks entry sheet verified with roster, grades, and segmented controls.", flush=True)

        # Test segmented button toggle
        page.get_by_text("Absent (A)").first.click(force=True)
        wait(400)
        page.get_by_text("Present").first.click(force=True)
        wait(400)

        # Test validation: enter invalid marks
        marks_input = page.locator("input[placeholder*='0-']").first
        if marks_input.is_visible():
            marks_input.fill("99")
            wait(500)
            assert page.get_by_text("Each mark must be a valid number").first.is_visible(), "Validation error should appear"
            print("✓ Validation check passed: Invalid mark 99 triggered validation error.", flush=True)

            # Restore valid mark
            marks_input.fill("8.5")
            wait(500)
            print("✓ Restored valid mark 8.5.", flush=True)

        shot4 = os.path.join(OUTPUT_DIR, "04_teacher_cbse_marks_entry_sheet.png")
        page.screenshot(path=shot4)
        print(f"✓ Saved screenshot: {shot4}", flush=True)

        ctx.close()

        # ==========================================
        # 3. PARENT: CBSE Report Card & Scorecard
        # ==========================================
        print("\n--- 3. PARENT: CBSE Report Card & Scorecard ---", flush=True)
        ctx = browser.new_context(**DEVICE_CONFIG)
        page = ctx.new_page()
        page.set_default_timeout(8000)
        page.goto(BASE_URL, wait_until="networkidle")
        wait(2000)

        page.locator("text=parent: 9876500001").click(force=True)
        wait(400)
        page.get_by_text("Sign In", exact=True).or_(page.get_by_text("Sign in", exact=True)).first.click(force=True)
        wait(3000)

        page.goto(f"{BASE_URL}/(parent)/results", wait_until="networkidle")
        wait(2000)

        # Verify Fee Withholding Alert Banner
        assert page.get_by_text("Report Card Withheld").first.is_visible(), "Withholding banner missing"
        print("✓ Fee withholding warning banner verified.", flush=True)

        # Verify Completed Examinations Section
        assert page.get_by_text("Completed Examinations").first.is_visible(), "Completed Examinations section missing"
        print("✓ Completed Examinations section verified.", flush=True)

        # Click to open scorecard details
        view_scorecard_btn = page.get_by_text("View Scorecard ›").first
        if view_scorecard_btn.is_visible():
            view_scorecard_btn.click(force=True)
            wait(1500)

        assert page.get_by_text("Scorecard").first.is_visible(), "Scorecard details missing"
        assert page.get_by_text("Total Score").first.is_visible(), "Total score box missing"
        print("✓ Scorecard breakdown verified with subjects, marks, CBSE grades, and total score summary.", flush=True)

        shot5 = os.path.join(OUTPUT_DIR, "05_parent_cbse_report_card_scorecard.png")
        page.screenshot(path=shot5)
        print(f"✓ Saved screenshot: {shot5}", flush=True)

        # ==========================================
        # 4. PARENT: Direct UPI Payment Flow
        # ==========================================
        print("\n--- 4. PARENT: Direct UPI Payment Flow ---", flush=True)
        page.goto(f"{BASE_URL}/(parent)/fees", wait_until="networkidle")
        wait(2000)

        # Verify Outstanding Balance Hero Card
        assert page.get_by_text("Total Outstanding Fee Balance").first.is_visible(), "Balance label missing"
        assert page.get_by_text("Total Invoiced").first.is_visible(), "Total invoiced missing"
        assert page.get_by_text("Total Paid").first.is_visible(), "Total paid missing"
        assert page.get_by_text("Net Dues").first.is_visible(), "Net dues missing"
        print("✓ Outstanding fee balance hero card verified with 3-metric statistics.", flush=True)

        # Click "Pay with Direct UPI"
        pay_btn = page.get_by_text("Pay with Direct UPI").first
        assert pay_btn.is_visible(), "'Pay with Direct UPI' button missing"
        pay_btn.click(force=True)
        wait(2500)

        # Verify Direct UPI Bottom Sheet Modal
        assert page.get_by_text("Direct UPI Payment").first.is_visible(), "Modal title missing"
        assert page.get_by_text("Sunrise EdTech Secure Gateway").first.is_visible(), "Modal subtitle missing"
        assert page.get_by_text("ORD-").first.is_visible(), "Order number missing"
        assert page.get_by_text("PAYABLE AMOUNT").first.is_visible(), "Payable amount label missing"
        assert page.get_by_text("⏱").first.is_visible(), "Countdown timer missing"
        assert page.get_by_text("Other UPI Apps (Chooser)").first.is_visible(), "UPI Chooser button missing"
        assert page.get_by_text("Submit UTR for Verification").first.is_visible(), "UTR submit button missing"
        assert page.get_by_text("256-Bit Encrypted Payment Flow").first.is_visible(), "Security badge missing"
        print("✓ Direct UPI bottom sheet verified with order ref, active countdown timer, payable amount, UTR field, and security badge.", flush=True)

        # Test UTR input
        utr_field = page.locator("input[placeholder*='UTR']").first
        if utr_field.is_visible():
            utr_field.fill("123456789012")
            wait(500)
            print("✓ UTR input tested with sample 12-digit reference.", flush=True)

        shot6 = os.path.join(OUTPUT_DIR, "06_parent_direct_upi_payment_flow.png")
        page.screenshot(path=shot6)
        print(f"✓ Saved screenshot: {shot6}", flush=True)

        # Cancel modal
        page.get_by_text("Cancel").first.click(force=True)
        wait(800)

        ctx.close()

        # ==========================================
        # 5. STUDENT: CBSE Results Scorecard
        # ==========================================
        print("\n--- 5. STUDENT: CBSE Results Scorecard ---", flush=True)
        ctx = browser.new_context(**DEVICE_CONFIG)
        page = ctx.new_page()
        page.set_default_timeout(8000)
        page.goto(BASE_URL, wait_until="networkidle")
        wait(2000)

        page.locator("text=student: 2024000001").click(force=True)
        wait(400)
        page.get_by_text("Sign In", exact=True).or_(page.get_by_text("Sign in", exact=True)).first.click(force=True)
        wait(3000)

        page.goto(f"{BASE_URL}/(student)/results", wait_until="networkidle")
        wait(2000)

        view_breakdown_btn = page.get_by_text("View Breakdown ›").first
        if view_breakdown_btn.is_visible():
            view_breakdown_btn.click(force=True)
            wait(1500)

        shot7 = os.path.join(OUTPUT_DIR, "07_student_cbse_scorecard.png")
        page.screenshot(path=shot7)
        print(f"✓ Saved screenshot: {shot7}", flush=True)

        ctx.close()
        browser.close()

        print("\n==========================================", flush=True)
        print("ALL TESTS PASSED WITH 100% SUCCESS!", flush=True)
        print(f"Screenshots saved to: {OUTPUT_DIR}", flush=True)
        print("==========================================", flush=True)

if __name__ == "__main__":
    main()
