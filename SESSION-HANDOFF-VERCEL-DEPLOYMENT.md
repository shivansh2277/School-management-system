# SESSION-HANDOFF: Vercel Website Update & Neon Database Guide

> **Project:** Sunrise School ERP  
> **Target Website URL (Fixed Production Link):** `https://school-management-system-blush-iota.vercel.app`  
> **Backend API (Render):** `https://school-management-system-12ks.onrender.com`  
> **Backend Health Endpoint:** `https://school-management-system-12ks.onrender.com/healthz`  
> **Database:** Neon Tech Serverless PostgreSQL (`postgresql+psycopg://`)  
> **GitHub Repository:** `https://github.com/shivansh2277/School-management-system.git`  
> **Vercel & Render Tracked Branch:** `main`  
> **Local Working Branch:** `slice/office-feedback`  
> **Local Project Root:** `c:\Users\SHIVANSH\OneDrive\Documents\AGENTS\school-management-system`  

---

## 1. Executive Summary

This session handoff provides everything needed to:
1. **Update your live website on Vercel** to the exact same URL (`https://school-management-system-blush-iota.vercel.app`).
2. **Upgrade your database on Neon Tech** (apply new Alembic migrations, add new columns/tables, and update demo seed data) using PowerShell commands directly in your project folder.
3. Understand how the database, backend (Render), and frontend (Vercel) interact.

---

## 2. Part 1: How to Update Your Website on Vercel on the Same Link

Because Vercel is connected directly to your GitHub repository and monitors the **`main`** branch, updating your live website requires **zero manual file uploads** and **zero configuration changes**. Pushing the latest commits to GitHub automatically triggers a fresh build and instantly deploys it to the same link.

### Method 1: The Standard & Recommended Way (Git Push to `main`)

Open PowerShell in your project root:

```powershell
# 1. Navigate to your project root
cd c:\Users\SHIVANSH\OneDrive\Documents\AGENTS\school-management-system

# 2. Stage and commit all your latest changes
git add .
git commit -m "feat: deploy latest website features to production"

# 3. Push your branch directly to GitHub's main branch
git push origin slice/office-feedback:main
```

> **What happens immediately after this command:**
> 1. GitHub receives the new commits on `main`.
> 2. Vercel automatically detects the push via GitHub Webhook.
> 3. Vercel runs `npm run build` in the `web` directory.
> 4. In ~60 seconds, your site at `https://school-management-system-blush-iota.vercel.app` updates automatically to the exact same link!
> 5. Render.com also receives the push and keeps the backend API completely in sync.

---

### Method 2: Manual Trigger via Vercel Dashboard

If your latest code is already pushed to GitHub:
1. Open your browser and go to [vercel.com/dashboard](https://vercel.com/dashboard).
2. Click on your project: **`school-management-system-blush-iota`**.
3. Click on the **Deployments** tab.
4. On the latest deployment row, click the **three dots (`...`)** on the right side.
5. Select **Redeploy** and click **Redeploy**.

---

### Method 3: Deploy via Vercel CLI (From PowerShell)

If you ever want to build and deploy directly from your local terminal:
```powershell
cd c:\Users\SHIVANSH\OneDrive\Documents\AGENTS\school-management-system\web
npx vercel --prod
```

---

## 3. Part 2: How to Upgrade Your Neon Tech Database Using PowerShell

When you add new database tables, add new columns, or update the demo seed data, follow these exact instructions using PowerShell.

### Your Project Folders:
- **Project Root:** `c:\Users\SHIVANSH\OneDrive\Documents\AGENTS\school-management-system`
- **Backend Folder (where Alembic and Seed live):** `c:\Users\SHIVANSH\OneDrive\Documents\AGENTS\school-management-system\backend`
- **Python Virtualenv:** `..\.venv\Scripts\python.exe` (from `backend`)

---

### Step-by-Step PowerShell Database Upgrade:

#### 1. Open PowerShell and navigate to the backend folder
```powershell
cd c:\Users\SHIVANSH\OneDrive\Documents\AGENTS\school-management-system\backend
```

#### 2. Set your Neon Tech connection string
> ⚠️ **Important Driver Rule**: Always use `postgresql+psycopg://` instead of `postgresql://` so SQLAlchemy uses the modern `psycopg` (v3) driver installed in your virtual environment.

```powershell
$env:DATABASE_URL = "postgresql+psycopg://neondb_owner:YOUR_PASSWORD@ep-YOUR-ENDPOINT.neon.tech/neondb?sslmode=require"
```

#### 3. Apply Schema Migrations (Add New Tables & Columns)
To apply any new Alembic migration files to Neon Tech:
```powershell
..\.venv\Scripts\python.exe -m alembic upgrade head
```
*(If you ever encounter a conflict with pre-existing tables, stamp the previous migration first, e.g.: `..\.venv\Scripts\python.exe -m alembic stamp f6a7b8c9d0e1` and then run `upgrade head`)*

#### 4. Update or Re-populate Seed Data
To populate or update demo seed data on Neon Tech:
```powershell
..\.venv\Scripts\python.exe seed.py --force
```
> **Why `--force` is required:**
> `seed.py` has a built-in safety guard to prevent accidental data wipes on production/cloud hosts (`neon.tech`, `rds`, `supabase`). Passing `--force` explicitly confirms you intend to update the demo database on Neon.
>
> **Note on Timing:**
> Seeding Neon Tech over the internet takes ~15–20 minutes because it creates:
> - 224 user accounts with 12-round bcrypt password hashing
> - 5,800 daily attendance records
> - 2,400 exam marks records
> - 300 monthly invoices and 140+ payment allocations
> - Timetables, routes, inventory, and RBAC roles

#### 5. Verify the Connection
```powershell
..\.venv\Scripts\python.exe -c "from app.core.db import engine; from sqlalchemy import text; print('Connected School:', engine.connect().execute(text('SELECT name, code FROM schools')).fetchone())"
```

#### 6. Clear your database key from PowerShell memory (Security)
```powershell
$env:DATABASE_URL = ""
```

---

### Alternative: Automated Runner (`upgrade_neon.py`)

You can also use the automated runner script:
1. Create a temporary file `backend/.env.neon`:
   ```env
   DATABASE_URL=postgresql+psycopg://neondb_owner:YOUR_PASSWORD@ep-YOUR-ENDPOINT.neon.tech/neondb?sslmode=require
   ```
2. Run in PowerShell:
   ```powershell
   cd c:\Users\SHIVANSH\OneDrive\Documents\AGENTS\school-management-system\backend
   ..\.venv\Scripts\python.exe upgrade_neon.py
   ```
3. Delete `backend/.env.neon` when finished:
   ```powershell
   Remove-Item -Path "backend\.env.neon" -Force
   ```

---

## 4. Key Configuration Summary

| Layer | Host / Provider | URL / Connection |
|---|---|---|
| **Website (Frontend)** | Vercel | `https://school-management-system-blush-iota.vercel.app` |
| **Backend API** | Render | `https://school-management-system-12ks.onrender.com` |
| **Database** | Neon Tech | PostgreSQL Serverless (`postgresql+psycopg://`) |
| **Repo** | GitHub | `https://github.com/shivansh2277/School-management-system.git` |
| **Deploy Branch** | GitHub `main` | Linked to Vercel production auto-deployment |
