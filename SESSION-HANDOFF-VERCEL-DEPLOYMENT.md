# SESSION-HANDOFF: Vercel Website Update & Deployment Guide

> **Project:** Sunrise School ERP  
> **Target URL (Fixed Production Link):** `https://school-management-system-blush-iota.vercel.app`  
> **Backend API (Render):** `https://school-management-system-12ks.onrender.com`  
> **Database:** Neon Tech Serverless PostgreSQL  
> **GitHub Repository:** `https://github.com/shivansh2277/School-management-system.git`  
> **Vercel Tracked Branch:** `main`  
> **Local Working Branch:** `slice/office-feedback`  

---

## 1. Executive Summary

This handoff document provides the complete, authoritative guide to updating your live web project on Vercel so that all your vast new features (Public Website Pages, User Access Management, Attendance, Admissions, Timetables, etc.) go live on the exact same production URL:
👉 **`https://school-management-system-blush-iota.vercel.app`**

Because Vercel is connected directly to your GitHub repository and monitors the **`main`** branch, updating your live website requires **zero manual file uploads** and **zero configuration changes**. Pushing the latest commits to GitHub automatically triggers a fresh build and instantly deploys it to the same link.

---

## 2. Pre-Deployment Verification (Already Tested & Verified)

Before deploying to Vercel, the local web build was tested and confirmed **100% clean**:
- **TypeScript Typecheck:** Passed with `0 errors` (`npx tsc -b`)
- **Vite Production Bundler:** Built in `21.62s` without errors (`dist/` directory cleanly generated)
- **Vercel Routing Configuration (`web/vercel.json`):** Verified with SPA rewrite rule `source: "/(.*)" -> destination: "/index.html"` to guarantee client-side React routes work on direct link refresh without 404s.

---

## 3. Step-by-Step Instructions: How to Update Vercel Yourself

Follow these simple steps whenever you want to update your live website on Vercel.

### Method 1: The Standard & Recommended Way (Git Push to `main`)

Open PowerShell or terminal in your project root (`c:\Users\SHIVANSH\OneDrive\Documents\AGENTS\school-management-system`) and run:

#### Step 1: Stage and commit all your latest changes
```powershell
# Navigate to project root
cd c:\Users\SHIVANSH\OneDrive\Documents\AGENTS\school-management-system

# Stage all files
git add .

# Create a clear commit message
git commit -m "feat: update web app with latest features and pages for production"
```

#### Step 2: Push your branch directly to GitHub's `main` branch
Since your Vercel project is linked to GitHub's `main` branch, push your current `slice/office-feedback` branch directly into `origin/main`:
```powershell
git push origin slice/office-feedback:main
```

> **What happens immediately after this command:**
> 1. GitHub receives the new commits.
> 2. Vercel automatically detects the push via GitHub Webhook.
> 3. Vercel runs `npm run build` in the `web` directory.
> 4. In ~60 seconds, your site at `https://school-management-system-blush-iota.vercel.app` updates automatically!
> 5. Render.com also receives the push and keeps the backend API completely in sync.

#### Step 3 (Optional): Keep your local `main` branch synced
```powershell
git checkout main
git merge slice/office-feedback
git checkout slice/office-feedback
```

---

### Method 2: Instant Redeploy from the Vercel Dashboard

If your latest code is already on GitHub, or if you want to rebuild without touching the terminal:

1. Open your browser and go to [vercel.com/dashboard](https://vercel.com/dashboard).
2. Click on your project: **`school-management-system-blush-iota`**.
3. Click on the **Deployments** tab at the top.
4. On the latest deployment row, click the **three dots (`...`)** on the right side.
5. Select **Redeploy**.
6. Check **"Include existing build cache"** (or uncheck to do a 100% clean rebuild) and click **Redeploy**.
7. Vercel will build and deploy to the exact same link in under 1 minute.

---

### Method 3: Direct Deploy via Vercel CLI (Optional Alternative)

If you ever want to deploy directly from your computer without pushing to GitHub first:

1. In PowerShell, navigate to the `web/` folder:
   ```powershell
   cd c:\Users\SHIVANSH\OneDrive\Documents\AGENTS\school-management-system\web
   ```
2. Run:
   ```powershell
   npx vercel --prod
   ```
3. If prompted to link to an existing project:
   - "Set up and deploy?": **Yes**
   - "Which scope?": Select your personal account
   - "Link to existing project?": **Yes**
   - "What's the name of existing project?": **`school-management-system-blush-iota`**
4. Vercel CLI will upload the local build and point the production alias to your link.

---

## 4. Key Configuration Checklist (Do Not Modify)

To ensure the deployment never breaks:
1. **Production URL:** `https://school-management-system-blush-iota.vercel.app` (Managed under Vercel Project Settings → Domains).
2. **Environment Variable on Vercel:**
   - Key: `VITE_API_URL`
   - Value: `https://school-management-system-12ks.onrender.com`
   - Target: Production, Preview, Development
3. **Root Directory on Vercel:** Set to `web`.
4. **Build Command on Vercel:** `npm run build` (or Vite framework default).
5. **Output Directory on Vercel:** `dist`.
6. **SPA Routing (`web/vercel.json`):**
   ```json
   {
     "framework": "vite",
     "buildCommand": "npm run build",
     "outputDirectory": "dist",
     "rewrites": [
       {
         "source": "/(.*)",
         "destination": "/index.html"
       }
     ]
   }
   ```

---

## 5. Summary of Live Links

| Component | Provider | Live URL |
| :--- | :--- | :--- |
| **Web Application** | Vercel | `https://school-management-system-blush-iota.vercel.app` |
| **Backend API** | Render | `https://school-management-system-12ks.onrender.com` |
| **Backend Health** | Render | `https://school-management-system-12ks.onrender.com/healthz` |
| **Database** | Neon Tech | Serverless PostgreSQL |
| **GitHub Repo** | GitHub | `https://github.com/shivansh2277/School-management-system.git` |
