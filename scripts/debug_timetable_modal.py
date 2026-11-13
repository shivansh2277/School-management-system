from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.on("console", lambda msg: print("BROWSER CONSOLE:", msg.type, msg.text))
    page.on("pageerror", lambda err: print("BROWSER ERROR:", err))
    page.goto("http://localhost:5173/#/login")
    page.click("button:has-text('Academic Coordinator')")
    page.click("button:has-text('Sign in to ERP')")
    page.wait_for_url("**/timetable**")
    page.wait_for_timeout(2000)
    print("PAGE URL:", page.url)
    
    # Check classes
    classes_select = page.locator("select")
    print("Select elements count:", classes_select.count())
    for i in range(classes_select.count()):
        print(f"Select {i} text:", classes_select.nth(i).inner_text())

    btn = page.locator("button:has-text('+ Add Lesson Slot')")
    print("Add Lesson Slot btn count:", btn.count())
    if btn.count() > 0:
        print("Btn is_enabled:", btn.first.is_enabled())
        print("Btn is_visible:", btn.first.is_visible())
        btn.first.click()
        page.wait_for_timeout(1000)
        print("After click, modal count:", page.locator(".fixed.inset-0").count())
        cancel_btn = page.locator("button:has-text('Cancel')")
        print("Cancel btn count:", cancel_btn.count())
        if cancel_btn.count() == 0:
            print("Modal inner text:", page.locator(".fixed").all_inner_texts())
            print("Body HTML snippet:", page.locator("body").inner_html()[-1000:])
    browser.close()
