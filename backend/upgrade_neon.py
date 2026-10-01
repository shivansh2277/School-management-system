import os
import subprocess
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent
neon_env_file = backend_dir / ".env.neon"

if not neon_env_file.exists():
    print("Error: .env.neon file not found!")
    sys.exit(1)

# Read DATABASE_URL from .env.neon
db_url = ""
for line in neon_env_file.read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if line.startswith("DATABASE_URL="):
        db_url = line[len("DATABASE_URL="):].strip().strip('"').strip("'")
        break

if not db_url or db_url == "your_neon_tech_connection_string_here":
    print("Error: DATABASE_URL is empty in .env.neon. Please paste your connection string into .env.neon and save it.")
    sys.exit(1)

# Normalize postgresql:// to postgresql+psycopg://
if db_url.startswith("postgresql://"):
    normalized_url = "postgresql+psycopg://" + db_url[len("postgresql://"):]
elif db_url.startswith("postgres://"):
    normalized_url = "postgresql+psycopg://" + db_url[len("postgres://"):]
else:
    normalized_url = db_url

env = os.environ.copy()
env["DATABASE_URL"] = normalized_url
python_exe = sys.executable

print("1. Running alembic stamp f6a7b8c9d0e1...")
res = subprocess.run([python_exe, "-m", "alembic", "stamp", "f6a7b8c9d0e1"], env=env, cwd=backend_dir)
if res.returncode != 0:
    print("Failed to stamp alembic.")
    sys.exit(res.returncode)

print("\n2. Running alembic upgrade head...")
res = subprocess.run([python_exe, "-m", "alembic", "upgrade", "head"], env=env, cwd=backend_dir)
if res.returncode != 0:
    print("Failed to upgrade alembic schema.")
    sys.exit(res.returncode)

print("\n3. Running seed.py --force...")
res = subprocess.run([python_exe, "seed.py", "--force"], env=env, cwd=backend_dir)
if res.returncode != 0:
    print("Failed to seed database.")
    sys.exit(res.returncode)

print("\n4. Verifying database connection...")
from app.core.db import make_engine
from sqlalchemy.orm import Session
from app.models import School

engine = make_engine(normalized_url)
with Session(engine) as session:
    school = session.query(School).first()
    if school:
        print(f"\nSUCCESS: Connected School on Neon Tech: '{school.name}' ({school.code})")
    else:
        print("\nNotice: School table query returned None.")
