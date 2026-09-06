# Deploying Sunrise ERP

The target is a single **Oracle Cloud Always Free** ARM instance running the
whole stack under Docker Compose: API, worker, PostgreSQL and MinIO. That is
enough for one school and comfortably enough for several.

Vercel is no longer the target. It has no scheduler and no worker, and this
system needs both — see `docs/ERP_BLUEPRINT.md` §0.1.

## Before you start

Two things about the free tier are worth knowing up front:

- Oracle **halved** the Always Free ARM allocation in July 2026, from
  4 OCPU / 24 GB to **2 OCPU / 12 GB**, with no announcement. Still free, still
  200 GB of block storage, and still enough — but they have changed it once.
- ARM capacity is genuinely hard to get in some regions. "Out of capacity" on
  instance creation is common and people retry for days.

**Free hosting is right for building and demoing, and wrong the day a real
school's records live on it.** Budget roughly ₹400–500/month for a small VPS
before the first paying school. The stack is plain Docker on plain Linux, so
moving is a redeploy rather than a rewrite.

## Setup

```bash
git clone <repo> && cd school-management-system
cp .env.example .env
openssl rand -hex 32          # paste into JWT_SECRET
# set POSTGRES_PASSWORD and MINIO_PASSWORD too

docker compose up -d
docker compose exec api alembic upgrade head
docker compose exec api python seed.py        # demo data only
```

The API is on `:8000`, the MinIO console on `127.0.0.1:9001` (loopback only),
and PostgreSQL on `127.0.0.1:5433` — 5433 rather than 5432 so it does not
collide with a natively installed PostgreSQL.

## What runs

| Service | Purpose |
|---|---|
| `api` | FastAPI. Never runs jobs, so a slow report cannot time out a request. |
| `worker` | Drains the job queue and ticks the schedule. Same image as `api`. |
| `db` | PostgreSQL 18. Also holds the job queue — no Redis, no broker. |
| `storage` | MinIO, S3-compatible, for student and admission documents. |

Scheduled out of the box: `fees.overdue_sweep` nightly at 02:00 IST, and
`system.heartbeat` hourly as a liveness signal.

```bash
docker compose logs -f worker      # should show a heartbeat every hour
docker compose exec api python worker.py --once   # drain by hand
```

## Backups

**An untested backup is not a backup.** Restore into a scratch database and
check the row counts before trusting it.

```bash
# Back up
docker compose exec -T db pg_dump -U sunrise sunrise | gzip > backup-$(date +%F).sql.gz

# Restore into a scratch database and verify
zcat backup-2026-09-06.sql.gz | docker compose exec -T db psql -U sunrise -d postgres \
  -c "CREATE DATABASE restore_check" && \
zcat backup-2026-09-06.sql.gz | docker compose exec -T db psql -U sunrise -d restore_check
docker compose exec -T db psql -U sunrise -d restore_check \
  -c "SELECT count(*) FROM students; SELECT count(*) FROM fee_payments;"
```

Put the `pg_dump` line in cron nightly and copy the file off the box. A backup
that only exists on the machine it backs up is not one either.

## Still to do before real school data

- TLS in front of the API (Caddy or nginx; Let's Encrypt).
- Move off the free tier.
- Rotate `JWT_SECRET` and every seeded password; the demo passwords are public.
- Take down or make read-only the writable public demo.
