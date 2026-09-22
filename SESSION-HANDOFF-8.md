# SESSION-HANDOFF-8: Mobile App Refinements & Core Workflow Hardening Specification

> **Target Implementation Session:** Session 8  
> **Status:** READY FOR EXECUTION  
> **Branch:** `slice/office-feedback` (strictly local development; NEVER push to remote)  
> **Backend Test Baseline:** 722 passed, 2 skipped, 0 failed (100% green with `school-management-system/.venv/Scripts/python.exe -m pytest -q`)  
> **Web Test Baseline:** 85 passed across 19 test files (100% green with `npm test` in `web/`)  
> **Mobile Typecheck Baseline:** Clean (`npm run typecheck` in `mobile/`)  
> **Corpus / Repository Root:** `c:\Users\SHIVANSH\OneDrive\Documents\AGENTS\school-management-system`  

---

## 0. AUTHORITATIVE PRODUCT OVERRIDES & LOCKED INVARIANTS

The following 6 product requirements define the scope of Session 8. Implementations must follow the established Sunrise ERP architecture, tenant isolation, role-based access control, database relationships, and UI design tokens. Superficial UI-only fixes, duplicate models, or hardcoded demo values are strictly prohibited.

1. **Student Home Isolation:**
   - Remove the `Today's Schedule` (Timetable) and `Latest Notices` (Notices) sections from the Student Home dashboard (`mobile/app/(student)/dashboard.tsx`).
   - Do **NOT** remove or modify the dedicated tab navigation or stand-alone screens (`timetable.tsx` and `notices.tsx`). They remain fully available from the student navigation bar.

2. **Parent Fee Accurate Invoicing:**
   - In `mobile/app/(parent)/fees.tsx`, the top-right invoice amount must accurately reflect the invoice total rather than displaying `₹0.00`.
   - Root cause: The backend `/parent/fees` returns `{ payable, balance, charged, discount, paid }`. The frontend was looking for `invoice.total ?? invoice.amount`, which are `undefined`.
   - Sourced dynamically from `invoice.payable` (and fallback `invoice.total`/`invoice.amount`).
   - Display must remain consistent with `invoice.balance` (Remaining due).

3. **Teacher Supplies Real Stock Consumption:**
   - In Teacher Supplies (`mobile/app/(teacher)/stock.tsx`), teachers must be able to record actual stock consumption through a dedicated `"Use / Consume Stock"` action.
   - Teachers enter **quantity consumed** (e.g., 5 units), NOT the remaining quantity.
   - The transaction is persisted to the database via a real backend service and audit trail.
   - **Over-consumption prevention:** Validation must reject attempts to consume more units than currently available (`HTTP 400 Bad Request`).
   - **Automatic threshold comparison:** After deduction, if `current_quantity <= min_quantity`, the item is automatically flagged with `is_low_stock = True` and visible to the admin/store inventory dashboard.
   - The existing `"Flag Diminishing"` replenishment request workflow is preserved in parallel.

4. **Universal Standardized Date Display:**
   - Standardize all user-facing date displays across the mobile app to `DD-MM-YYYY` (e.g., `2026-08-21` displays as `21-08-2026`).
   - Implement a shared, robust formatting utility `formatDate(date)` in `mobile/src/api/client.ts` and apply it consistently across Student, Parent, and Teacher screens.
   - Database storage formats (`DATE`, `TIMESTAMPTZ`) and API payloads remain ISO-8601; this is strictly a user-facing display standardization.

5. **Class Teacher Only Attendance Authorization:**
   - Only the designated **Class Teacher** (`ClassSection.class_teacher_id == teacher.id`) may view and mark the roll sheet for that class/section.
   - A subject teacher who merely teaches a subject in that section must NOT be allowed to mark attendance.
   - Enforced at the **backend API authorization level** (`HTTP 403 Forbidden`), not merely by hiding options in the UI.
   - The mobile UI dropdown must only list sections where the authenticated teacher is the assigned class teacher.

6. **Student Homework Submitted Tab Fix:**
   - In `mobile/app/(student)/homework.tsx`, fixing the critical boolean bug where `item.marks === null && item.marks === undefined` (a mathematical impossibility) caused the `Submitted` tab to always display empty.
   - Ensure the `Pending`, `Submitted`, `Graded`, and `All` tabs correctly filter assignments according to their actual submission and grading state.

---

## 1. DETAILED ENGINEERING SPECIFICATIONS BY TASK

