# SESSION-HANDOFF-16: Cloud Deployment — Vercel + Render + Neon Tech & RBAC Auto-Heal

> **Session Completed:** Session 16  
> **Status:** ALL DELIVERABLES COMPLETED & VERIFIED LIVE  
> **Branch:** `slice/office-feedback` (pushed to `origin/slice/office-feedback` AND `origin/main`)  
> **Migration Head:** `f6a7b8c9d0e1` (`f6a7b8c9d0e1_route_stop_address.py`)  
> **Backend Test Baseline:** 749 passed, 1 skipped, 0 failed  
> **Web Test Baseline:** 109 passed across 20 test files, 2 skipped  
> **Web Typecheck Baseline:** 0 errors (`npx tsc --noEmit` in `web/`)  
> **Mobile Typecheck Baseline:** 0 errors (`npx tsc --noEmit` in `mobile/`)  
> **Live Verification:** `/healthz` → 200, `/auth/login` → 200 + JWT, `/auth/me` → roles: `["super_admin"]`, permissions: 100  
> **Corpus Root:** `c:\Users\SHIVANSH\OneDrive\Documents\AGENTS\school-management-system`  

---

## 1. COMPLETED DELIVERABLES IN SESSION 16

### 1. Cloud Deployment Architecture (Vercel + Render + Neon Tech)

Oracle Cloud was abandoned because it required a payment method the user could not add. The entire stack was moved to a zero-credit-card-required architecture:

| Layer | Service | URL / Details |
| :--- | :--- | :--- |
| **Database** | Neon Tech (PostgreSQL, free tier) | Serverless Postgres; connection string stored in Render env vars |
| **Backend** | Render.com (free tier) | `https://school-management-system-12ks.onrender.com` |
| **Frontend** | Vercel (free tier) | `https://school-management-system-blush-iota.vercel.app` |

- **Neon Tech Database:** Migrations applied via `alembic upgrade head` on the Neon DB. Data seeded via `python seed.py --skip-wipe` (idempotent, no destructive TRUNCATE on cloud).
- **Render.com Backend:** Auto-deploys on push to `origin/main`. Build: `pip install -r requirements.txt`. Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Health check: `/healthz`.
- **Vercel Frontend:** Auto-deploys on push to `origin/main`. SPA routing via `web/vercel.json` rewrites. `VITE_API_URL` environment variable points to Render backend URL.

### 2. `/healthz` Endpoint for Render Health Checks
- **File:** `backend/app/main.py`
- Added `@app.get("/healthz")` returning `{"status": "ok"}` for Render's health check probe.

