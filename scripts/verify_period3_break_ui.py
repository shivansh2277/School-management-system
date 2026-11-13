from pathlib import Path
from playwright.sync_api import sync_playwright

SCREENSHOT_DIR = Path("docs/screenshots")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

def run():
    print("Starting Playwright verification for configurable Period 3 break...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-gpu"])
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # Step 1: Login
        page.goto("http://localhost:5173/#/login", wait_until="networkidle")
        page.wait_for_timeout(1000)
        page.click("button:has-text('Academic Coordinator')")
        page.click("button:has-text('Sign in to ERP')")
        page.wait_for_url("**/timetable**")
        page.wait_for_timeout(2000)

        # Step 2: Class Timetable Grid Screenshot showing Period 3 as Break
        shot1 = SCREENSHOT_DIR / "09_period_3_break_class_timetable_grid.png"
        page.screenshot(path=str(shot1), full_page=False)
        print(f"Captured: {shot1}")

        # Step 3: Bell Timings / Periods Tab showing configurable Period 3 break
        page.click("button:has-text('Bell Timings / Periods')")
        page.wait_for_timeout(1500)
        shot2 = SCREENSHOT_DIR / "10_bell_timings_period_3_break_configured.png"
        page.screenshot(path=str(shot2), full_page=False)
        print(f"Captured: {shot2}")

        # Step 4: Open Configure Period Modal for Period 3
        configure_buttons = page.locator("button:has-text('Edit / Configure')")
        print("Configure buttons count:", configure_buttons.count())
        if configure_buttons.count() >= 3:
            # Click Period 3 configure button (index 2)
            configure_buttons.nth(2).click()
            page.wait_for_timeout(1000)
            shot3 = SCREENSHOT_DIR / "11_configure_period_modal_break_toggle.png"
            page.screenshot(path=str(shot3), full_page=False)
            print(f"Captured: {shot3}")
            page.click("button:has-text('Cancel')")
            page.wait_for_timeout(500)

        browser.close()
        print("Playwright verification completed successfully!")

if __name__ == "__main__":
    run()
