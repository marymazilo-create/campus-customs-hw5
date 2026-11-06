"""Append-only audit trail for every step of every agent loop."""

import json
import os
from datetime import datetime, timezone

from config import AUDIT_PATH, MODEL_NAME
from models import AuditEntry

MAX_RESULT_CHARS = 4000


def _shorten(value):
    """Keep very long results from filling the audit file."""
    if isinstance(value, str) and len(value) > MAX_RESULT_CHARS:
        return value[:MAX_RESULT_CHARS] + " ...[shortened]"
    return value


def _read_trail() -> list:
    """Read the trail. A damaged file stops the run so nothing goes unrecorded."""
    if not AUDIT_PATH.exists() or not AUDIT_PATH.read_text(encoding="utf-8").strip():
        return []
    trail = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    if not isinstance(trail, list):
        raise ValueError(f"{AUDIT_PATH} must hold a JSON list.")
    return trail


def record(**fields) -> None:
    """Add one entry to output/audit_trail.json. Earlier entries are always kept."""
    fields["result"] = _shorten(fields.get("result"))
    fields["text"] = _shorten(fields.get("text"))
    fields.setdefault("model", MODEL_NAME)
    entry = AuditEntry(
        timestamp=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        **fields,
    )

    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    trail = _read_trail()
    trail.append(entry.model_dump())

    temporary = AUDIT_PATH.with_suffix(".tmp")
    temporary.write_text(json.dumps(trail, indent=2, default=str), encoding="utf-8")
    os.replace(temporary, AUDIT_PATH)
