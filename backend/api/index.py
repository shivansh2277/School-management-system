"""Vercel Python entry point.

Vercel's runtime serves an ASGI app exported as `app`, so this re-exports the
same FastAPI instance `uvicorn` runs locally. No behaviour differs between the
two — only the process model does.
"""

import sys
from pathlib import Path

# The function runs with this file's directory on the path, not the project root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.main import app  # noqa: E402

__all__ = ["app"]
