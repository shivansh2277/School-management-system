# Demo script

The cross-role walkthrough from BLUEPRINT section 13, in the order to run it live.
Every step is also an assertion in `backend/tests/test_walkthrough.py`, so the
script and the test never drift apart.

Before starting: `make seed`. It is idempotent and safe immediately before a demo.

Have three things open: the web dashboard signed in as admin, the Expo app on a
phone, and this page.

---

## The point of the demo

One database, four roles. A teacher writes; the admin, the student and the parent
all read the same row. Nothing on any screen is mocked.

---

## Attendance loop

1. **Mobile, teacher `TCH001`** - Attendance tab, class 10-A, today.
   Mark two students absent, tap Save.
2. **Web, admin** - Attendance screen, 10-A, today. The two absences are there.
   The Dashboard attendance donut reflects them too.
3. **Mobile, student `SPS2024001`** (one of the two) - Attendance tab.
   Today shows as absent on the month calendar.
4. **Mobile, parent `9876500001`** - Attendance tab for that child. Same absence.

Say out loud: leave counts against presence, and the label on the screen says so.

## Homework loop

5. **Teacher** - Homework tab, New assignment, 10-A / Mathematics, due tomorrow.
6. **Student** - Homework tab, Pending. The new item is there. Open it, type an
   answer, Submit.
7. **Teacher** - open that assignment. The student shows Submitted, not late.
8. **Parent** - Homework tab. The submitted count went up by one.

There is no `status` column anywhere: a submission row exists or it does not, and
pending is computed as roster minus submissions.

## Marks loop

9. **Web, admin** - Exams, Create Exam "Term 1 - Unit Test 2", then add a
   Mathematics paper for 10-A with max marks 50.
10. **Teacher** - Results tab, that paper. Type 51 for one student: the field turns
    red and the API rejects it naming the student. Enter valid marks, Save.
11. **Student** - Results tab, that exam. Subject row, percentage and grade band.
12. **Parent** - Results tab. The identical report card.

Leave one student blank and show the report card: that subject reads as absent and
is excluded from the total rather than counted as zero.

## Fees loop

13. **Web, admin** - Fees, pick the current month, Generate invoices. It reports how
    many were created. Press it again: created 0, skipped 24. It is idempotent.
14. **Parent** - Fees tab. Pay Now on a pending invoice, confirm the simulated
    payment. The pill flips to Paid and a receipt number appears. Download Receipt
    opens the PDF, with the amount in figures and in words.
15. **Web, admin** - Fees. The collected total has risen by exactly that amount.

No payment gateway is involved; the transaction reference is generated locally and
the receipt sequence is `SPS/RCP/{year}/{000001}`.

## Notices

16. **Web, admin** - Notices, publish to audience `parents`.
    The parent sees it in their feed; the student does not.

Then try the other direction on the app: a teacher's Announcements tab can only
publish to a section they teach, and the API returns 403 for any school-wide
audience. That restriction is a test, not a UI convention.

---

## If asked "what happens when there is no data?"

Open a month with no attendance, or a section with no marks. Every panel shows an
explicit empty state - "No attendance marked for this date yet." - and the fee
trend chart carries only months that actually have collections. There are no
zero-filled bars and no invented percentage deltas anywhere in the system.
