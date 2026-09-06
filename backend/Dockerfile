# Runs both the API and the worker: same image, different command, so the two
# can never drift apart in dependencies.
#
# python:3.13-slim is multi-arch, which matters because the target is an Oracle
# Cloud Ampere (ARM64) box while development happens on x86.
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Kolkata

WORKDIR /app

# Dependencies first, so a code change does not invalidate the install layer.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir "uvicorn[standard]"

COPY . .

# Never run as root: a container escape should not land on a root shell.
RUN useradd --create-home --uid 10001 sunrise && chown -R sunrise:sunrise /app
USER sunrise

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health', timeout=4).status == 200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
