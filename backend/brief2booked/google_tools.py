import base64
import os
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from typing import Any

from google.cloud import firestore
from google.oauth2 import service_account
from googleapiclient.discovery import build


def _demo() -> bool:
    return os.getenv("DEMO_MODE", "true").lower() == "true"


def _workspace_service(api: str, version: str, scopes: list[str]):
    credentials_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if credentials_file:
        credentials = service_account.Credentials.from_service_account_file(
            credentials_file, scopes=scopes
        )
        delegated_user = os.getenv("GOOGLE_WORKSPACE_USER")
        if delegated_user:
            credentials = credentials.with_subject(delegated_user)
        return build(api, version, credentials=credentials, cache_discovery=False)
    return build(api, version, cache_discovery=False)


def record_action(run_id: str, action: str, payload: dict[str, Any]) -> dict:
    """Append an auditable, idempotent action to Firestore."""
    result = {"action": action, "payload": payload, "created_at": datetime.now(timezone.utc).isoformat()}
    try:
        db = firestore.Client()
        db.collection("workflow_runs").document(run_id).collection("actions").document(action).set(result)
    except Exception:
        # Local demo runs may not have Google credentials. Cloud Run demo runs do,
        # so their audit trail is still persisted to the project's Firestore DB.
        if not _demo():
            raise
    return result


def record_workflow(
    run_id: str,
    status: str,
    event: dict[str, Any],
    decision: dict[str, Any],
    actions: list[dict],
) -> None:
    """Persist the queryable workflow summary used by the production dashboard."""
    document = {
        "run_id": run_id,
        "status": status,
        "source": event.get("source"),
        "company": event.get("company") or event.get("sender_name"),
        "contact": event.get("sender_name"),
        "sender_email": event.get("sender_email"),
        "subject": event.get("subject"),
        "service": decision.get("service"),
        "estimated_value_zar": decision.get("estimated_value_zar"),
        "fit_score": decision.get("fit_score"),
        "confidence": decision.get("confidence"),
        "action_count": len(actions),
        "created_at": firestore.SERVER_TIMESTAMP,
    }
    try:
        firestore.Client().collection("workflow_runs").document(run_id).set(document, merge=True)
    except Exception:
        if not _demo():
            raise


def create_proposal(run_id: str, client: str, proposal_markdown: str) -> dict:
    """Create a Google Doc proposal inside the configured Drive folder."""
    if _demo():
        return record_action(run_id, "proposal_created", {"title": f"Proposal — {client}", "document_id": "demo-proposal-001"})
    scopes = [
        "https://www.googleapis.com/auth/documents",
        "https://www.googleapis.com/auth/drive.file",
    ]
    docs = _workspace_service("docs", "v1", scopes)
    drive = _workspace_service("drive", "v3", scopes)
    document = docs.documents().create(body={"title": f"Proposal — {client}"}).execute()
    document_id = document["documentId"]
    docs.documents().batchUpdate(
        documentId=document_id,
        body={"requests": [{"insertText": {"location": {"index": 1}, "text": proposal_markdown}}]},
    ).execute()
    folder = os.getenv("DRIVE_PROPOSALS_FOLDER_ID")
    if folder:
        current = drive.files().get(fileId=document_id, fields="parents").execute()
        drive.files().update(
            fileId=document_id,
            addParents=folder,
            removeParents=",".join(current.get("parents", [])),
            fields="id,parents",
        ).execute()
    file_data = drive.files().get(fileId=document_id, fields="id,webViewLink").execute()
    return record_action(
        run_id,
        "proposal_created",
        {"document_id": document_id, "url": file_data.get("webViewLink")},
    )


def reserve_follow_up(run_id: str, client: str, attendee: str) -> dict:
    """Reserve the next discovery slot on Google Calendar."""
    start = (datetime.now(timezone.utc) + timedelta(days=2)).replace(hour=8, minute=30, second=0, microsecond=0)
    end = start + timedelta(minutes=30)
    if _demo():
        return record_action(run_id, "calendar_reserved", {"event_id": "demo-calendar-001", "start": start.isoformat(), "client": client})
    calendar = _workspace_service("calendar", "v3", ["https://www.googleapis.com/auth/calendar.events"])
    event = calendar.events().insert(calendarId="primary", body={
        "summary": f"Discovery call — {client}",
        "description": "Reserved autonomously by Brief2Booked; confirm before external notification.",
        "start": {"dateTime": start.isoformat(), "timeZone": "Africa/Johannesburg"},
        "end": {"dateTime": end.isoformat(), "timeZone": "Africa/Johannesburg"},
        "attendees": [{"email": attendee}],
        "guestsCanModify": False,
    }, sendUpdates="none").execute()
    return record_action(run_id, "calendar_reserved", {"event_id": event["id"], "url": event.get("htmlLink"), "start": start.isoformat()})


def draft_client_reply(run_id: str, recipient: str, subject: str, body: str) -> dict:
    """Create, but never automatically send, a Gmail reply draft."""
    if _demo():
        return record_action(run_id, "reply_drafted", {"draft_id": "demo-draft-001", "recipient": recipient, "subject": subject})
    gmail = _workspace_service("gmail", "v1", ["https://www.googleapis.com/auth/gmail.compose"])
    message = EmailMessage()
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)
    encoded = base64.urlsafe_b64encode(message.as_bytes()).decode()
    draft = gmail.users().drafts().create(userId="me", body={"message": {"raw": encoded}}).execute()
    return record_action(run_id, "reply_drafted", {"draft_id": draft["id"], "recipient": recipient, "subject": subject})


def create_delivery_tasks(run_id: str, client: str, service: str) -> dict:
    """Persist the delivery checklist used by the dashboard pipeline."""
    tasks = [f"Discovery for {client}", "Confirm scope", "Approve proposal", f"Deliver {service}", "Client handover"]
    return record_action(run_id, "tasks_created", {"tasks": tasks})
