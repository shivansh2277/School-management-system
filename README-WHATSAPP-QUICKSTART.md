# Sunrise School ERP — Quickstart Guide

Welcome to the **Sunrise School ERP** codebase. This archive contains the full-stack multi-tenant school enterprise system:
1. **Backend API**: Python FastAPI, SQLAlchemy, Alembic, PostgreSQL / SQLite.
2. **Web ERP & Public Website**: React 18, TypeScript, Tailwind CSS, Vite.
3. **Mobile App**: React Native, Expo SDK, TypeScript.
4. **Documentation**: Architecture guides, database data flows, and viva guides in `docs/`.

---

## 1. Quick Setup & Execution

### A. Backend API (FastAPI)
```bash
cd backend

# 1. Create and activate a Python virtual environment
python -m venv .venv

# On Windows:
.venv\Scripts\activate
# On macOS / Linux:
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt
# (or if using pip editable: pip install -e .)

# 3. Run database migrations & seed demo data
alembic upgrade head
python seed.py

# 4. Start the backend API server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
- **API Base URL:** `http://localhost:8000`
- **Interactive Swagger Docs:** `http://localhost:8000/docs`

---

### B. Web ERP Portal & Public Website (React + Vite)
Both the public school website and the admin management portal run together on the Vite dev server:

```bash
cd web

# 1. Install dependencies
npm install

# 2. Start the Vite development server
npm run dev
```
- **Local Dev URL:** `http://localhost:5173`

#### Available Routes:
- **Public School Website:**
  - Homepage: `http://localhost:5173/#/`
  - About Us: `http://localhost:5173/#/about`
  - Academics: `http://localhost:5173/#/academics`
  - Admissions Overview: `http://localhost:5173/#/admissions`
  - Online Application Form: `http://localhost:5173/#/apply`
  - Facilities: `http://localhost:5173/#/facilities`
- **Admin ERP Portal:**
  - Login Screen: `http://localhost:5173/#/login`
  - Main Dashboard: `http://localhost:5173/#/dashboard`

---

### C. Mobile App (React Native / Expo)
```bash
cd mobile

# 1. Install dependencies
npm install

# 2. Start the Expo development server
npx expo start
```
- Scan the QR code in your terminal with the **Expo Go** app on iOS or Android, or press `a` for Android Emulator / `w` for web preview.

---

## 2. Key Demo Logins & Passwords

All demo accounts share the password: **`Admin@123`**

| Role | Email / Login ID | Password | Access Scope |
|---|---|---|---|
| **Admin / Principal** | `admin@sunrisepublic.edu` | `Admin@123` | Full administrative governance & executive dashboard |
| **Transport In-Charge** | `transport@sunrisepublic.edu` | `Admin@123` | Dedicated transport routes, stops, vehicle documents, and bus assignments |
| **Accounts Officer** | `accounts@sunrisepublic.edu` | `Admin@123` | Student fee ledger, defaulters, fee structure setup, period close, payroll |
| **Admission Officer** | `admission@sunrisepublic.edu` | `Admin@123` | Full admission pipeline (enquiries, applications, merit list, waitlist, reports) |
| **Receptionist** | `receptionist@sunrisepublic.edu` | `Admin@123` | Found & Lost, gate passes, meeting slips, school directory, fee counter |
| **Fee Counter Clerk** | `counter@sunrisepublic.edu` | `Admin@123` | Segregated daily fee collection ledger |

---

## 3. Architecture & Documentation Guides
See the `docs/` folder for comprehensive PDF and Markdown documentation:
- `docs/Sunrise-ERP-Operational-Data-Flows.pdf`: Complete database table-to-table data flows.
- `docs/Sunrise-ERP-Admission-Demo-Guide.pdf`: Digital admission walkthrough and dossier guide.
- `docs/Sunrise-ERP-Database-Tables-and-Features.pdf`: Comprehensive mapping of all 93 tables.
- `docs/Sunrise-ERP-Database-Viva-100.pdf`: 100 project-specific viva questions and answers.
- `SINGLE_SOURCE_OF_TRUTH.md`: Project directives and technical state metrics.
- `CLAUDE.md`: System reference and test suite commands.
