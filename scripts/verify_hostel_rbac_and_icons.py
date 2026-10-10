"""E2E Browser Visual Verification Script for Hostel & Mess Module RBAC and Icons.

Verifies:
1. Admin:
   - Full non-hostel ERP retained.
   - Hostel group has EXACTLY 2 items: "Hostel Dashboard" and "Hostel Admissions".
   - Hostel dashboard displays "Hostel Administrative Overview" badge.
   - Direct navigation to operational screens (/hostel/rooms) is restricted.
2. Chief Provost:
   - Hostel domain authority across tenant.
   - Sidebar has EXACTLY 9 hostel items under "Hostel".
   - Hostel dashboard displays "Chief Provost Portal" badge.
   - Both Boys Hostel and Girls Hostel visible.
   - Can access rooms, beds, admissions.
3. Boys Hostel Warden:
   - Scoped strictly to Boys Hostel.
   - Sidebar group titled "My Hostel" with EXACTLY 8 items.
   - "Hostel Admissions" completely absent.
   - Direct navigation to /hostel/admissions renders Access Restricted.
   - Direct API call to admissions returns HTTP 403 Forbidden.
   - Girls Hostel is completely invisible.
   - Direct API call to Girls Hostel returns HTTP 403 Forbidden.
4. Girls Hostel Warden:
   - Scoped strictly to Girls Hostel.
   - Boys Hostel completely invisible.
   - Direct API call to Boys Hostel returns HTTP 403 Forbidden.
5. Golden-Amber Lucide Icons:
   - All 9 hostel navigation links render custom SVG icons without placeholder rects.
"""

import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from playwright.sync_api import sync_playwright

EVIDENCE_DIR = Path("docs/visual_evidence")
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
BASE_URL = "http://localhost:5173"

