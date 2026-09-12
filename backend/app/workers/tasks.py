"""Async job placeholders for OCR, RAG ingestion, exports, reminders and billing reconciliation."""


def enqueue_job(job_type: str, payload: dict[str, object]) -> dict[str, object]:
    return {"job_id": f"job_stub_{job_type}", "status": "queued", "payload": payload}

