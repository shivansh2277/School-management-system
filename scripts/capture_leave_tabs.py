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
        
        # Open drawer and click Leave
        page.locator('[aria-label="Open Menu"]').first.click()
        page.wait_for_timeout(800)
        page.get_by_text("Leave & Substitution Duties", exact=True).last.click()
        page.wait_for_timeout(2000)
        
        print("Leave page text preview:\n", page.inner_text("body")[:300])
        
        # Click Requests
        print("Clicking Requests tab...")
        page.locator('text=/Requests/').first.click(force=True)
        page.wait_for_timeout(1000)
        page.screenshot(path="school-management-system/docs/screenshots/mobile_app_redesign/01_teacher/12_teacher_leave_requests_tab.png")
        print("Saved 12_teacher_leave_requests_tab.png")
        
        # Click My Leaves
        print("Clicking My Leaves tab...")
        page.locator('text=/My Leaves/').first.click(force=True)
        page.wait_for_timeout(1000)
        page.screenshot(path="school-management-system/docs/screenshots/mobile_app_redesign/01_teacher/13_teacher_leave_history_tab.png")
        print("Saved 13_teacher_leave_history_tab.png")
        
        # Click Duties
        print("Clicking Duties tab...")
        page.locator('text=/Duties/').first.click(force=True)
        page.wait_for_timeout(1000)
        page.screenshot(path="school-management-system/docs/screenshots/mobile_app_redesign/01_teacher/14_teacher_leave_duties_tab.png")
        print("Saved 14_teacher_leave_duties_tab.png")
        
        browser.close()

if __name__ == "__main__":
    test()
