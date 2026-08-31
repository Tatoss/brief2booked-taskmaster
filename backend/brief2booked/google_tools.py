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
    if not _demo():
        db = firestore.Client()
        db.collection("workflow_runs").document(run_id).collection("actions").document(action).set(result)
    return result


def create_proposal(run_id: str, client: str, proposal_markdown: str) -> dict:
    """Create a Google Doc proposal inside the configured Drive folder."""
    if _demo():
        return record_action(run_id, "proposal_created", {"title": f"Proposal — {client}", "document_id": "demo-proposal-001"})
    drive = _workspace_service("drive", "v3", ["https://www.googleapis.com/auth/drive.file"])
    metadata = {"name": f"Proposal — {client}", "mimeType": "application/vnd.google-apps.document"}
    folder = os.getenv("DRIVE_PROPOSALS_FOLDER_ID")
    if folder:
        metadata["parents"] = [folder]
    document = drive.files().create(body=metadata, fields="id,webViewLink").execute()
    return record_action(run_id, "proposal_created", {"document_id": document["id"], "url": document.get("webViewLink"), "content": proposal_markdown})


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
