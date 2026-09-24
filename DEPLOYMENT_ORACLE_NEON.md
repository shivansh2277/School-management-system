# Production Deployment Guide: Oracle Cloud & Neon Tech

This guide details the complete deployment process for hosting the **Sunrise School ERP** on **Oracle Cloud Infrastructure (OCI)** with **Neon Tech** as the serverless PostgreSQL cloud database.

---

## 1. Architecture Overview

```
                      +---------------------------------------+
                      |               End User                |
                      |   (Mobile / Tablet / Laptop / PC)     |
                      +-------------------+-------------------+
                                          |
                                    HTTPS | (Port 443)
                                          v
                      +---------------------------------------+
                      |         Oracle Cloud Compute          |
                      |   +-------------------------------+   |
                      |   |     Nginx Web Server          |   |
                      |   |   - SSL / Let's Encrypt       |   |
                      |   |   - Serves React ERP (SPA)    |   |
                      |   |   - Reverse proxy /api & media|   |
                      |   +---------------+---------------+   |
                      |                   |                   |
                      |   +---------------v---------------+   |
                      |   |     FastAPI / Uvicorn         |   |
                      |   |   - Port 8000 (Internal)      |   |
                      |   |   - Connection pooling (300s) |   |
                      |   |   - Seed safety guards        |   |
                      |   +---------------+---------------+   |
                      +-------------------|-------------------+
                                          |
                        Secure SSL (WAN)  | Port 5432 / PgBouncer
                                          v
                      +---------------------------------------+
                      |         Neon Tech PostgreSQL          |
                      |   - Cloud Serverless PostgreSQL       |
                      |   - Auto-scaling / Branching          |
                      |   - Persistent Data Volume            |
                      +---------------------------------------+
```

---

## 2. Neon Tech Cloud Database Configuration

### Step 2.1: Obtain Neon Connection String
1. Create a project on [Neon Console](https://console.neon.tech/).
2. Copy the connection string. Neon provides URIs formatted like:
   ```
   postgresql://user:password@ep-cool-butterfly-123456.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```
3. **No manual dialect tweaking needed:** The backend engine automatically detects `postgresql://` and converts it to `postgresql+psycopg://` for Psycopg 3 compatibility.

### Step 2.2: Apply Migrations
From the Oracle Cloud compute instance (or locally with the Neon `DATABASE_URL`):
```bash
# In school-management-system/backend
alembic upgrade head
```

### Step 2.3: Safe Database Seeding
The backend seed script (`backend/seed.py`) includes safety guards to protect cloud and production environments:
- **Cloud Guard:** When pointing to `neon.tech` or `oraclecloud`, `wipe()` refuses to truncate existing data unless `--force` or `ALLOW_SEED_WIPE=true` is explicitly provided.
- **Idempotent Population:** Running `python seed.py --skip-wipe` populates default roles, fee heads, academic years, and transport routes without destroying any existing operational records:
```bash
python seed.py --skip-wipe
```

---

## 3. Backend Deployment on Oracle Cloud

### Step 3.1: Backend Environment Configuration (`.env`)
Create `school-management-system/backend/.env`:
```ini
ENVIRONMENT=production
DATABASE_URL=postgresql://user:password@ep-cool-butterfly-123456.us-east-2.aws.neon.tech/neondb?sslmode=require
SECRET_KEY=generate-a-strong-random-hex-key-here
JWT_SECRET=generate-another-strong-random-hex-key-here
CORS_ORIGINS=["https://erp.yourdomain.com", "http://your-oracle-ip"]
ALLOW_SEED_WIPE=false
```

### Step 3.2: Run Backend with Systemd
Create `/etc/systemd/system/sunrise-backend.service`:
```ini
[Unit]
Description=Sunrise School ERP FastAPI Backend
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/school-management-system/backend
ExecStart=/home/ubuntu/school-management-system/backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=5
EnvironmentFile=/home/ubuntu/school-management-system/backend/.env

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable sunrise-backend
sudo systemctl start sunrise-backend
```

---

## 4. Frontend Deployment on Oracle Cloud

### Step 4.1: Production Build
In `school-management-system/web`:
```bash
# Set production API URL
export VITE_API_URL="https://erp.yourdomain.com"
npm run build
```
This produces optimized production static assets in `web/dist/`.

### Step 4.2: Nginx Web Server Configuration
Configure `/etc/nginx/sites-available/sunrise-erp`:
```nginx
server {
    listen 80;
    server_name erp.yourdomain.com;

    # Gzip Compression for maximum speed over cloud WAN
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # Frontend SPA
    location / {
        root /home/ubuntu/school-management-system/web/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
        expires 1d;
        add_header Cache-Control "public, no-cache";
    }

    # API Proxy
    location /admin/ {
        proxy_pass http://127.0.0.1:8000/admin/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /auth/ {
        proxy_pass http://127.0.0.1:8000/auth/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /media/ {
        proxy_pass http://127.0.0.1:8000/media/;
        proxy_set_header Host $host;
    }
}
```

Enable site and restart Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/sunrise-erp /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 4.3: Secure with HTTPS (Let's Encrypt)
```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d erp.yourdomain.com
```

---

## 5. Performance Optimizations Active

1. **WAN Latency Defense:**
   - **React Query 30s Freshness (`staleTime: 30_000`):** Prevents UI network stalls when switching tabs.
   - **Connection Pool Recycling (`pool_recycle=300`, `pool_pre_ping=True`):** Drops stale serverless connections before they cause 500 errors.
2. **N+1 Query Batching:**
   - In `backend/app/services/fees.py`, `defaulters()` executes in 4 bulk queries rather than 3,000+ individual round trips.
3. **Zero Horizontal Layout Drift:**
   - Off-canvas drawer and responsive grids verified at 390px, 768px, 1280px, and 1440px.