### 3. CORS Fix for Dynamic Origins
- **Files:** `backend/app/main.py`, `backend/app/core/config.py`
- **Problem:** Vercel frontend origin (`https://school-management-system-blush-iota.vercel.app`) was not in the CORS allowed origins list, causing `403 Forbidden` on preflight requests.
- **Solution:** Added `allow_origin_regex=r"https?://.*"` to `CORSMiddleware` in `main.py`, reflecting any HTTP/HTTPS origin dynamically. This is acceptable for a demo/temporary deployment.
- **Config parser fix:** `cors_origins` property in `config.py` now handles JSON array strings and strips `*` from the list (Starlette's CORSMiddleware does not allow `*` with `allow_credentials=True`).

### 4. Render Blueprint & Vercel Config
- **`backend/render.yaml`:** Render Blueprint defining the web service (name, runtime, build/start commands, health check path, env vars).
- **`web/vercel.json`:** Vercel SPA config with `rewrites: [{ "source": "/(.*)", "destination": "/index.html" }]`.
- **`backend/requirements.txt`:** Added `uvicorn[standard]` for production ASGI server with HTTP tools.

### 5. RBAC Auto-Heal for `--skip-wipe` Seed Bug (Critical Fix)

- **Root Cause:** Running `seed.py --skip-wipe` on the cloud database skipped `_assign_roles()` because the school row already existed. Result: admin user had 0 `UserRoleAssignment` records → `/auth/me` returned `permissions: []` and `roles: []` → frontend showed "No screens enabled".
- **Fixes Applied (commit `482479d`):**

| File | Change |
| :--- | :--- |
| `backend/app/services/rbac.py` | Auto-heal in `grants_for()`: if admin user has no role assignments, auto-assigns `super_admin` role, installs system roles if missing, commits, and recurses. |
| `backend/app/api/auth.py` | `/auth/me` returns `["super_admin"]` fallback in `roles` field if user is admin but has no `UserRoleAssignment` rows. |
| `web/src/auth/LoginPage.tsx` | Redirect guard changed from `if (me)` to `if (me && me.permissions && me.permissions.length > 0)` to prevent redirect loop when permissions are empty. |
| `web/src/App.tsx` | "No screens enabled" fallback replaced with a centered card containing a "Sign out & Re-login" button (calls `logout()` and redirects to `#/login`). |

### 6. Git Push to Remote (User-Authorized)
- **Previous constraint:** "Do not push to GitHub until explicitly approved."
- **User authorized push** during this session.
- Pushed `slice/office-feedback` to `origin/slice/office-feedback` AND `origin/main`.
- Commits pushed: `a2c17a1`, `dd86198`, `783e4aa`, `482479d`.

---

## 2. COMMITS IN SESSION 16

| Hash | Message |
| :--- | :--- |
| `a2c17a1` | `feat: responsive layout across 4 breakpoints, neon tech db, oracle cloud deployment & query latency tuning` |
| `dd86198` | `fix(health): add /healthz endpoint for Render deployment health check` |
| `783e4aa` | `fix(cors): allow dynamic CORS origin reflection for all Vercel domains` |
| `482479d` | `fix: auto-heal admin RBAC roles on cloud (skip-wipe seed bug)` |

---

## 3. FILES MODIFIED IN SESSION 16

### Backend Files:
1. `backend/app/main.py` — Added `/healthz` endpoint, CORS `allow_origin_regex`.
2. `backend/app/core/config.py` — `cors_origins` property handles JSON arrays, strips `*`.
3. `backend/app/core/db.py` — Dialect normalization (`postgresql://` → `postgresql+psycopg://`), connection pooling (`pool_recycle=300`, `pool_pre_ping=True`).
4. `backend/app/services/rbac.py` — Auto-heal in `grants_for()` for admin with 0 role assignments.
5. `backend/app/api/auth.py` — `["super_admin"]` fallback for admin roles in `/auth/me`.
6. `backend/seed.py` — Production safety guard in `wipe()`, `--skip-wipe` support.
7. `backend/render.yaml` — Render Blueprint (created).
8. `backend/requirements.txt` — Added `uvicorn[standard]`.

### Frontend Files:
9. `web/src/api/client.ts` — Centralized `API_BASE_URL`, `toMediaUrl()` helper.
10. `web/src/auth/LoginPage.tsx` — Redirect guard checks permissions exist before navigating away.
11. `web/src/App.tsx` — "No screens enabled" fallback with Sign out & Re-login button.
12. `web/src/layout/Shell.tsx` — Mobile off-canvas drawer with backdrop.
13. `web/src/components/ui.tsx` — Responsive Modal padding for mobile.
14. `web/src/pages/Transport.tsx` — 2x2 stat card grid on mobile.
15. `web/src/main.tsx` — QueryClient `staleTime: 30_000`, `gcTime: 300_000`.
16. `web/vercel.json` — Vercel SPA config (created).

---

## 4. LIVE DEPLOYMENT VERIFICATION

```
HEALTHZ: 200 {"status":"ok"}
LOGIN:   200 token_len=159
ME:      roles=["super_admin"], permissions_count=100
         first 5 perms: academics.class.read, academics.class.write, admin.audit.read, admin.role.read, admin.role.write
```

- **Login credentials:** `admin@sunrisepublic.edu` / `Admin@123`
- **Frontend URL:** `https://school-management-system-blush-iota.vercel.app`
- **Backend URL:** `https://school-management-system-12ks.onrender.com`

---

## 5. KNOWN BEHAVIORS & NOTES

1. **Render free tier cold starts:** Render spins down free instances after inactivity (~15 min), causing ~50 second cold starts on first request.
2. **CORS regex is permissive:** `allow_origin_regex=r"https?://.*"` reflects all origins. Acceptable for temporary demo; should be restricted for production.
3. **`--skip-wipe` seed is now safe:** The auto-heal in `grants_for()` ensures admin always gets `super_admin` even if the seed skipped role assignments.
4. **Git push policy changed:** Branch is now pushed to remote. Future agents should push changes to `origin/main` for auto-deploy after user approval.

---

## 6. REPOSITORY STATE

- **Branch:** `slice/office-feedback` (synced with `origin/main`)
- **Latest commit:** `482479d` — `fix: auto-heal admin RBAC roles on cloud (skip-wipe seed bug)`
- **GitHub:** `https://github.com/shivansh2277/School-management-system.git`
- **All tests green, 0 typecheck errors, live deployment verified.**
