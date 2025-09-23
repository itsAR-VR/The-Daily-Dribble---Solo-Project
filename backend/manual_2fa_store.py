"""Thread-safe in-memory store for manual 2FA codes.

Selenium automation can block waiting for a human-supplied 2FA code while the
FastAPI API receives the code via `/manual-2fa/{job_id}`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Event, Lock
from typing import Dict, Optional


@dataclass
class _ManualCodeEntry:
    event: Event = field(default_factory=Event)
    code: Optional[str] = None
    submitted_at: Optional[datetime] = None
    platform: Optional[str] = None
    status: str = "waiting"


_lock = Lock()
_codes: Dict[str, _ManualCodeEntry] = {}


def prepare(job_id: str, platform: Optional[str] = None) -> None:
    """Ensure a manual entry exists for the given job."""
    with _lock:
        entry = _codes.get(job_id)
        if entry is None:
            entry = _ManualCodeEntry(platform=platform)
            _codes[job_id] = entry
        else:
            entry.platform = platform or entry.platform
            entry.status = "waiting"
            entry.code = None
            entry.event.clear()
            entry.submitted_at = None


def submit_code(job_id: str, code: str) -> None:
    now = datetime.now(timezone.utc)
    with _lock:
        entry = _codes.get(job_id)
        if entry is None:
            entry = _ManualCodeEntry()
            _codes[job_id] = entry
        entry.code = code.strip()
        entry.submitted_at = now
        entry.status = "submitted"
        entry.event.set()


def wait_for_code(job_id: str, timeout: float | None = None) -> Optional[str]:
    with _lock:
        entry = _codes.get(job_id)
        if entry is None:
            entry = _ManualCodeEntry()
            _codes[job_id] = entry
        # Return immediately if already submitted
        if entry.code:
            return entry.code
        event = entry.event
    if event.wait(timeout or 0):
        with _lock:
            entry = _codes.get(job_id)
            return entry.code if entry else None
    return None


def fetch_and_clear(job_id: str) -> Optional[str]:
    with _lock:
        entry = _codes.get(job_id)
        if not entry:
            return None
        code = entry.code
        entry.code = None
        entry.status = "used"
        entry.event.clear()
        return code


def get_status(job_id: str) -> dict:
    with _lock:
        entry = _codes.get(job_id)
        if not entry:
            return {"job_id": job_id, "status": "unknown"}
        return {
            "job_id": job_id,
            "status": entry.status,
            "platform": entry.platform,
            "submitted_at": entry.submitted_at.isoformat() if entry.submitted_at else None,
            "has_code": bool(entry.code),
        }


def clear(job_id: str) -> None:
    with _lock:
        _codes.pop(job_id, None)
