import base64
import json
import logging
import os
from hashlib import sha256
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.cloud import firestore
from google.oauth2 import id_token

from .agent import process_enquiry
from .gmail_events import resolve_gmail_notification
from .models import EnquiryEvent, WorkflowResult

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("brief2booked")

app = FastAPI(
    title="Brief2Booked Agent API",
    version="1.1.0",
    docs_url="/api/docs" if os.getenv("ENABLE_API_DOCS", "false").lower() == "true" else None,
    redoc_url=None,
)


@app.exception_handler(Exception)
async def unhandled_exception(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled Brief2Booked error", exc_info=exc)
    return JSONResponse(status_code=500, content={"detail": "The workflow could not be completed."})


@app.get("/health")
async def health() -> dict:
    return {
        "status": "healthy",
        "agent": "brief2booked",
        "runtime": "cloud-run",
        "model": os.getenv("GEMINI_MODEL", "gemini-3.5-flash"),
        "project": os.getenv("GOOGLE_CLOUD_PROJECT", "not-configured"),
    }


@app.post("/v1/demo", response_model=WorkflowResult)
async def demo() -> WorkflowResult:
    event = EnquiryEvent(
        event_id="demo-ubuntu-engineering",
        source="demo",
        sender_name="Naledi Mokoena",
        sender_email="naledi@example.com",
        company="Ubuntu Engineering",
        subject="Website redesign and client portal enquiry",
        body="We need a modern company website and secure client document portal. Our budget is around R45,000 and we hope to launch within eight weeks.",
    )
    return await process_enquiry(event)


@app.get("/v1/overview")
async def overview() -> dict:
    """Return Firestore-backed metrics and recent agent runs for the dashboard."""
    documents = list(
        firestore.Client()
        .collection("workflow_runs")
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .limit(50)
        .stream()
    )
    runs = []
    for document in documents:
        item = document.to_dict()
        created_at = item.get("created_at")
        if created_at:
            item["created_at"] = created_at.isoformat()
        runs.append(item)
    completed = sum(run.get("status") == "completed" for run in runs)
    estimated_hours = round(sum(run.get("action_count", 0) for run in runs) * 0.12, 1)
    return {
        "stats": {
            "workflows": len(runs),
            "hours_returned": estimated_hours,
            "qualified_leads": completed,
            "success_rate": round((completed / len(runs) * 100), 1) if runs else 0,
        },
        "runs": runs[:10],
    }


@app.post("/events/gmail", status_code=202)
async def gmail_pubsub(request: Request) -> dict:
    expected_audience = os.getenv("PUBSUB_PUSH_AUDIENCE")
    expected_email = os.getenv("PUBSUB_PUSH_SERVICE_ACCOUNT")
    if expected_audience:
        authorization = request.headers.get("authorization", "")
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing Pub/Sub identity token")
        try:
            token_info = id_token.verify_oauth2_token(
                authorization.removeprefix("Bearer ").strip(),
                GoogleAuthRequest(),
                expected_audience,
            )
        except (ValueError, TypeError) as exc:
            raise HTTPException(status_code=401, detail="Invalid Pub/Sub identity token") from exc
        if expected_email and token_info.get("email") != expected_email:
            raise HTTPException(status_code=403, detail="Unexpected Pub/Sub service account")

    envelope = await request.json()
    try:
        message = envelope["message"]
        raw = base64.b64decode(message["data"]).decode()
        data = json.loads(raw)
    except (KeyError, ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail="Invalid Pub/Sub envelope") from exc

    event_id = message.get("messageId") or sha256(raw.encode()).hexdigest()
    db = firestore.Client()
    marker = db.collection("event_receipts").document(event_id)
    receipt = marker.get().to_dict() or {}
    if receipt.get("status") in {"completed", "needs_review"}:
        return {"accepted": True, "duplicate": True, "event_id": event_id}
    marker.set({"status": "received", "payload": data}, merge=True)

    try:
        if "emailAddress" in data and "historyId" in data:
            events = resolve_gmail_notification(data)
        else:
            events = [EnquiryEvent(event_id=event_id, **data)]
        results = [await process_enquiry(event) for event in events]
        final_status = results[-1].status if results else "completed"
        marker.set(
            {"status": final_status, "run_ids": [result.run_id for result in results]},
            merge=True,
        )
        return {
            "accepted": True,
            "processed": len(results),
            "run_ids": [result.run_id for result in results],
        }
    except Exception as exc:
        marker.set({"status": "failed", "error": type(exc).__name__}, merge=True)
        raise


web_root = Path(os.getenv("WEB_ROOT", "/app/dashboard"))
if web_root.is_dir():
    app.mount("/", StaticFiles(directory=web_root, html=True), name="dashboard")
