from pathlib import Path

# Update App.tsx
app_path = Path("web/src/App.tsx")
app_c = app_path.read_text(encoding="utf-8")

old_app_block = """    const hostelScreen =
      userRoles.includes("chief_provost") || userRoles.includes("warden")
        ? screens.find((s) => s.path === "/hostel")
        : undefined;
    const first = transportScreen ?? librarianScreen ?? hostelScreen ?? screens[0];"""

new_app_block = """    const hostelScreen =
      userRoles.includes("chief_provost") || userRoles.includes("warden")
        ? screens.find((s) => s.path === "/hostel")
        : undefined;
    const coordinatorScreen = userRoles.includes("academic_coordinator")
      ? screens.find((s) => s.path === "/timetable")
      : undefined;
    const first = coordinatorScreen ?? transportScreen ?? librarianScreen ?? hostelScreen ?? screens[0];"""

if old_app_block in app_c:
    app_c = app_c.replace(old_app_block, new_app_block, 1)
    app_path.write_text(app_c, encoding="utf-8")
    print("Updated App.tsx (LF)")
elif old_app_block.replace("\n", "\r\n") in app_c:
    app_c = app_c.replace(old_app_block.replace("\n", "\r\n"), new_app_block.replace("\n", "\r\n"), 1)
    app_path.write_text(app_c, encoding="utf-8")
    print("Updated App.tsx (CRLF)")
else:
    print("Could not find block in App.tsx")

# Update LoginPage.tsx
login_path = Path("web/src/auth/LoginPage.tsx")
login_c = login_path.read_text(encoding="utf-8")

old_login_block = """                  <button
                    type="button"
                    onClick={() => setDemoRole("admin@sunrisepublic.edu")}
                    className="px-2 py-0.5 rounded-md bg-white border border-slate-200 hover:border-primary text-ink text-[11px] font-medium transition-colors cursor-pointer"
                  >
                    Admin
                  </button>"""

new_login_block = """                  <button
                    type="button"
                    onClick={() => setDemoRole("admin@sunrisepublic.edu")}
                    className="px-2 py-0.5 rounded-md bg-white border border-slate-200 hover:border-primary text-ink text-[11px] font-medium transition-colors cursor-pointer"
                  >
                    Admin
                  </button>
                  <button
                    type="button"
                    onClick={() => setDemoRole("coordinator@sunrisepublic.edu")}
                    className="px-2 py-0.5 rounded-md bg-white border border-slate-200 hover:border-primary text-ink text-[11px] font-medium transition-colors cursor-pointer"
                  >
                    Academic Coordinator
                  </button>"""

if old_login_block in login_c:
    login_c = login_c.replace(old_login_block, new_login_block, 1)
    login_path.write_text(login_c, encoding="utf-8")
    print("Updated LoginPage.tsx (LF)")
elif old_login_block.replace("\n", "\r\n") in login_c:
    login_c = login_c.replace(old_login_block.replace("\n", "\r\n"), new_login_block.replace("\n", "\r\n"), 1)
    login_path.write_text(login_c, encoding="utf-8")
    print("Updated LoginPage.tsx (CRLF)")
else:
    print("Could not find block in LoginPage.tsx")