def run_verification():
    print("=" * 80)
    print("STARTING FULL E2E VISUAL VERIFICATION: HOSTEL RBAC & ICONS")
    print("=" * 80)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        def login(page, demo_role_name):
            page.goto(f"{BASE_URL}/#/login")
            page.wait_for_load_state("networkidle")
            time.sleep(1)
            btn = page.locator(f"button:has-text('{demo_role_name}')").first
            btn.scroll_into_view_if_needed()
            btn.click()
            time.sleep(0.5)
            val = page.input_value("input[type='text']")
            print(f"  Logging in as '{demo_role_name}' ({val})...")
            page.click("button[type='submit']")
            page.wait_for_timeout(3000)
            page.wait_for_load_state("networkidle")
            time.sleep(1)
            print(f"  Landed on: {page.url}")

        # ======================================================================
        # 1. ADMIN / OFFICE ADMINISTRATOR
        # ======================================================================
        print("\n[1/5] Verifying Admin / Office Administrator...")
        ctx_admin = browser.new_context(viewport={"width": 1440, "height": 900})
        page_admin = ctx_admin.new_page()
        login(page_admin, "Admin")

        # Capture ERP landing with intact ERP modules
        page_admin.screenshot(path=str(EVIDENCE_DIR / "43_admin_erp_dashboard_intact.png"))
        print("  [OK] Captured: 43_admin_erp_dashboard_intact.png")

        # Scroll sidebar to Hostel section
        hostel_header = page_admin.locator("text=HOSTEL").first
        hostel_header.scroll_into_view_if_needed()
        time.sleep(0.5)

        # Inspect hostel sidebar links
        hostel_links = page_admin.locator("#app-sidebar a[href*='/hostel']").all_inner_texts()
        cleaned_links = [l.strip() for l in hostel_links if l.strip()]
        print(f"  Admin Hostel links visible in sidebar: {cleaned_links}")
        assert "Hostel Dashboard" in cleaned_links, "Admin must see Hostel Dashboard"
        assert "Hostel Admissions" in cleaned_links, "Admin must see Hostel Admissions"
        assert len(cleaned_links) == 2, f"Admin must see EXACTLY 2 hostel links, found: {cleaned_links}"
        for prohibited in ["Rooms & Beds", "Residents", "Attendance", "Leave & Outing", "Complaints & Incidents", "Notices", "Mess Menu"]:
            assert prohibited not in cleaned_links, f"Admin must NOT see operational item: {prohibited}"

        # Capture pruned sidebar screenshot
        page_admin.screenshot(path=str(EVIDENCE_DIR / "44_admin_hostel_sidebar_pruned.png"))
        print("  [OK] Captured: 44_admin_hostel_sidebar_pruned.png")

        # Navigate to /hostel
        page_admin.goto(f"{BASE_URL}/#/hostel")
        page_admin.wait_for_load_state("networkidle")
        time.sleep(1.5)

        # Verify role badge
        badge_text = page_admin.locator("text=Hostel Administrative Overview").first.inner_text()
        assert "Hostel Administrative Overview" in badge_text
        print(f"  [OK] Admin Dashboard Role Badge: '{badge_text}'")

        # Verify operational quick action buttons are absent for Admin
        quick_actions = page_admin.locator("text=Mark 8:00 PM Attendance").count()
        assert quick_actions == 0, "Admin must not see Mark 8:00 PM Attendance button"

        page_admin.screenshot(path=str(EVIDENCE_DIR / "45_admin_hostel_dashboard_overview.png"))
        print("  [OK] Captured: 45_admin_hostel_dashboard_overview.png")

        # Navigate to /hostel/admissions
        page_admin.goto(f"{BASE_URL}/#/hostel/admissions")
        page_admin.wait_for_load_state("networkidle")
        time.sleep(1.5)
        admissions_title = page_admin.locator("h1:has-text('Hostel Admissions')").count()
        assert admissions_title > 0, "Admin must have access to Hostel Admissions page"
        page_admin.screenshot(path=str(EVIDENCE_DIR / "46_admin_hostel_admissions_page.png"))
        print("  [OK] Captured: 46_admin_hostel_admissions_page.png")

        # Direct navigation attempt to /hostel/rooms -> Expect in-page refusal
        page_admin.goto(f"{BASE_URL}/#/hostel/rooms")
        page_admin.wait_for_load_state("networkidle")
        time.sleep(1)
        refusal_msg = page_admin.locator("text=Access Restricted").count()
        assert refusal_msg > 0, "Admin must be refused when directly accessing /hostel/rooms"
        page_admin.screenshot(path=str(EVIDENCE_DIR / "47_admin_denied_hostel_rooms.png"))
        print("  [OK] Captured: 47_admin_denied_hostel_rooms.png")
        ctx_admin.close()

        # ======================================================================
        # 2. CHIEF PROVOST
        # ======================================================================
        print("\n[2/5] Verifying Chief Provost...")
        ctx_provost = browser.new_context(viewport={"width": 1440, "height": 900})
        page_provost = ctx_provost.new_page()
        login(page_provost, "Chief Provost")

        # Chief provost lands on /hostel
        print("  Chief Provost URL:", page_provost.url)
        assert "/hostel" in page_provost.url

        # Check badge
        provost_badge = page_provost.locator("text=Chief Provost Portal").first.inner_text()
        assert "Chief Provost Portal" in provost_badge
        print(f"  [OK] Provost Role Badge: '{provost_badge}'")

        # Check all 9 navigation links
        provost_links = page_provost.locator("#app-sidebar a[href*='/hostel']").all_inner_texts()
        cleaned_provost_links = [l.strip() for l in provost_links if l.strip()]
        print(f"  Chief Provost Hostel links: {cleaned_provost_links}")
        expected_9 = [
            "Hostel Dashboard",
            "Rooms & Beds",
            "Residents",
            "Hostel Admissions",
            "Attendance",
            "Leave & Outing",
            "Complaints & Incidents",
            "Notices",
            "Mess Menu",
        ]
        assert cleaned_provost_links == expected_9, f"Provost must see all 9 links in order, got: {cleaned_provost_links}"

        page_provost.screenshot(path=str(EVIDENCE_DIR / "48_provost_hostel_dashboard_and_sidebar.png"))
        print("  [OK] Captured: 48_provost_hostel_dashboard_and_sidebar.png")

        # Verify Rooms & Beds (Both Boys and Girls Hostels)
        page_provost.goto(f"{BASE_URL}/#/hostel/rooms")
        page_provost.wait_for_load_state("networkidle")
        time.sleep(2)

        has_boys = page_provost.locator("text=Boys Hostel").count() > 0
        has_girls = page_provost.locator("text=Girls Hostel").count() > 0
        assert has_boys, "Chief Provost must see Boys Hostel"
        assert has_girls, "Chief Provost must see Girls Hostel"
        print("  [OK] Chief Provost sees both Boys and Girls Hostels in Rooms & Beds")
        page_provost.screenshot(path=str(EVIDENCE_DIR / "49_provost_both_hostels_rooms_beds.png"))
        print("  [OK] Captured: 49_provost_both_hostels_rooms_beds.png")

        # Verify Admissions
        page_provost.goto(f"{BASE_URL}/#/hostel/admissions")
        page_provost.wait_for_load_state("networkidle")
        time.sleep(1.5)
        page_provost.screenshot(path=str(EVIDENCE_DIR / "50_provost_admissions_page.png"))
        print("  [OK] Captured: 50_provost_admissions_page.png")
        ctx_provost.close()

        # ======================================================================
        # 3. BOYS HOSTEL WARDEN
        # ======================================================================
        print("\n[3/5] Verifying Boys Hostel Warden...")
        ctx_bw = browser.new_context(viewport={"width": 1440, "height": 900})
        page_bw = ctx_bw.new_page()
        login(page_bw, "Boys Warden")

        assert "/hostel" in page_bw.url
        bw_badge = page_bw.locator("text=Warden Portal").first.inner_text()
        assert "Warden Portal" in bw_badge
        print(f"  [OK] Boys Warden Role Badge: '{bw_badge}'")

        # Check sidebar group header is 'My Hostel'
        my_hostel_header = page_bw.locator("#app-sidebar").locator("text=MY HOSTEL").count()
        assert my_hostel_header > 0, "Warden sidebar group must be 'MY HOSTEL'"

        # Check exactly 8 links, admissions must be ABSENT
        bw_links = page_bw.locator("#app-sidebar a[href*='/hostel']").all_inner_texts()
        cleaned_bw_links = [l.strip() for l in bw_links if l.strip()]
        print(f"  Boys Warden links: {cleaned_bw_links}")
        expected_bw = [
            "Hostel Dashboard",
            "Rooms & Beds",
            "Residents",
            "Attendance",
            "Leave & Outing",
            "Complaints & Incidents",
            "Notices",
            "Mess Menu",
        ]
        assert cleaned_bw_links == expected_bw, f"Boys Warden must see 8 links without admissions, got: {cleaned_bw_links}"
        assert "Hostel Admissions" not in cleaned_bw_links

        # Confirm ONLY Boys Hostel is on Dashboard
        assert page_bw.locator("text=Boys Hostel").count() > 0, "Boys Hostel must be present"
        assert page_bw.locator("text=Girls Hostel").count() == 0, "Girls Hostel must NOT be visible to Boys Warden"
        print("  [OK] Boys Warden dashboard shows ONLY Boys Hostel")

        page_bw.screenshot(path=str(EVIDENCE_DIR / "51_boys_warden_dashboard_and_sidebar.png"))
        print("  [OK] Captured: 51_boys_warden_dashboard_and_sidebar.png")

        # Navigate to Rooms & Beds
        page_bw.goto(f"{BASE_URL}/#/hostel/rooms")
        page_bw.wait_for_load_state("networkidle")
        time.sleep(2)
        assert page_bw.locator("text=Girls Hostel").count() == 0, "Girls Hostel must NOT appear in Rooms & Beds"
        page_bw.screenshot(path=str(EVIDENCE_DIR / "52_boys_warden_rooms_isolation.png"))
        print("  [OK] Captured: 52_boys_warden_rooms_isolation.png")

        # Direct navigation to /hostel/admissions -> Expect in-page refusal
        page_bw.goto(f"{BASE_URL}/#/hostel/admissions")
        page_bw.wait_for_load_state("networkidle")
        time.sleep(1)
        refusal_count = page_bw.locator("text=Access Restricted").count()
        assert refusal_count > 0, "Warden direct navigation to /hostel/admissions must show Access Restricted"
        page_bw.screenshot(path=str(EVIDENCE_DIR / "53_warden_denied_hostel_admissions.png"))
        print("  [OK] Captured: 53_warden_denied_hostel_admissions.png")

        # Direct API call to admissions -> Expect 403
        token_bw = page_bw.evaluate("() => localStorage.getItem('sunrise.token')")
        resp_adm = page_bw.request.get(
            f"http://127.0.0.1:8000/admin/hostel/admissions/pending-applications",
            headers={"Authorization": f"Bearer {token_bw}"},
        )
        assert resp_adm.status == 403, f"Expected 403 Forbidden for Warden on admissions API, got {resp_adm.status}"
        print(f"  [OK] Warden API direct admissions refused with HTTP {resp_adm.status} Forbidden")

        # Direct API call to Girls Hostel (hostel_id=2) -> Expect 403
        resp_gh = page_bw.request.get(
            f"http://127.0.0.1:8000/admin/hostel/2/structure",
            headers={"Authorization": f"Bearer {token_bw}"},
        )
        assert resp_gh.status == 403, f"Expected 403 Forbidden for Boys Warden on Girls Hostel API, got {resp_gh.status}"
        print(f"  [OK] Boys Warden API call to Girls Hostel refused with HTTP {resp_gh.status} Forbidden")

        ctx_bw.close()

        # ======================================================================
        # 4. GIRLS HOSTEL WARDEN
        # ======================================================================
        print("\n[4/5] Verifying Girls Hostel Warden...")
        ctx_gw = browser.new_context(viewport={"width": 1440, "height": 900})
        page_gw = ctx_gw.new_page()
        login(page_gw, "Girls Warden")

        assert "/hostel" in page_gw.url
        assert page_gw.locator("text=Girls Hostel").count() > 0, "Girls Hostel must be present"
        assert page_gw.locator("text=Boys Hostel").count() == 0, "Boys Hostel must NOT be visible to Girls Warden"
        print("  [OK] Girls Warden dashboard shows ONLY Girls Hostel")

        page_gw.screenshot(path=str(EVIDENCE_DIR / "54_girls_warden_dashboard_isolation.png"))
        print("  [OK] Captured: 54_girls_warden_dashboard_isolation.png")

        # Direct API call to Boys Hostel (hostel_id=1) -> Expect 403
        token_gw = page_gw.evaluate("() => localStorage.getItem('sunrise.token')")
        resp_bh = page_gw.request.get(
            f"http://127.0.0.1:8000/admin/hostel/1/structure",
            headers={"Authorization": f"Bearer {token_gw}"},
        )
        assert resp_bh.status == 403, f"Expected 403 Forbidden for Girls Warden on Boys Hostel API, got {resp_bh.status}"
        print(f"  [OK] Girls Warden API call to Boys Hostel refused with HTTP {resp_bh.status} Forbidden")

        ctx_gw.close()

        # ======================================================================
        # 5. SIDEBAR LUCIDE SVG ICONS VERIFICATION
        # ======================================================================
        print("\n[5/5] Verifying Golden-Amber Lucide SVG Icons...")
        ctx_icons = browser.new_context(viewport={"width": 1440, "height": 900})
        page_icons = ctx_icons.new_page()
        login(page_icons, "Chief Provost")

        # Find all hostel nav items
        nav_items = page_icons.locator("#app-sidebar a[href*='/hostel']").all()
        assert len(nav_items) == 9
        for item in nav_items:
            href = item.get_attribute("href")
            svg = item.locator("svg").first
            assert svg.count() > 0, f"Link {href} must have an SVG icon"
            
            # Check for fallback placeholder rects (width='7' height='7')
            fallback_rects = svg.locator("rect[width='7'][height='7']").count()
            assert fallback_rects == 0, f"Link {href} must NOT use the 4 square placeholder fallback icon!"
            
            # Check golden-amber text class
            svg_class = svg.get_attribute("class") or ""
            assert "#ffa726" in svg_class, f"Link {href} SVG icon must have golden-amber text styling class"

        print(f"  [OK] All 9 hostel navigation links render custom Lucide SVGs with golden-amber styling!")
        page_icons.screenshot(path=str(EVIDENCE_DIR / "55_hostel_lucide_golden_amber_icons.png"))
        print("  [OK] Captured: 55_hostel_lucide_golden_amber_icons.png")
        ctx_icons.close()

        browser.close()
        print("\n" + "=" * 80)
        print("ALL E2E VISUAL AND RBAC VERIFICATIONS PASSED SUCCESSFULLY (100% GREEN)")
        print("=" * 80)

if __name__ == "__main__":
    run_verification()
