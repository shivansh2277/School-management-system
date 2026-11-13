import sys
from playwright.sync_api import sync_playwright

def inspect():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("http://localhost:5173/#/login")
        page.click("button:has-text('Academic Coordinator')")
        page.click("button:has-text('Sign in to ERP')")
        page.wait_for_url("**/timetable**")
        page.wait_for_timeout(2000)

        buttons = page.locator("button").all_text_contents()
        print("BUTTONS ON TIMETABLE PAGE:")
        for b in buttons:
            if b.strip():
                print(" -", repr(b.strip()))

        add_btn = page.locator("button:has-text('+ Add Lesson Slot')")
        print("\nAdd btn count:", add_btn.count())
        if add_btn.count() > 0:
            print("Clicking Add btn...")
            add_btn.first.click()
            page.wait_for_timeout(1000)
            buttons_after = page.locator("button").all_text_contents()
            print("\nBUTTONS AFTER CLICK:")
            for b in buttons_after:
                if b.strip():
                    print(" -", repr(b.strip()))

        browser.close()

if __name__ == "__main__":
    inspect()
