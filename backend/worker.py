"""Background worker: runs due jobs and ticks the schedule.

Started as its own container alongside the API. The API process never runs jobs
itself, so a slow report or a hung email provider cannot make a request time out.

    python worker.py            # loop forever
    python worker.py --once     # drain the queue and exit (used by CI)
"""

from __future__ import annotations

import argparse
import logging
import signal
import sys
import time
from datetime import UTC, datetime

import app.jobs  # noqa: F401  - importing registers the handlers
from app.core.db import SessionLocal
from app.services import jobs

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
)
log = logging.getLogger("worker")

_stop = False


def _handle_signal(signum, _frame):
    """Finish the job in hand, then exit. Killing a worker mid-job would leave
    it `running` forever."""
    global _stop
    _stop = True
    log.info("signal %s received, stopping after the current job", signum)


def run(once: bool = False, poll_seconds: float = 1.0) -> int:
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, _handle_signal)

    processed = 0
    last_tick = 0.0

    while not _stop:
        with SessionLocal() as db:
            # Check the schedule about once a minute rather than every poll.
            if time.monotonic() - last_tick > 60:
                queued = jobs.tick_schedules(db, datetime.now(UTC))
                if queued:
                    log.info("scheduler queued %s job(s)", len(queued))
                last_tick = time.monotonic()

            processed += jobs.drain(db)

        if once:
            break
        time.sleep(poll_seconds)

    log.info("worker stopped after %s job(s)", processed)
    return processed


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true", help="drain the queue and exit")
    parser.add_argument("--poll", type=float, default=1.0, help="seconds between polls")
    args = parser.parse_args()
    sys.exit(0 if run(once=args.once, poll_seconds=args.poll) >= 0 else 1)