---

### TASK 1 — Student Home: Remove Notices & Timetable from Home Only

#### 1.1 Root Cause & Target Files
- **File:** [`mobile/app/(student)/dashboard.tsx`](file:///c:/Users/SHIVANSH/OneDrive/Documents/AGENTS/school-management-system/mobile/app/%28student%29/dashboard.tsx)
- **Current State:**
  - Lines 70–94 render `<Card title="Today">` with the student's daily period timetable.
  - Lines 96–110 render `<Card title="Latest notices">` with recent announcements.
- **Dedicated Route Integrity:**
  - `mobile/app/(student)/timetable.tsx` remains registered in `mobile/app/(student)/_layout.tsx` (Tab navigation).
  - `mobile/app/(student)/notices.tsx` remains registered in `mobile/app/(student)/_layout.tsx` (Tab navigation).

#### 1.2 Implementation Steps
1. In `mobile/app/(student)/dashboard.tsx`:
   - Remove the `<Card title="Today">` block (lines 70–94).
   - Remove the `<Card title="Latest notices">` block (lines 96–110).
   - Keep the Welcome Card (`Hello, {student.name}`), Key Metrics Card (`Attendance`, `Homework due`, `Latest result`), and `<Card title="Next exam">`.
2. Do not delete or alter `today_schedule` and `recent_notices` from the backend schema `StudentDashboard` if other clients or tests expect them.

---

### TASK 2 — Parent Fees: Fix Incorrect ₹0.00 Display

#### 2.1 Root Cause & Analysis
- **Frontend File:** [`mobile/app/(parent)/fees.tsx`](file:///c:/Users/SHIVANSH/OneDrive/Documents/AGENTS/school-management-system/mobile/app/%28parent%29/fees.tsx)
- **Backend Service:** [`backend/app/services/fees.py`](file:///c:/Users/SHIVANSH/OneDrive/Documents/AGENTS/school-management-system/backend/app/services/fees.py) line 807 (`invoice_out`) and `totals` function:
  ```python
  def totals(db: Session, invoice: FeeInvoice) -> dict:
      # ...
      return {
          "charged": money(charged),
          "discount": money(discount),
          "payable": money(net),
          "paid": money(paid),
          "balance": money(net - paid),
      }
  ```
- **The Bug:**
  In `mobile/app/(parent)/fees.tsx`:
  - Line 18: Type `Invoice` declares `total?: number | string; amount?: number | string; payable?: number | string;`
  - Line 169: `const invTotal = invoice.total ?? invoice.amount ?? 0;`
  - Because the backend returns `"payable": "5400.00"` and `"balance": "5400.00"`, `invoice.total` is `undefined` and `invoice.amount` is `undefined`.
  - As a result, `invTotal` resolved to `0`, causing line 192:
    ```tsx
    <Text style={{ fontWeight: "700", color: theme.ink }}>
      {money(invTotal)}
    </Text>
    ```
    to render `₹0.00` while line 184 rendered `Remaining due: ₹5,400.00`!

#### 2.2 Implementation Steps
1. Update `Invoice` type in `mobile/app/(parent)/fees.tsx`:
   ```typescript
   type Invoice = {
     id: number;
     invoice_no: string;
     period_month?: number;
     period_year?: number;
     month?: number;
     year?: number;
     payable?: number | string;
     total?: number | string;
     amount?: number | string;
     charged?: number | string;
     discount?: number | string;
     paid?: number | string;
     balance?: number | string;
     due_date: string;
     status: string;
     receipt_no: string | null;
   };
   ```
2. Update line 169 in `fees.tsx`:
   ```typescript
   const invTotal = Number(invoice.payable ?? invoice.total ?? invoice.amount ?? invoice.balance ?? 0);
   ```
3. Update line 212 payment confirmation text:
   ```typescript
   const paymentAmount = invBalance > 0 ? invBalance : invTotal;
   ```
4. Verify backend endpoint `GET /parent/fees?student_id={id}` response schema and ensure both `payable` and `balance` are correctly serialized.

---

### TASK 3 — Teacher Supplies: Add Quantity-Consumed Stock Update

#### 3.1 Architecture & Data Flow
When a teacher uses materials (e.g., 5 sets of beakers or chalks):
```
Teacher enters quantity_consumed (e.g., 5)
                 │
                 ▼
API: POST /teacher/stock/{item_id}/consume
                 │
  ┌──────────────┴────────────────┐
  ▼                               ▼
Validate: qty > 0         Validate: qty <= item.current_quantity
(else HTTP 400)           (else HTTP 400: "Cannot consume more than available")
                 │
                 ▼
Atomic DB Transaction:
  1. item.current_quantity -= qty
  2. item.last_checked_at = now()
  3. item.last_checked_by_id = teacher.id
  4. Write AuditLog (action="consume", item_id, consumed=5, remaining=13)
  5. Check: is_low_stock = (item.current_quantity <= item.min_quantity)
                 │
                 ▼
Return updated StockItemOut (reflecting new quantity and low_stock status)
```

#### 3.2 Backend Service Implementation
In [`backend/app/services/inventory.py`](file:///c:/Users/SHIVANSH/OneDrive/Documents/AGENTS/school-management-system/backend/app/services/inventory.py):
```python
class StockConsumeIn(BaseModel):
    model_config = {"extra": "forbid"}
    quantity: int = Field(gt=0, description="Quantity consumed")
    reason: str | None = Field(default=None, max_length=255)

def consume_stock(
    db: Session, user: User, item_id: int, data: StockConsumeIn
) -> StockItemOut:
    item = get_item(db, user.school_id, item_id)
    if data.quantity <= 0:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Quantity consumed must be greater than zero"
        )
    if data.quantity > item.current_quantity:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Cannot consume {data.quantity} units; only {item.current_quantity} available in stock",
        )

    old_qty = item.current_quantity
    item.current_quantity -= data.quantity
    item.last_checked_at = datetime.now(UTC)
    item.last_checked_by_id = user.id

    db.flush()
    audit.record(
        db,
        actor=user,
        school_id=user.school_id,
        entity_type="stock_item",
        entity_id=item.id,
        action=AuditAction.update,
        before={"current_quantity": old_qty},
        after={"current_quantity": item.current_quantity, "consumed": data.quantity},
        reason=data.reason or "Stock consumed by teacher",
    )
    db.commit()
    db.refresh(item)
    return to_item_out(item)
```

#### 3.3 Backend Route Implementation
In [`backend/app/api/teacher/stock.py`](file:///c:/Users/SHIVANSH/OneDrive/Documents/AGENTS/school-management-system/backend/app/api/teacher/stock.py):
```python
@router.post(
    "/{item_id}/consume",
    response_model=StockItemOut,
    status_code=status.HTTP_200_OK,
)
def consume_teacher_stock(
    item_id: int,
    body: StockConsumeIn,
    user: User = Depends(teacher_access),
    db: Session = Depends(get_db),
) -> StockItemOut:
    """Records stock usage/consumption by teaching staff in classroom or lab."""
    return svc.consume_stock(db, user, item_id, body)
```

#### 3.4 Mobile Frontend UI
In [`mobile/app/(teacher)/stock.tsx`](file:///c:/Users/SHIVANSH/OneDrive/Documents/AGENTS/school-management-system/mobile/app/%28teacher%29/stock.tsx):
- Add state: `const [consumeItem, setConsumeItem] = useState<StockItem | null>(null);`
- Add input states: `consumeQuantity` (default `"1"`), `consumeReason` (`""`).
- Add mutation:
  ```typescript
  const consumeMutation = useMutation({
    mutationFn: ({ itemId, quantity, reason }: { itemId: number; quantity: number; reason?: string }) =>
      api.post<StockItem>(`/teacher/stock/${itemId}/consume`, { quantity, reason }),
    onSuccess: (updated) => {
      Alert.alert(
        "Stock Updated",
        `Successfully logged usage of ${updated.name}. Remaining: ${updated.current_quantity} ${updated.unit}${
          updated.is_low_stock ? " (Low Stock Threshold Reached!)" : ""
        }`
      );
      setConsumeItem(null);
      queryClient.invalidateQueries({ queryKey: ["teacher-stock-items"] });
    },
    onError: (err: any) => {
      Alert.alert("Consumption Failed", err?.message || "Could not record stock consumption.");
    },
  });
  ```
- Render a `"Use / Consume"` button on each item card.
- In the modal, enforce:
  - Input is restricted to numeric digits.
  - Show warning if input exceeds `consumeItem.current_quantity`.
  - Disable the button if `quantity <= 0` or `quantity > consumeItem.current_quantity`.
  - Automatically show `Low Stock` badge when remaining reaches `<= min_quantity`.

---

### TASK 4 — Date Format: Standardize Display to DD-MM-YYYY

#### 4.1 Specification
- **Target Format:** `DD-MM-YYYY` (e.g. `21-08-2026`).
- **Scope:** Universal display across all mobile screens.

#### 4.2 Utility Helper
In [`mobile/src/api/client.ts`](file:///c:/Users/SHIVANSH/OneDrive/Documents/AGENTS/school-management-system/mobile/src/api/client.ts):
```typescript
/**
 * Formats ISO date or Date object to standardized DD-MM-YYYY.
 * Example: '2026-08-21' -> '21-08-2026'
 */
export function formatDate(input: string | Date | null | undefined): string {
  if (!input) return "-";
  if (typeof input === "string") {
    const trimmed = input.trim();
    // Fast path for ISO YYYY-MM-DD
    if (/^\d{4}-\d{2}-\d{2}$/.test(trimmed)) {
      const [y, m, d] = trimmed.split("-");
      return `${d}-${m}-${y}`;
    }
  }
  const d = typeof input === "string" ? new Date(input) : input;
  if (isNaN(d.getTime())) return String(input);
  const day = String(d.getDate()).padStart(2, "0");
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const year = d.getFullYear();
  return `${day}-${month}-${year}`;
}
```

#### 4.3 Screen-by-Screen Replacement Checklist
1. **Student Screens:**
   - [`dashboard.tsx`](file:///c:/Users/SHIVANSH/OneDrive/Documents/AGENTS/school-management-system/mobile/app/%28student%29/dashboard.tsx): `formatDate(data.next_exam.exam_date)`
   - [`homework.tsx`](file:///c:/Users/SHIVANSH/OneDrive/Documents/AGENTS/school-management-system/mobile/app/%28student%29/homework.tsx): `Due {formatDate(item.due_date)}`, `Graded on {formatDate(item.graded_at)}`
   - [`results.tsx`](file:///c:/Users/SHIVANSH/OneDrive/Documents/AGENTS/school-management-system/mobile/app/%28student%29/results.tsx): `formatDate(exam.start_date)`
2. **Parent Screens:**
   - [`fees.tsx`](file:///c:/Users/SHIVANSH/OneDrive/Documents/AGENTS/school-management-system/mobile/app/%28parent%29/fees.tsx): `Due {formatDate(invoice.due_date)}`
   - [`notices.tsx`](file:///c:/Users/SHIVANSH/OneDrive/Documents/AGENTS/school-management-system/mobile/app/%28parent%29/notices.tsx): `formatDate(n.published_at)`
   - [`grievances.tsx`](file:///c:/Users/SHIVANSH/OneDrive/Documents/AGENTS/school-management-system/mobile/app/%28parent%29/grievances.tsx): `formatDate(g.created_at)`
3. **Teacher Screens:**
   - [`attendance.tsx`](file:///c:/Users/SHIVANSH/OneDrive/Documents/AGENTS/school-management-system/mobile/app/%28teacher%29/attendance.tsx): `formatDate(selectedDate)`
   - [`homework.tsx`](file:///c:/Users/SHIVANSH/OneDrive/Documents/AGENTS/school-management-system/mobile/app/%28teacher%29/homework.tsx): `Due {formatDate(item.due_date)}`
   - [`announcements.tsx`](file:///c:/Users/SHIVANSH/OneDrive/Documents/AGENTS/school-management-system/mobile/app/%28teacher%29/announcements.tsx): `formatDate(n.published_at)`
   - [`leave.tsx`](file:///c:/Users/SHIVANSH/OneDrive/Documents/AGENTS/school-management-system/mobile/app/%28teacher%29/leave.tsx): `formatDate(item.start_date)} - {formatDate(item.end_date)`
   - [`grievances.tsx`](file:///c:/Users/SHIVANSH/OneDrive/Documents/AGENTS/school-management-system/mobile/app/%28teacher%29/grievances.tsx): `formatDate(g.created_at)`

---

### TASK 5 — Teacher Attendance: Class Teacher Only Authorization

#### 5.1 Business Rule & Rationale
- Under standard school administrative practice, the **Class Teacher** is the sole authority responsible for marking morning registration/daily attendance for their designated class section.
- Subject teachers teach individual periods and must not mark or alter daily section attendance registers.

#### 5.2 Backend Authorization Enforcement
1. In [`backend/app/services/scoping.py`](file:///c:/Users/SHIVANSH/OneDrive/Documents/AGENTS/school-management-system/backend/app/services/scoping.py):
   Add strict class-teacher verification:
   ```python
   def class_teacher_section_ids_for(db: Session, user: User) -> list[int]:
       """Sections where this teacher is specifically the designated class teacher."""
       teacher = employee_for(db, user)
       return list(
           db.scalars(
               select(ClassSection.id)
               .where(ClassSection.class_teacher_id == teacher.id)
               .order_by(ClassSection.grade_level, ClassSection.section_name)
           )
       )

   def assert_is_class_teacher(db: Session, user: User, class_section_id: int) -> None:
       """Requires caller to be the assigned class teacher of this specific section."""
       allowed = class_teacher_section_ids_for(db, user)
       if class_section_id not in allowed:
           raise forbidden("Only the designated class teacher can mark attendance for this section")
   ```
2. In [`backend/app/api/teacher/attendance.py`](file:///c:/Users/SHIVANSH/OneDrive/Documents/AGENTS/school-management-system/backend/app/api/teacher/attendance.py):
   Update both `roll_sheet` and `mark`:
   ```python
   @router.get("/attendance", response_model=list[RollRow])
   def roll_sheet(
       class_section_id: int,
       date: Date,
       user: User = Depends(teacher_only),
       db: Session = Depends(get_db),
   ) -> list[RollRow]:
       scoping.assert_is_class_teacher(db, user, class_section_id)
       return svc.roll_sheet(db, class_section_id, date)

   @router.post("/attendance", response_model=list[RollRow], dependencies=[Depends(require_permission("attendance.record.mark"))])
   def mark(
       body: AttendanceMarkRequest,
       user: User = Depends(teacher_only),
       db: Session = Depends(get_db),
   ) -> list[RollRow]:
       scoping.assert_is_class_teacher(db, user, body.class_section_id)
       return svc.mark(db, user, body)
   ```
3. In [`backend/app/api/teacher/classes.py`](file:///c:/Users/SHIVANSH/OneDrive/Documents/AGENTS/school-management-system/backend/app/api/teacher/classes.py) or classes list endpoint:
   Ensure `is_class_teacher: bool` is returned on each section so the client knows which sections are eligible for attendance marking.

#### 5.3 Mobile UI Filter
In [`mobile/app/(teacher)/attendance.tsx`](file:///c:/Users/SHIVANSH/OneDrive/Documents/AGENTS/school-management-system/mobile/app/%28teacher%29/attendance.tsx):
- Filter available class sections to only those where `is_class_teacher === true` (or fetch from `/teacher/classes/class-teacher-sections`).
- If a teacher has no assigned class teacher section, display an informative banner:
  *"You are not currently assigned as a Class Teacher for any section. Daily attendance registration is reserved for designated class teachers."*

---

### TASK 6 — Student Homework: Fix Submitted Tab Bug

#### 6.1 Root Cause Analysis
- **File:** [`mobile/app/(student)/homework.tsx`](file:///c:/Users/SHIVANSH/OneDrive/Documents/AGENTS/school-management-system/mobile/app/%28student%29/homework.tsx) line 63.
- **The Bug:**
  ```typescript
  const filtered = allItems.filter((item) => {
    if (filter === "pending") return !item.submitted;
    if (filter === "submitted") return item.submitted && item.marks === null && item.marks === undefined;
    if (filter === "graded") return item.marks !== null && item.marks !== undefined;
    return true;
  });
  ```
- **Explanation:**
  The condition `item.marks === null && item.marks === undefined` can **never evaluate to true**. In JavaScript, a variable cannot simultaneously equal strict `null` and strict `undefined`.
  Therefore, every single submitted assignment was filtered out, resulting in the misleading message: *"No submitted homework assignments."*

#### 6.2 Implementation Steps
1. In `mobile/app/(student)/homework.tsx`:
   Fix the filter logic:
   ```typescript
   const filtered = allItems.filter((item) => {
     const isGraded = item.marks !== null && item.marks !== undefined;
     if (filter === "pending") return !item.submitted;
     if (filter === "submitted") return item.submitted && !isGraded;
     if (filter === "graded") return isGraded;
     return true;
   });
   ```
2. Also align the backend endpoint query parameter:
   In `homework.tsx`:
   ```typescript
   const { data, isLoading } = useQuery({
     queryKey: ["student-homework"],
     queryFn: () => api.get<Item[]>("/student/homework?status=all"),
   });
   ```
   Now when a student submits homework:
   - `submit.mutate` records the answer and attachment.
   - `qc.invalidateQueries({ queryKey: ["student-homework"] })` refetches all homework.
   - The item immediately appears in `Submitted` with badge `"Submitted"`.
   - Once the teacher grades the homework (`marks` awarded), it automatically moves from `Submitted` to `Graded`.

---

## 2. STEP-BY-STEP EXECUTION PLAN

```
┌─────────────────────────────────────────────────────────────┐
│ PHASE 1: Backend Services & API Authorization               │
│ - Add consume_stock service & endpoint in teacher/stock     │
│ - Add class_teacher scoping & enforce in teacher/attendance │
│ - Verify /parent/fees returns payable & balance properly    │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 2: Mobile Date & Format Standardization               │
│ - Add formatDate(d) helper to mobile/src/api/client.ts     │
│ - Apply formatDate to Student, Parent, and Teacher screens │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 3: Mobile UI Corrections & Workflows                  │
│ - Task 1: Remove Today & Notices cards from student dash   │
│ - Task 2: Fix invTotal = invoice.payable in parent fees     │
│ - Task 3: Add "Use Stock" action & modal in teacher stock   │
│ - Task 5: Restrict teacher attendance UI to class teacher   │
│ - Task 6: Fix submitted filter in student homework          │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 4: Verification & Automated Regression Testing         │
│ - Pytest suite (verify backend 722+ tests green)            │
│ - Mobile TypeScript typecheck (0 errors)                    │
│ - E2E browser verification of all 6 workflows               │
│ - Visual capture of updated mobile dashboards & screens     │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. VERIFICATION & TEST PLAN

### 3.1 Backend Pytest Suite
Create or update tests in `backend/tests/`:
1. `test_inventory_consumption.py`:
   - Test teacher consumes valid quantity (`18 -> 13`): verify DB update and audit log.
   - Test teacher cannot consume zero or negative quantity (`HTTP 400`).
   - Test teacher cannot consume more than current stock (`HTTP 400`).
   - Test low stock status triggers when stock drops to `<= min_quantity`.
2. `test_teacher_attendance_class_teacher_scoping.py`:
   - Test class teacher can read roll sheet and mark attendance.
   - Test non-class teacher (subject teacher only) is refused (`HTTP 403 Forbidden`).
   - Test teacher with no classes is refused (`HTTP 403 Forbidden`).
3. `test_student_homework_workflow.py`:
   - Test student submits homework: status becomes `submitted`.
   - Test student submitted homework filter in backend returns submitted item.

### 3.2 Mobile Automated E2E & Browser Validation
Run headless browser verification against `http://localhost:8081` (Expo web):
1. **Student Dashboard:** Confirm `Today` and `Latest notices` are absent from Home. Confirm `Next exam` and top stats remain visible.
2. **Parent Fees:** Confirm fee invoice card displays actual amount (e.g. `₹5,400.00`) instead of `₹0.00`.
3. **Teacher Supplies:** Open "Use Stock", consume 2 units, verify remaining updates in real time.
4. **Dates Display:** Confirm all dates render as `DD-MM-YYYY`.
5. **Teacher Attendance:** Confirm only class teacher sections appear in dropdown; verify unauthorized attempts yield refusal.
6. **Student Homework:** Submit an assignment, switch to `Submitted` tab, confirm assignment appears with `Submitted` badge.

---

## 4. ACCEPTANCE CRITERIA FOR SESSION 8

- [ ] **Item 1:** Student Home dashboard does not display Notices or Timetable cards, while navigation to dedicated Timetable and Notices tabs remains intact.
- [ ] **Item 2:** Parent Fees screen displays the correct invoice total (`₹5,400.00`) matching the underlying fee invoice balance.
- [ ] **Item 3:** Teacher Supplies allows entering quantity consumed, validates against current stock, updates inventory atomically, logs audit trail, and flags low stock.
- [ ] **Item 4:** Dates across all student, parent, and teacher mobile views display consistently in `DD-MM-YYYY` format.
- [ ] **Item 5:** Teacher Attendance API rejects requests from teachers who are not designated class teachers with `403 Forbidden`, and UI only lists authorized class-teacher sections.
- [ ] **Item 6:** Student Homework `Submitted` tab correctly displays submitted assignments awaiting grading.
- [ ] **Regression:** 100% green pytest backend suite (722+ tests passing) and 0 TypeScript compilation errors.
