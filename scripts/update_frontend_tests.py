from pathlib import Path

# 1. Update screens.test.tsx
screens_test_path = Path("web/src/screens.test.tsx")
content = screens_test_path.read_text(encoding="utf-8")

old_def = """const TRANSPORT_MANAGER = ["""
new_def = """const ACADEMIC_COORDINATOR = [
  "academics.class.read",
  "timetable.slot.read",
  "timetable.slot.write",
  "timetable.slot.override",
  "timetable.substitution.manage",
  "comms.notice.read",
];

const TRANSPORT_MANAGER = ["""

old_case = """  it("shows a transport manager no Fees entry", () => {"""
new_case = """  it("shows an academic coordinator timetable and classes, but strictly no fees, hr, or settings", () => {
    const labels = labelsFor(ACADEMIC_COORDINATOR, ALL_MODULES);
    expect(labels).toContain("Timetable");
    expect(labels).toContain("Classes");
    expect(labels).toContain("Notices");
    expect(labels).not.toContain("Fees");
    expect(labels).not.toContain("Staff");
    expect(labels).not.toContain("Students");
    expect(labels).not.toContain("Settings");
    expect(labels).not.toContain("Attendance");
    expect(labels).not.toContain("Payroll");
    expect(labels).not.toContain("Transport");
  });

  it("shows a transport manager no Fees entry", () => {"""

if old_def in content and old_case in content:
    content = content.replace(old_def, new_def, 1)
    content = content.replace(old_case, new_case, 1)
    screens_test_path.write_text(content, encoding="utf-8")
    print("Updated screens.test.tsx")
else:
    print("Could not match in screens.test.tsx")

# 2. Update LoginPage.test.tsx
login_test_path = Path("web/src/auth/LoginPage.test.tsx")
l_content = login_test_path.read_text(encoding="utf-8")

old_l_check = '    expect(screen.getByRole("button", { name: "Admin" })).toBeInTheDocument();'
new_l_check = """    expect(screen.getByRole("button", { name: "Admin" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Academic Coordinator" })).toBeInTheDocument();"""

old_l_test = """  it("clicking Chief Provost populates provost login and password", () => {"""
new_l_test = """  it("clicking Academic Coordinator populates coordinator login and password", () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    );

    fireEvent.click(screen.getByRole("button", { name: "Academic Coordinator" }));

    const emailInput = screen.getByPlaceholderText("admin@sunrisepublic.edu") as HTMLInputElement;
    const passwordInput = screen.getByPlaceholderText("••••••••••••") as HTMLInputElement;

    expect(emailInput.value).toBe("coordinator@sunrisepublic.edu");
    expect(passwordInput.value).toBe("Admin@123");
  });

  it("clicking Chief Provost populates provost login and password", () => {"""

if old_l_check in l_content and old_l_test in l_content:
    l_content = l_content.replace(old_l_check, new_l_check, 1)
    l_content = l_content.replace(old_l_test, new_l_test, 1)
    login_test_path.write_text(l_content, encoding="utf-8")
    print("Updated LoginPage.test.tsx")
else:
    print("Could not match in LoginPage.test.tsx")
