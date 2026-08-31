import base64
import json
from hashlib import sha256

from fastapi import FastAPI, HTTPException, Request
from google.cloud import firestore

from .agent import process_enquiry
from .models import EnquiryEvent, WorkflowResult

app = FastAPI(title="Brief2Booked Agent API", version="1.0.0")


@app.get("/health")
async def health() -> dict:
    return {"status": "healthy", "agent": "brief2booked", "runtime": "cloud-run"}


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


@app.post("/events/gmail", status_code=202)
async def gmail_pubsub(request: Request) -> dict:
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
    if marker.get().exists:
        return {"accepted": True, "duplicate": True, "event_id": event_id}
    marker.create({"status": "received", "payload": data})

    # Gmail watch events contain a historyId. A production connector resolves the
    # changed message through Gmail history.list before publishing this normalized event.
    event = EnquiryEvent(event_id=event_id, **data)
    result = await process_enquiry(event)
    marker.update({"status": result.status, "run_id": result.run_id})
    return {"accepted": True, "run_id": result.run_id}
