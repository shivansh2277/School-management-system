# Packet: Academics & Examination Depth + Reports Library

Branch `slice/office-feedback`, off `main`. Local development only.

---

## Executive Summary

This packet delivers:
1. **Academics & Examination Depth** (`/exams`):
   - Interactive paper datesheets by class and subject.
   - Live Marks Entry Grid (`web/src/pages/exams/MarksEntryModal.tsx`) with real-time scoring, validation bounds (`0 <= marks <= max_marks`), absent/exempted flags, and remarks.
   - Paper lock (`POST /admin/exams/papers/{id}/lock` & `unlock`) to prevent modification once verified.
   - Audited overrides (`POST /admin/exams/papers/{id}/marks`) requiring `exam.marks.override` and mandatory justification stored in audit logs alongside old marks.
   - CBSE Assessment Schemes & Weightages (`web/src/pages/exams/SchemesAndGrading.tsx`): Active `CBSE 2026-27` scheme with PT (10M), Notebook (5M), Subject Enrichment (5M), and Term Exam (80M) totaling 100M.
   - CBSE 8-Point Grading Scale (`A1: ≥91%` down to `E: ≥0%`) with frozen scale versions (§0.8).
   - Report Cards Roster & Publication (`web/src/pages/exams/ReportCardsTab.tsx`):
     - Publication readiness validation (`GET /admin/report-cards/readiness`) verifying locked papers (§5.4.9) and unsettled fee balances (§0.6b).
     - Continuous & Comprehensive Evaluation (CCE) CBSE Report Card preview (`ReportCardModal.tsx`).
     - Automated Fee Dues Withholdings (`POST /admin/report-cards/publish`): students with unpaid dues are published with `result_status="withheld"` and an official withholding banner until cleared.
2. **Reports Library** (`/reports`):
   - Full reporting dashboard (`web/src/pages/Reports.tsx`) for the 21 registered backend reports in `core/report_registry.py` across 9 categories.
   - Category filter pills with live counts and real-time search.
   - Dynamic parameter runner modal generating inputs based on report parameters (`class_section_id`, `on`, `date_from`, `date_to`, `threshold`, `min_amount`, `cycle_id`, etc.).
   - Multi-mode visualizer: tabular rosters/ledgers with formatted student & contact details, or KPI stat cards for summaries.
   - Authenticated CSV export (`GET /admin/reports/{code}/export`) with audit logging.

---

## Endpoints Used

| Feature | Endpoints |
|---|---|
| **Exams & Datesheets** | `GET /admin/exams`, `POST /admin/exams`, `GET /admin/exams/{id}/schedule`, `POST /admin/exams/{id}/schedule` |
| **Marks Entry & Lock** | `GET /admin/exams/papers/{id}/marks`, `POST /admin/exams/papers/{id}/marks`, `POST /admin/exams/papers/{id}/lock`, `POST /admin/exams/papers/{id}/unlock` |
| **CBSE Schemes & Scales** | `GET /admin/assessment-schemes`, `POST /admin/assessment-schemes`, `POST /admin/assessment-schemes/{id}/activate`, `GET /admin/grading-scales`, `POST /admin/grading-scales`, `POST /admin/grading-scales/{id}/activate` |
| **Report Cards** | `GET /admin/report-cards/readiness`, `GET /admin/report-cards/preview`, `POST /admin/report-cards/publish`, `GET /admin/report-cards/{id}`, `GET /admin/report-cards`, `POST /admin/report-cards/{id}/release` |
| **Reports Library** | `GET /admin/reports`, `GET /admin/reports/{code}`, `GET /admin/reports/{code}/export` |

---

## Verified Technical Metrics

- **TypeScript**: 0 errors (`npm run typecheck`)
- **Vitest**: 14 test files passed, 62 passed, 2 skipped
- **Production Build**: Clean build in 14.02s
- **Browser CDP Verification**: 13 automated screenshots captured across all screens, modals, and report generations.
