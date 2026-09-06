"""Object storage behind a small interface.

Two backends. `S3Storage` talks to anything S3-compatible — MinIO in the compose
stack, real S3 later — through the `minio` client, which is 94 KB against
botocore's ~100 MB installed and does exactly this one job. `LocalStorage`
writes to a directory so the tests and a bare `uvicorn` need no running bucket.

Callers never learn which one they have, and never receive a permanent URL:
`presigned_url` issues a short-lived one *after* the caller has done its own
permission check (ERP_BLUEPRINT §3.8).
"""

from __future__ import annotations

import hashlib
import shutil
import uuid
from datetime import timedelta
from pathlib import Path
from typing import BinaryIO, Protocol

from app.core.config import settings

# Deliberately narrow: what a school actually uploads. Anything executable is
# absent by design — this list is a security control, not a convenience.
ALLOWED_MIME = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

MAX_BYTES = 10 * 1024 * 1024  # a scanned certificate is well under this


class StorageError(RuntimeError):
    pass


def build_key(school_id: int, owner_type: str, owner_id: int, filename: str) -> str:
    """Keys are opaque and unguessable.

    A predictable key (`students/17/birth_certificate.pdf`) plus a
    misconfigured bucket is a directory of children's documents, so the random
    component stays even though access is signed.
    """
    suffix = Path(filename).suffix.lower()[:10]
    return f"{school_id}/{owner_type}/{owner_id}/{uuid.uuid4().hex}{suffix}"


def checksum(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class Storage(Protocol):
    def put(self, key: str, data: bytes, mime_type: str) -> None: ...
    def get(self, key: str) -> bytes: ...
    def delete(self, key: str) -> None: ...
    def presigned_url(self, key: str, expires_seconds: int = 300) -> str: ...
    def exists(self, key: str) -> bool: ...


class LocalStorage:
    """Filesystem backend for tests and for running without a bucket.

    `presigned_url` returns an API path rather than a signed URL, because there
    is nothing to sign against — the API streams the bytes after checking
    permission, which is the same guarantee by a different route.
    """

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        # Keys are generated, never user-supplied, but a traversal here would
        # write anywhere on disk so it is checked anyway.
        p = (self.root / key).resolve()
        if not str(p).startswith(str(self.root.resolve())):
            raise StorageError("Refusing a key that escapes the storage root")
        return p

    def put(self, key: str, data: bytes, mime_type: str) -> None:
        p = self._path(key)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)

    def get(self, key: str) -> bytes:
        p = self._path(key)
        if not p.exists():
            raise StorageError(f"No such object: {key}")
        return p.read_bytes()

    def delete(self, key: str) -> None:
        p = self._path(key)
        if p.exists():
            p.unlink()

    def exists(self, key: str) -> bool:
        return self._path(key).exists()

    def presigned_url(self, key: str, expires_seconds: int = 300) -> str:
        return f"/documents/raw/{key}"

    def clear(self) -> None:  # pragma: no cover - test helper
        shutil.rmtree(self.root, ignore_errors=True)
        self.root.mkdir(parents=True, exist_ok=True)


class S3Storage:
    """Anything S3-compatible: MinIO in compose, S3 or OCI Object Storage later."""

    def __init__(self, endpoint: str, access_key: str, secret_key: str, bucket: str):
        from minio import Minio  # imported here so tests need no client at all

        secure = endpoint.startswith("https://")
        host = endpoint.split("://", 1)[-1]
        self.bucket = bucket
        self.client = Minio(
            host, access_key=access_key, secret_key=secret_key, secure=secure
        )
        if not self.client.bucket_exists(bucket):
            self.client.make_bucket(bucket)

    def put(self, key: str, data: bytes, mime_type: str) -> None:
        from io import BytesIO

        self.client.put_object(
            self.bucket, key, BytesIO(data), length=len(data), content_type=mime_type
        )

    def get(self, key: str) -> bytes:
        response = self.client.get_object(self.bucket, key)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    def delete(self, key: str) -> None:
        self.client.remove_object(self.bucket, key)

    def exists(self, key: str) -> bool:
        try:
            self.client.stat_object(self.bucket, key)
            return True
        except Exception:  # noqa: BLE001 - any failure to stat means "treat as absent"
            return False

    def presigned_url(self, key: str, expires_seconds: int = 300) -> str:
        return self.client.presigned_get_object(
            self.bucket, key, expires=timedelta(seconds=expires_seconds)
        )


_backend: Storage | None = None


def get_storage() -> Storage:
    """One backend per process, chosen by configuration.

    No endpoint configured means local files, so a developer or the test suite
    never needs a bucket running to work on anything else.
    """
    global _backend
    if _backend is None:
        if settings.STORAGE_ENDPOINT:
            _backend = S3Storage(
                settings.STORAGE_ENDPOINT,
                settings.STORAGE_ACCESS_KEY,
                settings.STORAGE_SECRET_KEY,
                settings.STORAGE_BUCKET,
            )
        else:
            _backend = LocalStorage(settings.STORAGE_LOCAL_PATH)
    return _backend


def reset_storage() -> None:  # pragma: no cover - test helper
    global _backend
    _backend = None


def validate_upload(filename: str, mime_type: str, data: bytes) -> None:
    """Reject at the boundary, before anything is written.

    The MIME type is checked against an allow-list rather than a deny-list: a
    deny-list is a list of the attacks someone already thought of.
    """
    if mime_type not in ALLOWED_MIME:
        raise StorageError(
            f"{mime_type} is not an accepted document type "
            f"({', '.join(sorted(ALLOWED_MIME))})"
        )
    if not data:
        raise StorageError("The uploaded file is empty")
    if len(data) > MAX_BYTES:
        raise StorageError(
            f"File is {len(data) // 1024 // 1024} MB; the limit is "
            f"{MAX_BYTES // 1024 // 1024} MB"
        )
    if not filename.strip():
        raise StorageError("A file name is required")
