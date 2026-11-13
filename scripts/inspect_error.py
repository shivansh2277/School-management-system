import sys
from playwright.sync_api import sync_playwright

def inspect_error():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.on("pageerror", lambda err: print("PAGE ERROR:", str(err).encode("ascii", "replace").decode()))
        page.goto("http://localhost:5173/#/login")
        page.click("button:has-text('Academic Coordinator')")
        page.click("button:has-text('Sign in to ERP')")
        page.wait_for_url("**/timetable**")
        page.wait_for_timeout(2000)

        add_btn = page.locator("button:has-text('+ Add Lesson Slot')")
        add_btn.first.click()
        page.wait_for_timeout(1500)
        browser.close()

if __name__ == "__main__":
    inspect_error()
