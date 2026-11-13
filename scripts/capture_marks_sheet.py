import sys
from playwright.sync_api import sync_playwright

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 390, "height": 844},
            device_scale_factor=2,
            is_mobile=True,
            has_touch=True,
        )
        page = context.new_page()
        page.goto("http://localhost:8081", wait_until="networkidle")
        page.wait_for_timeout(1500)
        
        # Teacher login
        page.locator("text=teacher: TCH001").click()
        page.wait_for_timeout(500)
        page.get_by_text("Sign in", exact=True).click()
        page.wait_for_timeout(2500)
        
        # Open drawer and click Results
        page.locator('[aria-label="Open Menu"]').first.click()
        page.wait_for_timeout(800)
        page.get_by_text("Marks Entry & Results", exact=True).last.click()
        page.wait_for_timeout(2000)
        
        # Click on Mathematics - 10-A
        page.locator('text=Mathematics - 10-A').first.click(force=True)
        page.wait_for_timeout(2000)
        
        print("Marks entry sheet preview:\n", page.inner_text("body")[:300])
        page.screenshot(path="school-management-system/docs/screenshots/mobile_app_redesign/01_teacher/10_teacher_marks_entry_sheet.png")
        print("Saved 10_teacher_marks_entry_sheet.png!")
        
        browser.close()

if __name__ == "__main__":
    test()
