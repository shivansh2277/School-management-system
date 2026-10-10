import time
from pathlib import Path
from playwright.sync_api import sync_playwright

EVIDENCE_DIR = Path("docs/visual_evidence")
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
BASE_URL = "http://127.0.0.1:5173"

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1280, "height": 850})
        page = ctx.new_page()

        # 1. Navigate to login
        print("Navigating to login page...")
        page.goto(f"{BASE_URL}/#/login")
        page.wait_for_load_state("networkidle")
        time.sleep(1)

        # 2. Capture initial login page with all demo buttons
        shot_path_1 = EVIDENCE_DIR / "39_login_page_with_hostel_roles.png"
        page.screenshot(path=str(shot_path_1))
        print(f"Captured: {shot_path_1}")

        # 3. Click Chief Provost
        print("Clicking 'Chief Provost' demo button...")
        page.click("button:has-text('Chief Provost')")
        time.sleep(0.5)
        shot_path_2 = EVIDENCE_DIR / "40_login_chief_provost_selected.png"
        page.screenshot(path=str(shot_path_2))
        print(f"Captured: {shot_path_2}")

        # Verify inputs
        email_val = page.input_value("input[type='text']")
        pwd_val = page.input_value("input[type='password']")
        assert email_val == "provost@sunrisepublic.edu", f"Expected provost email, got {email_val}"
        assert pwd_val == "Admin@123", f"Expected Admin@123, got {pwd_val}"

        # 4. Click Boys Warden
        print("Clicking 'Boys Warden' demo button...")
        page.click("button:has-text('Boys Warden')")
        time.sleep(0.5)
        shot_path_3 = EVIDENCE_DIR / "41_login_boys_warden_selected.png"
        page.screenshot(path=str(shot_path_3))
        print(f"Captured: {shot_path_3}")

        email_val = page.input_value("input[type='text']")
        pwd_val = page.input_value("input[type='password']")
        assert email_val == "warden.boys@sunrisepublic.edu", f"Expected warden.boys email, got {email_val}"
        assert pwd_val == "Admin@123", f"Expected Admin@123, got {pwd_val}"

        # 5. Click Girls Warden
        print("Clicking 'Girls Warden' demo button...")
        page.click("button:has-text('Girls Warden')")
        time.sleep(0.5)
        shot_path_4 = EVIDENCE_DIR / "42_login_girls_warden_selected.png"
        page.screenshot(path=str(shot_path_4))
        print(f"Captured: {shot_path_4}")

        email_val = page.input_value("input[type='text']")
        pwd_val = page.input_value("input[type='password']")
        assert email_val == "warden.girls@sunrisepublic.edu", f"Expected warden.girls email, got {email_val}"
        assert pwd_val == "Admin@123", f"Expected Admin@123, got {pwd_val}"

        browser.close()
        print("All login role verification assertions passed successfully!")

if __name__ == "__main__":
    main()
