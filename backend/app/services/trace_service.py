"""Persistence helpers for provider-independent request execution traces."""

import json
from collections.abc import Mapping
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.database import SessionLocal, initialize_database
from app.database.models import RequestLog, RequestTraceEvent


def record_event(request_id: int, stage: str, event: str,
                 metadata: Mapping[str, Any] | None = None, *,
                 session: Session | None = None) -> RequestTraceEvent:
    """Persist a JSON-compatible event for an existing logged request."""
    payload = dict(metadata or {})
    encoded = json.dumps(payload, allow_nan=False)
    initialize_database()
    owns_session = session is None
    db = session or SessionLocal()
    try:
        if db.get(RequestLog, request_id) is None:
            raise ValueError(f"Request {request_id} does not exist")
        row = RequestTraceEvent(request_id=request_id, stage=stage, event=event, metadata_json=encoded)
        db.add(row)
        db.commit()
        db.refresh(row)
        return row
    except Exception:
        db.rollback()
        raise
    finally:
        if owns_session:
            db.close()


def get_trace(request_id: int) -> list[dict[str, Any]]:
    """Return events ordered by timestamp and insertion ID."""
    initialize_database()
    with SessionLocal() as db:
        rows = db.scalars(select(RequestTraceEvent).where(
            RequestTraceEvent.request_id == request_id
        ).order_by(RequestTraceEvent.timestamp, RequestTraceEvent.id)).all()
    return [{"request_id": row.request_id, "timestamp": row.timestamp, "stage": row.stage,
             "event": row.event, "metadata": json.loads(row.metadata_json)} for row in rows]
